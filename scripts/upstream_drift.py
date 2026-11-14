#!/usr/bin/env python3
"""List what changed upstream since the toolkit last checked its text against each source.

Usage:
  python3 scripts/upstream_drift.py                  # every upstream in toolkit/upstreams.json
  python3 scripts/upstream_drift.py gstack superpowers
  python3 scripts/upstream_drift.py --json
  python3 scripts/upstream_drift.py --externals --since 2026-11-01   # what update.sh would install

For each credited path (taken from skill and rule `sources:`), it asks GitHub (`gh api`, which must
be authenticated) whether the path still exists and which commits touched it after the reviewed
commit's date. A removed path means a credit now points at nothing: re-read and retag it. A
changed path means the port may be stale: re-read the diff, update the skill, then set
reviewed_sha / reviewed_on in toolkit/upstreams.json. Nothing here edits the repo.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "toolkit" / "upstreams.json"
UPSTREAM_RE = re.compile(r"upstream/(\{[^}]+\}|[A-Za-z0-9._-]+)(/[^\s(]*)?")

sys.path.insert(0, str(ROOT / "scripts"))
import check  # noqa: E402


def expand_braces(text: str) -> list[str]:
    """Expand one level of {a,b} groups (repeatedly): x/{a,b}.md -> [x/a.md, x/b.md]."""
    m = re.search(r"\{([^{}]*)\}", text)
    if not m:
        return [text]
    out = []
    for part in m.group(1).split(","):
        out += expand_braces(text[: m.start()] + part.strip() + text[m.end():])
    return out


def glob_root(path: str) -> str:
    """The directory before the first wildcard segment: a/b/*/c.md -> a/b (GitHub has no globs)."""
    if "*" not in path:
        return path
    parts = path.split("/")
    i = next(i for i, part in enumerate(parts) if "*" in part)
    return "/".join(parts[:i])


def credited_paths(sources: list[str]) -> dict[str, set[str]]:
    """upstream name -> repo-relative paths credited in these source strings ("" = whole repo)."""
    out: dict[str, set[str]] = {}
    for src in sources:
        text = check.split_coverage(src)[0]
        text = re.sub(r"\{[^}]*\}", lambda m: re.sub(r",\s+", ",", m.group(0)), text)  # "{a, b}" -> "{a,b}"
        for m in UPSTREAM_RE.finditer(text):
            names = expand_braces(m.group(1))
            rest = (m.group(2) or "").lstrip("/").rstrip(",;")
            # trailing words like "and skills/..." are separate paths; keep the first token only
            paths = [glob_root(p.rstrip(".,;")) for p in expand_braces(rest)] if rest else [""]
            for n in names:
                out.setdefault(n, set()).update(p for p in paths)
    return out


def all_sources() -> list[str]:
    errors: list[str] = []
    srcs: list[str] = []
    for smd in sorted((ROOT / "toolkit").glob("*/skills/*/SKILL.md")):
        fm = check.parse_skill_frontmatter(smd, errors)
        srcs += [str(s) for s in fm.get("sources", []) or []]
    for items in check.parse_rule_sources(ROOT / "toolkit" / "rules" / "sources.yaml", errors).values():
        srcs += items
    return srcs


def gh(args: list[str]) -> tuple[int, str]:
    p = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    return p.returncode, p.stdout if p.returncode == 0 else p.stderr


def drift(name: str, entry: dict, paths: set[str], api=gh) -> dict:
    repo = entry.get("repo")
    if not repo:
        return {"upstream": name, "status": "unlocatable", "note": entry.get("note", "")}
    since = entry.get("reviewed_on")
    report = {"upstream": name, "repo": repo, "reviewed_on": since, "paths": []}
    for path in sorted(paths):
        row: dict = {"path": path or "(whole repo)"}
        if path:
            code, _ = api([f"repos/{repo}/contents/{path}", "--silent"])
            row["exists"] = code == 0
        q = f"repos/{repo}/commits?per_page=20" + (f"&path={path}" if path else "") + (f"&since={since}T23:59:59Z" if since else "")
        code, body = api([q])
        if code != 0:
            row["error"] = body.strip()[:120]
        else:
            commits = json.loads(body or "[]")
            row["commits"] = [{"sha": c["sha"][:10], "date": c["commit"]["committer"]["date"][:10],
                               "subject": c["commit"]["message"].splitlines()[0][:90]} for c in commits]
        report["paths"].append(row)
    retired = entry.get("retired_paths", {})
    for r in report["paths"]:
        if r.get("exists") is False and r["path"] in retired:
            r["exists"], r["retired"] = None, retired[r["path"]]
    removed = [r["path"] for r in report["paths"] if r.get("exists") is False]
    changed = [r["path"] for r in report["paths"] if r.get("commits")]
    report["status"] = ("removed paths" if removed else "changed" if changed else
                        "unreviewed baseline" if not since else "unchanged")
    return report


def external_changes(since: str, api=gh) -> list[dict]:
    """For each installed (non-optional) external: latest release and commits since `since`."""
    errors: list[str] = []
    out = []
    for e in check.parse_external_yaml(ROOT / "toolkit" / "external.yaml", errors):
        if str(e.get("optional", "")).lower() == "true":
            continue
        m = re.search(r"github\.com/([^/\s]+/[^/\s]+?)(?:\.git)?/?$", e.get("repo", ""))
        if not m:
            continue
        repo = m.group(1)
        row: dict = {"name": e["name"], "repo": repo}
        code, body = api([f"repos/{repo}/releases/latest"])
        if code == 0:
            rel = json.loads(body or "{}")
            row["release"] = {"tag": rel.get("tag_name"), "date": (rel.get("published_at") or "")[:10],
                              "notes": (rel.get("body") or "").strip().splitlines()[:3]}
        code, body = api([f"repos/{repo}/commits?per_page=10&since={since}T00:00:00Z"])
        row["commits"] = [] if code != 0 else [
            {"date": c["commit"]["committer"]["date"][:10], "subject": c["commit"]["message"].splitlines()[0][:90]}
            for c in json.loads(body or "[]")]
        out.append(row)
    return out


def main(argv: list[str] | None = None, api=gh) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--externals", action="store_true", help="report installed externals instead of credits")
    ap.add_argument("--since", default="", help="YYYY-MM-DD for --externals (default: 30 days ago)")
    a = ap.parse_args(argv)
    if a.externals:
        from datetime import date, timedelta
        since = a.since or (date.today() - timedelta(days=30)).isoformat()
        rows = external_changes(since, api)
        if a.json:
            print(json.dumps(rows, indent=2))
        for r in rows if not a.json else []:
            rel = r.get("release") or {}
            head = f"{rel.get('tag')} ({rel.get('date')})" if rel else "no release"
            print(f"{r['name']:28} {r['repo']}  latest {head}  {len(r['commits'])} commit(s) since {since}")
            for line in rel.get("notes", []) if rel.get("date", "") >= since else []:
                print(f"    | {line[:110]}")
            for c in r["commits"][:3]:
                print(f"    {c['date']} {c['subject']}")
        return 0
    lock = json.loads(LOCK.read_text(encoding="utf-8"))["upstreams"]
    credited = credited_paths(all_sources())
    names = a.names or sorted(credited)
    unknown = [n for n in names if n not in lock]
    if unknown:
        print(f"error: not in toolkit/upstreams.json: {', '.join(unknown)}", file=sys.stderr)
        return 2
    reports = [drift(n, lock[n], credited.get(n, {""}), api) for n in names]
    if a.json:
        print(json.dumps(reports, indent=2))
    else:
        for r in reports:
            print(f"{r['status']:20} {r['upstream']}  ({r.get('repo')}, reviewed {r.get('reviewed_on')})")
            for p in r.get("paths", []):
                if p.get("exists") is False:
                    print(f"    REMOVED  {p['path']}")
                if p.get("retired"):
                    print(f"    retired (acknowledged) {p['path']}: {p['retired']}")
                for c in p.get("commits", [])[:5]:
                    print(f"    {c['date']} {c['sha']} {p['path']}: {c['subject']}")
                if p.get("error"):
                    print(f"    error {p['path']}: {p['error']}")
    return 1 if any(r["status"] == "removed paths" for r in reports) else 0


if __name__ == "__main__":
    sys.exit(main())
