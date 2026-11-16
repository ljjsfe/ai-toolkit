#!/usr/bin/env python3
"""Tests for new_specifics.py: additions are caught, rewording of existing facts is not."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import new_specifics as ns  # noqa: E402

BEFORE = "We cut build time from 14 minutes to 6 after moving tests into parallel shards.\n"


class NewSpecificsTests(unittest.TestCase):
    def kinds(self, after: str, sources: list[str] | None = None) -> list[tuple[str, str]]:
        return [(k, s) for k, s, _ in ns.new_specifics(BEFORE, after, sources or [])]

    def test_rewording_keeps_facts_and_passes(self) -> None:
        self.assertEqual(self.kinds("Moving tests into parallel shards took builds from 14 minutes down to 6.\n"), [])

    def test_added_number_name_and_quote_are_flagged(self) -> None:
        after = ("Builds fell from 14 minutes to 6, a 57% drop, after we followed advice from "
                 "the Google Testing Blog: \"parallelise everything you can\".\n")
        got = self.kinds(after)
        self.assertIn(("number", "57%"), got)
        self.assertIn(("name", "Google Testing Blog"), got)
        self.assertIn(("quote", "parallelise everything you can"), got)

    def test_sources_count_as_known(self) -> None:
        after = "Builds fell from 14 minutes to 6, a 57% drop.\n"
        self.assertEqual(self.kinds(after, ["Notes: drop was 57% per the CI dashboard."]), [])

    def test_dates_and_cjk_numbers(self) -> None:
        got = self.kinds("2026年3月，构建时间从14分钟降到6分钟，节省了约3万元。\n")
        self.assertIn(("date", "2026年3月"), got)
        self.assertTrue(any(k == "number" and "3万" in s for k, s in got), got)

    def test_number_formatting_is_normalised(self) -> None:
        before = "Revenue reached 1,200,000 dollars."
        self.assertEqual(ns.new_specifics(before, "Revenue reached 1200000 dollars.", []), [])

    def test_substring_of_known_number_or_name_is_still_new(self) -> None:
        got = self.kinds("Builds fell from 14 minutes to 6 for 4 engineers.\n")
        self.assertIn(("number", "4"), got)
        names = ns.new_specifics("We met Ada Lovelace Institute staff.", "We met, then Ada Love signed.", [])
        self.assertIn("Ada Love", [s for _, s, _ in names])
        self.assertEqual(ns.new_specifics("Ratio was 6.5 overall.", "Ratio was 6.5 overall.", []), [])
        self.assertIn("6", [s for _, s, _ in ns.new_specifics("Ratio was 6.5 overall.", "Ratio was 6.", [])])

    def test_name_does_not_run_into_the_next_sentence(self) -> None:
        # Seen in a live humanizer run: "...to GitHub Actions. Median build..." was flagged as the
        # new name "GitHub Actions. Median" although GitHub Actions was in the draft.
        before = "We moved our CI from Jenkins to GitHub Actions, and median build time fell."
        after = "We moved our CI from Jenkins to GitHub Actions. Median build time fell."
        self.assertEqual(ns.new_specifics(before, after, []), [])
        got = ns.new_specifics(before, "We then tried Buildkite Pipelines. Median time fell.", [])
        self.assertIn("Buildkite Pipelines", [s for _, s, _ in got])
        self.assertNotIn("Buildkite Pipelines. Median", [s for _, s, _ in got])
        for after, name in (
            ("We switched to the Vue.js Router for routing.", "Vue.js Router"),
            ("We met with Dr. Ada Smith yesterday.", "Dr. Ada Smith"),
            ("We flew to St. Louis on Monday.", "St. Louis"),
            ("It came from the U.S. Army archive.", "U.S. Army"),
        ):
            self.assertIn(name, [s for _, s, _ in ns.new_specifics("Plain text.", after, [])], after)

    def test_cli_exit_codes(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            b, a = Path(tmp, "b.md"), Path(tmp, "a.md")
            b.write_text(BEFORE, encoding="utf-8")
            a.write_text(BEFORE, encoding="utf-8")
            self.assertEqual(ns.main([str(b), str(a)]), 0)
            a.write_text(BEFORE + "It saved 3 engineers a week.\n", encoding="utf-8")
            self.assertEqual(ns.main([str(b), str(a)]), 1)


if __name__ == "__main__":
    unittest.main()
