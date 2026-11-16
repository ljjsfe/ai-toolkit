#!/usr/bin/env python3
"""Tests for research_audit.py (offline: the link check runs against a local HTTP server)."""
from __future__ import annotations

import sys
import tempfile
import threading
import unittest
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_audit as ra  # noqa: E402

RECORDS = """# Records

- R1 · Postgres 17 adds incremental backup · https://www.postgresql.org/docs/17/release-17.html · "pg_basebackup now supports incremental backups" · postgresql.org · 2026-09-26
- R2 · Same change reported in a blog · https://blog.example.com/pg17 · "incremental backups arrive in PostgreSQL 17" · postgresql.org · 2026-10-01
- R3 · Vendor benchmark claims 3x restore speed · https://vendor.example.com/bench · "restores ran three times faster" · vendor.example.com · 2024-02-01
- D1 · Restore time falls by two thirds · R3 · 1 − 1/3 = 0.67
"""

DRAFT = """# Answer

## Incremental backup, not a new tool, decides this

Postgres 17 ships incremental backup [R1] and coverage elsewhere repeats it [R2].
Restores ran 67% faster in one benchmark [D1].
A survey found 41% of teams still run nightly full dumps.
See also https://invented.example.org/report for detail [R1].
Cited [R9] for good measure.

## Not verified

The 41% figure above.

## Sources
- https://www.postgresql.org/docs/17/release-17.html
"""


def write(tmp: str, name: str, text: str) -> Path:
    p = Path(tmp) / name
    p.write_text(text, encoding="utf-8")
    return p


class RecordTests(unittest.TestCase):
    def test_parse_and_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records, errors = ra.parse_records(write(tmp, "r.md", RECORDS))
        self.assertEqual(errors, [])
        self.assertEqual(set(records), {"R1", "R2", "R3", "D1"})
        self.assertEqual(records["D1"].inputs, ["R3"])
        self.assertEqual(records["R1"].when, date(2026, 9, 26))

    def test_bad_records(self) -> None:
        bad = ("R1 · claim · not-a-url · \"short\" · · 2026-13-40\n"
               "D1 · claim · R7 · step\nR1 · dup · https://a.b/c · \"long enough passage\" · a · 2026-01-01\n")
        with tempfile.TemporaryDirectory() as tmp:
            _, errors = ra.parse_records(write(tmp, "r.md", bad))
        text = "\n".join(errors)
        for needle in ("not an http(s) URL", "too short", "origin is empty", "date is missing",
                       "R7 does not exist", "duplicate record"):
            self.assertIn(needle, text)

    def test_origins_follow_derived_records(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            records, _ = ra.parse_records(write(tmp, "r.md", RECORDS))
        self.assertEqual(ra.origins_of({"R1", "R2"}, records), {"postgresql.org"})
        self.assertEqual(ra.origins_of({"D1"}, records), {"vendor.example.com"})

    def test_stale_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, info = ra.cmd_records(write(tmp, "r.md", RECORDS), date(2025, 1, 1))
        self.assertTrue(any(i.startswith("stale: R3") for i in info), info)
        self.assertIn("2 independent origin(s)", info[0])


class DraftTests(unittest.TestCase):
    def test_draft_findings_and_claims_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "claims.md"
            errors, info = ra.cmd_draft(write(tmp, "draft.md", DRAFT), write(tmp, "r.md", RECORDS), out)
            claims = out.read_text(encoding="utf-8")
        text = "\n".join(errors)
        self.assertIn("invented.example.org", text)
        self.assertIn("cites R9", text)
        self.assertNotIn("postgresql.org/docs", text)  # gathered URL in Sources is fine
        joined = "\n".join(info)
        self.assertIn("uncited", joined)
        self.assertIn("41% of teams", joined)
        self.assertNotIn("The 41% figure above", joined)  # exempt section
        self.assertIn("C1 — Postgres 17 ships", claims)
        self.assertIn('passage: "pg_basebackup now supports incremental backups"', claims)
        self.assertIn("derived from R3", claims)

    def test_single_origin_section_flagged(self) -> None:
        draft = "## Restore speed triples\n\nRestores ran 3x faster [R3] and two thirds less time [D1].\n"
        with tempfile.TemporaryDirectory() as tmp:
            _, info = ra.cmd_draft(write(tmp, "d.md", draft), write(tmp, "r.md", RECORDS), None)
        self.assertTrue(any(i.startswith("single origin") for i in info), info)


class _Handler(BaseHTTPRequestHandler):
    pages = {
        "/ok": "<html><script>var x='pg_basebackup';</script><p>Now pg_basebackup now supports "
               "incremental backups for large clusters.</p></html>",
        "/other": "<p>Nothing relevant on this page at all, sorry.</p>",
        "/": "<p>home</p>",
    }

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/moved":
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()
            return
        body = self.pages.get(self.path)
        code = 200 if body is not None else (403 if self.path == "/blocked" else 404)
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write((body or "x").encode())

    def log_message(self, *args: object) -> None:
        pass


class LinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = HTTPServer(("127.0.0.1", 0), _Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()

    def test_statuses(self) -> None:
        passage = "pg_basebackup now supports incremental backups"
        lines = [f"R{i} · c · {self.base}{p} · \"{passage}\" · o{i} · 2026-01-01"
                 for i, p in enumerate(["/ok", "/other", "/missing", "/blocked", "/moved"], 1)]
        with tempfile.TemporaryDirectory() as tmp:
            errors, info = ra.cmd_links(write(tmp, "r.md", "\n".join(lines)), timeout=5, workers=2)
        status = {ln[13:].split()[0]: ln[:13].strip() for ln in info}
        self.assertEqual(status, {"R1": "OK", "R2": "QUOTE?", "R3": "NOT FOUND", "R4": "BLOCKED", "R5": "HOMEPAGE"})
        self.assertEqual(len(errors), 3)  # QUOTE?, NOT FOUND, HOMEPAGE; BLOCKED needs a manual re-open

    def test_blocked_network_is_reported_not_counted(self) -> None:
        def offline(url: str, timeout: float):
            raise ra.URLError(OSError("network unreachable"))
        with tempfile.TemporaryDirectory() as tmp:
            errors, info = ra.cmd_links(write(tmp, "r.md", RECORDS), 1, 2, fetcher=offline)
        self.assertEqual(errors, [])
        self.assertIn("network looks blocked", info[0])

    def test_passage_matching(self) -> None:
        words = ra.page_words("<p>The quick brown fox jumps over the lazy dog</p>")
        self.assertEqual(ra.passage_found("quick brown fox jumps over", words), 1.0)
        self.assertLess(ra.passage_found("quick brown cat jumps over", words), 0.9)


if __name__ == "__main__":
    unittest.main()
