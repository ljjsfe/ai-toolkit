#!/usr/bin/env python3
"""Minimum data probe for analysis-design: profile one CSV extract before analysing it.
Standard library only; reads the file, never modifies it.

Usage:
  profile_csv.py FILE.csv [--key COL[,COL...]] [--date COL]... [--today YYYY-MM-DD]
                 [--delimiter ,] [--json]

Reports:
  rows and columns;
  per column: null count and rate (empty or a null token such as NULL, NA, None, nan),
    distinct non-null values, and a flag when the null rate is above 5%;
  duplicate keys for --key (a composite key when several columns are given): how many key
    values occur more than once, how many rows they cover, a few examples, and rows whose key
    has a null part;
  for every date column (auto-detected when at least 95% of non-null values parse as ISO
    dates or datetimes, or forced with --date): min, max, unparsable values, values after
    --today (default: today), calendar days with no rows between min and max, and the
    timezone mix (naive values vs each UTC offset seen). Days are the value's own local date,
    not UTC, so 23:30-05:00 counts on its local day; with mixed offsets the day buckets differ
    from a UTC rollup.

Sentinel dates (year before 1900 or after 2999, such as 9999-12-31 "valid to" markers) are
counted separately and left out of min/max and the gap scan. Ragged rows (more or fewer fields
than the header) and duplicate header names are reported, never silently merged.

What it cannot see: whether the extract covers the population the decision is about, bot or
test traffic, join fan-out upstream of the export, or business-rule violations. Those stay
manual checks in the skill. Exit 0 after a report, 2 on bad input.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path

NULL_TOKENS = {"", "null", "na", "n/a", "none", "nan", "nil", "\\n"}
NULL_FLAG_RATE = 0.05
DATE_DETECT_SHARE = 0.95
EXAMPLES = 5
SENTINEL_BEFORE, SENTINEL_AFTER = 1900, 2999
MAX_GAP_SCAN_DAYS = 36_600  # ~100 years; beyond that the gap count is not meaningful


def is_null(value: str) -> bool:
    return value.strip().lower() in NULL_TOKENS


def parse_when(value: str) -> tuple[date, str] | None:
    """Return (calendar date, tz label) for an ISO date/datetime, else None.
    tz label is 'naive' or the UTC offset such as '+00:00'."""
    v = value.strip()
    if len(v) < 10 or not v[:4].isdigit():
        return None
    if v.endswith(("Z", "z")):
        v = v[:-1] + "+00:00"
    try:
        if len(v) == 10:
            return date.fromisoformat(v), "naive"
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.date(), "naive"
    off = dt.utcoffset() or timedelta(0)
    sign = "-" if off < timedelta(0) else "+"
    mins = abs(int(off.total_seconds())) // 60
    return dt.date(), f"{sign}{mins // 60:02d}:{mins % 60:02d}"


def missing_day_ranges(days: set[date]) -> tuple[int, list[str]]:
    """Calendar days between min and max that have no row, as a count and compact ranges."""
    if not days:
        return 0, []
    lo, hi = min(days), max(days)
    if (hi - lo).days > MAX_GAP_SCAN_DAYS:
        return -1, [f"span {lo.isoformat()}..{hi.isoformat()} too long to scan"]
    ranges: list[str] = []
    count = 0
    start: date | None = None
    d = lo
    while d <= hi:
        absent = d not in days
        if absent:
            count += 1
            if start is None:
                start = d
        elif start is not None:
            end = d - timedelta(days=1)
            ranges.append(start.isoformat() if start == end else f"{start.isoformat()}..{end.isoformat()}")
            start = None
        d += timedelta(days=1)
    if start is not None:
        ranges.append(start.isoformat() if start == hi else f"{start.isoformat()}..{hi.isoformat()}")
    return count, ranges


def profile(rows: list[dict[str, str]], columns: list[str], keys: list[str],
            force_dates: list[str], today: date) -> dict:
    n = len(rows)
    out: dict = {"rows": n, "columns": len(columns), "column_profiles": [], "dates": [], "keys": None,
                 "rows_with_extra_fields": sum(1 for r in rows if None in r),
                 "rows_with_missing_fields": sum(1 for r in rows if any(v is None for k, v in r.items() if k is not None))}
    for col in columns:
        values = [r.get(col) or "" for r in rows]
        nulls = sum(1 for v in values if is_null(v))
        non_null = [v for v in values if not is_null(v)]
        rate = nulls / n if n else 0.0
        out["column_profiles"].append({
            "column": col, "nulls": nulls, "null_rate": round(rate, 4),
            "distinct": len(set(non_null)), "flag": rate > NULL_FLAG_RATE,
        })
        parsed = [parse_when(v) for v in non_null]
        ok = [p for p in parsed if p is not None]
        detected = bool(non_null) and len(ok) / len(non_null) >= DATE_DETECT_SHARE
        if col in force_dates or detected:
            sentinels = [p for p in ok if not SENTINEL_BEFORE <= p[0].year <= SENTINEL_AFTER]
            ok = [p for p in ok if SENTINEL_BEFORE <= p[0].year <= SENTINEL_AFTER]
            days = {p[0] for p in ok}
            gap_count, gap_ranges = missing_day_ranges(days)
            out["dates"].append({
                "column": col,
                "min": min(days).isoformat() if days else None,
                "max": max(days).isoformat() if days else None,
                "unparsable": len(non_null) - len(ok) - len(sentinels),
                "sentinel_dates": dict(sorted(Counter(p[0].isoformat() for p in sentinels).most_common(EXAMPLES))),
                "after_today": sum(1 for p in ok if p[0] > today),
                "missing_days": gap_count,
                "missing_ranges": gap_ranges[:EXAMPLES],
                "timezones": dict(sorted(Counter(p[1] for p in ok).items())),
            })
    if keys:
        null_key_rows = 0
        counts: Counter = Counter()
        for r in rows:
            parts = tuple(r.get(k) or "" for k in keys)
            if any(is_null(p) for p in parts):
                null_key_rows += 1
                continue
            counts[parts] += 1
        dupes = {k: c for k, c in counts.items() if c > 1}
        out["keys"] = {
            "key": keys,
            "duplicate_values": len(dupes),
            "rows_in_duplicates": sum(dupes.values()),
            "null_key_rows": null_key_rows,
            "examples": [{"key": list(k), "count": c} for k, c in sorted(dupes.items(), key=lambda kv: -kv[1])[:EXAMPLES]],
        }
    return out


def render(p: dict) -> str:
    lines = [f"rows: {p['rows']}   columns: {p['columns']}"]
    if p.get("duplicate_headers"):
        lines.append(f"duplicate header names (renamed with #n): {', '.join(p['duplicate_headers'])}")
    if p["rows_with_extra_fields"] or p["rows_with_missing_fields"]:
        lines.append(f"ragged rows: {p['rows_with_extra_fields']} with extra fields, "
                     f"{p['rows_with_missing_fields']} with missing fields (missing fields count as null)")
    lines += ["", "column            nulls   null%   distinct"]
    for c in p["column_profiles"]:
        flag = "  > 5% null" if c["flag"] else ""
        lines.append(f"{c['column'][:16]:<16} {c['nulls']:>6} {c['null_rate'] * 100:>6.1f}% {c['distinct']:>9}{flag}")
    for d in p["dates"]:
        lines += ["", f"date column {d['column']}: {d['min']} .. {d['max']}",
                  f"  unparsable: {d['unparsable']}   after today: {d['after_today']}   "
                  f"missing days: {d['missing_days'] if d['missing_days'] >= 0 else 'not scanned'}"
                  + (f" ({', '.join(d['missing_ranges'])})" if d["missing_ranges"] else ""),
                  "  timezones: " + ", ".join(f"{k}={v}" for k, v in d["timezones"].items())]
        if d["sentinel_dates"]:
            lines.append("  sentinel dates (excluded above): " + ", ".join(f"{k}={v}" for k, v in d["sentinel_dates"].items()))
        if len(d["timezones"]) > 1:
            lines.append("  mixed timezones: normalise before bucketing by day")
    k = p["keys"]
    if k:
        lines += ["", f"key ({', '.join(k['key'])}): {k['duplicate_values']} duplicated values covering "
                      f"{k['rows_in_duplicates']} rows; {k['null_key_rows']} rows with a null key part"]
        for ex in k["examples"]:
            lines.append(f"  {ex['key']} x{ex['count']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Profile a CSV extract before analysis.")
    ap.add_argument("file")
    ap.add_argument("--key", default="", help="key column(s), comma-separated")
    ap.add_argument("--date", action="append", default=[], help="force a column to be read as a date")
    ap.add_argument("--today", default="", help="YYYY-MM-DD used for the after-today count")
    ap.add_argument("--delimiter", default=",")
    ap.add_argument("--encoding", default="utf-8-sig")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    path = Path(a.file)
    if not path.is_file():
        print(f"error: no such file {a.file}", file=sys.stderr)
        return 2
    try:
        today = date.fromisoformat(a.today) if a.today else date.today()
    except ValueError:
        print(f"error: --today must be YYYY-MM-DD, got {a.today!r}", file=sys.stderr)
        return 2
    try:
        with path.open(newline="", encoding=a.encoding) as fh:
            header = next(csv.reader(fh, delimiter=a.delimiter), [])
            seen: Counter = Counter()
            columns, dup = [], []
            for h in header:
                seen[h] += 1
                if seen[h] > 1:
                    dup.append(h)
                    h = f"{h}#{seen[h]}"
                columns.append(h)
            rows = list(csv.DictReader(fh, fieldnames=columns, delimiter=a.delimiter))
    except UnicodeDecodeError as e:
        print(f"error: {a.file} is not {a.encoding} ({e.reason} at byte {e.start}); pass --encoding, e.g. latin-1",
              file=sys.stderr)
        return 2
    if not columns:
        print("error: no header row", file=sys.stderr)
        return 2
    keys = [k.strip() for k in a.key.split(",") if k.strip()]
    unknown = [c for c in keys + a.date if c not in columns]
    if unknown:
        print(f"error: unknown column(s) {unknown}; header has {columns}", file=sys.stderr)
        return 2
    result = profile(rows, columns, keys, a.date, today)
    result["duplicate_headers"] = sorted(set(dup))
    print(json.dumps(result, indent=2) if a.json else render(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
