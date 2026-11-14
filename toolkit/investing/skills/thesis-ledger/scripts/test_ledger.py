#!/usr/bin/env python3
"""Tests for ledger.py; THESIS_DIR points at a temporary directory."""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ledger  # noqa: E402


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["THESIS_DIR"] = self.tmp.name

    def tearDown(self) -> None:
        os.environ.pop("THESIS_DIR", None)
        self.tmp.cleanup()

    def run_cli(self, *argv: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ledger.main(list(argv))
        return code, out.getvalue() + err.getvalue()

    def path(self) -> Path:
        return Path(self.tmp.name) / "ACME.md"

    def test_lifecycle(self) -> None:
        self.assertEqual(self.run_cli("new", "acme", "--side", "long", "--date", "2026-02-29")[0], 2)  # not a date
        self.assertEqual(self.run_cli("new", "acme", "--side", "long", "--date", "2026-03-01")[0], 0)
        self.assertIn("Pre-mortem (2027-03-01)", self.path().read_text())
        self.assertEqual(self.run_cli("new", "ACME", "--side", "short")[0], 2)  # never overwritten
        code, _ = self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "Q1 revenue +18%",
                               "--next", "2026-05-01", "--reason", "Q2 earnings", "--date", "2026-03-10")
        self.assertEqual(code, 0)
        self.run_cli("log", "ACME", "--outcome", "insufficient", "--fact", "no new figure",
                     "--next", "2026-08-01", "--reason", "Q2 10-Q", "--date", "2026-05-02")
        h = ledger.read_header(self.path().read_text())
        self.assertEqual(h["last_confirmed"], "intact (2026-03-10)")  # insufficient leaves it
        self.assertEqual(h["latest_outcome"], "insufficient")
        self.assertEqual(self.run_cli("verify", "ACME"), (0, "OK\n"))
        self.assertEqual(self.run_cli("close", "ACME", "--as", "invalidated", "--reason", "kill criterion 2 fired",
                                      "--date", "2026-06-01")[0], 0)
        self.assertEqual(ledger.read_header(self.path().read_text())["state"], "invalidated")
        self.assertEqual(self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "x", "--next", "2026-09-01",
                                      "--reason", "r", "--date", "2026-06-02")[0], 2)

    def test_edited_history_is_detected_and_blocks_logging(self) -> None:
        self.run_cli("new", "ACME", "--side", "long", "--date", "2026-03-01")
        self.run_cli("log", "ACME", "--outcome", "weakened", "--fact", "gross margin 41% vs 45% threshold",
                     "--next", "2026-05-01", "--reason", "Q2", "--date", "2026-03-10")
        self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "margin back to 46%",
                     "--next", "2026-08-01", "--reason", "Q3", "--date", "2026-05-02")
        text = self.path().read_text()
        self.path().write_text(text.replace("gross margin 41%", "gross margin 44%"))
        code, out = self.run_cli("verify", "ACME")
        self.assertEqual(code, 1)
        self.assertIn("row 1 was edited", out)
        code, out = self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "x", "--next", "2026-09-01",
                                 "--reason", "r", "--date", "2026-08-02")
        self.assertEqual(code, 2)
        self.assertIn("fails verify", out)

    def test_deleted_row_is_detected(self) -> None:
        self.run_cli("new", "ACME", "--side", "long", "--date", "2026-03-01")
        for d, n in (("2026-03-10", "2026-05-01"), ("2026-05-02", "2026-08-01")):
            self.run_cli("log", "ACME", "--outcome", "intact", "--fact", d, "--next", n, "--reason", "r", "--date", d)
        lines = self.path().read_text().splitlines()
        first = next(i for i, ln in enumerate(lines) if ln.startswith("| 2026-03-10"))
        self.path().write_text("\n".join(lines[:first] + lines[first + 1:]) + "\n")
        self.assertEqual(self.run_cli("verify", "ACME")[0], 1)

    def test_dates_must_move_forward(self) -> None:
        self.run_cli("new", "ACME", "--side", "long", "--date", "2026-03-01")
        self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "a", "--next", "2026-05-01", "--reason", "r",
                     "--date", "2026-03-10")
        self.assertEqual(self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "b", "--next", "2026-05-01",
                                      "--reason", "r", "--date", "2026-03-01")[0], 2)
        self.assertEqual(self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "b", "--next", "2026-03-05",
                                      "--reason", "r", "--date", "2026-04-01")[0], 2)

    def test_book_flags_overdue(self) -> None:
        self.run_cli("new", "ACME", "--side", "long", "--date", "2026-03-01")
        self.run_cli("new", "BETA", "--side", "short", "--date", "2026-03-01")
        self.run_cli("log", "ACME", "--outcome", "intact", "--fact", "a", "--next", "2026-05-01", "--reason", "r",
                     "--date", "2026-03-10")
        _, out = self.run_cli("book", "--today", "2026-06-01")
        acme = next(ln for ln in out.splitlines() if ln.startswith("| ACME"))
        beta = next(ln for ln in out.splitlines() if ln.startswith("| BETA"))
        self.assertTrue(acme.endswith("| yes |"))
        self.assertTrue(beta.endswith("| no check set |"))

    def test_calc_prints_formula(self) -> None:
        self.assertEqual(ledger.cmd_calc("growth", 200.0, 236.0), "growth = 236.0 / 200.0 − 1 = 18.0000%")
        self.assertEqual(ledger.cmd_calc("margin", 41.0, 100.0), "margin = 41.0 / 100.0 = 41.0000%")
        self.assertIn("= -4 (-8.89% of threshold)", ledger.cmd_calc("distance", 41.0, 45.0))
        with self.assertRaises(ValueError):
            ledger.cmd_calc("growth", 0, 5)

    def test_bad_ticker_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ledger.path_for("../etc/passwd")


if __name__ == "__main__":
    unittest.main()
