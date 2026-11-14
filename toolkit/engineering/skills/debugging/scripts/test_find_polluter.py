#!/usr/bin/env python3
"""Tests for find_polluter.py with fake runners (no real test suite is executed)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import find_polluter as fp  # noqa: E402


def quiet(_msg: str) -> None:
    pass


def victim_runner(victim: str, polluters: set[str], needs_all: bool = False):
    """Victim fails when it runs after any (or, with needs_all, every) polluter in the same run."""
    calls: list[list[str]] = []

    def run(tests: list[str]) -> bool:
        calls.append(list(tests))
        if victim not in tests:
            return True
        before = set(tests[: tests.index(victim)])
        hit = polluters <= before if needs_all else bool(polluters & before)
        return not hit

    return run, calls


class BuildArgv(unittest.TestCase):
    def test_placeholder_expands_to_separate_args(self):
        self.assertEqual(fp.build_argv("pytest -q {tests} -x", ["a b.py", "c.py"]), ["pytest", "-q", "a b.py", "c.py", "-x"])

    def test_no_placeholder_appends(self):
        self.assertEqual(fp.build_argv("npm test --", ["a"]), ["npm", "test", "--", "a"])


class Victim(unittest.TestCase):
    def test_finds_single_polluter_among_many(self):
        cands = [f"t{i}" for i in range(37)]
        run, calls = victim_runner("v", {"t23"})
        code, found = fp.bisect_victim(run, "v", cands, log=quiet)
        self.assertEqual((code, found), (0, ["t23"]))
        self.assertLess(len(calls), 20)  # bisection, not one run per candidate

    def test_victim_failing_alone_is_setup_error(self):
        code, found = fp.bisect_victim(lambda tests: False, "v", ["a", "b"], log=quiet)
        self.assertEqual((code, found), (2, []))

    def test_no_reproduction_is_setup_error(self):
        run, _ = victim_runner("v", set())
        self.assertEqual(fp.bisect_victim(run, "v", ["a", "b"], log=quiet), (2, []))

    def test_interacting_polluters_return_smallest_set(self):
        cands = ["a", "b", "c", "d"]
        run, _ = victim_runner("v", {"a", "d"}, needs_all=True)
        code, found = fp.bisect_victim(run, "v", cands, log=quiet)
        self.assertEqual(code, 0)
        self.assertTrue({"a", "d"} <= set(found))

    def test_victim_excluded_from_candidates(self):
        run, calls = victim_runner("v", {"b"})
        code, found = fp.bisect_victim(run, "v", ["a", "v", "b"], log=quiet)
        self.assertEqual(found, ["b"])
        self.assertTrue(all(c.count("v") == 1 for c in calls))


class Artifact(unittest.TestCase):
    def test_finds_creator_and_stops(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "leak"
            ran: list[str] = []

            def run(tests: list[str]) -> bool:
                ran.extend(tests)
                if tests == ["c"]:
                    target.write_text("x")
                return True

            self.assertEqual(fp.scan_artifact(run, target, ["a", "b", "c", "d"], log=quiet), (0, ["c"]))
            self.assertEqual(ran, ["a", "b", "c"])

    def test_existing_artifact_refuses(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(fp.scan_artifact(lambda t: True, Path(d), ["a"], log=quiet), (2, []))

    def test_not_found(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(fp.scan_artifact(lambda t: True, Path(d) / "nope", ["a"], log=quiet), (1, []))


class Cli(unittest.TestCase):
    def test_end_to_end_with_real_subprocess(self):
        with tempfile.TemporaryDirectory() as d:
            flag = Path(d) / "polluted"
            script = Path(d) / "fake_suite.py"
            # Each arg is a test name; "dirty" pollutes, "victim" fails if polluted in this run.
            script.write_text(
                "import sys, pathlib\n"
                f"flag = pathlib.Path({str(flag)!r})\n"
                "flag.unlink(missing_ok=True)\n"
                "for t in sys.argv[1:]:\n"
                "    if t == 'dirty': flag.write_text('1')\n"
                "    if t == 'victim' and flag.exists(): sys.exit(1)\n"
            )
            cmd = f"{sys.executable} {script} {{tests}}"
            self.assertEqual(fp.main(["--cmd", cmd, "--victim", "victim", "clean1", "dirty", "clean2"]), 0)

    def test_missing_command_is_clean_setup_error(self):
        import contextlib
        import io
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = fp.main(["--cmd", "no-such-runner-xyz {tests}", "--victim", "v", "a", "b"])
        self.assertEqual(code, 2)
        self.assertIn("test command not found: no-such-runner-xyz", err.getvalue())


if __name__ == "__main__":
    unittest.main()
