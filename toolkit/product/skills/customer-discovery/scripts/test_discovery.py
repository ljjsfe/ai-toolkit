#!/usr/bin/env python3
"""Tests for discovery.py: folder resolution, append-only interviews, status merge rules and
the evidence cross-check."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discovery  # noqa: E402


def run(*args: str) -> tuple[int, str]:
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = discovery.main(list(args))
    return code, buf.getvalue()


class MergeRuleTests(unittest.TestCase):
    def test_combine_within_call(self) -> None:
        self.assertEqual(discovery.combine(["supported", "weakened"]), "weakened")
        self.assertEqual(discovery.combine(["supported", "killed", "weakened"]), "killed")
        self.assertEqual(discovery.combine(["untouched"]), "untouched")

    def test_merge_across_calls(self) -> None:
        self.assertEqual(discovery.merge("weakened", "supported"), "supported")  # later wins
        self.assertEqual(discovery.merge("killed", "supported"), "killed")       # sticky
        self.assertEqual(discovery.merge("supported", "untouched"), "supported")


class FolderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "disc"
        self.old = os.environ.get("DISCOVERY_DIR")
        os.environ["DISCOVERY_DIR"] = str(self.dir)
        run("init", "no-shows")
        self.notes = Path(self.tmp.name) / "n.md"
        self.notes.write_text('# call\n- [A1+] rung 13 "we built a spreadsheet"\n', encoding="utf-8")

    def tearDown(self) -> None:
        if self.old is None:
            os.environ.pop("DISCOVERY_DIR", None)
        else:
            os.environ["DISCOVERY_DIR"] = self.old
        self.tmp.cleanup()

    def test_home_default_uses_idea_slug(self) -> None:
        os.environ.pop("DISCOVERY_DIR")
        with tempfile.TemporaryDirectory() as cwd:
            old = Path.cwd()
            os.chdir(cwd)
            try:
                self.assertEqual(discovery.folder("No Shows!"), Path.home() / ".discovery" / "no-shows")
            finally:
                os.chdir(old)

    def test_init_never_overwrites(self) -> None:
        (self.dir / "decisions.md").write_text("mine\n", encoding="utf-8")
        _, out = run("init", "no-shows")
        self.assertIn("kept", out)
        self.assertEqual((self.dir / "decisions.md").read_text(encoding="utf-8"), "mine\n")

    def test_interviews_append_only(self) -> None:
        run("interview", "x", str(self.notes), "--date", "2026-11-01", "--role", "Clinic Manager")
        run("interview", "x", str(self.notes), "--date", "2026-11-01", "--role", "Clinic Manager")
        names = sorted(p.name for p in (self.dir / "interviews").iterdir())
        self.assertEqual(names, ["2026-11-01-clinic-manager-2.md", "2026-11-01-clinic-manager.md"])

    def test_verdict_flow_and_status(self) -> None:
        run("assume", "x", "--text", "managers track no-shows by hand", "--segment", "clinic manager",
            "--kill", "fewer than 2 of 5 track them", "--date", "2026-11-01")
        run("assume", "x", "--text", "they would pay", "--segment", "clinic manager",
            "--kill", "no pre-order", "--date", "2026-11-01")
        run("interview", "x", str(self.notes), "--date", "2026-11-02", "--role", "clinic manager")
        base = "2026-11-02-clinic-manager"
        run("verdict", "x", "A1=supported", "A2=supported", "A2=weakened", "--interview", base,
            "--date", "2026-11-02")
        _, rows, _ = discovery.read_rows(self.dir)
        self.assertEqual(rows[0][4:], ["supported", base, "2026-11-02"])
        self.assertEqual(rows[1][4:6], ["weakened", ""])  # no A2 tag in the file → no evidence link
        run("verdict", "x", "A1=killed", "--interview", base, "--date", "2026-11-03")
        run("verdict", "x", "A1=supported", "--interview", base, "--date", "2026-11-04")
        _, rows, _ = discovery.read_rows(self.dir)
        self.assertEqual(rows[0][4], "killed")
        code, out = run("status", "x")
        self.assertEqual(code, 1, out)  # A2 is weakened with no tagged evidence
        self.assertIn("riskiest: A2", out)
        self.assertIn("A2: error: status weakened with no tagged evidence", out)
        self.assertNotIn("A1: error", out)

    def test_status_flags_mismatch(self) -> None:
        run("assume", "x", "--text", "t", "--segment", "s", "--kill", "k")
        run("interview", "x", str(self.notes), "--date", "2026-11-02", "--role", "ops lead")
        code, out = run("status", "x")
        self.assertEqual(code, 1)
        self.assertIn("A1: cell [] vs tags ['2026-11-02-ops-lead']", out)

    def test_bad_date_refused_and_nothing_escapes(self) -> None:
        for bad in ("../../escaped", "2026-13-01", "2026-11-01/x"):
            with self.assertRaises(SystemExit):
                run("interview", "x", str(self.notes), "--date", bad, "--role", "ops lead")
        self.assertFalse((Path(self.tmp.name) / "escaped-ops-lead.md").exists())
        self.assertEqual(list((self.dir / "interviews").iterdir()), [])

    def test_verdict_interview_must_stay_inside(self) -> None:
        run("assume", "x", "--text", "t", "--segment", "s", "--kill", "k")
        (self.dir / "outside.md").write_text("[A1+]\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            run("verdict", "x", "A1=supported", "--interview", "../outside")

    def test_decide_escapes_pipes_and_newlines(self) -> None:
        run("decide", "x", "--decision", "ship a|b", "--verdict", "BUILD", "--because", "A1\nA2")
        last = (self.dir / "decisions.md").read_text(encoding="utf-8").splitlines()[-1]
        self.assertTrue(last.endswith("| ship a/b | BUILD | A1 A2 |"), last)
        self.assertEqual(last.count("|"), 5)

    def test_unknown_id_refused(self) -> None:
        run("interview", "x", str(self.notes), "--date", "2026-11-02", "--role", "ops lead")
        with self.assertRaises(SystemExit):
            run("verdict", "x", "A9=supported", "--interview", "2026-11-02-ops-lead")


if __name__ == "__main__":
    unittest.main()
