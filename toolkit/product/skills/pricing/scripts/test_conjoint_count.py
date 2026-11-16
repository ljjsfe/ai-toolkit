#!/usr/bin/env python3
"""Tests for conjoint_count.py. Expected values counted by hand from the fixture:

Two respondents, two tasks each, two profiles per task (8 rows).
  r1 t1: A(analytics=adv, price=79) chosen; B(basic, 29)
  r1 t2: A(basic, 79); B(adv, 149) chosen
  r2 t1: A(adv, 79) chosen; B(basic, 29)
  r2 t2: A(basic, 79); B(adv, 149)  -> none chosen
analytics: adv shown 4 chosen 3 = 75%; basic shown 4 chosen 0 = 0%; spread 75%
price: 79 shown 4 chosen 2 = 50%; 29 shown 2 chosen 0; 149 shown 2 chosen 1 = 50%; spread 50%
none rate: 1 of 4 tasks = 25%
none rate per price shown: 79 in 4 tasks, 1 none = 25%; 29 in 2 tasks, 0 = 0%;
  149 in 2 tasks (r1t2, r2t2), 1 none = 50%
presence vs absence (analytics): adv 75% vs basic 0% -> no flag; basic 0% vs 75% -> killer signal
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conjoint_count  # noqa: E402

CSV = """respondent,task,chosen,analytics,price
r1,t1,1,adv,79
r1,t1,0,basic,29
r1,t2,0,basic,79
r1,t2,1,adv,149
r2,t1,1,adv,79
r2,t1,0,basic,29
r2,t2,0,basic,79
r2,t2,0,adv,149
"""


def rows(text: str) -> list[dict]:
    import csv
    return list(csv.DictReader(io.StringIO(text)))


class CountTests(unittest.TestCase):
    def test_win_rates(self) -> None:
        res = conjoint_count.count(rows(CSV))
        an = res["attributes"]["analytics"]
        self.assertEqual(an["levels"]["adv"][:2], (4, 3))
        self.assertAlmostEqual(an["levels"]["adv"][2], 0.75)
        self.assertAlmostEqual(an["spread"], 0.75)
        pr = res["attributes"]["price"]
        self.assertEqual(pr["levels"]["29"][:2], (2, 0))
        self.assertAlmostEqual(pr["spread"], 0.5)
        self.assertAlmostEqual(res["none_rate"], 0.25)
        self.assertEqual(res["respondents"], 2)

    def test_none_rate_per_price(self) -> None:
        res = conjoint_count.count(rows(CSV))
        self.assertEqual(res["none_by_price"]["79"][:2], (1, 4))
        self.assertEqual(res["none_by_price"]["29"][:2], (0, 2))
        self.assertAlmostEqual(res["none_by_price"]["149"][2], 0.5)

    def test_killer_signal_presence_vs_absence(self) -> None:
        res = conjoint_count.count(rows(CSV))
        pres = res["attributes"]["analytics"]["presence"]
        self.assertEqual(pres["adv"], (0.75, 0.0, False))
        self.assertEqual(pres["basic"], (0.0, 0.75, True))
        self.assertEqual(res["attributes"]["price"]["presence"], {})  # price is not a feature

    def test_two_choices_in_one_task_rejected(self) -> None:
        bad = CSV.replace("r1,t1,0,basic,29", "r1,t1,1,basic,29")
        with self.assertRaises(ValueError):
            conjoint_count.count(rows(bad))

    def test_cli_warns_on_small_sample(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "c.csv"
            p.write_text(CSV, encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(conjoint_count.main([str(p)]), 0)
            self.assertIn("directional only", buf.getvalue())
            self.assertIn("adv: chosen 3/4 = 75.0%", buf.getvalue())
            self.assertIn("basic present 0.0% vs absent 75.0%  <- killer signal", buf.getvalue())
            self.assertIn("none rate when price 149 shown: 1/2 = 50.0%", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
