#!/usr/bin/env python3
"""Zero-dependency eval runner for agent-evals. It runs commands you supply; it never calls a
model itself.

Usage (all output is JSON):
  eval_run.py validate TASK.json
  eval_run.py run TASK.json --out DIR [--runs N] [--k K] [--seed S] [--keep]
  eval_run.py iterate TASK.json --arm NAME --out DIR [--max-iter N] [--patience P] [--keep]
  eval_run.py report DIR/results.json [--k K]

TASK.json (see references/eval-task-format.md for every field):
  {"name": "add-retry", "runs": 3, "timeout_s": 900,
   "workspace": {"repo": "/abs/repo", "commit": "abc1234"}  |  {"fixture": "/abs/dir"}  |  {},
   "arms": [{"name": "baseline", "command": ["claude", "-p", "..."]}, ...],
   "checks": [{"type": "command", "command": ["pytest", "-q"], "expect_exit": 0},
              {"type": "file_exists", "path": "src/x.py"},
              {"type": "file_contains", "path": "src/x.py", "pattern": "backoff"},
              {"type": "file_absent", "path": "NOTES.md"},
              {"type": "stdout_contains", "pattern": "DONE"}],
   "judge": {"command": ["python3", "/abs/hidden/judge.py"], "threshold": 7.0,
             "rubric": [{"name": "correctness", "weight": 0.6}, {"name": "clarity", "weight": 0.4}]}}

Commands are argv lists, run without a shell, with the run's workspace as cwd. Each command gets
EVAL_WORKDIR, EVAL_ARM, EVAL_RUN_ID, EVAL_USAGE_FILE and (iterate only) EVAL_FEEDBACK_FILE in its
environment. An arm that writes {"input_tokens", "output_tokens", "cost_usd"} JSON to
EVAL_USAGE_FILE gets those recorded; nothing is estimated.

The judge command prints JSON {"criteria": {"<name>": {"justification": "...", "score": N}}}.
A criterion without a non-empty justification, or with a score outside the rubric scale, fails
the judge. The weighted score is sum(weight*score)/sum(weight).

A run passes only when every deterministic check passes and, if a judge is set, the weighted
score reaches the threshold. Exit code: 0 ok, 1 task error or refused, 2 usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

CHECK_TYPES = {"command", "file_exists", "file_contains", "file_absent", "stdout_contains"}
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
OUTPUT_CAP = 200_000  # bytes of stdout/stderr kept per command


class TaskError(ValueError):
    pass


# ---------------------------------------------------------------- task file

def _argv(value: object, where: str) -> list[str]:
    if not isinstance(value, list) or not value or not all(isinstance(a, str) and a for a in value):
        raise TaskError(f"{where}: command must be a non-empty list of strings (argv, no shell)")
    return list(value)


def _rel_path(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise TaskError(f"{where}: path must be a non-empty string")
    p = Path(value)
    if p.is_absolute() or ".." in p.parts:
        raise TaskError(f"{where}: path must be relative to the workspace and contain no '..'")
    return value


def load_task(path: str | Path) -> dict:
    raw = Path(path).read_bytes()
    try:
        task = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TaskError(f"task file is not valid JSON: {exc}") from None
    if not isinstance(task, dict):
        raise TaskError("task file must be a JSON object")
    validate(task)
    task = dict(task)
    task["_sha256"] = hashlib.sha256(raw).hexdigest()
    return task


def validate(task: dict) -> None:
    if not isinstance(task.get("name"), str) or not NAME_RE.match(task["name"]):
        raise TaskError("name: required, letters/digits/._- only, at most 64 chars")
    runs = task.get("runs", 3)
    if not isinstance(runs, int) or not 1 <= runs <= 100:
        raise TaskError("runs: integer 1..100")
    timeout = task.get("timeout_s", 900)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise TaskError("timeout_s: positive number")
    ws = task.get("workspace", {})
    if not isinstance(ws, dict) or ("repo" in ws and "fixture" in ws):
        raise TaskError("workspace: an object with either repo (+ optional commit) or fixture, not both")
    for key in ("repo", "fixture"):
        if key in ws and not (isinstance(ws[key], str) and Path(ws[key]).is_dir()):
            raise TaskError(f"workspace.{key}: must be an existing directory")
    arms = task.get("arms")
    if not isinstance(arms, list) or not arms:
        raise TaskError("arms: a non-empty list")
    names = set()
    for i, arm in enumerate(arms):
        if not isinstance(arm, dict) or not isinstance(arm.get("name"), str) or not NAME_RE.match(arm["name"]):
            raise TaskError(f"arms[{i}].name: required, letters/digits/._- only")
        if arm["name"] in names:
            raise TaskError(f"arms[{i}].name: duplicate {arm['name']!r}")
        names.add(arm["name"])
        _argv(arm.get("command"), f"arms[{i}]")
    checks = task.get("checks")
    if not isinstance(checks, list) or not checks:
        raise TaskError("checks: at least one deterministic check is required")
    for i, chk in enumerate(checks):
        where = f"checks[{i}]"
        if not isinstance(chk, dict) or chk.get("type") not in CHECK_TYPES:
            raise TaskError(f"{where}.type: one of {sorted(CHECK_TYPES)}")
        if chk["type"] == "command":
            _argv(chk.get("command"), where)
        if chk["type"] in {"file_exists", "file_contains", "file_absent"}:
            _rel_path(chk.get("path"), where)
        if chk["type"] in {"file_contains", "stdout_contains"}:
            try:
                re.compile(chk.get("pattern", ""))
            except (re.error, TypeError):
                raise TaskError(f"{where}.pattern: a valid regular expression") from None
            if not chk.get("pattern"):
                raise TaskError(f"{where}.pattern: required")
    judge = task.get("judge")
    if judge is not None:
        if not isinstance(judge, dict):
            raise TaskError("judge: an object")
        _argv(judge.get("command"), "judge")
        rubric = judge.get("rubric")
        if not isinstance(rubric, list) or not rubric:
            raise TaskError("judge.rubric: a non-empty list of {name, weight}")
        for j, crit in enumerate(rubric):
            if not isinstance(crit, dict) or not isinstance(crit.get("name"), str) or not crit["name"]:
                raise TaskError(f"judge.rubric[{j}].name: required")
            w = crit.get("weight")
            if not isinstance(w, (int, float)) or w <= 0:
                raise TaskError(f"judge.rubric[{j}].weight: positive number")
        lo, hi = judge.get("scale", [1, 5])
        thr = judge.get("threshold")
        if not isinstance(thr, (int, float)) or not lo <= thr <= hi:
            raise TaskError(f"judge.threshold: a number on the scale {lo}..{hi}")


# ---------------------------------------------------------------- workspaces

def make_workspace(task: dict, run_id: str) -> tuple[Path, callable]:
    ws = task.get("workspace", {})
    base = Path(tempfile.mkdtemp(prefix=f"eval-{task['name']}-{run_id}-"))
    if "repo" in ws:
        target = base / "wt"
        commit = ws.get("commit", "HEAD")
        made = subprocess.run(["git", "-C", ws["repo"], "worktree", "add", "--detach", str(target), commit],
                              capture_output=True, text=True)
        if made.returncode != 0:
            shutil.rmtree(base, ignore_errors=True)
            raise TaskError(f"git worktree add failed for commit {commit!r}: {made.stderr.strip()[:200]}")

        def cleanup() -> None:
            subprocess.run(["git", "-C", ws["repo"], "worktree", "remove", "--force", str(target)],
                           capture_output=True, text=True)
            shutil.rmtree(base, ignore_errors=True)
        return target, cleanup
    target = base / "ws"
    if "fixture" in ws:
        shutil.copytree(ws["fixture"], target, symlinks=True)
    else:
        target.mkdir()
    return target, lambda: shutil.rmtree(base, ignore_errors=True)


def run_cmd(argv: list[str], cwd: Path, env: dict, timeout: float) -> dict:
    """Run argv (never through a shell) in its own process group; a timeout kills the whole group."""
    start = time.monotonic()
    try:
        proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
    except OSError as exc:
        out, err, code, timed_out = b"", f"could not start: {exc.strerror}".encode(), None, False
    else:
        try:
            out, err = proc.communicate(timeout=timeout)
            code, timed_out = proc.returncode, False
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError, AttributeError):
                proc.kill()
            out, err = proc.communicate()
            code, timed_out = None, True
    return {
        "exit": code,
        "timed_out": timed_out,
        "seconds": round(time.monotonic() - start, 3),
        "stdout": out[:OUTPUT_CAP].decode("utf-8", "replace"),
        "stderr": err[:OUTPUT_CAP].decode("utf-8", "replace"),
    }


# ---------------------------------------------------------------- grading

def apply_checks(checks: list[dict], ws: Path, arm_stdout: str, env: dict, timeout: float) -> list[dict]:
    results = []
    for chk in checks:
        kind = chk["type"]
        res = {"type": kind}
        if kind == "command":
            r = run_cmd(chk["command"], ws, env, timeout)
            res.update(command=chk["command"], exit=r["exit"], passed=r["exit"] == chk.get("expect_exit", 0))
        elif kind == "stdout_contains":
            res.update(pattern=chk["pattern"], passed=re.search(chk["pattern"], arm_stdout) is not None)
        else:
            target = ws / chk["path"]
            res["path"] = chk["path"]
            if kind == "file_exists":
                res["passed"] = target.is_file()
            elif kind == "file_absent":
                res["passed"] = not target.exists()
            else:
                text = target.read_text("utf-8", "replace") if target.is_file() else ""
                res.update(pattern=chk["pattern"], passed=re.search(chk["pattern"], text) is not None)
        results.append(res)
    return results


def score_judge(judge: dict, raw_stdout: str) -> dict:
    """Parse the judge's JSON and compute the weighted score. Rejects scores with no justification."""
    lo, hi = judge.get("scale", [1, 5])
    try:
        data = json.loads(raw_stdout)
        crits = data["criteria"]
        if not isinstance(crits, dict):
            raise TypeError
    except (json.JSONDecodeError, KeyError, TypeError):
        return {"ok": False, "error": "judge output is not {\"criteria\": {...}} JSON"}
    total = weight_sum = 0.0
    per = {}
    for crit in judge["rubric"]:
        entry = crits.get(crit["name"])
        if not isinstance(entry, dict):
            return {"ok": False, "error": f"criterion {crit['name']!r} missing"}
        just, score = entry.get("justification"), entry.get("score")
        if not isinstance(just, str) or not just.strip():
            return {"ok": False, "error": f"criterion {crit['name']!r} has no justification"}
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not lo <= score <= hi:
            return {"ok": False, "error": f"criterion {crit['name']!r} score outside {lo}..{hi}"}
        per[crit["name"]] = {"score": score, "weight": crit["weight"], "justification": just}
        total += crit["weight"] * score
        weight_sum += crit["weight"]
    weighted = round(total / weight_sum, 4)
    return {"ok": True, "weighted": weighted, "passed": weighted >= judge["threshold"], "criteria": per}


def grader_files(task: dict) -> list[Path]:
    """Absolute paths of existing files named in check and judge commands (the scripts that grade)."""
    argvs = [c["command"] for c in task["checks"] if c["type"] == "command"]
    if task.get("judge"):
        argvs.append(task["judge"]["command"])
    return sorted({Path(a) for argv in argvs for a in argv if os.path.isabs(a) and os.path.isfile(a)})


def fingerprint(paths: list[Path]) -> dict[str, str]:
    out = {}
    for p in paths:
        try:
            out[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            out[str(p)] = "unreadable"
    return out


def grade(task: dict, ws: Path, arm_result: dict, env: dict, before: dict[str, str] | None = None) -> dict:
    """Grade a finished arm. If a grader file changed while the arm ran, the run is void."""
    if before is not None:
        changed = [p for p, h in fingerprint([Path(x) for x in before]).items() if h != before[p]]
        if changed:
            return {"checks": [], "deterministic_pass": False, "passed": False,
                    "void": "grader files changed during the arm's run: " + ", ".join(changed)}
    timeout = task.get("timeout_s", 900)
    checks = apply_checks(task["checks"], ws, arm_result["stdout"], env, timeout)
    det_pass = all(c["passed"] for c in checks) and arm_result["exit"] == 0
    out = {"checks": checks, "deterministic_pass": det_pass}
    if task.get("judge"):
        j = run_cmd(task["judge"]["command"], ws, env, timeout)
        out["judge"] = score_judge(task["judge"], j["stdout"])
        out["judge"]["stderr_tail"] = j["stderr"][-2000:]
    out["passed"] = det_pass and (not task.get("judge") or out["judge"].get("passed", False))
    return out


def read_usage(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    keep = {k: data[k] for k in ("input_tokens", "output_tokens", "cost_usd")
            if isinstance(data.get(k), (int, float)) and not isinstance(data.get(k), bool)}
    return keep or None


# ---------------------------------------------------------------- metrics

def pass_at_k(n: int, c: int, k: int) -> float | None:
    """Unbiased estimate of P(at least one of k tries passes) from c passes in n runs."""
    if k > n:
        return None
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float | None:
    """Estimate of P(all k tries pass) from c passes in n runs."""
    if k > n:
        return None
    return math.comb(c, k) / math.comb(n, k)


def spread(values: list[float]) -> dict | None:
    if not values:
        return None
    return {"min": min(values), "median": statistics.median(values), "max": max(values), "n": len(values)}


def summarise(runs: list[dict], k: int) -> dict:
    arms: dict[str, list[dict]] = {}
    for r in runs:
        arms.setdefault(r["arm"], []).append(r)
    summary = {}
    for arm, rs in sorted(arms.items()):
        n, c = len(rs), sum(1 for r in rs if r["passed"])
        tokens = [u["input_tokens"] + u["output_tokens"] for r in rs
                  if (u := r.get("usage")) and "input_tokens" in u and "output_tokens" in u]
        costs = [r["usage"]["cost_usd"] for r in rs if r.get("usage") and "cost_usd" in r["usage"]]
        scores = [r["grade"]["judge"]["weighted"] for r in rs
                  if r["grade"].get("judge", {}).get("ok")]
        summary[arm] = {
            "n": n, "passes": c, "pass_rate": round(c / n, 4), "k": k,
            "pass_at_k": pass_at_k(n, c, k), "pass_hat_k": pass_hat_k(n, c, k),
            "seconds": spread([r["arm_result"]["seconds"] for r in rs]),
            "tokens": spread(tokens), "cost_usd": spread(costs), "judge_weighted": spread(scores),
            "timeouts": sum(1 for r in rs if r["arm_result"]["timed_out"]),
        }
    return summary


# ---------------------------------------------------------------- commands

def _prepare_out(out: Path, task: dict, overwrite: bool = False) -> Path:
    """Results are never replaced silently: an existing results.json needs --overwrite (same task only)."""
    results = out / "results.json"
    if results.exists() or (out / "runs").exists():
        prev = json.loads(results.read_text("utf-8")) if results.exists() else {}
        if prev and prev.get("task_sha256") != task["_sha256"]:
            raise TaskError("refused: the task file changed since results in this directory were "
                            "recorded; a changed eval is a new eval, use a new --out directory")
        if not overwrite:
            raise TaskError(f"refused: {out} already holds results; use a new --out, or --overwrite "
                            "to discard them")
        for sub in ("runs", "feedback"):
            shutil.rmtree(out / sub, ignore_errors=True)
        results.unlink(missing_ok=True)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    return results


def _env(ws: Path, arm: str, run_id: str, usage: Path, feedback: Path | None = None) -> dict:
    env = dict(os.environ, EVAL_WORKDIR=str(ws), EVAL_ARM=arm, EVAL_RUN_ID=run_id, EVAL_USAGE_FILE=str(usage))
    if feedback is not None:
        env["EVAL_FEEDBACK_FILE"] = str(feedback)
    return env


def cmd_run(task: dict, out: Path, runs: int, k: int, seed: int | None, keep: bool,
            overwrite: bool = False) -> dict:
    results_path = _prepare_out(out, task, overwrite)
    schedule = [arm for arm in task["arms"] for _ in range(runs)]
    random.Random(seed).shuffle(schedule)  # interleave arms in one batch
    records, mapping = [], {}
    doc = {"task": task["name"], "task_sha256": task["_sha256"], "mode": "run",
           "runs_per_arm": runs, "seed": seed, "complete": False}
    try:
        _run_schedule(task, out, schedule, keep, records, mapping)
        doc["complete"] = True
    finally:
        # a failure mid-batch still leaves every finished run on record, marked incomplete
        (out / "mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
        doc.update(runs=records, summary=summarise(records, k))
        results_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc


def _run_schedule(task: dict, out: Path, schedule: list[dict], keep: bool,
                  records: list[dict], mapping: dict) -> None:
    graders = grader_files(task)
    for i, arm in enumerate(schedule, 1):
        run_id = f"run-{i:03d}"
        run_dir = out / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        usage_file = run_dir / "usage.json"
        ws, cleanup = make_workspace(task, run_id)
        try:
            env = _env(ws, arm["name"], run_id, usage_file)
            before = fingerprint(graders)
            arm_result = run_cmd(arm["command"], ws, env, task.get("timeout_s", 900))
            graded = grade(task, ws, arm_result, env, before)
        finally:
            if keep:
                (run_dir / "workspace.txt").write_text(str(ws) + "\n", encoding="utf-8")
            else:
                cleanup()
        (run_dir / "stdout.txt").write_text(arm_result["stdout"], encoding="utf-8")
        (run_dir / "stderr.txt").write_text(arm_result["stderr"], encoding="utf-8")
        (run_dir / "grade.json").write_text(json.dumps(graded, indent=2), encoding="utf-8")
        mapping[run_id] = arm["name"]
        records.append({
            "run_id": run_id, "arm": arm["name"], "passed": graded["passed"], "grade": graded,
            "usage": read_usage(usage_file),
            "arm_result": {k2: arm_result[k2] for k2 in ("exit", "timed_out", "seconds")},
        })


def cmd_iterate(task: dict, arm_name: str, out: Path, max_iter: int, patience: int, keep: bool,
                overwrite: bool = False) -> dict:
    """Generator → judge → feedback loop in one workspace, until the threshold or a plateau."""
    if not task.get("judge"):
        raise TaskError("iterate needs a judge with a threshold")
    arm = next((a for a in task["arms"] if a["name"] == arm_name), None)
    if arm is None:
        raise TaskError(f"no arm named {arm_name!r}")
    results_path = _prepare_out(out, task, overwrite)
    (out / "feedback").mkdir(exist_ok=True)
    graders = grader_files(task)
    ws, cleanup = make_workspace(task, "iter")
    iterations, best, since_best, stop = [], None, 0, "max_iter"
    try:
        for i in range(1, max_iter + 1):
            run_dir = out / "runs" / f"iter-{i:03d}"
            run_dir.mkdir(parents=True, exist_ok=True)
            # feedback lives apart from grade.json (which holds the rubric weights); keeping the generator
            # from reading the out directory at all needs a sandbox or a separate user
            feedback = out / "feedback" / f"iter-{i - 1:03d}.json"
            env = _env(ws, arm_name, f"iter-{i:03d}", run_dir / "usage.json", feedback if i > 1 else None)
            before = fingerprint(graders)
            arm_result = run_cmd(arm["command"], ws, env, task.get("timeout_s", 900))
            graded = grade(task, ws, arm_result, env, before)
            if graded.get("void"):
                (run_dir / "grade.json").write_text(json.dumps(graded, indent=2), encoding="utf-8")
                stop = "void"
                iterations.append({"iteration": i, "passed": False, "weighted": None, "void": graded["void"]})
                break
            # feedback for the next round: failed checks and the judge's justifications, never the rubric weights
            fb = {"failed_checks": [c for c in graded["checks"] if not c["passed"]],
                  "judge": {n: {"score": v["score"], "justification": v["justification"]}
                            for n, v in graded.get("judge", {}).get("criteria", {}).items()}}
            (out / "feedback" / f"iter-{i:03d}.json").write_text(json.dumps(fb, indent=2), encoding="utf-8")
            (run_dir / "grade.json").write_text(json.dumps(graded, indent=2), encoding="utf-8")
            score = graded["judge"].get("weighted") if graded["judge"].get("ok") else None
            iterations.append({"iteration": i, "passed": graded["passed"], "weighted": score,
                               "usage": read_usage(run_dir / "usage.json"),
                               "seconds": arm_result["seconds"]})
            if graded["passed"]:
                stop = "threshold"
                break
            if score is not None and (best is None or score > best):
                best, since_best = score, 0
            else:
                since_best += 1
            if since_best >= patience:
                stop = "plateau"
                break
    finally:
        if keep:
            (out / "workspace.txt").write_text(str(ws) + "\n", encoding="utf-8")
        else:
            cleanup()
    doc = {"task": task["name"], "task_sha256": task["_sha256"], "mode": "iterate", "arm": arm_name,
           "threshold": task["judge"]["threshold"], "stopped": stop, "iterations": iterations}
    results_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("task")
    r = sub.add_parser("run"); r.add_argument("task"); r.add_argument("--out", required=True)
    r.add_argument("--runs", type=int); r.add_argument("--k", type=int)
    r.add_argument("--seed", type=int); r.add_argument("--keep", action="store_true")
    r.add_argument("--overwrite", action="store_true", help="discard earlier results in --out (same task only)")
    it = sub.add_parser("iterate"); it.add_argument("task"); it.add_argument("--arm", required=True)
    it.add_argument("--out", required=True); it.add_argument("--max-iter", type=int, default=5)
    it.add_argument("--patience", type=int, default=3); it.add_argument("--keep", action="store_true")
    it.add_argument("--overwrite", action="store_true", help="discard earlier results in --out (same task only)")
    rp = sub.add_parser("report"); rp.add_argument("results"); rp.add_argument("--k", type=int)
    try:
        args = ap.parse_args(argv)
    except SystemExit as exc:
        return 2 if exc.code else 0
    try:
        if args.cmd == "report":
            doc = json.loads(Path(args.results).read_text("utf-8"))
            if doc.get("mode") != "run":
                raise TaskError("report reads results.json from a run, not an iterate")
            k = args.k or doc["runs_per_arm"]
            print(json.dumps(summarise(doc["runs"], k), indent=2))
            return 0
        task = load_task(args.task)
        if args.cmd == "validate":
            print(json.dumps({"ok": True, "task": task["name"], "sha256": task["_sha256"]}))
            return 0
        if args.cmd == "run":
            runs = args.runs or task.get("runs", 3)
            k = args.k or runs
            if not 1 <= k <= runs:
                raise TaskError("--k must be between 1 and the number of runs")
            doc = cmd_run(task, Path(args.out), runs, k, args.seed, args.keep, args.overwrite)
            print(json.dumps(doc["summary"], indent=2))
            return 0
        doc = cmd_iterate(task, args.arm, Path(args.out), args.max_iter, args.patience, args.keep, args.overwrite)
        print(json.dumps({k2: doc[k2] for k2 in ("stopped", "threshold", "iterations")}, indent=2))
        return 0
    except (TaskError, OSError, subprocess.CalledProcessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
