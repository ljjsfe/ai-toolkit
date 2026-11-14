#!/usr/bin/env python3
"""Persistent discovery folder for customer-discovery. Plain Markdown, standard library only.

Folder: $DISCOVERY_DIR if set, else ./discovery/ when it exists in the working directory (an
in-repo folder the team shares), else ~/.discovery/<idea>/.

Usage:
  discovery.py path IDEA
  discovery.py init IDEA
  discovery.py assume IDEA --text "..." --segment "..." --kill "..."
  discovery.py interview IDEA --date YYYY-MM-DD --role "clinic office manager" NOTES.md
  discovery.py verdict IDEA --interview BASENAME A1=supported A2=weakened [--date YYYY-MM-DD]
  discovery.py decide IDEA --decision "..." --verdict "BUILD AS EXPERIMENT" --because "..."
  discovery.py status IDEA

Write discipline (the skill relies on it):
  interviews/ and decisions.md are append-only: an interview file is never overwritten and a
  second interview with the same date and role is written as -2, -3.
  assumptions.md: ids A<n> are never renumbered or deleted; only status, evidence and updated
  change in place.
Status merge (one `verdict` call may carry several verdicts for one id, e.g. a batch debrief):
  killed is sticky; within one call weakened beats supported; across calls the later call
  wins; untouched never changes the cell.
`status` re-derives evidence from the [A<n>+] / [A<n>-] tags in interviews/ and lists every
assumption whose evidence cell disagrees with the files, plus every supported / weakened
assumption with no tagged evidence at all (exit 1 on either).
Paths: --date must be YYYY-MM-DD and every interview path must resolve inside interviews/.
Free-text cells have "|" replaced by "/" and line breaks by spaces so a row stays one row.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

STATUSES = ("untested", "supported", "weakened", "killed")
ASSUMPTION_HEADER = (
    "| id | assumption (falsifiable) | segment | kill condition | status | evidence | updated |\n"
    "|---|---|---|---|---|---|---|"
)
FILES = {
    "assumptions.md": "# Assumptions\n\nRow order is priority, riskiest first. Ids never change.\n\n"
                      + ASSUMPTION_HEADER + "\n",
    "segments.md": "# Segments\n\nOne row per real interview.\n\n"
                   "| interview | role | attrs | top problem (unprompted) | highest rung |\n"
                   "|---|---|---|---|---|\n",
    "decisions.md": "# Decisions\n\nAppend only.\n\n| date | decision | verdict | justified by |\n"
                    "|---|---|---|---|\n",
}
TAG_RE = re.compile(r"\[(A\d+)([+-])\]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def iso_date(text: str) -> str:
    """argparse type: a real YYYY-MM-DD date, nothing else (it becomes part of a file name)."""
    if not DATE_RE.match(text):
        raise argparse.ArgumentTypeError(f"date must be YYYY-MM-DD, got {text!r}")
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not a real date: {text!r}") from exc
    return text


def cell(text: str) -> str:
    """One Markdown table cell: no column breaks, no row breaks."""
    return " ".join(text.replace("|", "/").split())


def inside_interviews(d: Path, name: str) -> Path:
    """d/interviews/<name>, refusing anything that resolves outside interviews/."""
    root = (d / "interviews").resolve()
    target = (root / name).resolve()
    if target.parent != root:
        raise SystemExit(f"{name!r} resolves outside {root}; refusing")
    return target


def slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if not s:
        raise SystemExit("slug is empty; use a role or company, never a person's name")
    return s


def folder(idea: str) -> Path:
    env = os.environ.get("DISCOVERY_DIR")
    if env:
        return Path(env).expanduser()
    local = Path.cwd() / "discovery"
    if local.is_dir():
        return local
    return Path.home() / ".discovery" / slug(idea)


def need(d: Path) -> None:
    if not (d / "assumptions.md").exists():
        raise SystemExit(f"{d} has no assumptions.md; run init first")


def read_rows(d: Path) -> tuple[list[str], list[list[str]], list[str]]:
    """Return (lines before table rows, rows as cell lists, lines after)."""
    lines = (d / "assumptions.md").read_text(encoding="utf-8").splitlines()
    rows, head, tail = [], [], []
    for ln in lines:
        if re.match(r"^\|\s*A\d+\s*\|", ln):
            rows.append([c.strip() for c in ln.strip().strip("|").split("|")])
        elif rows:
            tail.append(ln)
        else:
            head.append(ln)
    return head, rows, tail


def write_rows(d: Path, head: list[str], rows: list[list[str]], tail: list[str]) -> None:
    body = head + ["| " + " | ".join(r) + " |" for r in rows] + tail
    (d / "assumptions.md").write_text("\n".join(body) + "\n", encoding="utf-8")


def combine(verdicts: list[str]) -> str:
    """Several verdicts for one id inside one call."""
    if "killed" in verdicts:
        return "killed"
    if "weakened" in verdicts:
        return "weakened"
    if "supported" in verdicts:
        return "supported"
    return "untouched"


def merge(cell: str, incoming: str) -> str:
    if cell == "killed" or incoming == "untouched":
        return cell
    return incoming


def cmd_path(a) -> int:
    print(folder(a.idea))
    return 0


def cmd_init(a) -> int:
    d = folder(a.idea)
    (d / "interviews").mkdir(parents=True, exist_ok=True)
    for name, text in FILES.items():
        p = d / name
        if p.exists():
            print(f"kept {p}")
        else:
            p.write_text(text, encoding="utf-8")
            print(f"created {p}")
    return 0


def cmd_assume(a) -> int:
    d = folder(a.idea)
    need(d)
    head, rows, tail = read_rows(d)
    n = max((int(r[0][1:]) for r in rows), default=0) + 1
    clean = [cell(x) for x in (a.text, a.segment, a.kill)]
    rows.append([f"A{n}", *clean, "untested", "", a.date])
    write_rows(d, head, rows, tail)
    print(f"A{n} added")
    return 0


def cmd_interview(a) -> int:
    d = folder(a.idea)
    need(d)
    base = f"{a.date}-{slug(a.role)}"
    target, k = inside_interviews(d, f"{base}.md"), 1
    while target.exists():
        k += 1
        target = inside_interviews(d, f"{base}-{k}.md")
    target.write_text(Path(a.notes).read_text(encoding="utf-8"), encoding="utf-8")
    print(f"wrote {target}")
    return 0


def cmd_verdict(a) -> int:
    d = folder(a.idea)
    need(d)
    if not inside_interviews(d, f"{a.interview}.md").exists():
        raise SystemExit(f"interview {a.interview} not found; record it first")
    per_id: dict[str, list[str]] = {}
    for item in a.verdicts:
        aid, _, v = item.partition("=")
        v = v.strip().lower()
        if v not in STATUSES[1:] + ("untouched",):
            raise SystemExit(f"bad verdict {item!r}")
        per_id.setdefault(aid.strip(), []).append(v)
    head, rows, tail = read_rows(d)
    known = {r[0] for r in rows}
    for aid in per_id:
        if aid not in known:
            raise SystemExit(f"{aid} does not exist; add it with `assume` or drop the verdict")
    tags = interview_tags(d).get(a.interview, set())
    for r in rows:
        if r[0] not in per_id:
            continue
        new = merge(r[4], combine(per_id[r[0]]))
        ev = [e for e in r[5].split(", ") if e]
        if r[0] in tags and a.interview not in ev:
            ev.append(a.interview)
        if new != r[4] or ev != [e for e in r[5].split(", ") if e]:
            r[6] = a.date
        r[4], r[5] = new, ", ".join(ev)
        print(f"{r[0]}: {r[4]} (evidence {r[5] or 'none'})")
    write_rows(d, head, rows, tail)
    return 0


def cmd_decide(a) -> int:
    d = folder(a.idea)
    need(d)
    row = "| " + " | ".join(cell(x) for x in (a.date, a.decision, a.verdict, a.because)) + " |\n"
    with (d / "decisions.md").open("a", encoding="utf-8") as fh:
        fh.write(row)
    print("decision appended")
    return 0


def interview_tags(d: Path) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for f in sorted((d / "interviews").glob("*.md")):
        if f.name.startswith("_"):
            continue
        out[f.stem] = {m.group(1) for m in TAG_RE.finditer(f.read_text(encoding="utf-8"))}
    return out


def status_report(d: Path) -> list[str]:
    _, rows, _ = read_rows(d)
    tags = interview_tags(d)
    counts = {s: sum(1 for r in rows if r[4] == s) for s in STATUSES}
    lines = [f"{len(tags)} interviews, {len(rows)} assumptions",
             "status: " + " · ".join(f"{s} {counts[s]}" for s in STATUSES)]
    risky = next((r for r in rows if r[4] in ("untested", "weakened")), None)
    lines.append(f"riskiest: {risky[0]} {risky[1]!r}" if risky else "riskiest: list exhausted")
    mismatches = []
    for r in rows:
        have = sorted(e for e in r[5].split(", ") if e)
        found = sorted(stem for stem, ids in tags.items() if r[0] in ids)
        if have != found:
            mismatches.append(f"{r[0]}: cell {have} vs tags {found}")
        if r[4] in ("supported", "weakened") and not found:
            mismatches.append(f"{r[0]}: error: status {r[4]} with no tagged evidence in interviews/")
    lines.extend(mismatches or ["evidence: all cells match the interview tags"])
    return lines


def cmd_status(a) -> int:
    d = folder(a.idea)
    need(d)
    lines = status_report(d)
    print("\n".join(lines))
    return 1 if any("cell [" in ln or ": error:" in ln for ln in lines) else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    today = date.today().isoformat()
    for name, fn in (("path", cmd_path), ("init", cmd_init), ("status", cmd_status)):
        s = sub.add_parser(name)
        s.add_argument("idea")
        s.set_defaults(func=fn)
    s = sub.add_parser("assume")
    s.add_argument("idea")
    s.add_argument("--text", required=True)
    s.add_argument("--segment", required=True)
    s.add_argument("--kill", required=True)
    s.add_argument("--date", default=today, type=iso_date)
    s.set_defaults(func=cmd_assume)
    s = sub.add_parser("interview")
    s.add_argument("idea")
    s.add_argument("notes")
    s.add_argument("--date", default=today, type=iso_date)
    s.add_argument("--role", required=True)
    s.set_defaults(func=cmd_interview)
    s = sub.add_parser("verdict")
    s.add_argument("idea")
    s.add_argument("verdicts", nargs="+")
    s.add_argument("--interview", required=True)
    s.add_argument("--date", default=today, type=iso_date)
    s.set_defaults(func=cmd_verdict)
    s = sub.add_parser("decide")
    s.add_argument("idea")
    s.add_argument("--decision", required=True)
    s.add_argument("--verdict", required=True)
    s.add_argument("--because", required=True)
    s.add_argument("--date", default=today, type=iso_date)
    s.set_defaults(func=cmd_decide)
    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
