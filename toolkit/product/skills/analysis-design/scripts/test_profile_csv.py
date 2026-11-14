#!/usr/bin/env python3
"""Tests for profile_csv.py. Expected values are counted by hand from the fixtures below."""
from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profile_csv  # noqa: E402

FIXTURE = """order_id,user_id,amount,created_at,channel
1,u1,10.5,2026-03-01T09:00:00Z,web
2,u2,,2026-03-01T10:00:00+00:00,web
2,u2,7,2026-03-02,NULL
3,,4,2026-03-05T23:30:00-05:00,app
4,u4,8,2026-03-06T08:00:00,app
5,u5,n/a,2027-01-01,app
"""


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = profile_csv.main(list(args))
    return code, out.getvalue(), err.getvalue()


class ParseTests(unittest.TestCase):
    def test_iso_forms(self) -> None:
        self.assertEqual(profile_csv.parse_when("2026-03-01"), (date(2026, 3, 1), "naive"))
        self.assertEqual(profile_csv.parse_when("2026-03-01T09:00:00Z"), (date(2026, 3, 1), "+00:00"))
        self.assertEqual(profile_csv.parse_when("2026-03-05T23:30:00-05:00"), (date(2026, 3, 5), "-05:00"))
        self.assertIsNone(profile_csv.parse_when("web"))
        self.assertIsNone(profile_csv.parse_when("2026-13-01"))
        self.assertIsNone(profile_csv.parse_when("10.5"))

    def test_missing_day_ranges(self) -> None:
        days = {date(2026, 3, 1), date(2026, 3, 2), date(2026, 3, 5), date(2026, 3, 7)}
        self.assertEqual(profile_csv.missing_day_ranges(days), (3, ["2026-03-03..2026-03-04", "2026-03-06"]))
        self.assertEqual(profile_csv.missing_day_ranges({date(2026, 3, 1)}), (0, []))
        self.assertEqual(profile_csv.missing_day_ranges(set()), (0, []))


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "orders.csv"
        self.path.write_text(FIXTURE, encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def profile(self, *extra: str) -> dict:
        code, out, _ = run(str(self.path), "--json", "--today", "2026-11-14", *extra)
        self.assertEqual(code, 0)
        return json.loads(out)

    def test_rows_nulls_distinct(self) -> None:
        p = self.profile()
        self.assertEqual((p["rows"], p["columns"]), (6, 5))
        cols = {c["column"]: c for c in p["column_profiles"]}
        self.assertEqual(cols["amount"]["nulls"], 2)            # "" and "n/a"
        self.assertEqual(cols["amount"]["null_rate"], 0.3333)
        self.assertTrue(cols["amount"]["flag"])
        self.assertEqual(cols["channel"]["nulls"], 1)           # "NULL"
        self.assertEqual(cols["channel"]["distinct"], 2)
        self.assertEqual(cols["order_id"]["nulls"], 0)
        self.assertFalse(cols["order_id"]["flag"])

    def test_date_detection_range_gaps_timezones(self) -> None:
        p = self.profile()
        self.assertEqual([d["column"] for d in p["dates"]], ["created_at"])  # amount is not a date
        d = p["dates"][0]
        self.assertEqual((d["min"], d["max"]), ("2026-03-01", "2027-01-01"))
        self.assertEqual(d["after_today"], 1)
        self.assertEqual(d["unparsable"], 0)
        self.assertEqual(d["timezones"], {"+00:00": 2, "-05:00": 1, "naive": 3})
        # 2026-03-01..2027-01-01 spans 307 days; 5 distinct days have rows.
        self.assertEqual(d["missing_days"], 302)
        self.assertEqual(d["missing_ranges"][0], "2026-03-03..2026-03-04")

    def test_duplicate_composite_key(self) -> None:
        k = self.profile("--key", "order_id")["keys"]
        self.assertEqual((k["duplicate_values"], k["rows_in_duplicates"], k["null_key_rows"]), (1, 2, 0))
        self.assertEqual(k["examples"], [{"key": ["2"], "count": 2}])
        k2 = self.profile("--key", "order_id,user_id")["keys"]
        self.assertEqual((k2["duplicate_values"], k2["null_key_rows"]), (1, 1))

    def test_forced_date_reports_unparsable(self) -> None:
        d = {x["column"]: x for x in self.profile("--date", "channel")["dates"]}["channel"]
        self.assertEqual((d["unparsable"], d["min"]), (5, None))

    def test_text_report_flags_mixed_timezones(self) -> None:
        code, out, _ = run(str(self.path), "--today", "2026-11-14", "--key", "order_id")
        self.assertEqual(code, 0)
        self.assertIn("rows: 6   columns: 5", out)
        self.assertIn("mixed timezones", out)
        self.assertIn("1 duplicated values covering 2 rows", out)

    def test_bad_input(self) -> None:
        self.assertEqual(run(str(self.path), "--key", "nope")[0], 2)
        self.assertEqual(run(str(self.path) + ".missing")[0], 2)
        self.assertEqual(run(str(self.path), "--today", "14/11/2026")[0], 2)
        empty = Path(self.tmp.name) / "empty.csv"
        empty.write_text("", encoding="utf-8")
        self.assertEqual(run(str(empty))[0], 2)


    def test_sentinel_dates_do_not_crash_or_skew_the_range(self) -> None:
        p = Path(self.tmp.name) / "scd.csv"
        p.write_text("id,valid_to\n1,2026-03-01\n2,9999-12-31\n3,2026-03-03\n4,0001-01-01\n", encoding="utf-8")
        code, out, _ = run(str(p), "--json", "--today", "2026-11-14")
        self.assertEqual(code, 0)
        d = json.loads(out)["dates"][0]
        self.assertEqual((d["min"], d["max"], d["missing_days"]), ("2026-03-01", "2026-03-03", 1))
        self.assertEqual(d["sentinel_dates"], {"0001-01-01": 1, "9999-12-31": 1})

    def test_non_utf8_ragged_rows_and_duplicate_headers(self) -> None:
        latin = Path(self.tmp.name) / "latin.csv"
        latin.write_bytes("name,city\nJos\xe9,M\xe1laga\n".encode("latin-1"))
        code, _, err = run(str(latin))
        self.assertEqual(code, 2)
        self.assertIn("--encoding", err)
        self.assertEqual(run(str(latin), "--encoding", "latin-1")[0], 0)
        rag = Path(self.tmp.name) / "rag.csv"
        rag.write_text("a,a,b\n1,2,3\n1,2,3,4\n1,2\n", encoding="utf-8")
        code, out, _ = run(str(rag), "--json")
        prof = json.loads(out)
        self.assertEqual(prof["duplicate_headers"], ["a"])
        self.assertEqual([c["column"] for c in prof["column_profiles"]], ["a", "a#2", "b"])
        self.assertEqual((prof["rows_with_extra_fields"], prof["rows_with_missing_fields"]), (1, 1))

if __name__ == "__main__":
    unittest.main()
