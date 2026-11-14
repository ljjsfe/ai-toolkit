#!/usr/bin/env python3
"""Fetch the macro-regime dashboard from FRED (no API key) and compare it with the last saved one.

Usage:
  fred_dashboard.py dashboard [--dir ~/.investing/macro] [--no-save]
  fred_dashboard.py series UNRATE T10Y3M ...         # latest and prior value of any FRED series

Every figure comes from https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES> and carries
its own observation date. `dashboard` prints the ten rows of the skill (nine plus recession
signals), derived values with their formula, and — when an earlier snapshot exists in --dir —
each signal's previous reading, so "sustained" can be judged across releases. A series that
cannot be fetched is reported as missing; the skill then does not classify the regime.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import io
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen

FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}&cosd={}"
HISTORY_DAYS = 3 * 366  # enough for 12-month changes and the 24-month inversion window
SERIES = {
    "growth": ["A191RL1Q225SBEA", "PAYEMS", "GACDISA066MSFRBNY", "GACDFSA066MSFRBPHI"],
    "inflation": ["PCEPILFE", "CPILFESL"],
    "labour": ["UNRATE", "JTSJOL", "UNEMPLOY"],
    "policy": ["DFEDTARU", "DFEDTARL", "DFF"],
    "real rates": ["DFII10", "DGS10", "T10YIE"],
    "curve": ["T10Y2Y", "T10Y3M"],
    "credit": ["BAMLH0A0HYM2"],
    "financial conditions": ["NFCI", "WALCL"],
    "dollar": ["DTWEXBGS"],
    "recession": ["SAHMREALTIME", "RECPROUSM156N"],
}
Obs = list[tuple[str, float]]


def fetch_csv(series_id: str, timeout: float = 30) -> str:
    start = (date.today() - timedelta(days=HISTORY_DAYS)).isoformat()
    # Keep urllib's default User-Agent: FRED stalls custom and browser-like agents until timeout.
    req = Request(FRED_CSV.format(series_id, start))
    with urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https host)
        return resp.read().decode("utf-8")


def parse_csv(text: str) -> Obs:
    """FRED CSV → [(date, value)], skipping the '.' FRED writes for a missing observation."""
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or len(rows[0]) < 2:
        raise ValueError("not a FRED CSV")
    out = []
    for r in rows[1:]:
        if len(r) >= 2 and r[1] not in ("", "."):
            out.append((r[0], float(r[1])))
    if not out:
        raise ValueError("no observations")
    return out


def load(ids: list[str], fetcher=fetch_csv) -> tuple[dict[str, Obs], dict[str, str]]:
    data, missing = {}, {}

    def one(sid: str) -> tuple[str, Obs | None, str]:
        try:
            return sid, parse_csv(fetcher(sid)), ""
        except Exception as e:  # noqa: BLE001 — any failure makes the row missing, never guessed
            return sid, None, f"{type(e).__name__}: {e}"[:120]

    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        for sid, obs, err in ex.map(one, ids):
            if obs is None:
                missing[sid] = err
            else:
                data[sid] = obs
    return data, missing


def _latest(obs: Obs, back: int = 0) -> tuple[str, float]:
    return obs[-1 - back]


def pct_change(obs: Obs, periods: int) -> float:
    return obs[-1][1] / obs[-1 - periods][1] - 1


def annualised(obs: Obs, periods: int, per_year: int) -> float:
    return (obs[-1][1] / obs[-1 - periods][1]) ** (per_year / periods) - 1


def inversion_stats(obs: Obs) -> dict:
    """Months (of the last 24, by month-end reading) with 10y−3m below zero, and the current run."""
    month_end: dict[str, float] = {}
    for d, v in obs:
        month_end[d[:7]] = v
    months = sorted(month_end)[-24:]
    inverted = [m for m in months if month_end[m] < 0]
    run = 0
    for m in reversed(months):
        if month_end[m] < 0:
            run += 1
        else:
            break
    last_inverted = inverted[-1] if inverted else None
    return {"months_inverted_of_last_24": len(inverted), "current_inverted_run_months": run,
            "last_inverted_month": last_inverted}


def build(data: dict[str, Obs], missing: dict[str, str]) -> dict:
    rows: dict[str, dict] = {}

    def have(*ids: str) -> bool:
        return all(i in data for i in ids)

    def obs(sid: str, back: int = 0) -> dict:
        d, v = _latest(data[sid], back)
        return {"value": v, "date": d}

    def row(name: str, ids: list[str], fill) -> None:
        gone = [i for i in ids if i not in data]
        rows[name] = {"missing": {i: missing.get(i, "not fetched") for i in gone}} if gone else fill()

    row("growth", SERIES["growth"], lambda: {
        "real_gdp_qoq_saar_pct": obs("A191RL1Q225SBEA"),
        "real_gdp_prior": obs("A191RL1Q225SBEA", 1),
        "payrolls_3m_avg_change_k": {
            "value": round((data["PAYEMS"][-1][1] - data["PAYEMS"][-4][1]) / 3, 1),
            "date": data["PAYEMS"][-1][0], "formula": "(PAYEMS[t] − PAYEMS[t−3]) / 3"},
        "ny_fed_survey": obs("GACDISA066MSFRBNY"), "philly_fed_survey": obs("GACDFSA066MSFRBPHI"),
    })

    def infl(sid: str) -> dict:
        return {"yoy_pct": round(100 * pct_change(data[sid], 12), 2),
                "3m_annualised_pct": round(100 * annualised(data[sid], 3, 12), 2),
                "date": data[sid][-1][0], "formula": "x[t]/x[t−12] − 1; (x[t]/x[t−3])^4 − 1"}
    row("inflation", SERIES["inflation"], lambda: {"core_pce": infl("PCEPILFE"), "core_cpi": infl("CPILFESL")})
    row("labour", SERIES["labour"], lambda: {
        "unemployment_pct": obs("UNRATE"), "unemployment_prior": obs("UNRATE", 1),
        "openings_per_unemployed": {"value": round(data["JTSJOL"][-1][1] / _match(data["UNEMPLOY"], data["JTSJOL"][-1][0]), 2),
                                    "date": data["JTSJOL"][-1][0], "formula": "JTSJOL / UNEMPLOY (same month)"},
    })
    row("policy", SERIES["policy"], lambda: {
        "target_range_pct": {"value": [data["DFEDTARL"][-1][1], data["DFEDTARU"][-1][1]], "date": data["DFEDTARU"][-1][0]},
        "effective_pct": obs("DFF"),
        "neutral_estimate": "read the latest FOMC Summary of Economic Projections (longer-run median); not on this feed",
    })
    row("real rates", SERIES["real rates"], lambda: {
        "real_10y_pct": obs("DFII10"), "nominal_10y_pct": obs("DGS10"), "breakeven_10y_pct": obs("T10YIE"),
    })
    row("curve", SERIES["curve"], lambda: {"2s10s_pct": obs("T10Y2Y"), "3m10y_pct": obs("T10Y3M")})
    row("credit", SERIES["credit"], lambda: {"hy_oas_pct": obs("BAMLH0A0HYM2"),
                                             "hy_oas_3m_ago": obs("BAMLH0A0HYM2", min(63, len(data["BAMLH0A0HYM2"]) - 1))})
    row("financial conditions", SERIES["financial conditions"], lambda: {
        "nfci": obs("NFCI"), "nfci_prior": obs("NFCI", 1),
        "fed_balance_sheet_13w_change_pct": {"value": round(100 * pct_change(data["WALCL"], 13), 2),
                                             "date": data["WALCL"][-1][0], "formula": "WALCL[t]/WALCL[t−13w] − 1"},
    })
    row("dollar", SERIES["dollar"], lambda: {
        "broad_dollar": obs("DTWEXBGS"),
        "3m_change_pct": {"value": round(100 * pct_change(data["DTWEXBGS"], min(63, len(data["DTWEXBGS"]) - 1)), 2),
                          "date": data["DTWEXBGS"][-1][0]},
    })
    rec_ids = SERIES["recession"] + ["T10Y3M"]
    row("recession", rec_ids, lambda: {
        "sahm_realtime_pp": dict(obs("SAHMREALTIME"), triggered=data["SAHMREALTIME"][-1][1] >= 0.5,
                                 rule="triggered at 0.50 or above"),
        "smoothed_recession_probability_pct": obs("RECPROUSM156N"),
        "yield_curve_inversion": inversion_stats(data["T10Y3M"]),
    })
    complete = not any("missing" in r for r in rows.values())
    return {"as_of_run": date.today().isoformat(), "source": "FRED fredgraph.csv",
            "complete": complete, "rows": rows,
            "note": None if complete else "rows missing: the skill does not classify the regime"}


def _match(obs: Obs, when: str) -> float:
    for d, v in reversed(obs):
        if d <= when:
            return v
    return obs[0][1]


def signals(snapshot: dict) -> dict[str, object]:
    """The few readings whose persistence across releases matters for a regime call."""
    r = snapshot["rows"]
    out: dict[str, object] = {}
    try:
        out["core_pce_3m_above_yoy"] = r["inflation"]["core_pce"]["3m_annualised_pct"] > r["inflation"]["core_pce"]["yoy_pct"]
        out["curve_3m10y_inverted"] = r["curve"]["3m10y_pct"]["value"] < 0
        out["sahm_triggered"] = r["recession"]["sahm_realtime_pp"]["triggered"]
        out["unemployment_rising"] = r["labour"]["unemployment_pct"]["value"] > r["labour"]["unemployment_prior"]["value"]
        out["nfci_tighter_than_prior"] = r["financial conditions"]["nfci"]["value"] > r["financial conditions"]["nfci_prior"]["value"]
    except (KeyError, TypeError):
        pass
    return out


def compare(current: dict, previous: dict | None) -> dict:
    if not previous:
        return {"previous": None, "note": "no earlier snapshot; nothing can be called sustained yet"}
    now, before = signals(current), signals(previous)
    return {"previous": previous.get("as_of_run"),
            "signals": {k: {"now": v, "previous": before.get(k),
                            "sustained": before.get(k) == v}
                        for k, v in now.items()}}


def main(argv: list[str] | None = None, fetcher=fetch_csv) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dashboard")
    d.add_argument("--dir", type=Path, default=Path.home() / ".investing" / "macro")
    d.add_argument("--no-save", action="store_true")
    s = sub.add_parser("series")
    s.add_argument("ids", nargs="+")
    a = ap.parse_args(argv)

    if a.cmd == "series":
        data, missing = load(a.ids, fetcher)
        out = {sid: {"latest": obs[-1], "prior": obs[-2] if len(obs) > 1 else None} for sid, obs in data.items()}
        out.update({sid: {"missing": why} for sid, why in missing.items()})
        print(json.dumps(out, indent=2))
        return 1 if missing else 0

    ids = sorted({i for v in SERIES.values() for i in v} | {"T10Y3M"})
    data, missing = load(ids, fetcher)
    snap = build(data, missing)
    previous = None
    if a.dir.is_dir():
        earlier = sorted(p for p in a.dir.glob("*.json") if p.stem < snap["as_of_run"])
        if earlier:
            previous = json.loads(earlier[-1].read_text(encoding="utf-8"))
    snap["comparison"] = compare(snap, previous)
    if not a.no_save:
        a.dir.mkdir(parents=True, exist_ok=True)
        (a.dir / f"{snap['as_of_run']}.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")
        snap["saved_to"] = str(a.dir / f"{snap['as_of_run']}.json")
    print(json.dumps(snap, indent=2))
    return 0 if snap["complete"] else 1


if __name__ == "__main__":
    sys.exit(main())
