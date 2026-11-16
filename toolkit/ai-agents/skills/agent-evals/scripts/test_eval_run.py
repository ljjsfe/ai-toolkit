#!/usr/bin/env python3
"""Tests for eval_run.py. Arms and judges are tiny Python one-liners; no model is called."""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import eval_run  # noqa: E402

PY = sys.executable


def py(code: str) -> list[str]:
    return [PY, "-c", code]


WRITE_OK = py("open('out.txt','w').write('hello backoff')")
WRITE_BAD = py("open('out.txt','w').write('nope')")
# passes on even-numbered runs: decided by the run id so the result is deterministic
FLAKY = py("import os; n=int(os.environ['EVAL_RUN_ID'][-3:]); "
           "open('out.txt','w').write('hello backoff' if n % 2 == 0 else 'x')")
USAGE = py("import os,json; open('out.txt','w').write('hello backoff'); "
           "json.dump({'input_tokens':100,'output_tokens':20,'cost_usd':0.01}, open(os.environ['EVAL_USAGE_FILE'],'w'))")


def judge_cmd(score: float, justification: str = "it handles the case") -> list[str]:
    payload = {"criteria": {"correctness": {"justification": justification, "score": score},
                            "clarity": {"justification": justification, "score": score}}}
    return py(f"print({json.dumps(json.dumps(payload))})")


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.fixture = self.tmp / "fixture"
        self.fixture.mkdir()
        (self.fixture / "README").write_text("seed\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def task(self, **over) -> Path:
        t = {"name": "demo", "runs": 2, "timeout_s": 30, "workspace": {"fixture": str(self.fixture)},
             "arms": [{"name": "good", "command": WRITE_OK}, {"name": "bad", "command": WRITE_BAD}],
             "checks": [{"type": "file_exists", "path": "out.txt"},
                        {"type": "file_contains", "path": "out.txt", "pattern": "backoff"},
                        {"type": "file_absent", "path": "NOTES.md"}]}
        t.update(over)
        p = self.tmp / "task.json"
        p.write_text(json.dumps(t))
        return p

    def quiet(self, args: list[str]) -> int:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return eval_run.main(args)


class ValidateTests(Base):
    def test_requires_a_deterministic_check(self) -> None:
        with self.assertRaisesRegex(eval_run.TaskError, "deterministic"):
            eval_run.load_task(self.task(checks=[]))

    def test_rejects_shell_string_commands(self) -> None:
        with self.assertRaisesRegex(eval_run.TaskError, "argv"):
            eval_run.load_task(self.task(arms=[{"name": "a", "command": "echo hi"}]))

    def test_rejects_paths_leaving_workspace(self) -> None:
        with self.assertRaisesRegex(eval_run.TaskError, "relative"):
            eval_run.load_task(self.task(checks=[{"type": "file_exists", "path": "../x"}]))

    def test_threshold_must_be_on_scale(self) -> None:
        judge = {"command": judge_cmd(5), "threshold": 11, "rubric": [{"name": "c", "weight": 1}]}
        with self.assertRaisesRegex(eval_run.TaskError, "threshold"):
            eval_run.load_task(self.task(judge=judge))


class MetricTests(unittest.TestCase):
    def test_pass_at_k_and_pass_hat_k(self) -> None:
        self.assertAlmostEqual(eval_run.pass_at_k(4, 2, 2), 1 - 1 / 6)
        self.assertAlmostEqual(eval_run.pass_hat_k(4, 2, 2), 1 / 6)
        self.assertEqual(eval_run.pass_at_k(3, 0, 3), 0.0)
        self.assertEqual(eval_run.pass_hat_k(3, 3, 3), 1.0)
        self.assertEqual(eval_run.pass_at_k(5, 4, 3), 1.0)
        self.assertIsNone(eval_run.pass_at_k(2, 1, 3))

    def test_judge_requires_justification_and_scale(self) -> None:
        judge = {"scale": [1, 10], "threshold": 7, "rubric": [{"name": "a", "weight": 3}, {"name": "b", "weight": 1}]}
        ok = eval_run.score_judge(judge, json.dumps({"criteria": {
            "a": {"justification": "x", "score": 8}, "b": {"justification": "y", "score": 4}}}))
        self.assertEqual(ok["weighted"], 7.0)
        self.assertTrue(ok["passed"])
        nojust = eval_run.score_judge(judge, json.dumps({"criteria": {
            "a": {"justification": " ", "score": 8}, "b": {"justification": "y", "score": 4}}}))
        self.assertFalse(nojust["ok"])
        off = eval_run.score_judge(judge, json.dumps({"criteria": {
            "a": {"justification": "x", "score": 80}, "b": {"justification": "y", "score": 4}}}))
        self.assertFalse(off["ok"])
        self.assertFalse(eval_run.score_judge(judge, "not json")["ok"])


class RunTests(Base):
    def test_run_records_layout_and_summary(self) -> None:
        out = self.tmp / "res"
        self.assertEqual(self.quiet(["run", str(self.task()), "--out", str(out), "--seed", "1"]), 0)
        doc = json.loads((out / "results.json").read_text())
        s = doc["summary"]
        self.assertEqual((s["good"]["passes"], s["bad"]["passes"]), (2, 0))
        self.assertEqual(s["good"]["pass_hat_k"], 1.0)
        self.assertEqual(s["bad"]["pass_at_k"], 0.0)
        mapping = json.loads((out / "mapping.json").read_text())
        self.assertEqual(sorted(mapping), ["run-001", "run-002", "run-003", "run-004"])
        for run_id in mapping:
            for f in ("stdout.txt", "stderr.txt", "grade.json"):
                self.assertTrue((out / "runs" / run_id / f).is_file())
        # workspaces are isolated: the fixture was never written to
        self.assertFalse((self.fixture / "out.txt").exists())

    def test_flaky_arm_separates_pass_at_k_from_pass_hat_k(self) -> None:
        out = self.tmp / "res"
        task = self.task(runs=4, arms=[{"name": "flaky", "command": FLAKY}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out), "--k", "2"]), 0)
        s = json.loads((out / "results.json").read_text())["summary"]["flaky"]
        self.assertEqual(s["passes"], 2)
        self.assertGreater(s["pass_at_k"], s["pass_hat_k"])

    def test_usage_is_recorded_only_when_reported(self) -> None:
        out = self.tmp / "res"
        task = self.task(arms=[{"name": "u", "command": USAGE}, {"name": "good", "command": WRITE_OK}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        s = json.loads((out / "results.json").read_text())["summary"]
        self.assertEqual(s["u"]["tokens"]["median"], 120)
        self.assertIsNone(s["good"]["tokens"])

    def test_command_check_and_judge_gate(self) -> None:
        out = self.tmp / "res"
        judge = {"command": judge_cmd(6), "scale": [1, 10], "threshold": 7,
                 "rubric": [{"name": "correctness", "weight": 2}, {"name": "clarity", "weight": 1}]}
        checks = [{"type": "command", "command": py("import sys; sys.exit(0)")}]
        task = self.task(runs=1, arms=[{"name": "good", "command": WRITE_OK}], checks=checks, judge=judge)
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        run = json.loads((out / "results.json").read_text())["runs"][0]
        self.assertTrue(run["grade"]["deterministic_pass"])
        self.assertFalse(run["passed"])  # judge 6 < threshold 7

    def test_changed_task_is_refused_in_same_out_dir(self) -> None:
        out = self.tmp / "res"
        self.assertEqual(self.quiet(["run", str(self.task(runs=1)), "--out", str(out)]), 0)
        self.assertEqual(self.quiet(["run", str(self.task(runs=2)), "--out", str(out)]), 1)

    def test_existing_results_are_not_overwritten_without_flag(self) -> None:
        out = self.tmp / "res"
        task = self.task(runs=1)
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        first = (out / "results.json").read_text()
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 1)
        self.assertEqual((out / "results.json").read_text(), first)
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out), "--overwrite"]), 0)

    def test_grader_edited_by_the_arm_voids_the_run(self) -> None:
        out = self.tmp / "res"
        grader = self.tmp / "grader.py"
        grader.write_text("import sys; sys.exit(1)\n")
        cheat = py(f"open({str(grader)!r},'w').write('import sys; sys.exit(0)')")
        task = self.task(runs=1, arms=[{"name": "cheat", "command": cheat}],
                         checks=[{"type": "command", "command": [PY, str(grader)]}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        run = json.loads((out / "results.json").read_text())["runs"][0]
        self.assertFalse(run["passed"])
        self.assertIn("grader files changed", run["grade"]["void"])

    def test_grader_tampering_voids_every_later_run(self) -> None:
        # run 1 rewrites the grader; run 2 must not baseline on the corrupted grader and pass
        out = self.tmp / "res"
        grader = self.tmp / "grader.py"
        grader.write_text("import sys; sys.exit(1)\n")
        cheat = py(f"open({str(grader)!r},'w').write('import sys; sys.exit(0)')")
        task = self.task(runs=3, arms=[{"name": "cheat", "command": cheat}],
                         checks=[{"type": "command", "command": [PY, str(grader)]}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        doc = json.loads((out / "results.json").read_text())
        self.assertFalse(any(run["passed"] for run in doc["runs"]))
        self.assertEqual(len(doc["runs"]), 1)  # batch aborted after the void run
        self.assertIn("grader files changed", doc["runs"][0]["grade"]["void"])
        self.assertFalse(doc["complete"])
        self.assertIn("not executed", doc["aborted"])

    def test_relative_out_dir_reaches_the_arm(self) -> None:
        # EVAL_USAGE_FILE must stay valid from the arm's cwd (the temp workspace)
        task = self.task(runs=1, arms=[{"name": "u", "command": USAGE}])
        saved = Path.cwd()
        os.chdir(self.tmp)
        try:
            self.assertEqual(self.quiet(["run", str(task), "--out", "rel/res"]), 0)
        finally:
            os.chdir(saved)
        doc = json.loads((self.tmp / "rel" / "res" / "results.json").read_text())
        self.assertTrue(doc["runs"][0]["passed"])
        self.assertEqual(doc["summary"]["u"]["tokens"]["median"], 120)

    def test_judge_must_exit_zero(self) -> None:
        payload = {"criteria": {"c": {"justification": "fine", "score": 9}}}
        failing = py(f"import sys; print({json.dumps(json.dumps(payload))}); sys.exit(1)")
        out = self.tmp / "res"
        task = self.task(runs=1, arms=[{"name": "good", "command": WRITE_OK}],
                         judge={"command": failing, "scale": [1, 10], "threshold": 7,
                                "rubric": [{"name": "c", "weight": 1}]})
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        run = json.loads((out / "results.json").read_text())["runs"][0]
        self.assertFalse(run["grade"]["judge"]["ok"])
        self.assertFalse(run["passed"])

    def test_judge_timeout_fails_even_after_printing(self) -> None:
        payload = {"criteria": {"c": {"justification": "fine", "score": 9}}}
        slow = py(f"import sys,time; print({json.dumps(json.dumps(payload))}, flush=True); time.sleep(5)")
        out = self.tmp / "res"
        task = self.task(runs=1, timeout_s=1, arms=[{"name": "good", "command": WRITE_OK}],
                         judge={"command": slow, "scale": [1, 10], "threshold": 7,
                                "rubric": [{"name": "c", "weight": 1}]})
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        run = json.loads((out / "results.json").read_text())["runs"][0]
        self.assertFalse(run["grade"]["judge"]["ok"])
        self.assertFalse(run["passed"])

    def test_bad_commit_leaves_no_temp_dir_and_marks_results_incomplete(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        repo = self.tmp / "repo2"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        out = self.tmp / "res"
        # a private temp root, so parallel runs of this suite cannot add or remove eval-demo-* dirs
        private = self.tmp / "tmproot"
        private.mkdir()
        saved, tempfile.tempdir = tempfile.tempdir, str(private)
        try:
            task = self.task(runs=1, workspace={"repo": str(repo), "commit": "no-such-ref"})
            self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 1)
            self.assertEqual(list(private.glob("eval-demo-*")), [])
        finally:
            tempfile.tempdir = saved
        self.assertFalse(json.loads((out / "results.json").read_text())["complete"])

    def test_timeout_kills_child_processes(self) -> None:
        marker = self.tmp / "survived"
        child = f"import time; time.sleep(2); open({str(marker)!r},'w').write('x')"
        parent = py(f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{child!r}]); time.sleep(10)")
        r = eval_run.run_cmd(parent, self.tmp, dict(__import__('os').environ), 0.5)
        self.assertTrue(r["timed_out"])
        __import__("time").sleep(2.5)
        self.assertFalse(marker.exists())

    def test_timeout_is_recorded_as_failure(self) -> None:
        out = self.tmp / "res"
        task = self.task(runs=1, timeout_s=0.5, arms=[{"name": "slow", "command": py("import time; time.sleep(5)")}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        s = json.loads((out / "results.json").read_text())["summary"]["slow"]
        self.assertEqual((s["passes"], s["timeouts"]), (0, 1))

    def test_git_worktree_workspace(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git not installed")
        repo = self.tmp / "repo"
        repo.mkdir()
        for cmd in (["init", "-q"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"]):
            subprocess.run(["git", "-C", str(repo), *cmd], check=True)
        (repo / "a.txt").write_text("a\n")
        subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-qm", "init"], check=True)
        out = self.tmp / "res"
        task = self.task(runs=1, workspace={"repo": str(repo)}, arms=[{"name": "good", "command": WRITE_OK}],
                         checks=[{"type": "file_exists", "path": "a.txt"}, {"type": "file_exists", "path": "out.txt"}])
        self.assertEqual(self.quiet(["run", str(task), "--out", str(out)]), 0)
        self.assertEqual(json.loads((out / "results.json").read_text())["summary"]["good"]["passes"], 1)
        self.assertFalse((repo / "out.txt").exists())
        wt = subprocess.run(["git", "-C", str(repo), "worktree", "list"], capture_output=True, text=True).stdout
        self.assertEqual(len(wt.strip().splitlines()), 1)  # worktree removed after the run


class IterateTests(Base):
    def test_stops_at_threshold_and_passes_feedback(self) -> None:
        # the generator scores 5 until it sees a feedback file, then the judge scores 8
        gen = py("import os; fb=os.environ.get('EVAL_FEEDBACK_FILE'); "
                 "open('out.txt','w').write('backoff'); "
                 "open('round.txt','w').write('2' if fb and os.path.exists(fb) else '1')")
        judge = py("import json; r=open('round.txt').read(); s=8 if r=='2' else 5; "
                   "print(json.dumps({'criteria':{'c':{'justification':'reads round','score':s}}}))")
        task = self.task(arms=[{"name": "gen", "command": gen}],
                         judge={"command": judge, "scale": [1, 10], "threshold": 7, "rubric": [{"name": "c", "weight": 1}]})
        out = self.tmp / "res"
        self.assertEqual(self.quiet(["iterate", str(task), "--arm", "gen", "--out", str(out)]), 0)
        doc = json.loads((out / "results.json").read_text())
        self.assertEqual(doc["stopped"], "threshold")
        self.assertEqual([i["weighted"] for i in doc["iterations"]], [5.0, 8.0])
        fb = json.loads((out / "feedback" / "iter-001.json").read_text())
        self.assertNotIn("weight", json.dumps(fb))  # feedback carries justifications, not the rubric

    def test_stops_on_plateau(self) -> None:
        task = self.task(arms=[{"name": "gen", "command": WRITE_OK}],
                         judge={"command": judge_cmd(4), "scale": [1, 10], "threshold": 7,
                                "rubric": [{"name": "correctness", "weight": 1}, {"name": "clarity", "weight": 1}]})
        out = self.tmp / "res"
        self.assertEqual(self.quiet(["iterate", str(task), "--arm", "gen", "--out", str(out),
                                     "--max-iter", "10", "--patience", "2"]), 0)
        doc = json.loads((out / "results.json").read_text())
        self.assertEqual(doc["stopped"], "plateau")
        self.assertEqual(len(doc["iterations"]), 3)

    def test_grader_baseline_is_taken_before_the_loop(self) -> None:
        # round 1's arm plants workspace code that the grader executes (as pytest runs conftest.py),
        # so the grader is rewritten after round 1's tamper check; round 2 must not re-baseline on it
        grader = self.tmp / "grader.py"
        grader.write_text("import os, sys\nos.path.exists('hook.py') and exec(open('hook.py').read())\n"
                          "sys.exit(0)\n")
        hook_src = f"open({str(grader)!r}, 'a').write('# tampered\\n')\n"
        plant = py(f"open('out.txt','w').write('backoff'); open('hook.py','w').write({hook_src!r})")
        task = self.task(arms=[{"name": "gen", "command": plant}],
                         checks=[{"type": "command", "command": [PY, str(grader)]}],
                         judge={"command": judge_cmd(4), "scale": [1, 10], "threshold": 7,
                                "rubric": [{"name": "correctness", "weight": 1}, {"name": "clarity", "weight": 1}]})
        out = self.tmp / "res"
        self.assertEqual(self.quiet(["iterate", str(task), "--arm", "gen", "--out", str(out),
                                     "--max-iter", "5", "--patience", "5"]), 0)
        doc = json.loads((out / "results.json").read_text())
        self.assertEqual(doc["stopped"], "void")
        self.assertEqual(len(doc["iterations"]), 2)


class ReportTests(Base):
    def test_report_recomputes_with_other_k(self) -> None:
        out = self.tmp / "res"
        task = self.task(runs=4, arms=[{"name": "flaky", "command": FLAKY}])
        self.quiet(["run", str(task), "--out", str(out)])
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(eval_run.main(["report", str(out / "results.json"), "--k", "1"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["flaky"]["pass_at_k"], 0.5)


if __name__ == "__main__":
    unittest.main()
