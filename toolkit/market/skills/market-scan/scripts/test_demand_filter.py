#!/usr/bin/env python3
"""Tests for demand_filter.py: each hard drop, each never-drop exception, and ordering."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import demand_filter as df  # noqa: E402

REAL = "We export every night with a 200-line shell script because the CLI cannot write CSV; it breaks on every release."


def issue(title: str, body: str = REAL, labels=(), r: int = 0, c: int = 0, n: int = 1) -> dict:
    return {"number": n, "title": title, "body": body, "labels": [{"name": x} for x in labels],
            "reactions": {"total_count": r}, "comments": c}


class IssueFilterTests(unittest.TestCase):
    def test_label_and_title_drops(self) -> None:
        self.assertEqual(df.drop_reason(issue("Add CSV export", labels=["Question"]), "issue"),
                         "label question")
        self.assertIn("support-question", df.drop_reason(issue("How do I enable CSV?"), "issue"))
        self.assertIn("support-question", df.drop_reason(issue("Failed to install on M1"), "issue"))
        self.assertIn("support-question", df.drop_reason(issue("Config problem with proxy"), "issue"))

    def test_body_drops(self) -> None:
        trace = "\n".join(f"    at Foo.bar (src/x.js:{i}:3)" for i in range(6))
        self.assertEqual(df.drop_reason(issue("Crash", body=trace), "issue"), "stack trace dump")
        self.assertEqual(df.drop_reason(issue("CSV please", body="+1"), "issue"), "thanks / +1 only")
        self.assertEqual(df.drop_reason(issue("CSV please", body=""), "issue"), "empty body")

    def test_wontfix_kept_as_confirmed_gap(self) -> None:
        for lab in ("wontfix", "works as intended"):
            it = issue("Native CSV export", labels=[lab])
            self.assertIsNone(df.drop_reason(it, "issue"))
            self.assertEqual(df.tag(it), "confirmed gap")
        self.assertEqual(df.tag(issue("Native CSV export")), "")

    def test_confirmed_gap_beats_ordinary_drop_rules(self) -> None:
        for it in (issue("How do I export CSV?", labels=["wontfix"]),
                   issue("Native CSV export", body="", labels=["not planned"]),
                   issue("Native CSV export", labels=["question", "won't fix"])):
            with self.subTest(title=it["title"]):
                self.assertIsNone(df.drop_reason(it, "issue"))
                self.assertEqual(df.tag(it), "confirmed gap")

    def test_workaround_kept(self) -> None:
        self.assertIsNone(df.drop_reason(issue("Native CSV export", r=40), "issue"))

    def test_four_stack_lines_kept(self) -> None:
        trace = REAL + "\n" + "\n".join(f"  at Foo.bar (x.js:{i}:1)" for i in range(4))
        self.assertIsNone(df.drop_reason(issue("Crash on export", body=trace), "issue"))


class PrFilterTests(unittest.TestCase):
    def test_maintenance_title_dropped_unless_popular(self) -> None:
        self.assertEqual(df.drop_reason(issue("docs: fix typo", r=3), "pr-open"), "maintenance PR title")
        self.assertIsNone(df.drop_reason(issue("Fix: add streaming export", r=25), "pr-open"))

    def test_rejected_pr_kept(self) -> None:
        self.assertIsNone(df.drop_reason(issue("fix: add CSV writer", r=2), "pr-rejected"))
        bot = dict(issue("bump deps", r=12, labels=["duplicate"]), user={"login": "dependabot[bot]"})
        self.assertIsNone(df.drop_reason(bot, "pr-rejected"))  # 10+ reactions on a rejected PR
        self.assertEqual(df.drop_reason(dict(bot, reactions={"total_count": 1}), "pr-rejected"),
                         "bot author")

    def test_bot_detection_not_substring(self) -> None:
        for login in ("abbott", "robotics-dev"):
            pr = dict(issue("Add streaming export", r=1), user={"login": login, "type": "User"})
            self.assertIsNone(df.drop_reason(pr, "pr-open"))
        app = dict(issue("Add streaming export", r=1), user={"login": "renovate", "type": "Bot"})
        self.assertEqual(df.drop_reason(app, "pr-open"), "bot author")

    def test_cli_orders_and_reports(self) -> None:
        items = [issue("Small", r=1, c=1, n=1), issue("Big", r=30, c=5, n=2),
                 issue("How to export?", n=3)]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "raw.json"
            p.write_text(json.dumps({"items": items}), encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                df.main([str(p)])
        lines = buf.getvalue().splitlines()
        self.assertEqual(lines[0], "kept 2 | dropped 1")
        self.assertTrue(lines[1].startswith("KEEP #2"))
        self.assertTrue(lines[3].startswith("DROP #3"))


if __name__ == "__main__":
    unittest.main()
