#!/usr/bin/env python3
"""Unit tests for scripts/check.py external.yaml trial governance."""
from __future__ import annotations

import sys
import tempfile
import unittest
from collections import OrderedDict
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


class SourceCoverageTests(unittest.TestCase):
    BODY = "## Iron laws\n\n1. **Build the reproduction** before theorising.\n"

    def _check(self, srcs: list[str]) -> list[str]:
        errors: list[str] = []
        check.validate_source_coverage("skill", srcs, self.BODY, errors)
        return errors

    def test_port_with_present_anchor_passes(self) -> None:
        self.assertEqual(self._check(['up/x (MIT) — repro first [port "build the reproduction"]']), [])

    def test_port_with_absent_anchor_fails(self) -> None:
        errors = self._check(['up/x (MIT) — read the full error [port "read the full error"]'])
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("not found", errors[0])

    def test_untagged_source_fails(self) -> None:
        self.assertEqual(len(self._check(["up/x (MIT) — something"])), 1)

    def test_short_or_missing_anchor_fails(self) -> None:
        self.assertEqual(len(self._check(['up/x [port "repro"]'])), 1)
        self.assertEqual(len(self._check(["up/x [port]"])), 1)

    def test_idea_and_gap_rules(self) -> None:
        self.assertEqual(self._check(["up/x — inspiration [idea]", "up/y — scripts [gap no SRM script]"]), [])
        self.assertEqual(len(self._check(["up/y [gap]"])), 1)
        self.assertEqual(len(self._check(["up/y [idea extra]"])), 1)

    def test_credits_split_into_sections(self) -> None:
        out = check.build_expected_credits(
            [("alpha", ['up/a — x [port "build the reproduction"]', "up/b — y [idea]", "up/c — z [gap no runner]"])],
            OrderedDict(),
            [],
        )
        port_i, idea_i, gap_i = out.index("## Ported"), out.index("## Ideas drawn on"), out.index("## Known gaps")
        self.assertLess(port_i, out.index("- up/a — x — used in: alpha"))
        self.assertLess(idea_i, out.index("- up/b — y — used in: alpha"))
        self.assertIn("- up/c — z — missing: no runner — used in: alpha", out[gap_i:])


class YamlStrictnessTests(unittest.TestCase):
    def test_values_a_real_yaml_loader_would_reject_or_truncate(self) -> None:
        self.assertIsNone(check.yaml_value_problem('"plain json string"'))
        self.assertIsNone(check.yaml_value_problem("'it''s fine [port \"abc\"]'"))
        self.assertIsNone(check.yaml_value_problem("upstream/x (MIT) — y [port \"abcdefghijklm\"]"))
        self.assertIn("unescaped", check.yaml_value_problem('"a [port "b"] c"'))
        self.assertIn("lone", check.yaml_value_problem("'don't'"))
        self.assertIn("comment", check.yaml_value_problem("ce-debug (MIT, PR #2039) — z [idea]"))

    def test_frontmatter_errors_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "toolkit" / "x" / "skills" / "demo"
            d.mkdir(parents=True)
            smd = d / "SKILL.md"
            smd.write_text('---\nname: demo\ndescription: d\nversion: 1.0.0\nsources:\n'
                           '  - "bad [port "quoted"] item"\n  - fix (PR #12) [idea]\n---\n# Demo\n',
                           encoding="utf-8")
            errors: list[str] = []
            saved, check.ROOT = check.ROOT, Path(tmp)
            try:
                check.parse_skill_frontmatter(smd, errors)
            finally:
                check.ROOT = saved
        self.assertEqual(len(errors), 2, errors)


if __name__ == "__main__":
    unittest.main()
