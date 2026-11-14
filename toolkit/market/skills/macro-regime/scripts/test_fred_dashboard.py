#!/usr/bin/env python3
"""Offline tests for fred_dashboard.py: a fake fetcher serves FRED-shaped CSV."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fred_dashboard as fd  # noqa: E402


def monthly(values: list[float], start_year: int = 2024) -> str:
    rows = ["observation_date,X"]
    for i, v in enumerate(values):
        y, m = start_year + i // 12, i % 12 + 1
        rows.append(f"{y}-{m:02d}-01,{v}")
    return "\n".join(rows) + "\n"


def fake_fetcher(overrides: dict[str, str] | None = None, fail: set[str] | None = None):
    base = monthly([100 + i for i in range(30)])
    overrides = overrides or {}

    def fetch(sid: str) -> str:
        if fail and sid in fail:
            raise OSError("HTTP 500")
        return overrides.get(sid, base)
    return fetch


class ParseTests(unittest.TestCase):
    def test_missing_dots_are_skipped(self) -> None:
        obs = fd.parse_csv("observation_date,T10Y3M\n2026-11-12,0.80\n2026-11-13,.\n")
        self.assertEqual(obs, [("2026-11-12", 0.80)])

    def test_garbage_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fd.parse_csv("<html>error</html>")


class DerivedTests(unittest.TestCase):
    def test_inflation_formulas(self) -> None:
        # 13 months rising 1% a month: yoy = 1.01^12 − 1 = 12.68%; 3m annualised = 1.01^12 − 1 too
        vals = [100 * 1.01 ** i for i in range(13)]
        obs = fd.parse_csv(monthly(vals))
        self.assertAlmostEqual(fd.pct_change(obs, 12), 0.12682503013196977, places=12)
        self.assertAlmostEqual(fd.annualised(obs, 3, 12), 0.12682503013196977, places=12)

    def test_inversion_stats(self) -> None:
        vals = [0.5] * 10 + [-0.2] * 8 + [0.3] * 3 + [-0.1] * 3
        stats = fd.inversion_stats(fd.parse_csv(monthly(vals)))
        self.assertEqual(stats["months_inverted_of_last_24"], 11)
        self.assertEqual(stats["current_inverted_run_months"], 3)

    def test_sahm_trigger(self) -> None:
        snap = fd.build(*fd.load(sorted({i for v in fd.SERIES.values() for i in v} | {"T10Y3M"}),
                                 fake_fetcher({"SAHMREALTIME": monthly([0.2, 0.4, 0.53])})))
        self.assertTrue(snap["rows"]["recession"]["sahm_realtime_pp"]["triggered"])


class DashboardTests(unittest.TestCase):
    def _run(self, fetcher, tmp: str) -> tuple[int, dict]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = fd.main(["dashboard", "--dir", tmp], fetcher=fetcher)
        return code, json.loads(buf.getvalue())

    def test_missing_series_blocks_classification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, snap = self._run(fake_fetcher(fail={"DFII10"}), tmp)
        self.assertEqual(code, 1)
        self.assertFalse(snap["complete"])
        self.assertIn("DFII10", snap["rows"]["real rates"]["missing"])
        self.assertIn("does not classify", snap["note"])

    def test_snapshot_saved_and_compared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            prev = {"as_of_run": "2000-01-01", "rows": {
                "inflation": {"core_pce": {"3m_annualised_pct": 1.0, "yoy_pct": 2.0}},
                "curve": {"3m10y_pct": {"value": 0.5}},
                "recession": {"sahm_realtime_pp": {"triggered": False}},
                "labour": {"unemployment_pct": {"value": 4.0}, "unemployment_prior": {"value": 4.1}},
                "financial conditions": {"nfci": {"value": -0.5}, "nfci_prior": {"value": -0.4}}}}
            Path(tmp, "2000-01-01.json").write_text(json.dumps(prev), encoding="utf-8")
            code, snap = self._run(fake_fetcher(), tmp)
            self.assertEqual(code, 0)
            self.assertTrue(Path(snap["saved_to"]).exists())
        cmp = snap["comparison"]
        self.assertEqual(cmp["previous"], "2000-01-01")
        self.assertIn("sustained", cmp["signals"]["curve_3m10y_inverted"])
        self.assertFalse(cmp["signals"]["unemployment_rising"]["sustained"])

    def test_first_run_has_nothing_sustained(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, snap = self._run(fake_fetcher(), tmp)
        self.assertIn("nothing can be called sustained", snap["comparison"]["note"])


if __name__ == "__main__":
    unittest.main()
