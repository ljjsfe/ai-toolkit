#!/usr/bin/env python3
"""Tests for spec_check.py; fixtures follow the delta format shown in the spec skill."""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec_check  # noqa: E402

PROPOSAL = """# Session hardening

## Why
Stolen sessions survive a password change today, which the March incident review showed attackers rely on.

## What changes
- auth-session: revoke other sessions on password change

## Non-goals
- MFA

## Decisions needing sign-off
None
"""

LIVING = """# Auth Session

## Purpose
Manages interactive user session lifecycle, rotation, and revocation across devices.

## Requirements

### Requirement: [REQ-AUTH-002] Idle session expiration
The system SHALL expire an interactive session after 12 hours of inactivity.

#### Scenario: Request within idle window extends activity timestamp
- **WHEN** an authenticated request arrives 11 hours after the prior request
- **THEN** the request succeeds and the idle window resets

#### Scenario: Idle session is rejected
- **WHEN** a request arrives 13 hours after the prior request
- **THEN** it fails with HTTP 401

### Requirement: [REQ-AUTH-003] Legacy query-string session token
The system SHALL accept a session token in the query string.

#### Scenario: Token in query string
- **WHEN** a request carries ?session=abc
- **THEN** it is authenticated

### Requirement: [REQ-AUTH-004] Login rate throttle
The system SHALL reject more than 10 login attempts per minute per account.

#### Scenario: Eleventh attempt
- **WHEN** an account makes an eleventh attempt within a minute
- **THEN** it is rejected with HTTP 429
"""

FULL_MODIFIED = """### Requirement: [REQ-AUTH-002] Idle session expiration
The system SHALL expire an interactive session after 24 hours of inactivity.

#### Scenario: Request within idle window extends activity timestamp
- **WHEN** an authenticated request arrives 23 hours after the prior request
- **THEN** the request succeeds and the idle window resets to 24 hours

#### Scenario: Idle session is rejected
- **WHEN** a request arrives 25 hours after the prior request
- **THEN** it fails with HTTP 401
"""

DELTA = """# Auth Session (Delta)

## ADDED Requirements

### Requirement: [REQ-AUTH-001] Session revocation on password change
The system SHALL revoke every active session of a user other than the initiating session when that user changes their password.

#### Scenario: Concurrent device session is rejected after password change
- **WHEN** an authenticated user changes their password from session A while session B is active
- **THEN** the next request authenticated with session B fails with HTTP 401

## MODIFIED Requirements

{modified}
## REMOVED Requirements

### Requirement: [REQ-AUTH-003] Legacy query-string session token
**Reason**: Query-string tokens leak through referrer headers.

## RENAMED Requirements

- FROM: `### Requirement: [REQ-AUTH-004] Login rate throttle`
- TO: `### Requirement: [REQ-AUTH-004] Credential-stuffing rate limit`
"""


class Fixture:
    def __init__(self, delta: str = DELTA.format(modified=FULL_MODIFIED), proposal: str = PROPOSAL,
                 living: str | None = LIVING) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.change = root / "specs" / "changes" / "harden-sessions"
        self.specs = root / "specs"
        (self.change / "specs" / "auth-session").mkdir(parents=True)
        (self.change / "proposal.md").write_text(proposal, encoding="utf-8")
        (self.change / "tasks.md").write_text("- [ ] 1.1 revoke sessions [REQ-AUTH-001]\n", encoding="utf-8")
        (self.change / "specs" / "auth-session" / "spec.md").write_text(delta, encoding="utf-8")
        self.living = self.specs / "auth-session" / "spec.md"
        if living is not None:
            self.living.parent.mkdir(parents=True, exist_ok=True)
            self.living.write_text(living, encoding="utf-8")

    def __enter__(self) -> "Fixture":
        return self

    def __exit__(self, *exc: object) -> None:
        self.tmp.cleanup()


class ValidateTests(unittest.TestCase):
    def test_skill_example_is_valid(self) -> None:
        with Fixture() as f:
            errors, _ = spec_check.validate_change(f.change)
            self.assertEqual(errors, [])

    def test_format_errors_are_caught(self) -> None:
        bad = """# X (Delta)

## Notes
### Requirement: Stray requirement
The system SHALL do a thing.

## ADDED Requirements

### Requirement: No keyword
The system does a thing.

- **Scenario**: bullet scenario

### Requirement: No then
The system SHALL log in.

#### Scenario: only when
- **WHEN** a user logs in

## MODIFIED Requirements

### Requirement: No keyword
The system SHALL do it.

#### Scenario: s
- **WHEN** a **THEN** b

## RENAMED Requirements

- FROM: `### Requirement: Old`
"""
        with Fixture(delta=bad) as f:
            errors, _ = spec_check.validate_change(f.change)
        text = "\n".join(errors)
        for needle in ("not a delta section", "no SHALL or MUST", "scenario as a bullet",
                       "needs at least one", "needs both WHEN and THEN", "both ADDED and MODIFIED",
                       "no matching TO"):
            self.assertIn(needle, text)

    def test_proposal_rules(self) -> None:
        with Fixture(proposal="# P\n\n## Why\nToo short.\n") as f:
            errors, _ = spec_check.validate_change(f.change)
        text = "\n".join(errors)
        self.assertIn("## Why is", text)
        self.assertIn("## What changes", text)
        self.assertIn("Decisions needing sign-off", text)

    def test_misplaced_delta_file(self) -> None:
        with Fixture() as f:
            (f.change / "specs" / "loose.md").write_text("x", encoding="utf-8")
            errors, _ = spec_check.validate_change(f.change)
        self.assertTrue(any("ignored" in e for e in errors))

    def test_modified_must_use_new_name_after_rename(self) -> None:
        delta = DELTA.format(modified=FULL_MODIFIED.replace("[REQ-AUTH-002] Idle session expiration",
                                                            "[REQ-AUTH-004] Login rate throttle"))
        with Fixture(delta=delta) as f:
            errors, _ = spec_check.validate_change(f.change)
        self.assertTrue(any("old name" in e for e in errors), errors)


class TaskTests(unittest.TestCase):
    def check(self, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tasks.md"
            p.write_text(text, encoding="utf-8")
            return spec_check.check_tasks(p)

    def test_plain_bullets_count_as_zero_tasks(self) -> None:
        errors = self.check("# Tasks\n\n## 1. Revoke\n- 1.1 revoke sessions\n- 1.2 add test\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("tasks.md:4: no task is a checkbox", errors[0])

    def test_bullets_inside_fences_and_comments_are_ignored(self) -> None:
        errors = self.check("<!-- - draft\n- note -->\n```\n- sample output\n```\n")
        self.assertEqual(errors, ["tasks.md: no task is a checkbox, so progress counts 0 tasks and nothing "
                                  'reads as unfinished; write each task as "- [ ] 1.1 <behaviour delivered>"'])

    def test_checkbox_variants_count(self) -> None:
        self.assertEqual(self.check("1. [ ] a\n+ [x] b\n* [~] c\n"), [])

    def test_task_in_wrong_group_and_duplicate_id(self) -> None:
        text = ("## 1. Sessions\n- [ ] 1.1 revoke\n- [ ] 2.1 misplaced\n\n"
                "## 2. Audit\n- [x] 2.1 log revocations\n- [ ] 2.1 again\n\n## Notes\n- [ ] 9.9 unnumbered group\n")
        joined = "\n".join(self.check(text))
        self.assertIn('tasks.md:3: task "2.1" sits under group 1', joined)
        self.assertIn('tasks.md:7: task ID "2.1" is duplicated (first on line 3)', joined)
        self.assertNotIn("9.9", joined)

    def test_validate_reports_task_errors(self) -> None:
        with Fixture() as f:
            (f.change / "tasks.md").write_text("- revoke sessions\n", encoding="utf-8")
            errors, _ = spec_check.validate_change(f.change)
        self.assertTrue(any("no task is a checkbox" in e for e in errors), errors)


class PurposeTests(unittest.TestCase):
    def test_placeholder_rules(self) -> None:
        cases = {
            "TBD - created by archiving change x. Update Purpose after archive.": True,
            "TODO write this later": True,
            "todo: fill in": True,
            "tbd.": True,
            "Todo el flujo de sesiones de usuario.": False,
            "The retry budget is TBD pending benchmarks.": False,
            "TODOs are tracked elsewhere; this manages sessions.": False,
            "```\nTBD - example\n```\nManages sessions across devices.": False,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertIs(spec_check.purpose_is_placeholder(text.splitlines()), expected)

    def test_audit_and_validate_reject_placeholder_purpose(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "spec.md"
            p.write_text(LIVING.replace("Manages interactive", "TBD. Manages interactive"), encoding="utf-8")
            self.assertTrue(any("placeholder" in e for e in spec_check.audit_living(p)))
        delta = DELTA.format(modified=FULL_MODIFIED).split("## MODIFIED Requirements")[0].replace(
            "## ADDED", "## Purpose\nTODO\n\n## ADDED")
        with Fixture(delta=delta, living=None) as f:
            errors, _ = spec_check.validate_change(f.change)
        self.assertTrue(any("placeholder" in e for e in errors), errors)


class MergeTests(unittest.TestCase):
    def test_merge_applies_all_four_operations(self) -> None:
        with Fixture() as f:
            spec_check.merge_change(f.change, f.specs, write=True, retire=set())
            text = f.living.read_text(encoding="utf-8")
            self.assertIn("[REQ-AUTH-001] Session revocation", text)
            self.assertIn("24 hours of inactivity", text)
            self.assertIn("Idle session is rejected", text)
            self.assertNotIn("Legacy query-string", text)
            self.assertIn("Credential-stuffing rate limit", text)
            self.assertNotIn("Login rate throttle", text)
            self.assertEqual(spec_check.audit_living(f.living), [])

    def test_partial_modified_block_aborts_and_writes_nothing(self) -> None:
        partial = FULL_MODIFIED.split("#### Scenario: Idle session is rejected")[0]
        with Fixture(delta=DELTA.format(modified=partial)) as f:
            before = f.living.read_text(encoding="utf-8")
            with self.assertRaises(spec_check.MergeError) as cm:
                spec_check.merge_change(f.change, f.specs, write=True, retire=set())
            self.assertIn("Idle session is rejected", str(cm.exception))
            self.assertEqual(f.living.read_text(encoding="utf-8"), before)

    def test_near_miss_header_aborts(self) -> None:
        delta = DELTA.format(modified=FULL_MODIFIED.replace("Idle session expiration", "idle  Session expiration", 1))
        with Fixture(delta=delta) as f:
            with self.assertRaises(spec_check.MergeError) as cm:
                spec_check.merge_change(f.change, f.specs, write=False, retire=set())
        self.assertIn("match it exactly", str(cm.exception))

    def test_rename_target_collision_aborts(self) -> None:
        living = LIVING.replace("[REQ-AUTH-003] Legacy query-string session token",
                                "[REQ-AUTH-004] Credential-stuffing rate limit")
        delta = DELTA.format(modified=FULL_MODIFIED).split("## REMOVED Requirements")[0] + \
            "## RENAMED Requirements\n\n- FROM: `### Requirement: [REQ-AUTH-004] Login rate throttle`\n" \
            "- TO: `### Requirement: [REQ-AUTH-004] Credential-stuffing rate limit`\n"
        with Fixture(delta=delta, living=living) as f:
            with self.assertRaises(spec_check.MergeError) as cm:
                spec_check.merge_change(f.change, f.specs, write=False, retire=set())
        self.assertIn("already exists", str(cm.exception))

    def test_all_or_nothing_across_capabilities(self) -> None:
        with Fixture() as f:
            other = f.change / "specs" / "billing" / "invoices"
            other.mkdir(parents=True)
            (other / "spec.md").write_text(
                "# Invoices (Delta)\n\n## MODIFIED Requirements\n\n### Requirement: [REQ-BILL-001] Missing\n"
                "The system SHALL x.\n\n#### Scenario: s\n- **WHEN** a\n- **THEN** b\n", encoding="utf-8")
            before = f.living.read_text(encoding="utf-8")
            with self.assertRaises(spec_check.MergeError):
                spec_check.merge_change(f.change, f.specs, write=True, retire=set())
            self.assertEqual(f.living.read_text(encoding="utf-8"), before)

    def test_retiring_a_capability_needs_explicit_flag(self) -> None:
        living = LIVING.split("### Requirement: [REQ-AUTH-003]")[0]
        delta = ("# Auth Session (Delta)\n\n## REMOVED Requirements\n\n"
                 "### Requirement: [REQ-AUTH-002] Idle session expiration\n**Reason**: moved.\n")
        with Fixture(delta=delta, living=living) as f:
            with self.assertRaises(spec_check.MergeError) as cm:
                spec_check.merge_change(f.change, f.specs, write=True, retire=set())
            self.assertIn("--retire auth-session", str(cm.exception))
            spec_check.merge_change(f.change, f.specs, write=True, retire={"auth-session"})
            self.assertFalse(f.living.exists())

    def test_new_capability_needs_purpose(self) -> None:
        delta = DELTA.format(modified=FULL_MODIFIED).split("## MODIFIED Requirements")[0]
        with Fixture(delta=delta, living=None) as f:
            with self.assertRaises(spec_check.MergeError) as cm:
                spec_check.merge_change(f.change, f.specs, write=False, retire=set())
            self.assertIn("## Purpose", str(cm.exception))
            f.change.joinpath("specs/auth-session/spec.md").write_text(
                delta.replace("## ADDED", "## Purpose\nManages sessions across devices.\n\n## ADDED"), encoding="utf-8")
            spec_check.merge_change(f.change, f.specs, write=True, retire=set())
            self.assertEqual(spec_check.audit_living(f.living), [])


class AuditTests(unittest.TestCase):
    def test_audit_flags_changelog_and_delta_leftovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "spec.md"
            p.write_text(LIVING + "\n## ADDED Requirements\n\nAdded in v2.3 by PR #412.\n", encoding="utf-8")
            text = "\n".join(spec_check.audit_living(p))
        self.assertIn("leftover delta header", text)
        self.assertIn("changelog", text)

    def test_dates_inside_scenarios_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "spec.md"
            p.write_text(LIVING.replace("arrives 13 hours", "arrives on 2026-01-02, 13 hours"), encoding="utf-8")
            self.assertEqual(spec_check.audit_living(p), [])


class CliTests(unittest.TestCase):
    def test_cli_exit_codes(self) -> None:
        with Fixture() as f, redirect_stdout(io.StringIO()):
            self.assertEqual(spec_check.main(["validate", str(f.change)]), 0)
            self.assertEqual(spec_check.main(["merge", str(f.change), "--specs", str(f.specs)]), 0)
            self.assertEqual(spec_check.main(["audit", str(f.specs)]), 0)
            (f.change / "proposal.md").write_text("# P\n", encoding="utf-8")
            self.assertEqual(spec_check.main(["validate", str(f.change)]), 1)


if __name__ == "__main__":
    unittest.main()
