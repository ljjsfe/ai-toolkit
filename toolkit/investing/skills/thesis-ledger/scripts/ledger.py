#!/usr/bin/env python3
"""Storage and arithmetic for thesis-ledger. One Markdown file per thesis, history append-only.

Theses live in $THESIS_DIR (default ~/.investing/theses/<TICKER>.md).

Usage:
  ledger.py new TICKER --side long|short [--expiry YYYY-MM-DD] [--date YYYY-MM-DD]
  ledger.py log TICKER --outcome intact|weakened|broken|insufficient --fact "..." \
                       --next YYYY-MM-DD --reason "next earnings" [--date YYYY-MM-DD]
  ledger.py close TICKER --as closed|invalidated --reason "..." [--date YYYY-MM-DD]
  ledger.py verify TICKER            # history chain intact, header consistent with history
  ledger.py book [--today YYYY-MM-DD]
  ledger.py calc growth OLD NEW | calc margin PART WHOLE | calc distance VALUE THRESHOLD

The skill fills the thesis, claims, kill criteria, pre-mortem, catalysts and promises sections
by editing the file; this script owns the header and the Status history table. Each history row
carries a short hash chained to the row before it, so `verify` catches an edited or deleted row;
the header (last_confirmed, last_check, latest_outcome, state) must match the history, which
catches a deleted final row or a closed thesis whose header was set back to open.
`log` with outcome `insufficient` leaves "last confirmed" unchanged (skill step 8).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
from datetime import date
from pathlib import Path

OUTCOMES = ("intact", "weakened", "broken", "insufficient")
HISTORY_HEADING = "## Status history"
HISTORY_HEADER = "| date | outcome | last confirmed | fact | chain |\n|---|---|---|---|---|"
CLOSING = {"closed as closed": "closed", "closed as invalidated": "invalidated"}
HEADER_KEYS = ("side", "expiry", "opened", "state", "last_confirmed", "last_check", "latest_outcome",
               "next_check", "next_reason")

TEMPLATE = """# {ticker} thesis

side: {side}
expiry: {expiry}
opened: {opened}
state: open
last_confirmed: none
last_check: none
latest_outcome: none
next_check: none
next_reason: none

## Thesis

(the business change, why the price does not reflect it, why now)

## Claims

| # | claim | KPI | threshold | by | baseline (source, as-of) |
|---|---|---|---|---|---|

## Kill criteria

| # | criterion | paired pre-mortem cause |
|---|---|---|

## Pre-mortem ({premortem})

## Catalysts

| date | event | claim tested | result that counts against |
|---|---|---|---|

## Promises

| promise | source | date | status |
|---|---|---|---|

{history_heading}

{history_header}
"""


def thesis_dir() -> Path:
    return Path(os.environ.get("THESIS_DIR", Path.home() / ".investing" / "theses"))


def path_for(ticker: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9.\-]{1,15}", ticker):
        raise ValueError(f"ticker {ticker!r} has unexpected characters")
    return thesis_dir() / f"{ticker.upper()}.md"


def iso(d: str | None) -> str:
    if d is None:
        return date.today().isoformat()
    date.fromisoformat(d)
    return d


def read_header(text: str) -> dict[str, str]:
    head = text.split("\n## ", 1)[0]
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^([a-z_]+):\s*(.*)$", head, re.M)}


def set_header(text: str, key: str, value: str) -> str:
    head, sep, rest = text.partition("\n## ")
    head, n = re.subn(rf"^{key}:.*$", f"{key}: {value}", head, count=1, flags=re.M)
    if n != 1:
        raise ValueError(f"header field {key} not found")
    return head + sep + rest


def history_rows(text: str) -> list[list[str]]:
    if HISTORY_HEADING not in text:
        raise ValueError("no Status history section")
    tail = text.split(HISTORY_HEADING, 1)[1]
    rows = []
    for ln in tail.splitlines():
        if ln.startswith("|") and not ln.startswith("|---") and not ln.startswith("| date |"):
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif ln.startswith("## "):
            break
    return rows


def chain(prev: str, cells: list[str]) -> str:
    return hashlib.sha256((prev + "\x1f" + "\x1f".join(cells)).encode("utf-8")).hexdigest()[:10]


def append_row(text: str, cells: list[str]) -> str:
    rows = history_rows(text)
    prev = rows[-1][-1] if rows else "genesis"
    clean = [c.replace("|", "/").replace("\n", " ") for c in cells]
    line = "| " + " | ".join(clean + [chain(prev, clean)]) + " |"
    return text.rstrip("\n") + "\n" + line + "\n"


def verify_text(text: str) -> list[str]:
    errors = []
    header = read_header(text)
    for k in HEADER_KEYS:
        if k not in header:
            errors.append(f"header field {k} is missing")
    prev, last_date = "genesis", ""
    last_confirmed, last_check, latest_outcome, state = "none", "none", "none", "open"
    for i, row in enumerate(history_rows(text), 1):
        if len(row) != 5:
            errors.append(f"history row {i} has {len(row)} cells, expected 5")
            continue
        if row[4] != chain(prev, row[:4]):
            errors.append(f"history row {i} was edited, or a row before it was removed (chain mismatch)")
        if row[0] < last_date:
            errors.append(f"history row {i} is dated before the row above it")
        prev, last_date = row[4], row[0]
        if state != "open":
            errors.append(f"history row {i} comes after the thesis was {state}")
        if row[1] in CLOSING:
            state = CLOSING[row[1]]
            continue
        if row[1] in OUTCOMES:
            last_check, latest_outcome = row[0], row[1]
        if row[1] in ("intact", "weakened", "broken"):
            last_confirmed = f"{row[1]} ({row[0]})"
    # the final row has no successor whose chain would break, so the header is checked against it
    for key, want in (("last_confirmed", last_confirmed), ("last_check", last_check),
                      ("latest_outcome", latest_outcome), ("state", state)):
        if header.get(key) != want:
            errors.append(f"header {key} is {header.get(key)!r} but history says {want!r}")
    return errors


def cmd_new(a: argparse.Namespace) -> str:
    p = path_for(a.ticker)
    if p.exists():
        raise ValueError(f"{p} exists; a thesis is never overwritten")
    opened = iso(a.date)
    y, m, d = map(int, opened.split("-"))
    try:
        premortem = date(y + 1, m, d).isoformat()
    except ValueError:  # 29 February
        premortem = date(y + 1, m, 28).isoformat()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(TEMPLATE.format(ticker=a.ticker.upper(), side=a.side, expiry=a.expiry or "none",
                                 opened=opened, premortem=premortem, history_heading=HISTORY_HEADING,
                                 history_header=HISTORY_HEADER), encoding="utf-8")
    return f"created {p}; fill every section before the first check"


def cmd_log(a: argparse.Namespace) -> str:
    p = path_for(a.ticker)
    text = p.read_text(encoding="utf-8")
    errors = verify_text(text)
    if errors:
        raise ValueError("refusing to append to a ledger that fails verify:\n  " + "\n  ".join(errors))
    header = read_header(text)
    if header.get("state") != "open":
        raise ValueError(f"thesis is {header.get('state')}; open a new one instead")
    when = iso(a.date)
    rows = history_rows(text)
    if rows and when < rows[-1][0]:
        raise ValueError(f"date {when} is before the last check {rows[-1][0]}")
    nxt = iso(a.next)
    if nxt <= when:
        raise ValueError("--next must be after the check date")
    confirmed = header["last_confirmed"]
    if a.outcome != "insufficient":
        confirmed = f"{a.outcome} ({when})"
    text = append_row(text, [when, a.outcome, confirmed, a.fact])
    for k, v in (("last_confirmed", confirmed), ("last_check", when), ("latest_outcome", a.outcome),
                 ("next_check", nxt), ("next_reason", a.reason)):
        text = set_header(text, k, v)
    p.write_text(text, encoding="utf-8")
    return f"logged {a.outcome} for {a.ticker.upper()} on {when}; last confirmed: {confirmed}; next check {nxt}"


def cmd_close(a: argparse.Namespace) -> str:
    p = path_for(a.ticker)
    text = p.read_text(encoding="utf-8")
    errors = verify_text(text)
    if errors:
        raise ValueError("ledger fails verify:\n  " + "\n  ".join(errors))
    when = iso(a.date)
    header = read_header(text)
    if header.get("state") != "open":
        raise ValueError(f"thesis is already {header.get('state')}")
    rows = history_rows(text)
    if rows and when < rows[-1][0]:
        raise ValueError(f"date {when} is before the last check {rows[-1][0]}")
    text = append_row(text, [when, f"closed as {a.as_}", header["last_confirmed"], a.reason])
    text = set_header(set_header(text, "state", a.as_), "next_check", "none")
    p.write_text(text, encoding="utf-8")
    return f"{a.ticker.upper()} marked {a.as_} on {when}"


def cmd_book(today: str) -> str:
    rows = ["| ticker | side | state | last confirmed | latest outcome | last check | next check | overdue |",
            "|---|---|---|---|---|---|---|---|"]
    files = sorted(thesis_dir().glob("*.md")) if thesis_dir().is_dir() else []
    for f in files:
        h = read_header(f.read_text(encoding="utf-8"))
        nxt = h.get("next_check", "none")
        overdue = "yes" if h.get("state") == "open" and nxt != "none" and nxt < today else "no"
        if h.get("state") == "open" and nxt == "none":
            overdue = "no check set"
        rows.append(f"| {f.stem} | {h.get('side')} | {h.get('state')} | {h.get('last_confirmed')} | "
                    f"{h.get('latest_outcome')} | {h.get('last_check')} | {nxt} | {overdue} |")
    return "\n".join(rows) if files else f"no theses in {thesis_dir()}"


def cmd_calc(kind: str, x: float, y: float) -> str:
    if kind == "growth":
        if x == 0:
            raise ValueError("growth from zero is undefined")
        r = y / x - 1
        return f"growth = {y} / {x} − 1 = {r:.4%}" + (" (base negative: read with care)" if x < 0 else "")
    if kind == "margin":
        if y == 0:
            raise ValueError("margin over zero is undefined")
        return f"margin = {x} / {y} = {x / y:.4%}"
    gap = x - y
    rel = f" ({gap / abs(y):+.2%} of threshold)" if y else ""
    return f"distance = value − threshold = {x} − {y} = {gap:+g}{rel}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new")
    n.add_argument("ticker")
    n.add_argument("--side", choices=("long", "short"), required=True)
    n.add_argument("--expiry")
    n.add_argument("--date")
    lg = sub.add_parser("log")
    lg.add_argument("ticker")
    lg.add_argument("--outcome", choices=OUTCOMES, required=True)
    lg.add_argument("--fact", required=True)
    lg.add_argument("--next", required=True)
    lg.add_argument("--reason", required=True)
    lg.add_argument("--date")
    c = sub.add_parser("close")
    c.add_argument("ticker")
    c.add_argument("--as", dest="as_", choices=("closed", "invalidated"), required=True)
    c.add_argument("--reason", required=True)
    c.add_argument("--date")
    v = sub.add_parser("verify")
    v.add_argument("ticker")
    b = sub.add_parser("book")
    b.add_argument("--today")
    k = sub.add_parser("calc")
    k.add_argument("kind", choices=("growth", "margin", "distance"))
    k.add_argument("x", type=float)
    k.add_argument("y", type=float)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "new":
            print(cmd_new(a))
        elif a.cmd == "log":
            print(cmd_log(a))
        elif a.cmd == "close":
            print(cmd_close(a))
        elif a.cmd == "verify":
            errors = verify_text(path_for(a.ticker).read_text(encoding="utf-8"))
            for e in errors:
                print(f"error: {e}")
            print("OK" if not errors else f"FAILED: {len(errors)} error(s)")
            return 1 if errors else 0
        elif a.cmd == "book":
            print(cmd_book(iso(a.today)))
        else:
            print(cmd_calc(a.kind, a.x, a.y))
    except (ValueError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
