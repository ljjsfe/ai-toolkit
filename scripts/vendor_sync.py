#!/usr/bin/env python3
"""Keep vendored skills (toolkit/vendored.json) in step with their upstream repos.

Usage:
  python3 scripts/vendor_sync.py                         # read-only: upstream commits since each pin
  python3 scripts/vendor_sync.py emilkowalski-skills     # same, for named sources only
  python3 scripts/vendor_sync.py --update [source ...]   # copy the upstream default branch, re-pin
  python3 scripts/vendor_sync.py --update SRC --ref SHA  # copy a given commit, tag or branch instead

A vendored skill is an upstream skill folder copied byte for byte, with the upstream licence
beside it as LICENSE. --update replaces each folder whole, records the new commit and the sha256
of every file, and never commits: read `git diff -- toolkit/*/vendor` before committing, the same
review update.sh asks for before installing an external. `python3 scripts/check.py` then fails if
a vendored file is edited by hand.

To vendor a new skill, add it under a source's "skills" with "from" (folder in the upstream repo,
"." for the repo root) and "to" (toolkit/<category>/vendor/<name>), then run --update for that
source. When "from" also holds packaging, CI or scripts, list the skill's own files in "include".

Upstream content is data: it is copied, never run. Only plain text files are vendored (see
check.VENDOR_FILE_OK); an upstream folder that gains scripts, executables or symlinks is refused,
as is a folder or licence that resolves outside the clone. Such a skill belongs in external.yaml.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check  # noqa: E402

UrlFor = Callable[[str], str]


def github_url(repo: str) -> str:
    return f"https://github.com/{repo}.git"


def git(cwd: Path, *args: str) -> str:
    res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {res.stderr.strip()}")
    return res.stdout


def clone(url: str, dest: Path) -> Path:
    """Blobless clone: full history for `git log`, file contents fetched only on checkout."""
    res = subprocess.run(
        ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", url, str(dest)],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"git clone {url} failed: {res.stderr.strip()}")
    return dest


def load(root: Path) -> dict:
    return json.loads((root / "toolkit" / "vendored.json").read_text(encoding="utf-8"))


def save(root: Path, data: dict) -> None:
    (root / "toolkit" / "vendored.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def pick(data: dict, names: list[str]) -> list[str]:
    known = list(data.get("sources", {}))
    unknown = [n for n in names if n not in known]
    if unknown:
        raise SystemExit(f"error: not in toolkit/vendored.json: {', '.join(unknown)} (known: {', '.join(known)})")
    return names or known


def watched_paths(src: dict) -> list[str]:
    paths = []
    for sk in src["skills"].values():
        inc = sk.get("include")
        paths += [f"{sk['from']}/{f}" for f in inc] if inc else [sk["from"]]
    return paths + [src["license_path"]]


def report(root: Path, names: list[str], url_for: UrlFor = github_url) -> list[dict]:
    """Commits on the upstream default branch since the pin that touch a vendored path."""
    data = load(root)
    rows = []
    for name in pick(data, names):
        src = data["sources"][name]
        with tempfile.TemporaryDirectory() as tmp:
            d = clone(url_for(src["repo"]), Path(tmp) / "repo")
            head = git(d, "rev-parse", "HEAD").strip()
            log = git(d, "log", "--format=%h %ad %s", "--date=short", f"{src['sha']}..HEAD", "--", *watched_paths(src))
        rows.append({"source": name, "repo": src["repo"], "pinned": src["sha"], "head": head,
                     "commits": [line for line in log.splitlines() if line.strip()]})
    return rows


def inside(path: Path, clone_dir: Path) -> bool:
    return path.resolve().is_relative_to(clone_dir.resolve())


SKIP_PARTS = {".git", "__pycache__", ".DS_Store"}


def copy_skill(src_dir: Path, dest: Path, license_file: Path, clone_dir: Path,
               include: list[str] | None = None) -> dict[str, str]:
    """Copy src_dir (or only the listed files in it) to dest, plus the repo licence as LICENSE.

    include lists file paths relative to src_dir; use it when the skill folder is the whole repo
    root and holds packaging, CI or scripts that are not part of the skill."""
    for p in (src_dir, license_file):
        if not inside(p, clone_dir):
            raise RuntimeError(f"{p}: resolves outside the upstream clone")
    if include:
        bad_inc = [f for f in include if check.include_problem(f)]
        if bad_inc:
            raise RuntimeError(f"{src_dir}: include entries must stay inside the folder: {', '.join(map(str, bad_inc))}")
        files = [src_dir / f for f in include]
        missing = [f for f in include if not (src_dir / f).is_file()]
        if missing:
            raise RuntimeError(f"{src_dir}: listed files missing upstream: {', '.join(missing)}")
    else:
        files = [p for p in src_dir.rglob("*") if not (SKIP_PARTS & set(p.relative_to(src_dir).parts))]
    if (src_dir / "SKILL.md") not in files:
        raise RuntimeError(f"{src_dir}: no SKILL.md upstream")
    links = [p for p in files if p.is_symlink() or not inside(p, src_dir)]
    if links:
        raise RuntimeError(f"{src_dir}: refusing upstream symlinks: {', '.join(str(p) for p in links)}")
    files = [p for p in files if p.is_file()]
    bad = [p.relative_to(src_dir).as_posix() for p in files if not check.vendor_file_ok(p)]
    if bad:
        raise RuntimeError(f"{src_dir}: not plain text, so not vendorable (use external.yaml): {', '.join(bad)}")
    if (src_dir / "LICENSE") in files:
        raise RuntimeError(f"{src_dir}: upstream folder already has a LICENSE; the repo licence cannot be placed beside it")
    if dest.exists():
        shutil.rmtree(dest)
    for f in files:
        target = dest / f.relative_to(src_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target)
    shutil.copyfile(license_file, dest / "LICENSE")
    return check.file_digests(dest)


def update(root: Path, names: list[str], ref: str = "", url_for: UrlFor = github_url,
           today: str | None = None) -> list[str]:
    """Copy each source's skills at ref (default: upstream HEAD) and re-pin. Returns changed folders."""
    data = load(root)
    chosen = pick(data, names)
    if ref and len(chosen) != 1:
        raise SystemExit("error: --ref needs exactly one source")
    changed = []
    for name in chosen:
        src = data["sources"][name]
        with tempfile.TemporaryDirectory() as tmp:
            d = clone(url_for(src["repo"]), Path(tmp) / "repo")
            if ref:
                git(d, "checkout", "--quiet", ref, "--")
            else:
                git(d, "checkout", "--quiet")
            sha = git(d, "rev-parse", "HEAD").strip()
            license_file = d / src["license_path"]
            if not license_file.is_file():
                raise RuntimeError(f"{src['repo']}@{sha[:7]}: licence {src['license_path']} missing")
            for skill, sk in src["skills"].items():
                dest = root / sk["to"]
                before = check.file_digests(dest) if dest.is_dir() else {}
                sk["files"] = copy_skill(d / sk["from"], dest, license_file, d, sk.get("include"))
                if sk["files"] != before:
                    changed.append(sk["to"])
        if src.get("sha") != sha:
            src["sha"] = sha
            src["synced_on"] = today or date.today().isoformat()
    save(root, data)
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="*")
    ap.add_argument("--update", action="store_true", help="copy upstream and re-pin (edits the working tree)")
    ap.add_argument("--ref", default="", help="with --update: commit, tag or branch to copy instead of HEAD")
    a = ap.parse_args(argv)
    try:
        if a.update:
            changed = update(ROOT, a.sources, a.ref)
            if changed:
                print("changed (review before committing):")
                for c in changed:
                    print(f"  {c}")
                print("next: git diff -- toolkit/vendored.json " + " ".join(changed))
                print("      python3 scripts/check.py --sync-credits")
            else:
                print("vendored folders unchanged")
            return 0
        rows = report(ROOT, a.sources)
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    for r in rows:
        state = "up to date" if r["pinned"] == r["head"] or not r["commits"] else f"{len(r['commits'])} commit(s) behind"
        print(f"{r['source']:24} {r['repo']}  pinned {r['pinned'][:7]}  head {r['head'][:7]}  {state}")
        for c in r["commits"][:10]:
            print(f"    {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
