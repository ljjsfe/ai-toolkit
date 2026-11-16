#!/usr/bin/env python3
"""Tests for scripts/vendor_sync.py and the vendored checks in scripts/check.py (local git only)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check  # noqa: E402
import vendor_sync  # noqa: E402

GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
}


def run(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True,
                          env=GIT_ENV).stdout.strip()


def skill_md(name: str, body: str = "Body.") -> str:
    return f"---\nname: {name}\ndescription: test skill\n---\n\n{body}\n"


class VendorFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.up = base / "upstream"
        (self.up / "skills" / "alpha").mkdir(parents=True)
        (self.up / "skills" / "alpha" / "SKILL.md").write_text(skill_md("alpha"), encoding="utf-8")
        (self.up / "skills" / "alpha" / "NOTES.md").write_text("notes v1\n", encoding="utf-8")
        (self.up / "LICENSE").write_text("MIT License\n", encoding="utf-8")
        run(self.up, "init", "-q", "-b", "main")
        run(self.up, "add", ".")
        run(self.up, "commit", "-q", "-m", "first")
        self.first = run(self.up, "rev-parse", "HEAD")
        self.root = base / "repo"
        (self.root / "toolkit").mkdir(parents=True)
        self.write_manifest()
        self.url_for = lambda repo: self.up.as_uri()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_manifest(self, sha: str = "0" * 40) -> None:
        data = {"sources": {"up": {
            "repo": "example/up", "license": "MIT", "license_path": "LICENSE", "sha": sha,
            "synced_on": "2026-01-01",
            "skills": {"alpha": {"from": "skills/alpha", "to": "toolkit/design/vendor/alpha"}},
        }}}
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")

    def manifest(self) -> dict:
        return json.loads((self.root / "toolkit" / "vendored.json").read_text(encoding="utf-8"))

    def validate(self, our=frozenset(), ext=frozenset()) -> list[str]:
        errors: list[str] = []
        entries = check.load_vendored(self.root / "toolkit" / "vendored.json", errors)
        check.validate_vendored(entries, self.root, set(our), set(ext), errors)
        return errors


class UpdateTests(VendorFixture):
    def test_update_copies_unchanged_with_licence_and_pins(self) -> None:
        changed = vendor_sync.update(self.root, [], url_for=self.url_for, today="2026-11-16")
        dest = self.root / "toolkit" / "design" / "vendor" / "alpha"
        self.assertEqual(changed, ["toolkit/design/vendor/alpha"])
        self.assertEqual((dest / "SKILL.md").read_text(encoding="utf-8"), skill_md("alpha"))
        self.assertEqual((dest / "LICENSE").read_text(encoding="utf-8"), "MIT License\n")
        src = self.manifest()["sources"]["up"]
        self.assertEqual(src["sha"], self.first)
        self.assertEqual(src["synced_on"], "2026-11-16")
        self.assertEqual(src["skills"]["alpha"]["files"], check.file_digests(dest))
        self.assertEqual(self.validate(), [])

    def test_rerun_without_upstream_change_reports_nothing(self) -> None:
        vendor_sync.update(self.root, [], url_for=self.url_for)
        self.assertEqual(vendor_sync.update(self.root, [], url_for=self.url_for), [])

    def test_upstream_removal_of_a_file_is_mirrored(self) -> None:
        vendor_sync.update(self.root, [], url_for=self.url_for)
        (self.up / "skills" / "alpha" / "NOTES.md").unlink()
        run(self.up, "commit", "-q", "-am", "drop notes")
        vendor_sync.update(self.root, [], url_for=self.url_for)
        self.assertFalse((self.root / "toolkit/design/vendor/alpha/NOTES.md").exists())
        self.assertEqual(self.validate(), [])

    def test_ref_pins_an_older_commit(self) -> None:
        (self.up / "skills" / "alpha" / "NOTES.md").write_text("notes v2\n", encoding="utf-8")
        run(self.up, "commit", "-q", "-am", "second")
        vendor_sync.update(self.root, ["up"], ref=self.first, url_for=self.url_for)
        self.assertEqual(self.manifest()["sources"]["up"]["sha"], self.first)
        self.assertEqual((self.root / "toolkit/design/vendor/alpha/NOTES.md").read_text(encoding="utf-8"), "notes v1\n")

    def test_upstream_symlink_is_refused(self) -> None:
        (self.up / "skills" / "alpha" / "leak").symlink_to("/etc/hosts")
        run(self.up, "add", ".")
        run(self.up, "commit", "-q", "-m", "link")
        with self.assertRaisesRegex(RuntimeError, "symlinks"):
            vendor_sync.update(self.root, [], url_for=self.url_for)

    def test_upstream_folder_symlinked_outside_the_clone_is_refused(self) -> None:
        outside = Path(self._tmp.name) / "outside"
        outside.mkdir()
        (outside / "SKILL.md").write_text(skill_md("alpha"), encoding="utf-8")
        (outside / "secret.md").write_text("private\n", encoding="utf-8")
        clone_dir = Path(self._tmp.name) / "clone"
        (clone_dir / "skills").mkdir(parents=True)
        (clone_dir / "skills" / "alpha").symlink_to(outside)
        (clone_dir / "LICENSE").write_text("MIT\n", encoding="utf-8")
        dest = self.root / "toolkit" / "design" / "vendor" / "alpha"
        with self.assertRaisesRegex(RuntimeError, "outside the upstream clone"):
            vendor_sync.copy_skill(clone_dir / "skills" / "alpha", dest, clone_dir / "LICENSE", clone_dir)
        self.assertFalse(dest.exists())

    def test_upstream_script_is_refused(self) -> None:
        (self.up / "skills" / "alpha" / "run.py").write_text("print(1)\n", encoding="utf-8")
        run(self.up, "add", ".")
        run(self.up, "commit", "-q", "-m", "script")
        with self.assertRaisesRegex(RuntimeError, "not plain text"):
            vendor_sync.update(self.root, [], url_for=self.url_for)

    def test_include_copies_only_listed_files_from_a_repo_root(self) -> None:
        (self.up / "SKILL.md").write_text(skill_md("alpha"), encoding="utf-8")
        (self.up / "build.py").write_text("print(1)\n", encoding="utf-8")
        run(self.up, "add", ".")
        run(self.up, "commit", "-q", "-m", "root skill")
        data = self.manifest()
        data["sources"]["up"]["skills"]["alpha"].update({"from": ".", "include": ["SKILL.md"]})
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")
        vendor_sync.update(self.root, [], url_for=self.url_for)
        dest = self.root / "toolkit" / "design" / "vendor" / "alpha"
        self.assertEqual(sorted(check.file_digests(dest)), ["LICENSE", "SKILL.md"])
        self.assertEqual(self.validate(), [])
        data = self.manifest()
        data["sources"]["up"]["skills"]["alpha"]["include"] = ["SKILL.md", "build.py"]
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "not plain text"):
            vendor_sync.update(self.root, [], url_for=self.url_for)

    def test_include_cannot_leave_the_folder(self) -> None:
        for bad in (["SKILL.md", "../repo/README.md"], ["/etc/hosts"], ["a//b.md"]):
            self.assertTrue(any(check.include_problem(f) for f in bad), bad)
        data = self.manifest()
        data["sources"]["up"]["skills"]["alpha"]["include"] = ["SKILL.md", "../x.md"]
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "stay inside the folder"):
            vendor_sync.update(self.root, [], url_for=self.url_for)
        errors: list[str] = []
        check.load_vendored(self.root / "toolkit" / "vendored.json", errors)
        self.assertTrue(any("'include' must be" in e for e in errors), errors)
        self.assertFalse(check.include_problem("references/a.md"))

    def test_unknown_source_is_refused(self) -> None:
        with self.assertRaises(SystemExit):
            vendor_sync.update(self.root, ["nope"], url_for=self.url_for)

    def test_report_lists_commits_touching_vendored_paths_only(self) -> None:
        self.write_manifest(sha=self.first)
        (self.up / "skills" / "alpha" / "NOTES.md").write_text("notes v2\n", encoding="utf-8")
        run(self.up, "commit", "-q", "-am", "touch alpha")
        (self.up / "README.md").write_text("unrelated\n", encoding="utf-8")
        run(self.up, "add", ".")
        run(self.up, "commit", "-q", "-m", "touch readme")
        rows = vendor_sync.report(self.root, [], url_for=self.url_for)
        self.assertEqual(len(rows[0]["commits"]), 1, rows)
        self.assertIn("touch alpha", rows[0]["commits"][0])


class ValidateTests(VendorFixture):
    def setUp(self) -> None:
        super().setUp()
        vendor_sync.update(self.root, [], url_for=self.url_for)
        self.dest = self.root / "toolkit" / "design" / "vendor" / "alpha"

    def test_local_edit_fails(self) -> None:
        (self.dest / "SKILL.md").write_text(skill_md("alpha", "Edited here."), encoding="utf-8")
        errors = self.validate()
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("never edited here", errors[0])

    def test_added_file_fails(self) -> None:
        (self.dest / "PATCH.md").write_text("x\n", encoding="utf-8")
        self.assertTrue(any("PATCH.md" in e for e in self.validate()))

    def test_executable_or_non_text_file_fails(self) -> None:
        (self.dest / "NOTES.md").chmod(0o755)
        self.assertTrue(any("not plain text" in e for e in self.validate()))

    def test_missing_licence_and_wrong_name_fail(self) -> None:
        data = self.manifest()
        files = data["sources"]["up"]["skills"]["alpha"]["files"]
        (self.dest / "LICENSE").unlink()
        del files["LICENSE"]
        (self.dest / "SKILL.md").write_text(skill_md("beta"), encoding="utf-8")
        files["SKILL.md"] = check.file_digests(self.dest)["SKILL.md"]
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")
        errors = self.validate()
        self.assertTrue(any("LICENSE missing" in e for e in errors), errors)
        self.assertTrue(any("frontmatter name must be 'alpha'" in e for e in errors), errors)

    def test_unlisted_vendor_folder_fails(self) -> None:
        (self.root / "toolkit" / "design" / "vendor" / "stray").mkdir()
        self.assertTrue(any("not listed" in e for e in self.validate()))

    def test_name_collisions_fail(self) -> None:
        self.assertTrue(any("also a toolkit skill" in e for e in self.validate(our={"alpha"})))
        self.assertTrue(any("external.yaml" in e for e in self.validate(ext={"alpha"})))

    def test_malformed_manifest_fails(self) -> None:
        data = self.manifest()
        data["sources"]["up"]["sha"] = "abc"
        data["sources"]["up"]["skills"]["alpha"]["to"] = "toolkit/design/skills/alpha"
        (self.root / "toolkit" / "vendored.json").write_text(json.dumps(data), encoding="utf-8")
        errors = self.validate()
        self.assertTrue(any("sha missing or malformed" in e for e in errors), errors)
        self.assertTrue(any("'to' must be" in e for e in errors), errors)


class CrossSkillPathTests(unittest.TestCase):
    def test_paths_resolve_as_installed_siblings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "review-animations"
            other.mkdir()
            (other / "STANDARDS.md").write_text("x\n", encoding="utf-8")
            dirs = {"web-platform": Path(tmp) / "web-platform", "review-animations": other}
            docs = [
                ("web-platform", Path("SKILL.md"), "read `../review-animations/STANDARDS.md`"),
                ("web-platform", Path("references/components.md"), "read `../../review-animations/STANDARDS.md`"),
            ]
            errors: list[str] = []
            check.validate_cross_skill_paths(docs, dirs, errors)
            self.assertEqual(errors, [])
            bad = [
                ("web-platform", Path("references/components.md"), "read `../review-animations/STANDARDS.md`"),
                ("web-platform", Path("SKILL.md"), "read `../gone/SKILL.md`"),
                ("web-platform", Path("SKILL.md"), "read `../../outside/SKILL.md`"),
            ]
            check.validate_cross_skill_paths(bad, dirs, errors)
            self.assertEqual(len(errors), 3, errors)


if __name__ == "__main__":
    unittest.main(verbosity=1)
