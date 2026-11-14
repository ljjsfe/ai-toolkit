#!/usr/bin/env python3
"""Arithmetic for valuation-audit: the WACC build and a consistency check of a DCF.

Usage:
  dcf_check.py wacc --rf 0.042 --beta 1.1 --erp 0.05 --kd 0.06 --tax 0.21 \
                    --equity 13020 --debt 2000 [--cash 500 --net]
  dcf_check.py check model.json

`wacc` prints each step of the build with values plugged in:
  cost of equity (CAPM)   = rf + beta × ERP
  after-tax cost of debt  = pre-tax kd × (1 − tax)
  weights                 = E ÷ (E + D), D ÷ (E + D), market values
  WACC                    = ke × wE + kd_after × wD
Debt is gross by default; `--net` uses debt − cash and says so. With net cash (D below zero) the
script refuses the net weighting and falls back to gross debt, because a negative debt weight
pushes WACC above the cost of equity for no economic reason.

`check` reads a JSON model (this example passes every check):
  {"fcf": [110, 121], "r": 0.10, "g": 0.0, "net_debt": 200, "shares": 10,
   "base_value": 20.0,                        # per-share value the model claims
   "terminal_fcf": 24.2,                      # optional; default last fcf × (1 + g)
   "mid_year": false,                         # optional; true for mid-year convention
   "grid": {"r": [0.09, 0.10, 0.11], "g": [-0.01, 0.0, 0.01],
            "values": [[18.1, 18.2, 18.4], [19.8, 20.0, 20.2], [21.0, 21.3, 21.6]]}}
  Worked: PV explicit 110/1.1 + 121/1.21 = 200; TV 24.2/0.10 = 242, PV 242/1.21 = 200;
  total 400, PV(TV) share 50%; per share (400 − 200)/10 = 20.
  (Only the grid's centre cell is checked; the other cells are illustrative.)
and recomputes the DCF (Gordon terminal value; end-of-year discounting at t = 1..n, or with
"mid_year": true the mid-year convention, explicit years at t − 0.5 and the terminal value at
n − 0.5, as in a model built that way) to test:
  g < r (stop otherwise) | recomputed per-share value within 0.5% of base_value |
  PV(terminal value) share of the DCF total, finding above 80%, harsh-check below 40% |
  grid axes centred on the model's r and g, and the grid centre cell equal to base_value |
  r outside 5%–20% flagged for a second look; grid values that are not len(r) rows × len(g)
  numbers is itself a FAIL.
Exit code 1 when any check fails, so a broken model cannot pass silently.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOLERANCE = 0.005  # 0.5% relative: rounding in a spreadsheet, not a modelling difference


def cost_of_equity(rf: float, beta: float, erp: float) -> float:
    return rf + beta * erp


def after_tax_cost_of_debt(kd: float, tax: float) -> float:
    return kd * (1 - tax)


def wacc(equity: float, debt: float, ke: float, kd_after: float) -> tuple[float, float, float]:
    """Return (wacc, equity weight, debt weight) from market values."""
    total = equity + debt
    if total <= 0:
        raise ValueError("equity + debt must be positive")
    we, wd = equity / total, debt / total
    return ke * we + kd_after * wd, we, wd


def dcf(fcf: list[float], r: float, g: float, net_debt: float, shares: float,
        terminal_fcf: float | None = None, mid_year: bool = False) -> dict:
    """Terminal value at the last forecast year by Gordon growth. End-of-year discounting
    (periods 1..n) by default; mid_year shifts every period, the terminal one included, by −0.5."""
    if g >= r:
        raise ValueError(f"g ({g}) >= r ({r}): the perpetuity formula has no meaning")
    n = len(fcf)
    shift = 0.5 if mid_year else 0.0
    pv_explicit = sum(cf / (1 + r) ** (t + 1 - shift) for t, cf in enumerate(fcf))
    tv_cf = fcf[-1] * (1 + g) if terminal_fcf is None else terminal_fcf
    tv = tv_cf / (r - g)
    pv_tv = tv / (1 + r) ** (n - shift)
    total = pv_explicit + pv_tv
    return {
        "pv_explicit": pv_explicit,
        "terminal_value": tv,
        "pv_terminal": pv_tv,
        "total": total,
        "tv_share": pv_tv / total if total else float("nan"),
        "per_share": (total - net_debt) / shares,
    }


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE * max(abs(a), abs(b), 1e-12)


def _grid_shape_ok(vals: object, n_r: int, n_g: int) -> bool:
    if not isinstance(vals, list) or len(vals) != n_r:
        return False
    return all(isinstance(row, list) and len(row) == n_g
               and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in row)
               for row in vals)


def check_model(model: dict) -> tuple[list[str], list[str]]:
    """Return (failures, notes)."""
    fails: list[str] = []
    notes: list[str] = []
    for key in ("fcf", "r", "g", "net_debt", "shares"):
        if key not in model:
            fails.append(f"missing input {key!r}: the DCF ledger is incomplete, label it a sketch")
    if fails:
        return fails, notes
    r, g = float(model["r"]), float(model["g"])
    if g >= r:
        return [f"g {g:.2%} >= r {r:.2%}: stop and fix before any value is read"], notes
    if not 0.05 <= r <= 0.20:
        notes.append(f"r {r:.2%} is outside 5%-20%; recheck the build")
    mid = bool(model.get("mid_year", False))
    res = dcf(model["fcf"], r, g, model["net_debt"], model["shares"], model.get("terminal_fcf"), mid)
    notes.append(
        f"recomputed ({'mid-year' if mid else 'end-of-year'} discounting): PV explicit {res['pv_explicit']:.2f} + PV(TV) {res['pv_terminal']:.2f} = "
        f"{res['total']:.2f}; per share ({res['total']:.2f} - {model['net_debt']}) / "
        f"{model['shares']} = {res['per_share']:.4f}"
    )
    share = res["tv_share"]
    if share > 0.80:
        fails.append(f"PV(TV) is {share:.1%} of the DCF total: the answer rests on the perpetuity; "
                     "say so and widen the grid")
    elif share < 0.40:
        notes.append(f"PV(TV) is {share:.1%} of the DCF total: check the terminal assumptions "
                     "are not unreasonably harsh")
    else:
        notes.append(f"PV(TV) share {share:.1%}")
    base = model.get("base_value")
    if base is None:
        fails.append("no base_value given: cannot tie the model's answer to its inputs")
    elif not _close(res["per_share"], float(base)):
        fails.append(f"base_value {base} != recomputed {res['per_share']:.4f}: the model's "
                     "answer does not follow from its own inputs")
    grid = model.get("grid")
    if grid:
        rs, gs, vals = grid.get("r", []), grid.get("g", []), grid.get("values", [])
        if not rs or not gs or len(rs) % 2 == 0 or len(gs) % 2 == 0:
            fails.append("grid needs odd-length r and g axes so it has a centre cell")
        else:
            ri, gi = len(rs) // 2, len(gs) // 2
            if not _grid_shape_ok(vals, len(rs), len(gs)):
                fails.append(f"grid values must be {len(rs)} rows × {len(gs)} numbers (one row per r, "
                             "one column per g); the grid cannot be read")
            elif not (_close(rs[ri], r) and _close(gs[gi], g)):
                fails.append(f"grid centre axes ({rs[ri]}, {gs[gi]}) are not the model's r, g "
                             f"({r}, {g})")
            elif base is not None and not _close(vals[ri][gi], float(base)):
                fails.append(f"grid centre cell {vals[ri][gi]} != base_value {base}: "
                             "the model is wrong somewhere")
            else:
                notes.append("grid centre = base")
    else:
        notes.append("no grid supplied")
    return fails, notes


def cmd_wacc(a: argparse.Namespace) -> int:
    ke = cost_of_equity(a.rf, a.beta, a.erp)
    kd_after = after_tax_cost_of_debt(a.kd, a.tax)
    debt, label = a.debt, "gross debt"
    if a.net:
        net = a.debt - a.cash
        if net < 0:
            print(f"net debt {net} is negative (net cash): using gross debt {a.debt} instead")
        else:
            debt, label = net, "net debt"
    w, we, wd = wacc(a.equity, debt, ke, kd_after)
    print(f"cost of equity = {a.rf} + {a.beta} × {a.erp} = {ke:.4f}")
    print(f"after-tax cost of debt = {a.kd} × (1 − {a.tax}) = {kd_after:.4f}")
    print(f"weights ({label}): E {a.equity} ÷ {a.equity + debt} = {we:.4f}; "
          f"D {debt} ÷ {a.equity + debt} = {wd:.4f}")
    print(f"WACC = {ke:.4f} × {we:.4f} + {kd_after:.4f} × {wd:.4f} = {w:.4f}")
    if not 0.05 <= w <= 0.20:
        print(f"note: WACC {w:.2%} is outside 5%-20%; recheck beta, ERP and the debt cost")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    model = json.loads(Path(a.model).read_text(encoding="utf-8"))
    fails, notes = check_model(model)
    for n in notes:
        print(f"ok/note: {n}")
    for f in fails:
        print(f"FAIL: {f}")
    return 1 if fails else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("wacc")
    for name in ("rf", "beta", "erp", "kd", "tax", "equity", "debt"):
        w.add_argument(f"--{name}", type=float, required=True)
    w.add_argument("--cash", type=float, default=0.0)
    w.add_argument("--net", action="store_true", help="weight on debt − cash")
    w.set_defaults(func=cmd_wacc)
    c = sub.add_parser("check")
    c.add_argument("model")
    c.set_defaults(func=cmd_check)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
