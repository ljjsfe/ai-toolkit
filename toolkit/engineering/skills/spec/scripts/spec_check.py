#!/usr/bin/env python3
"""Zero-dependency validator and merger for `spec` change packages (no CLI needed).

Usage:
  spec_check.py validate <changes/slug>                      # proposal + delta format; exit 1 on errors
  spec_check.py merge <changes/slug> --specs <specs-root>    # plan every capability; print the plan
  spec_check.py merge <changes/slug> --specs <specs-root> --write [--retire <capability> ...]
  spec_check.py audit <specs-root | spec.md ...>             # living specs: structure, no changelog

`merge` is all-or-nothing: every capability is planned in memory first and nothing is written
unless all of them apply cleanly. Operation order is RENAMED, REMOVED, MODIFIED, ADDED. A merge
aborts when a target is missing, a rename target exists, a header matches only after ignoring case
or spacing, a MODIFIED block lacks a scenario the living spec has, or a REMOVED would retire a
capability not named with --retire.

`validate` also checks tasks.md (every task a checkbox; a numbered task ID sits in its own
`## N.` group and appears once) and fails a `## Purpose` that opens with TBD or TODO; `audit`
applies the same Purpose rule to living specs. These are errors by toolkit policy (OpenSpec
reports them as warnings).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

DELTA_KINDS = ("ADDED", "MODIFIED", "REMOVED", "RENAMED")
DELTA_HEADER_RE = re.compile(r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+Requirements\s*$", re.I)
REQ_RE = re.compile(r"^###\s+Requirement:\s*(.+?)\s*$")
SCENARIO_RE = re.compile(r"^####\s+Scenario:\s*(.+?)\s*$")
BULLET_SCENARIO_RE = re.compile(r"^\s*[-*]\s+(\*\*)?Scenario\b", re.I)
RENAME_RE = re.compile(r"^\s*[-*]\s*(FROM|TO):\s*`?\s*(?:###\s+Requirement:\s*)?(.+?)\s*`?\s*$", re.I)
REQ_ID_RE = re.compile(r"\[REQ-[A-Z0-9-]+\]")
NORMATIVE_RE = re.compile(r"\b(SHALL|MUST)\b")
# Changelog wording only; a bare date can be legitimate scenario data, so it is not flagged.
CHANGELOG_RE = re.compile(r"\b(added|changed|removed|updated|introduced|deprecated) (in|on|by) (v?\d|pr\b|#|change\b)"
                          r"|\bsince v\d|\bPR #\d+", re.I)
MIN_WHY, MAX_WHY, MAX_REQ_CHARS, MAX_DELTAS = 50, 1000, 500, 10
# A task is a list item carrying a checkbox: `- [ ]`, `* [x]`, `1. [ ]`, `+ [~]`.
TASK_RE = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])\s*\[\s*[^\]\s]?\s*\]\s*(.*)$")
LIST_ITEM_RE = re.compile(r"^\s{0,3}(?:[-*+]|\d{1,9}[.)])\s+\S")
GROUP_HEADING_RE = re.compile(r"^ {0,3}##(?!#)\s*(?:(\d+)\.(?:\s|$))?")
TASK_ID_RE = re.compile(r"^(\d+(?:\.\d+)+[A-Za-z]*)(?=\s|$)")
# A Purpose nobody wrote: TBD/TODO opening it. In capitals it is the marker whatever follows;
# in any other case only when punctuation or the line end follows, so Spanish "Todo el..." passes.
PLACEHOLDER_SHOUTED_RE = re.compile(r"^(?:TBD|TODO)(?![^\W_]|_)")
PLACEHOLDER_PUNCT_RE = re.compile(r"^(?:tbd|todo)(?![^\W_]|_)(?=[ \t]*(?:$|[:\-–—.,;()\[\]{}]))", re.I)


def norm(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip().casefold()


# --- parsing --------------------------------------------------------------------------------

def strip_fences(lines: list[str]) -> list[str]:
    """Blank out fenced code so headings inside examples are not parsed."""
    out, fenced = [], False
    for ln in lines:
        if ln.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            out.append("")
        else:
            out.append("" if fenced else ln)
    return out


@dataclass
class Block:
    name: str
    lines: list[str]          # the whole block, header included, trailing blank lines trimmed
    line_no: int

    @property
    def scenarios(self) -> list[str]:
        return [m.group(1) for ln in self.lines if (m := SCENARIO_RE.match(ln))]

    @property
    def statement(self) -> str:
        body = []
        for ln in self.lines[1:]:
            if SCENARIO_RE.match(ln):
                break
            body.append(ln)
        return " ".join(x.strip() for x in body if x.strip())


@dataclass
class Doc:
    path: Path
    preamble: list[str] = field(default_factory=list)                 # lines before the first ## section
    sections: list[tuple[str, list[str], int]] = field(default_factory=list)  # (heading, lines, line_no)

    def section(self, title: str) -> list[str] | None:
        for h, body, _ in self.sections:
            if h.lower() == title.lower():
                return body
        return None


def parse_doc(path: Path) -> Doc:
    raw = path.read_text(encoding="utf-8").splitlines()
    lines = strip_fences(raw)
    doc = Doc(path)
    cur: list[str] | None = None
    for i, (ln, orig) in enumerate(zip(lines, raw), 1):
        if ln.startswith("## "):
            cur = []
            doc.sections.append((ln[3:].strip(), cur, i))
        elif cur is None:
            doc.preamble.append(orig)
        else:
            cur.append(orig)
    return doc


def parse_blocks(body: list[str], first_line: int) -> tuple[list[Block], list[tuple[int, str]]]:
    """Split a section body into requirement blocks; also return stray non-blank lines before the first."""
    blocks: list[Block] = []
    stray: list[tuple[int, str]] = []
    fenced_view = strip_fences(body)
    cur: Block | None = None
    for i, (ln, orig) in enumerate(zip(fenced_view, body)):
        m = REQ_RE.match(ln)
        if m:
            cur = Block(m.group(1), [orig], first_line + i + 1)
            blocks.append(cur)
        elif cur is not None:
            cur.lines.append(orig)
        elif orig.strip():
            stray.append((first_line + i + 1, orig))
    for b in blocks:
        while b.lines and not b.lines[-1].strip():
            b.lines.pop()
    return blocks, stray


def parse_renames(body: list[str]) -> tuple[list[tuple[str, str]], list[str]]:
    pairs, errors, pending = [], [], None
    for ln in body:
        m = RENAME_RE.match(ln)
        if not m:
            continue
        side, name = m.group(1).upper(), m.group(2).strip()
        if side == "FROM":
            if pending is not None:
                errors.append(f'RENAMED FROM "{pending}" has no matching TO line')
            pending = name
        else:
            if pending is None:
                errors.append(f'RENAMED TO "{name}" has no matching FROM line')
            else:
                pairs.append((pending, name))
                pending = None
    if pending is not None:
        errors.append(f'RENAMED FROM "{pending}" has no matching TO line')
    return pairs, errors


@dataclass
class Delta:
    capability: str
    path: Path
    purpose: list[str] | None
    added: list[Block] = field(default_factory=list)
    modified: list[Block] = field(default_factory=list)
    removed: list[Block] = field(default_factory=list)
    renamed: list[tuple[str, str]] = field(default_factory=list)


def parse_delta(path: Path, capability: str, errors: list[str], warnings: list[str]) -> Delta:
    doc = parse_doc(path)
    delta = Delta(capability, path, doc.section("Purpose"))
    rel = f"specs/{capability}/spec.md"
    seen_delta = False
    for heading, body, line_no in doc.sections:
        m = DELTA_HEADER_RE.match("## " + heading)
        if not m:
            if heading.lower() != "purpose":
                blocks, _ = parse_blocks(body, line_no)
                for b in blocks:
                    errors.append(f'{rel}:{b.line_no}: requirement "{b.name}" sits under "## {heading}", '
                                  "which is not a delta section, so a merge would ignore it")
            continue
        seen_delta = True
        kind = m.group(1).upper()
        if kind == "RENAMED":
            pairs, errs = parse_renames(body)
            delta.renamed.extend(pairs)
            errors.extend(f"{rel}: {e}" for e in errs)
            continue
        blocks, stray = parse_blocks(body, line_no)
        for ln_no, text in stray:
            warnings.append(f"{rel}:{ln_no}: text before the first requirement in {kind} is not merged: {text.strip()[:60]!r}")
        getattr(delta, kind.lower()).extend(blocks)
    if not seen_delta:
        errors.append(f"{rel}: no delta sections (## ADDED/MODIFIED/REMOVED/RENAMED Requirements)")
    return delta


# --- validate -------------------------------------------------------------------------------

def find_deltas(change: Path, errors: list[str]) -> list[tuple[str, Path]]:
    root = change / "specs"
    out = []
    if not root.is_dir():
        return out
    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root)
        if f.name != "spec.md" or len(rel.parts) < 2:
            errors.append(f"specs/{rel}: a delta must be specs/<capability-path>/spec.md; this file is ignored")
            continue
        out.append(("/".join(rel.parts[:-1]), f))
    return out


def purpose_is_placeholder(purpose: list[str]) -> bool:
    """True when a `## Purpose` opens with a TBD/TODO marker rather than written prose."""
    prose = "\n".join(strip_fences(purpose)).strip()
    return bool(PLACEHOLDER_SHOUTED_RE.match(prose) or PLACEHOLDER_PUNCT_RE.match(prose))


def check_tasks(path: Path) -> list[str]:
    """tasks.md must hold checkboxes, and numbered task IDs must sit in their own `## N.` group once."""
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8").splitlines()
    lines = strip_fences(raw)
    in_comment = False
    visible: list[tuple[int, str]] = []
    for i, ln in enumerate(lines, 1):
        if in_comment:
            in_comment = "-->" not in ln
            continue
        if ln.lstrip().startswith("<!--"):
            in_comment = "-->" not in ln[ln.index("<!--") + 4:]
            continue
        visible.append((i, ln))
    tasks = [(i, m.group(1)) for i, ln in visible if (m := TASK_RE.match(ln))]
    if not tasks:
        first = next((i for i, ln in visible if LIST_ITEM_RE.match(ln)), None)
        where = f"tasks.md:{first}" if first else "tasks.md"
        errors.append(f"{where}: no task is a checkbox, so progress counts 0 tasks and nothing reads as "
                      'unfinished; write each task as "- [ ] 1.1 <behaviour delivered>"')
        return errors
    group: str | None = None
    seen: dict[str, int] = {}
    task_lines = dict(tasks)
    for i, ln in visible:
        if (g := GROUP_HEADING_RE.match(ln)) and ln.lstrip().startswith("##"):
            group = g.group(1)
            continue
        if group is None or i not in task_lines:
            continue
        m = TASK_ID_RE.match(task_lines[i])
        if not m:
            continue
        tid = m.group(1)
        lead = tid.split(".")[0].lstrip("0") or "0"
        if lead != (group.lstrip("0") or "0"):
            errors.append(f'tasks.md:{i}: task "{tid}" sits under group {group} but its number points to '
                          f"group {tid.split('.')[0]}; move or renumber it")
        if tid in seen:
            errors.append(f'tasks.md:{i}: task ID "{tid}" is duplicated (first on line {seen[tid]})')
        else:
            seen[tid] = i
    return errors


def check_requirement(b: Block, label: str, rel: str, errors: list[str], warnings: list[str],
                      need_id: bool) -> None:
    where = f"{rel}:{b.line_no}"
    if not NORMATIVE_RE.search(b.statement):
        errors.append(f'{where}: {label} "{b.name}" has no SHALL or MUST in its statement')
    if len(b.statement) > MAX_REQ_CHARS:
        warnings.append(f'{where}: {label} "{b.name}" statement is over {MAX_REQ_CHARS} chars; move detail into scenarios')
    if any(BULLET_SCENARIO_RE.match(ln) for ln in b.lines):
        errors.append(f'{where}: {label} "{b.name}" writes a scenario as a bullet; use "#### Scenario: <name>"')
    if not b.scenarios:
        errors.append(f'{where}: {label} "{b.name}" needs at least one "#### Scenario:" block')
    text = "\n".join(b.lines)
    for sc in re.split(r"^####\s+Scenario:", text, flags=re.M)[1:]:
        name = sc.splitlines()[0].strip()
        if not re.search(r"\bWHEN\b", sc) or not re.search(r"\bTHEN\b", sc):
            errors.append(f'{where}: scenario "{name}" under "{b.name}" needs both WHEN and THEN')
    if need_id and not REQ_ID_RE.search(b.name):
        warnings.append(f'{where}: {label} "{b.name}" has no stable [REQ-...] ID')


def validate_change(change: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    proposal = change / "proposal.md"
    deltas = find_deltas(change, errors)
    if not proposal.exists():
        errors.append("proposal.md is missing")
        no_delta_ok = False
    else:
        doc = parse_doc(proposal)
        text = proposal.read_text(encoding="utf-8")
        why = doc.section("Why")
        if why is None:
            errors.append("proposal.md: missing ## Why")
        else:
            n = len(" ".join(x.strip() for x in why if x.strip()))
            if n < MIN_WHY:
                errors.append(f"proposal.md: ## Why is {n} chars; state the problem and trigger in at least {MIN_WHY}")
            elif n > MAX_WHY:
                warnings.append(f"proposal.md: ## Why is {n} chars; keep it under {MAX_WHY}")
        what = doc.section("What changes")
        if what is None or not any(x.strip() for x in what):
            errors.append("proposal.md: ## What changes is missing or empty")
        if doc.section("Decisions needing sign-off") is None:
            errors.append("proposal.md: missing ## Decisions needing sign-off (write `None` if there are none)")
        if doc.section("Non-goals") is None:
            warnings.append("proposal.md: no ## Non-goals section")
        no_delta_ok = "No spec delta: observable behaviour unchanged" in text
        if no_delta_ok and deltas:
            errors.append("proposal.md declares no spec delta, but delta files exist under specs/")
    if not (change / "tasks.md").exists():
        errors.append("tasks.md is missing")
    else:
        errors.extend(check_tasks(change / "tasks.md"))
    if not deltas and not no_delta_ok:
        errors.append("no delta specs under specs/ and proposal.md does not say "
                      "'No spec delta: observable behaviour unchanged'")

    total = 0
    for cap, path in deltas:
        rel = f"specs/{cap}/spec.md"
        d = parse_delta(path, cap, errors, warnings)
        total += len(d.added) + len(d.modified) + len(d.removed) + len(d.renamed)
        for kind in ("added", "modified", "removed"):
            names = [norm(b.name) for b in getattr(d, kind)]
            for n in {x for x in names if names.count(x) > 1}:
                errors.append(f'{rel}: duplicate requirement in {kind.upper()}: "{n}"')
        for b in d.added:
            check_requirement(b, "ADDED", rel, errors, warnings, need_id=True)
        for b in d.modified:
            check_requirement(b, "MODIFIED", rel, errors, warnings, need_id=False)
        sets = {k: {norm(b.name) for b in getattr(d, k)} for k in ("added", "modified", "removed")}
        for a, b_ in (("added", "modified"), ("modified", "removed"), ("added", "removed")):
            for n in sets[a] & sets[b_]:
                errors.append(f'{rel}: "{n}" is in both {a.upper()} and {b_.upper()}')
        froms = [norm(f) for f, _ in d.renamed]
        tos = [norm(t) for _, t in d.renamed]
        for n in {x for x in froms if froms.count(x) > 1}:
            errors.append(f'{rel}: duplicate FROM in RENAMED: "{n}"')
        for n in {x for x in tos if tos.count(x) > 1}:
            errors.append(f'{rel}: duplicate TO in RENAMED: "{n}"')
        for f in froms:
            if f in sets["modified"]:
                errors.append(f'{rel}: MODIFIED uses the old name "{f}"; after a RENAMED use the TO header')
        for t in tos:
            if t in sets["added"]:
                errors.append(f'{rel}: RENAMED TO "{t}" collides with an ADDED requirement')
        if d.purpose is not None and (d.modified or d.removed or d.renamed):
            warnings.append(f"{rel}: ## Purpose belongs only in a delta that creates a new capability")
        if d.purpose is not None and purpose_is_placeholder(d.purpose):
            errors.append(f"{rel}: ## Purpose is a TBD/TODO placeholder; say what the capability is for "
                          "before it is merged into a living spec")
    if total > MAX_DELTAS:
        warnings.append(f"{total} requirement deltas in one change; consider splitting it (over {MAX_DELTAS})")
    return errors, warnings


# --- merge ----------------------------------------------------------------------------------

class MergeError(Exception):
    pass


def render_living(title: str, purpose: list[str], blocks: list[Block]) -> str:
    out = [f"# {title}", "", "## Purpose", ""]
    out += [ln for ln in _trim(purpose)]
    out += ["", "## Requirements", ""]
    for b in blocks:
        out += b.lines + [""]
    return "\n".join(out).rstrip() + "\n"


def _trim(lines: list[str]) -> list[str]:
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _find(blocks: list[Block], name: str, cap: str, op: str) -> int:
    for i, b in enumerate(blocks):
        if b.name.strip() == name.strip():
            return i
    for b in blocks:
        if norm(b.name) == norm(name):
            raise MergeError(f'{cap}: {op} "{name}" not found, but "{b.name}" exists; fix the header to match it exactly')
    raise MergeError(f'{cap}: {op} target "{name}" not found in the living spec')


def plan_capability(delta: Delta, living_path: Path, retire: set[str]) -> str | None:
    """Return the new living-spec text, or None when the capability is retired."""
    cap = delta.capability
    if living_path.exists():
        doc = parse_doc(living_path)
        title = next((ln[2:].strip() for ln in doc.preamble if ln.startswith("# ")), cap)
        purpose = doc.section("Purpose") or []
        req_body = doc.section("Requirements")
        if req_body is None:
            raise MergeError(f"{cap}: living spec has no ## Requirements section")
        line_no = next(n for h, _, n in doc.sections if h.lower() == "requirements")
        blocks, _ = parse_blocks(req_body, line_no)
    else:
        if delta.modified or delta.removed or delta.renamed:
            raise MergeError(f"{cap}: no living spec exists, so only ADDED (with ## Purpose) is valid")
        if not delta.purpose or not any(x.strip() for x in delta.purpose):
            raise MergeError(f"{cap}: a new capability needs ## Purpose in its delta")
        title = next((ln[2:].replace("(Delta)", "").strip() for ln in parse_doc(delta.path).preamble
                      if ln.startswith("# ")), cap)
        purpose, blocks = delta.purpose, []

    blocks = list(blocks)
    for frm, to in delta.renamed:
        i = _find(blocks, frm, cap, "RENAMED")
        for b in blocks:
            if norm(b.name) == norm(to):
                raise MergeError(f'{cap}: RENAMED target "{to}" already exists' +
                                 ("" if b.name.strip() == to.strip() else f' (as "{b.name}", differing only in case or spacing)'))
        old = blocks[i]
        blocks[i] = Block(to, [f"### Requirement: {to}"] + old.lines[1:], old.line_no)
    for rem in delta.removed:
        blocks.pop(_find(blocks, rem.name, cap, "REMOVED"))
    for mod in delta.modified:
        i = _find(blocks, mod.name, cap, "MODIFIED")
        missing = [s for s in blocks[i].scenarios if norm(s) not in {norm(x) for x in mod.scenarios}]
        if missing:
            raise MergeError(f'{cap}: MODIFIED "{mod.name}" drops scenario(s) the living spec has: '
                             + ", ".join(f'"{s}"' for s in missing)
                             + "; copy the full block (law 4) or move them to REMOVED intent explicitly")
        blocks[i] = Block(blocks[i].name, mod.lines, blocks[i].line_no)
    for add in delta.added:
        for b in blocks:
            if norm(b.name) == norm(add.name):
                raise MergeError(f'{cap}: ADDED "{add.name}" already exists' +
                                 ("" if b.name.strip() == add.name.strip() else f' as "{b.name}"; use MODIFIED with that exact header'))
        ids = REQ_ID_RE.findall(add.name)
        for b in blocks:
            if ids and ids[0] in b.name:
                raise MergeError(f'{cap}: ADDED "{add.name}" reuses ID {ids[0]} already on "{b.name}"')
        blocks.append(add)

    if not blocks:
        if cap not in retire:
            raise MergeError(f"{cap}: these deltas remove every requirement; rerun with --retire {cap} "
                             "after confirming the capability should be deleted")
        return None
    return render_living(title, purpose, blocks)


def merge_change(change: Path, specs_root: Path, write: bool, retire: set[str]) -> list[str]:
    errors, warnings = validate_change(change)
    if errors:
        raise MergeError("validation failed; fix these first:\n  " + "\n  ".join(errors))
    plan: list[tuple[Path, str | None]] = []
    for cap, path in find_deltas(change, []):
        delta = parse_delta(path, cap, [], [])
        living = specs_root / cap / "spec.md"
        plan.append((living, plan_capability(delta, living, retire)))
    report = [f"warning: {w}" for w in warnings]
    for living, text in plan:
        verb = "retire" if text is None else ("update" if living.exists() else "create")
        report.append(f"{verb} {living}")
    if write:
        for living, text in plan:
            if text is None:
                living.unlink()
            else:
                living.parent.mkdir(parents=True, exist_ok=True)
                living.write_text(text, encoding="utf-8")
        report.append(f"wrote {len(plan)} capability spec(s); now run audit, then move the change to changes/archive/")
    else:
        report.append("dry run: nothing written (add --write)")
    return report


# --- audit ----------------------------------------------------------------------------------

def audit_living(path: Path) -> list[str]:
    errors: list[str] = []
    doc = parse_doc(path)
    heads = [h.lower() for h, _, _ in doc.sections]
    if heads.count("purpose") != 1 or heads.count("requirements") != 1:
        errors.append(f"{path}: needs exactly one ## Purpose and one ## Requirements")
    for h, _, n in doc.sections:
        if DELTA_HEADER_RE.match("## " + h):
            errors.append(f"{path}:{n}: leftover delta header ## {h}")
        elif h.lower() not in ("purpose", "requirements"):
            errors.append(f"{path}:{n}: unexpected section ## {h} in a living spec")
    purpose = doc.section("Purpose")
    if purpose is not None and purpose_is_placeholder(purpose):
        n = next(n for h, _, n in doc.sections if h.lower() == "purpose")
        errors.append(f"{path}:{n}: ## Purpose is still a TBD/TODO placeholder; write what the capability is for")
    body = doc.section("Requirements") or []
    line_no = next((n for h, _, n in doc.sections if h.lower() == "requirements"), 0)
    blocks, _ = parse_blocks(body, line_no)
    names = [norm(b.name) for b in blocks]
    for n in {x for x in names if names.count(x) > 1}:
        errors.append(f'{path}: duplicate requirement "{n}"')
    ids = [i for b in blocks for i in REQ_ID_RE.findall(b.name)]
    for i in {x for x in ids if ids.count(x) > 1}:
        errors.append(f"{path}: duplicate ID {i}")
    for b in blocks:
        if not b.scenarios:
            errors.append(f'{path}:{b.line_no}: requirement "{b.name}" has no scenario')
    for i, ln in enumerate(strip_fences(path.read_text(encoding="utf-8").splitlines()), 1):
        if CHANGELOG_RE.search(ln):
            errors.append(f"{path}:{i}: looks like changelog or date text; living specs hold current behaviour only: {ln.strip()[:60]!r}")
    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("change", type=Path)
    m = sub.add_parser("merge")
    m.add_argument("change", type=Path)
    m.add_argument("--specs", type=Path, required=True)
    m.add_argument("--write", action="store_true")
    m.add_argument("--retire", action="append", default=[])
    a_ = sub.add_parser("audit")
    a_.add_argument("paths", type=Path, nargs="+")
    a = ap.parse_args(argv)

    if a.cmd == "validate":
        if not a.change.is_dir():
            print(f"error: {a.change} is not a directory", file=sys.stderr)
            return 2
        errors, warnings = validate_change(a.change)
        for w in warnings:
            print(f"warning: {w}")
        for e in errors:
            print(f"error: {e}")
        print("OK" if not errors else f"FAILED: {len(errors)} error(s)")
        return 1 if errors else 0
    if a.cmd == "merge":
        try:
            for line in merge_change(a.change, a.specs, a.write, set(a.retire)):
                print(line)
        except MergeError as e:
            print(f"error: {e}\nnothing was written")
            return 1
        return 0
    files: list[Path] = []
    for p in a.paths:
        files += sorted(p.rglob("spec.md")) if p.is_dir() else [p]
    files = [f for f in files if "changes" not in f.parts]
    errors = [e for f in files for e in audit_living(f)]
    for e in errors:
        print(f"error: {e}")
    print(f"OK: {len(files)} living spec(s)" if not errors else f"FAILED: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
