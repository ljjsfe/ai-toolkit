#!/usr/bin/env python3
"""Tests for expstats.py. Expected values are literals from SciPy 1.18.1 / statsmodels 0.15.0
(computed once, outside this repo), never recomputed with the formulas under test."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import expstats  # noqa: E402


class Chi2Tests(unittest.TestCase):
    def test_survival_function_matches_scipy(self) -> None:
        for stat, df, want in [
            (16, 1, 6.33424836662399e-05),
            (10, 3, 0.01856613546304323),
            (3.0, 4, 0.5578254003710748),
            (0.5, 1, 0.47950012218695337),
        ]:
            self.assertAlmostEqual(expstats.chi2_sf(stat, df) / want, 1.0, places=9, msg=(stat, df))
        self.assertAlmostEqual(expstats.chi2_sf(250, 2) / 5.166420632837831e-55, 1.0, places=6)


class SrmTests(unittest.TestCase):
    def test_equal_split_halts(self) -> None:
        r = expstats.srm([4800, 5200])
        self.assertAlmostEqual(r["chi2"], 16.0)
        self.assertAlmostEqual(r["p"] / 6.33424836662399e-05, 1.0, places=9)
        self.assertEqual(r["verdict"], "HALT")

    def test_designed_allocation_is_used(self) -> None:
        r = expstats.srm([8150, 1850], [80, 20])
        self.assertAlmostEqual(r["chi2"], 14.0625)
        self.assertAlmostEqual(r["p"] / 0.00017683457040160795, 1.0, places=8)

    def test_three_arms_pass_final_but_threshold_shrinks_with_checks(self) -> None:
        r = expstats.srm([3300, 3350, 3500])
        self.assertAlmostEqual(r["p"] / 0.040681963445290285, 1.0, places=8)
        self.assertEqual(r["verdict"], "PASS")
        self.assertAlmostEqual(expstats.srm([3300, 3350, 3500], monitoring=True, checks=5)["threshold"], 0.0001)

    def test_bad_input_rejected(self) -> None:
        for counts, ratios in [([10], None), ([0, 0], None), ([5, 5], [1]), ([5, -1], None)]:
            with self.assertRaises(ValueError):
                expstats.srm(counts, ratios)

    def test_segments_flag_the_skewed_one(self) -> None:
        r = expstats.srm_segments([("ios", [5000, 5010]), ("android", [4800, 5200]), ("web", [2000, 1990])])
        verdicts = {s["segment"]: s["verdict"] for s in r["segments"]}
        self.assertEqual(verdicts, {"ios": "PASS", "android": "HALT", "web": "PASS"})
        self.assertTrue(r["any_halt"])


class PowerTests(unittest.TestCase):
    def test_two_proportions_equal_split(self) -> None:
        # statsmodels samplesize_proportions_2indep_onetail(diff=0.01, prop2=0.10, ratio=1) = 14750.79
        r = expstats.power_prop(0.10, 0.10)
        self.assertEqual(r["n_control"], 14751)
        self.assertEqual(r["n_treatment"], 14751)

    def test_two_proportions_uneven_split(self) -> None:
        # statsmodels with nobs2/nobs1 = 2 (control twice treatment): nobs1 = 11000.54
        r = expstats.power_prop(0.10, 0.10, ratio=0.5)
        self.assertIn(r["n_treatment"], (11001, 11002))
        self.assertIn(r["n_control"], (22001, 22002))

    def test_days(self) -> None:
        self.assertEqual(expstats.power_prop(0.10, 0.10, daily=1000)["days"], 30)

    def test_means(self) -> None:
        # statsmodels NormalIndPower(effect_size=0.04): 9811.08 at ratio 1, 7358.31 at ratio 2
        self.assertEqual(expstats.power_mean(12.5, 0.5)["n_control"], 9812)
        self.assertEqual(expstats.power_mean(12.5, 0.5, ratio=2)["n_control"], 7359)

    def test_invalid_rates(self) -> None:
        with self.assertRaises(ValueError):
            expstats.power_prop(0.95, 0.10)


class EffectTests(unittest.TestCase):
    def test_prop_test_matches_statsmodels(self) -> None:
        r = expstats.prop_test(480, 5000, 540, 5000)
        self.assertAlmostEqual(r["z"], 1.9824990878441187, places=9)
        self.assertAlmostEqual(r["p"], 0.04742340937488423, places=9)
        self.assertAlmostEqual(r["diff"], 0.012)

    def test_t_distribution_matches_scipy(self) -> None:
        self.assertAlmostEqual(expstats.t_two_sided_p(2.5, 3), 0.08770664700806556, places=10)
        self.assertAlmostEqual(expstats.t_inv(0.975, 5), 2.5705818356363146, places=8)

    def test_welch_matches_scipy(self) -> None:
        # scipy ttest_ind_from_stats(..., equal_var=False) reports control − treatment
        big = expstats.welch(52.1, 18.4, 4980, 53.0, 19.1, 5011)
        self.assertAlmostEqual(big["t"], 2.3986292566910943, places=9)
        self.assertAlmostEqual(big["p"], 0.016474806538029976, places=9)
        small = expstats.welch(10, 3, 8, 13, 6, 12)
        self.assertAlmostEqual(small["p"], 0.15790029056154756, places=9)
        self.assertAlmostEqual(small["df"], 17.03290676416819, places=9)
        half = (small["ci"][1] - small["ci"][0]) / 2
        self.assertAlmostEqual(half / small["diff"] * small["t"], 2.1095051215045832, places=6)

    def test_holm_matches_statsmodels(self) -> None:
        r = expstats.holm([0.01, 0.04, 0.03, 0.2])
        for got, want in zip(r["adjusted"], [0.04, 0.09, 0.09, 0.2]):
            self.assertAlmostEqual(got, want)
        self.assertEqual(r["reject"], [True, False, False, False])

    def test_ratio_metric_hand_example(self) -> None:
        # control ratio 10/10 = 1.0, treatment 15/10 = 1.5
        arms = {"control": ([1, 2, 3, 4], [2, 2, 3, 3]), "treatment": ([3, 3, 4, 5], [2, 2, 3, 3])}
        r = expstats.ratio_test(arms)
        self.assertAlmostEqual(r["ratio_control"], 1.0)
        self.assertAlmostEqual(r["ratio_treatment"], 1.5)
        self.assertLess(r["ci"][0], r["diff"])
        with self.assertRaises(ValueError):
            expstats.ratio_test({"only": ([1, 2], [1, 1])})


    def test_ratio_zero_variance(self) -> None:
        with self.assertRaises(ValueError) as cm:
            expstats.ratio_test({"control": ([1, 1], [1, 1]), "treatment": ([2, 2], [1, 1])})
        self.assertIn("zero variance", str(cm.exception))
        r = expstats.ratio_test({"control": ([1, 1], [1, 1]), "treatment": ([1, 1], [1, 1])})
        self.assertEqual((r["diff"], r["p"]), (0, 1.0))

class CliTests(unittest.TestCase):
    def _run(self, argv: list[str]) -> dict:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(expstats.main(argv), 0)
        return json.loads(buf.getvalue())

    def test_cli_srm_and_segments_csv(self) -> None:
        self.assertEqual(self._run(["srm", "--counts", "4800", "5200"])["verdict"], "HALT")
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "seg.csv"
            p.write_text("segment,control,treatment\nios,5000,5010\nandroid,4800,5200\n", encoding="utf-8")
            self.assertTrue(self._run(["srm-segments", "--csv", str(p)])["any_halt"])

    def test_cli_error_exit_code(self) -> None:
        self.assertEqual(expstats.main(["srm", "--counts", "5"]), 2)


if __name__ == "__main__":
    unittest.main()
