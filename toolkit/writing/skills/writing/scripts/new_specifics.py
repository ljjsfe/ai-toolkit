#!/usr/bin/env python3
"""List specifics an edit introduced: numbers, dates, quotes and names in AFTER that BEFORE lacks.

Usage:
  new_specifics.py BEFORE.md AFTER.md [--sources NOTES.md ...]

Run it after any rewriting pass (humanizer v4+ may add "a specific detail it knows to be true").
A specific counts as new when it appears in AFTER but in neither BEFORE nor any --sources file.
Each one must be traced to the writer or a source, or reverted / turned into [NEED: ...]
(writing law 1). Matching is literal after light normalisation (case, commas in numbers,
full-width digits) and on whole tokens: a number or date must not sit inside a longer number
("4" is not known from "14"), and a name or quote must not sit inside a longer word; it is a tripwire, so read the flagged lines rather than trusting a clean
run on prose that paraphrases heavily. Exit 1 when anything new is found.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

NUMBER_RE = re.compile(r"(?<![0-9A-Za-z_.])[-+]?\d+(?:,\d{3})*(?:\.\d+)?(?:\s?(?:%|percent|×|bn|万|亿|倍)|[xkm](?![a-z]))?", re.I)
DATE_RE = re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b|\b(?:19|20)\d{2}年(?:\d{1,2}月)?(?:\d{1,2}日)?")
QUOTE_RE = re.compile(r"[\"“「『]([^\"”」』]{6,})[\"”」』]")
# Two or more capitalised words (Latin), not at a sentence start: likely a proper name.
NAME_RE = re.compile(r"(?<=[a-z,;:)] )(?:[A-Z][a-zA-Z&.-]+(?:\s+(?:of|de|and|&)?\s*[A-Z][a-zA-Z&.-]+)+)")


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"(?<=\d),(?=\d)", "", text)


def specifics(text: str) -> list[tuple[str, str]]:
    """(kind, surface form) in document order, deduplicated."""
    seen: dict[str, tuple[str, str]] = {}
    date_spans = [m.span() for m in DATE_RE.finditer(text)]
    for kind, rx in (("date", DATE_RE), ("number", NUMBER_RE), ("quote", QUOTE_RE), ("name", NAME_RE)):
        for m in rx.finditer(text):
            if kind == "number" and any(a <= m.start() < b for a, b in date_spans):
                continue  # the year or month inside a date already counted as the date
            surface = (m.group(1) if kind == "quote" else m.group(0)).strip()
            if kind == "number" and len(re.sub(r"\D", "", surface)) == 0:
                continue
            key = norm(surface)
            if key and key not in seen:
                seen[key] = (kind, surface)
    return list(seen.values())


def is_known(kind: str, surface: str, known: str) -> bool:
    """True when the normalised surface occurs in `known` as a whole token, not inside a longer one."""
    s = norm(surface)
    if kind in ("number", "date"):
        left, right = r"(?<![\d.])", r"(?!\.?\d)"
    else:
        left = r"(?<!\w)" if re.match(r"\w", s) else ""
        right = r"(?!\w)" if re.search(r"\w$", s) else ""
    return re.search(left + re.escape(s) + right, known) is not None


def new_specifics(before: str, after: str, sources: list[str]) -> list[tuple[str, str, int]]:
    known = norm(before + "\n" + "\n".join(sources))
    out = []
    lines = after.splitlines()
    for kind, surface in specifics(after):
        if is_known(kind, surface, known):
            continue
        line = next((i for i, ln in enumerate(lines, 1) if surface in ln), 0)
        out.append((kind, surface, line))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    ap.add_argument("--sources", type=Path, nargs="*", default=[])
    a = ap.parse_args(argv)
    try:
        before, after = a.before.read_text(encoding="utf-8"), a.after.read_text(encoding="utf-8")
        sources = [p.read_text(encoding="utf-8") for p in a.sources]
    except (OSError, UnicodeDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    found = new_specifics(before, after, sources)
    for kind, surface, line in found:
        print(f"{a.after.name}:{line}: new {kind}: {surface}")
    print("OK: no new specifics" if not found else
          f"{len(found)} new specific(s): trace each to the writer or a source, or revert / mark [NEED: ...]")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
