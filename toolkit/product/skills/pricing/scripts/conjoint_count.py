#!/usr/bin/env python3
"""Count a simplified conjoint: win rate per attribute level = times chosen ÷ times shown.

Usage:
  conjoint_count.py choices.csv [--min-responses 200]

CSV, one row per profile shown (a task of 3 profiles is 3 rows), header required:
  respondent,task,chosen,<attribute>,<attribute>,...,price
`chosen` is 1 for the profile picked, 0 otherwise. A task where the respondent picked
"none of these" has every row at 0. The script reports the overall none rate and, per price
level, the none rate of the tasks in which that price was shown (none tasks with the price ÷
tasks with the price).

Output per attribute: each level's shown / chosen / win rate, and the spread between the best
and worst level (a large spread drives choice; a near-zero spread is filler). For every
non-price attribute it also prints each level's win rate when present against the win rate of
the same attribute's other levels (its absence), and marks "killer signal" when presence is
lower. Read that mark on on/off feature attributes (e.g. on-prem yes/no); on a multi-level
attribute the worst level is always below the rest, so it only says which level loses.
Fewer completed respondents than --min-responses prints a warning: below it, read only
rankings and the three-point probe.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

BASE_COLS = ("respondent", "task", "chosen")


def count(rows: list[dict], price_col: str = "price") -> dict:
    attrs = [c for c in rows[0].keys() if c not in BASE_COLS]
    shown: dict[str, dict[str, int]] = {a: defaultdict(int) for a in attrs}
    chosen: dict[str, dict[str, int]] = {a: defaultdict(int) for a in attrs}
    tasks: dict[tuple[str, str], int] = defaultdict(int)
    task_prices: dict[tuple[str, str], set[str]] = defaultdict(set)
    for r in rows:
        pick = int(r["chosen"])
        key = (r["respondent"], r["task"])
        tasks[key] += pick
        if price_col in r:
            task_prices[key].add(r[price_col])
        for a in attrs:
            shown[a][r[a]] += 1
            chosen[a][r[a]] += pick
    if any(v > 1 for v in tasks.values()):
        raise ValueError("a task has more than one chosen profile")
    out = {}
    for a in attrs:
        levels = {lv: (shown[a][lv], chosen[a][lv], chosen[a][lv] / shown[a][lv]) for lv in shown[a]}
        rates = [v[2] for v in levels.values()]
        presence = {}
        if a != price_col:
            tot_s, tot_c = sum(v[0] for v in levels.values()), sum(v[1] for v in levels.values())
            for lv, (sh, ch, w) in levels.items():
                rest_s = tot_s - sh
                absent = (tot_c - ch) / rest_s if rest_s else None
                presence[lv] = (w, absent, absent is not None and w < absent)
        out[a] = {"levels": levels, "spread": max(rates) - min(rates), "presence": presence}
    none_by_price: dict[str, tuple[int, int, float]] = {}
    for price in sorted({p for ps in task_prices.values() for p in ps}):
        with_p = [k for k, ps in task_prices.items() if price in ps]
        nones = sum(1 for k in with_p if tasks[k] == 0)
        none_by_price[price] = (nones, len(with_p), nones / len(with_p))
    return {
        "attributes": out,
        "none_by_price": none_by_price,
        "respondents": len({k[0] for k in tasks}),
        "tasks": len(tasks),
        "none_rate": sum(1 for v in tasks.values() if v == 0) / len(tasks),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("csv")
    p.add_argument("--min-responses", type=int, default=200)
    p.add_argument("--price-col", default="price", help="name of the price column")
    a = p.parse_args(argv)
    with Path(a.csv).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print("no rows")
        return 1
    res = count(rows, a.price_col)
    print(f"respondents {res['respondents']} | tasks {res['tasks']} | none chosen "
          f"{res['none_rate']:.1%}")
    if res["respondents"] < a.min_responses:
        print(f"warning: {res['respondents']} respondents < {a.min_responses}; directional only")
    for attr, info in res["attributes"].items():
        print(f"{attr} (spread {info['spread']:.1%})")
        for lv, (s, c, w) in sorted(info["levels"].items(), key=lambda kv: -kv[1][2]):
            print(f"  {lv}: chosen {c}/{s} = {w:.1%}")
        for lv, (w, absent, killer) in info["presence"].items():
            if absent is None:
                continue
            mark = "  <- killer signal" if killer else ""
            print(f"  {lv} present {w:.1%} vs absent {absent:.1%}{mark}")
    for price, (n, t, rate) in res["none_by_price"].items():
        print(f"none rate when {a.price_col} {price} shown: {n}/{t} = {rate:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
