#!/usr/bin/env python3
"""Find the test that pollutes another test (order-dependent failure) or leaves an artefact behind.

Two modes, both driven by your own test command:

  Victim mode — a test passes alone but fails after others. Bisects the candidate tests:
    find_polluter.py --cmd "pytest -q {tests}" --victim tests/test_b.py -- tests/test_a.py tests/test_c.py ...

  Artefact mode — something (a file, a directory) appears after the suite runs. Runs each
  candidate alone, in order, and stops at the first one after which the path exists:
    find_polluter.py --cmd "npx vitest run {tests}" --artifact .git -- src/a.test.ts src/b.test.ts ...

Victim mode assumes the runner runs the tests serially in the order given on the command line.
pytest does by default (unless pytest-xdist or a random-order plugin is on — turn them off with
`-p no:xdist -p no:randomly` or similar); vitest and jest run files in parallel by default, so
pass their serial flag (`vitest run --no-file-parallelism`, `jest --runInBand`) inside --cmd.

`{tests}` in --cmd is replaced by the test paths as separate arguments (no shell is used). If it
is absent, the paths are appended. Exit code 0: polluter found; 1: not found; 2: bad set-up
(victim fails alone, failure does not reproduce, artefact already present, command not found).

The script never deletes anything; in artefact mode remove the artefact yourself before running.
Standard library only.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

Runner = Callable[[list[str]], bool]  # returns True when the command passed


class CommandNotFound(Exception):
    """The test command's executable does not exist."""


def build_argv(cmd: str, tests: Sequence[str]) -> list[str]:
    parts = shlex.split(cmd)
    if "{tests}" not in parts:
        return parts + list(tests)
    out: list[str] = []
    for p in parts:
        if p == "{tests}":
            out.extend(tests)
        else:
            out.append(p)
    return out


def make_runner(cmd: str, timeout: float | None) -> Runner:
    def run(tests: list[str]) -> bool:
        argv = build_argv(cmd, tests)
        try:
            res = subprocess.run(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False
        except FileNotFoundError as e:
            raise CommandNotFound(argv[0] if argv else cmd) from e
        return res.returncode == 0

    return run


def bisect_victim(run: Runner, victim: str, candidates: list[str], log: Callable[[str], None] = print) -> tuple[int, list[str]]:
    """Return (exit code, smallest candidate set found that still breaks the victim)."""
    cands = [c for c in candidates if c != victim]
    if not run([victim]):
        log(f"victim fails on its own — not an ordering problem: {victim}")
        return 2, []
    if run(cands + [victim]):
        log("victim passes after all candidates — the failure does not reproduce with this order")
        return 2, []
    steps = 0
    while len(cands) > 1:
        steps += 1
        half = len(cands) // 2
        first, second = cands[:half], cands[half:]
        if not run(first + [victim]):
            cands = first
        elif not run(second + [victim]):
            cands = second
        else:
            log(f"step {steps}: neither half alone breaks the victim — the polluters interact; smallest set: {len(cands)}")
            return 0, cands
        log(f"step {steps}: {len(cands)} candidate(s) left")
    log(f"polluter: {cands[0]}  (confirm: run it, then the victim, on its own)")
    return 0, cands


def scan_artifact(run: Runner, artifact: Path, candidates: list[str], log: Callable[[str], None] = print) -> tuple[int, list[str]]:
    if artifact.exists():
        log(f"artefact already present before any test ran — remove it first: {artifact}")
        return 2, []
    for i, test in enumerate(candidates, 1):
        run([test])
        if artifact.exists():
            log(f"[{i}/{len(candidates)}] polluter: {test} created {artifact}")
            return 0, [test]
    log(f"no single candidate created {artifact}")
    return 1, []


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cmd", required=True, help="test command; {tests} marks where test paths go")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--victim", help="test that passes alone and fails after others")
    mode.add_argument("--artifact", type=Path, help="path that should not exist after the tests")
    ap.add_argument("--timeout", type=float, default=None, help="seconds per run; a timeout counts as a failure")
    ap.add_argument("candidates", nargs="+", help="candidate tests, in the order the suite runs them")
    args = ap.parse_args(argv)
    run = make_runner(args.cmd, args.timeout)
    try:
        if args.victim:
            code, _ = bisect_victim(run, args.victim, list(args.candidates))
            return code
        code, _ = scan_artifact(run, args.artifact, list(args.candidates))
        return code
    except CommandNotFound as e:
        print(f"error: test command not found: {e} (check --cmd)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
