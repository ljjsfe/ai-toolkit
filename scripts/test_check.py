#!/usr/bin/env python3
"""Unit tests for scripts/check.py external.yaml trial governance."""
from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check  # noqa: E402


BASE_ENTRY = """\
- name: sample-tool
  category: engineering
  repo: https://github.com/example/sample-tool
  license: MIT
  tools: claude, codex, agy
  optional: true
  install:
    - npm install -g sample-tool@latest
"""


class ExternalTrialGovernanceTests(unittest.TestCase):
    def _parse(self, extra_yaml: str, today: date = date(2026, 11, 14)) -> list[str]:
        errors: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "external.yaml"
            p.write_text(BASE_ENTRY + extra_yaml, encoding="utf-8")
            check.parse_external_yaml(p, errors, today=today)
        return errors

    def test_regular_optional_entry_without_trial_passes(self) -> None:
        errors = self._parse("  notes: >\n    Optional helper installed when needed.\n")
        self.assertEqual(errors, [])

    def test_active_dated_trial_passes(self) -> None:
        errors = self._parse(
            "  status: trial\n"
            "  trial_start: 2026-11-10\n"
            "  trial_review_by: 2026-11-24\n"
            "  notes: >\n"
            "    Two-week evaluation on multi-step repo changes.\n",
            today=date(2026, 11, 14),
        )
        self.assertEqual(errors, [])

    def test_status_trial_missing_dates_fails(self) -> None:
        errors = self._parse("  status: trial\n")
        self.assertTrue(any("must declare trial_start" in e for e in errors), errors)
        self.assertTrue(any("must declare trial_review_by" in e for e in errors), errors)

    def test_unstarted_prose_trial_without_dates_fails(self) -> None:
        errors = self._parse(
            "  notes: >\n"
            "    Trial decided 2026-10-30, not yet started: two weeks from the start date.\n"
        )
        self.assertTrue(any("unstarted" in e for e in errors), errors)
        self.assertTrue(any("must declare trial_start" in e for e in errors), errors)
        self.assertTrue(any("must declare trial_review_by" in e for e in errors), errors)

    def test_chinese_trial_marker_without_dates_fails(self) -> None:
        errors = self._parse("  notes: >\n    2026-11-01 决定试用，两周后复盘。\n")
        self.assertTrue(any("must declare trial_start" in e for e in errors), errors)
        self.assertTrue(any("must declare trial_review_by" in e for e in errors), errors)

    def test_expired_trial_fails(self) -> None:
        errors = self._parse(
            "  status: trial\n"
            "  trial_start: 2026-10-30\n"
            "  trial_review_by: 2026-11-13\n",
            today=date(2026, 11, 14),
        )
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("trial expired on 2026-11-13", errors[0])

    def test_review_date_before_start_date_fails(self) -> None:
        errors = self._parse(
            "  status: trial\n"
            "  trial_start: 2026-11-20\n"
            "  trial_review_by: 2026-11-10\n",
            today=date(2026, 11, 14),
        )
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("earlier than trial_start", errors[0])

    def test_invalid_status_value_fails(self) -> None:
        errors = self._parse("  status: maybe-later\n")
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("invalid status", errors[0])


class SkillStructureAndPrefixValidationTests(unittest.TestCase):
    def test_valid_intra_and_cross_skill_section_refs_pass(self) -> None:
        bodies = {
            "alpha": (
                Path("toolkit/eng/skills/alpha/SKILL.md"),
                "## Iron laws\n\n1. First.\n2. Second.\n\n## Step 1 — Start\n\nSee law 2 and `beta` §2.\n",
            ),
            "beta": (
                Path("toolkit/eng/skills/beta/SKILL.md"),
                "## 1. Intro\n\n## 2. Harvest\n\nDone.\n",
            ),
        }
        errors: list[str] = []
        check.validate_skill_section_refs(bodies, errors)
        self.assertEqual(errors, [])

    def test_dangling_step_law_or_section_ref_fails(self) -> None:
        bodies = {
            "alpha": (
                Path("toolkit/eng/skills/alpha/SKILL.md"),
                "## Iron laws\n\n1. Only one.\n\n## 1. Body\n\nFollow Step 2, law 4, Pass 1, and `beta` §9.\n",
            ),
            "beta": (
                Path("toolkit/eng/skills/beta/SKILL.md"),
                "## 1. Only section\n",
            ),
        }
        errors: list[str] = []
        check.validate_skill_section_refs(bodies, errors)
        self.assertEqual(len(errors), 4, errors)

    def test_stale_install_external_prefix_fails(self) -> None:
        errors: list[str] = []
        with tempfile.TemporaryDirectory() as tmp:
            sh = Path(tmp) / "install.sh"
            sh.write_text('BASE_EXTERNAL_PREFIXES = (\n    "impeccable",\n    "openspec-",\n)\n', encoding="utf-8")
            externals = [{"name": "impeccable", "install": ["npx impeccable install"]}]
            check.validate_install_external_prefixes(sh, externals, errors)
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("openspec-", errors[0])


if __name__ == "__main__":
    unittest.main()
