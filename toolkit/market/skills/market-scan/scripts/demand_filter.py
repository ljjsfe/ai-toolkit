#!/usr/bin/env python3
"""Mechanical noise filter for GitHub demand signals. Reads the JSON items of a `gh api
search/issues` call (a list, or the raw response with an "items" key) and splits them into
kept and dropped, each dropped item with its reason.

Usage:
  gh api "search/issues?q=..." > raw.json
  demand_filter.py raw.json [--kind issue|pr-open|pr-rejected|pr-stale]

Hard drops (no judgement involved):
  issue labels: question, invalid, duplicate, help wanted, good first issue, can't reproduce
  issue titles: how to / how do I / how can I, why does / why is / why can't / why won't,
                cannot / can't / failed to install, error when / while / on / during,
                installation / setup / config issue / problem / error / help
  issue bodies: five or more consecutive stack-trace lines; empty; under 100 characters that
                only say thanks / +1 / same issue
  PRs:          author is a bot (user.type "Bot" or a login ending in "[bot]"); label duplicate; a non-rejected PR whose title is maintenance
                (fix, bug, typo, chore, docs, readme, revert, bump, ci:, test:) unless it has
                20+ reactions
Never dropped, whatever else matches:
  an issue labelled wontfix / won't fix / works as intended / not planned: kept and tagged
  "confirmed gap" (the maintainer refused it, so the need is real and unserved);
  a rejected (closed, unmerged) PR with 10+ reactions; reactions with no comment text count
  as reach and are never a reason to drop.
Judgement filters (bikeshedding, wishes with no context, governance disputes) are left to the
reader and listed in references/github-demand.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DROP_LABELS = {"question", "invalid", "duplicate", "help wanted", "good first issue",
               "can't reproduce"}
CONFIRMED_GAP_LABELS = {"wontfix", "won't fix", "works as intended", "not planned"}
TITLE_PATTERNS = [re.compile(p, re.I) for p in (
    r"^how (to|do i|can i)\b",
    r"^why (does|is|can't|won't)\b",
    r"^(cannot|can't|failed to) install",
    r"^error (when|while|on|during)\b",
    r"^(installation|setup|config) (issue|problem|error|help)",
)]
MAINTENANCE_TITLE = re.compile(r"\b(fix|bug|typo|chore|docs|readme|revert|bump)\b|ci:|test:", re.I)
STACK_LINE = re.compile(r"^\s*(at \S+ \(.*:\d+(:\d+)?\)|File \".*\", line \d+|\S+\.\w+:\d+)")
NOISE_BODY = re.compile(r"^\W*(thanks|thank you|\+1|same issue|same here|me too)\W*$", re.I)


def labels(item: dict) -> set[str]:
    out = set()
    for lab in item.get("labels") or []:
        out.add((lab.get("name") if isinstance(lab, dict) else str(lab)).lower())
    return out


def reactions(item: dict) -> int:
    r = item.get("reactions")
    if isinstance(r, dict):
        return int(r.get("total_count", 0))
    return int(r or 0)


def stack_run(body: str) -> int:
    best = run = 0
    for line in body.splitlines():
        run = run + 1 if STACK_LINE.match(line) else 0
        best = max(best, run)
    return best


def drop_reason(item: dict, kind: str) -> str | None:
    title = item.get("title") or ""
    body = item.get("body") or ""
    labs = labels(item)
    if kind == "pr-rejected" and reactions(item) >= 10:
        return None
    if kind.startswith("pr"):
        user = item.get("user") or {}
        login = (user.get("login") or "").lower()
        if user.get("type") == "Bot" or login.endswith("[bot]"):
            return "bot author"
        if "duplicate" in labs:
            return "label duplicate"
        if kind != "pr-rejected" and MAINTENANCE_TITLE.search(title) and reactions(item) < 20:
            return "maintenance PR title"
        return None
    if labs & CONFIRMED_GAP_LABELS:
        return None  # confirmed gap: checked before every drop rule, so nothing else can drop it
    hit = sorted(labs & DROP_LABELS)
    if hit:
        return f"label {hit[0]}"
    for pat in TITLE_PATTERNS:
        if pat.search(title.strip()):
            return f"support-question title ({pat.pattern})"
    if not body.strip():
        return "empty body"
    if stack_run(body) >= 5:
        return "stack trace dump"
    if len(body.strip()) < 100 and NOISE_BODY.match(body.strip()):
        return "thanks / +1 only"
    return None


def tag(item: dict) -> str:
    """'confirmed gap' for a kept item whose labels say the maintainer refused it, else ''."""
    return "confirmed gap" if labels(item) & CONFIRMED_GAP_LABELS else ""


def split(items: list[dict], kind: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    kept, dropped = [], []
    for it in items:
        reason = drop_reason(it, kind)
        if reason:
            dropped.append((it, reason))
        else:
            kept.append(it)
    kept.sort(key=lambda it: reactions(it) + int(it.get("comments") or 0), reverse=True)
    return kept, dropped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("json")
    p.add_argument("--kind", default="issue", choices=["issue", "pr-open", "pr-rejected", "pr-stale"])
    a = p.parse_args(argv)
    data = json.loads(Path(a.json).read_text(encoding="utf-8"))
    items = data.get("items", []) if isinstance(data, dict) else data
    kept, dropped = split(items, a.kind)
    print(f"kept {len(kept)} | dropped {len(dropped)}")
    for it in kept:
        mark = f" [{tag(it)}]" if tag(it) else ""
        print(f"KEEP #{it.get('number')}{mark} r{reactions(it)} c{it.get('comments', 0)} {it.get('title')} "
              f"{it.get('html_url') or it.get('url') or ''}")
    for it, why in dropped:
        print(f"DROP #{it.get('number')} ({why}) {it.get('title')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
