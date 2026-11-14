#!/usr/bin/env python3
"""Tests for dcf_check.py. Expected values were worked by hand, not with the code under test:

WACC: rf 4%, beta 1.2, ERP 5%  -> ke = 0.04 + 1.2 × 0.05 = 0.10
      kd 5%, tax 20%           -> kd after tax = 0.05 × 0.8 = 0.04
      E 800, D 200             -> wE 0.8, wD 0.2; WACC = 0.10 × 0.8 + 0.04 × 0.2 = 0.088

DCF A: fcf [110, 121], r 10%, g 0, net debt 200, 10 shares
      PV explicit = 110/1.1 + 121/1.21 = 100 + 100 = 200
      TV = 121 × 1.0 / 0.10 = 1210; PV(TV) = 1210 / 1.21 = 1000
      total 1200; PV(TV) share = 1000/1200 = 83.3% (> 80%, a finding)
      per share = (1200 − 200) / 10 = 100
DCF B mid-year: periods 0.5, 1.5, TV at 1.5; every PV × 1.1 ** 0.5
      total 400 × 1.0488088 = 419.5235; per share (419.5235 − 200) / 10 = 21.95235
DCF B: same, but terminal_fcf 24.2
      TV = 24.2 / 0.10 = 242; PV(TV) = 242 / 1.21 = 200; total 400; share 50%
      per share = (400 − 200) / 10 = 20
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dcf_check  # noqa: E402

BASE_B = {"fcf": [110, 121], "r": 0.10, "g": 0.0, "net_debt": 200, "shares": 10,
          "terminal_fcf": 24.2, "base_value": 20.0}


class WaccTests(unittest.TestCase):
    def test_build(self) -> None:
        ke = dcf_check.cost_of_equity(0.04, 1.2, 0.05)
        kd = dcf_check.after_tax_cost_of_debt(0.05, 0.20)
        self.assertAlmostEqual(ke, 0.10)
        self.assertAlmostEqual(kd, 0.04)
        w, we, wd = dcf_check.wacc(800, 200, ke, kd)
        self.assertAlmostEqual(w, 0.088)
        self.assertAlmostEqual(we, 0.8)
        self.assertAlmostEqual(wd, 0.2)

    def test_net_cash_falls_back_to_gross(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            dcf_check.main(["wacc", "--rf", "0.04", "--beta", "1.2", "--erp", "0.05", "--kd", "0.05",
                            "--tax", "0.2", "--equity", "800", "--debt", "200", "--cash", "500", "--net"])
        out = buf.getvalue()
        self.assertIn("net cash", out)
        self.assertIn("= 0.0880", out)


class DcfTests(unittest.TestCase):
    def test_values_a(self) -> None:
        res = dcf_check.dcf([110, 121], 0.10, 0.0, 200, 10)
        self.assertAlmostEqual(res["pv_explicit"], 200)
        self.assertAlmostEqual(res["pv_terminal"], 1000)
        self.assertAlmostEqual(res["tv_share"], 1000 / 1200)
        self.assertAlmostEqual(res["per_share"], 100)

    def test_mid_year_convention(self) -> None:
        res = dcf_check.dcf([110, 121], 0.10, 0.0, 200, 10, terminal_fcf=24.2, mid_year=True)
        self.assertAlmostEqual(res["per_share"], 21.95235, places=4)
        self.assertAlmostEqual(res["tv_share"], 0.5)
        mid_model = dict(BASE_B, base_value=21.95, mid_year=True)
        self.assertEqual(dcf_check.check_model(mid_model)[0], [])
        fails, _ = dcf_check.check_model(dict(BASE_B, base_value=21.95))  # flag absent
        self.assertTrue(any("does not follow" in f for f in fails), fails)

    def test_malformed_grid_values_fail_not_crash(self) -> None:
        for vals in ([], [[0, 0, 0]], [[0, 0], [0, 20.0], [0, 0]], [[0, 0, 0], [0, "x", 0], [0, 0, 0]]):
            model = dict(BASE_B, grid={"r": [0.09, 0.10, 0.11], "g": [-0.01, 0.0, 0.01], "values": vals})
            fails, _ = dcf_check.check_model(model)
            self.assertTrue(any("grid values must be 3 rows" in f for f in fails), (vals, fails))

    def test_docstring_example_passes(self) -> None:
        model = {"fcf": [110, 121], "r": 0.10, "g": 0.0, "net_debt": 200, "shares": 10,
                 "base_value": 20.0, "terminal_fcf": 24.2, "mid_year": False,
                 "grid": {"r": [0.09, 0.10, 0.11], "g": [-0.01, 0.0, 0.01],
                          "values": [[18.1, 18.2, 18.4], [19.8, 20.0, 20.2], [21.0, 21.3, 21.6]]}}
        self.assertIn('"base_value": 20.0', dcf_check.__doc__)
        self.assertEqual(dcf_check.check_model(model)[0], [])

    def test_g_not_below_r_raises(self) -> None:
        with self.assertRaises(ValueError):
            dcf_check.dcf([100], 0.05, 0.05, 0, 1)

    def test_clean_model_passes(self) -> None:
        model = dict(BASE_B, grid={"r": [0.09, 0.10, 0.11], "g": [-0.01, 0.0, 0.01],
                                   "values": [[0, 0, 0], [0, 20.0, 0], [0, 0, 0]]})
        fails, notes = dcf_check.check_model(model)
        self.assertEqual(fails, [])
        self.assertIn("grid centre = base", notes)
        self.assertIn("PV(TV) share 50.0%", notes)

    def test_high_terminal_share_fails(self) -> None:
        model = {"fcf": [110, 121], "r": 0.10, "g": 0.0, "net_debt": 200, "shares": 10,
                 "base_value": 100.0}
        fails, _ = dcf_check.check_model(model)
        self.assertTrue(any("83.3%" in f for f in fails), fails)

    def test_base_mismatch_and_bad_centre(self) -> None:
        model = dict(BASE_B, base_value=22.0,
                     grid={"r": [0.09, 0.10, 0.11], "g": [-0.01, 0.0, 0.01],
                           "values": [[0, 0, 0], [0, 21.0, 0], [0, 0, 0]]})
        fails, _ = dcf_check.check_model(model)
        self.assertTrue(any("does not follow" in f for f in fails), fails)
        self.assertTrue(any("grid centre cell" in f for f in fails), fails)

    def test_off_centre_axes_fail(self) -> None:
        model = dict(BASE_B, grid={"r": [0.08, 0.09, 0.10], "g": [-0.01, 0.0, 0.01],
                                   "values": [[0, 0, 0], [0, 20.0, 0], [0, 0, 0]]})
        fails, _ = dcf_check.check_model(model)
        self.assertTrue(any("not the model's r, g" in f for f in fails), fails)

    def test_g_ge_r_stops(self) -> None:
        fails, _ = dcf_check.check_model(dict(BASE_B, g=0.10))
        self.assertTrue(fails and "stop and fix" in fails[0])

    def test_missing_input_is_sketch(self) -> None:
        fails, _ = dcf_check.check_model({"fcf": [1], "r": 0.1})
        self.assertTrue(any("sketch" in f for f in fails))

    def test_cli_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "m.json"
            p.write_text(json.dumps(BASE_B), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(dcf_check.main(["check", str(p)]), 0)
            p.write_text(json.dumps(dict(BASE_B, base_value=30)), encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(dcf_check.main(["check", str(p)]), 1)


if __name__ == "__main__":
    unittest.main()
