#!/usr/bin/env python3
"""Tests for upstream_drift.py; the GitHub API is replaced by a fake."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import upstream_drift as ud  # noqa: E402


class ParseTests(unittest.TestCase):
    def test_brace_expansion(self) -> None:
        self.assertEqual(ud.expand_braces("a/{x,y}.md"), ["a/x.md", "a/y.md"])
        self.assertEqual(ud.expand_braces("{p,q}/{1,2}"), ["p/1", "p/2", "q/1", "q/2"])

    def test_credited_paths(self) -> None:
        got = ud.credited_paths([
            'upstream/gstack/{review,cso} (MIT) — x [port "abcdefghijklm"]',
            "upstream/{blader-humanizer,op7418-humanizer-zh} (MIT) — y [idea]",
            "upstream/vila-lab/docs/architecture.md (CC BY-NC-SA 4.0) — z [idea]",
        ])
        self.assertEqual(got["gstack"], {"review", "cso"})
        self.assertEqual(got["blader-humanizer"], {""})
        self.assertEqual(got["vila-lab"], {"docs/architecture.md"})


def fake_api(existing: set[str], commits: dict[str, list[dict]]):
    def api(args: list[str]) -> tuple[int, str]:
        q = args[0]
        if "/contents/" in q:
            return (0, "{}") if q.split("/contents/")[1] in existing else (1, "Not Found")
        path = q.split("&path=")[1].split("&")[0] if "&path=" in q else ""
        return 0, json.dumps(commits.get(path, []))
    return api


def commit(sha: str, msg: str) -> dict:
    return {"sha": sha * 10, "commit": {"message": msg, "committer": {"date": "2026-11-20T00:00:00Z"}}}


class DriftTests(unittest.TestCase):
    entry = {"repo": "o/r", "reviewed_on": "2026-11-14"}

    def test_removed_path_is_reported(self) -> None:
        r = ud.drift("gstack", self.entry, {"investigate", "review"}, fake_api({"review"}, {}))
        self.assertEqual(r["status"], "removed paths")

    def test_acknowledged_retirement_is_not_an_alarm(self) -> None:
        entry = dict(self.entry, retired_paths={"investigate": "cut upstream"})
        r = ud.drift("gstack", entry, {"investigate"}, fake_api(set(), {}))
        self.assertEqual(r["status"], "unchanged")
        self.assertEqual(r["paths"][0]["retired"], "cut upstream")

    def test_changed_and_unchanged(self) -> None:
        api = fake_api({"review"}, {"review": [commit("a", "review: add enum check")]})
        self.assertEqual(ud.drift("gstack", self.entry, {"review"}, api)["status"], "changed")
        self.assertEqual(ud.drift("gstack", self.entry, {"review"}, fake_api({"review"}, {}))["status"], "unchanged")

    def test_unlocatable_and_unreviewed(self) -> None:
        self.assertEqual(ud.drift("x", {"repo": None, "note": "n"}, {""})["status"], "unlocatable")
        r = ud.drift("y", {"repo": "o/r", "reviewed_on": None}, {""}, fake_api(set(), {}))
        self.assertEqual(r["status"], "unreviewed baseline")


if __name__ == "__main__":
    unittest.main()
