#!/usr/bin/env python3
"""Zero-dependency repository validator and CREDITS.md synchronizer.

Usage:
  python3 scripts/check.py                 # validate skills, rules, externals, CREDITS.md, and hook tests
  python3 scripts/check.py --sync-credits  # regenerate CREDITS.md from skill/rule/external metadata, then validate
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLKIT = ROOT / "toolkit"
CREDITS = ROOT / "CREDITS.md"
VALID_TOOLS = {"claude", "codex", "agy"}
VALID_EXTERNAL_STATUS = {"adopted", "optional", "trial"}
MAX_DESC_CHARS = 360
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
REL_REF_RE = re.compile(
    r"(?:`|\]\()((?:references|resources|scripts)/[A-Za-z0-9_./-]+)(?:`|\))"
)
TRIAL_PROSE_RE = re.compile(
    r"\b(?:trial\s+decided|decided\s+to\s+trial|on\s+trial|status:\s*trial)\b|决定试用|试用期|试用中",
    re.I,
)
TRIAL_UNSTARTED_RE = re.compile(r"\bnot\s+yet\s+started\b|尚未开始|未开始", re.I)


def strip_quotes(val: str) -> str:
    val = val.strip()
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
        if val[0] == '"':
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return val[1:-1]
        return val[1:-1].replace("''", "'")
    return val


def strip_inline_comment(val: str) -> str:
    in_quote = None
    for i, ch in enumerate(val):
        if ch in ('"', "'"):
            in_quote = None if in_quote == ch else (ch if in_quote is None else in_quote)
        elif ch == "#" and in_quote is None and (i == 0 or val[i - 1].isspace()):
            return val[:i].strip()
    return val.strip()


def parse_skill_frontmatter(path: Path, errors: list[str]) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        errors.append(f"{path.relative_to(ROOT)}: missing opening/closing --- frontmatter")
        return {}
    end_idx = lines[1:].index("---") + 1
    fm_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :])

    data: dict[str, object] = {"_body": body}
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line[0].isspace():
            errors.append(f"{path.relative_to(ROOT)}: unexpected indentation in frontmatter: {line!r}")
            i += 1
            continue
        key, sep, raw_val = line.partition(":")
        if not sep:
            errors.append(f"{path.relative_to(ROOT)}: malformed frontmatter line: {line!r}")
            i += 1
            continue
        key = key.strip()
        val = raw_val.strip()

        if val in (">", ">-", "|", "|-"):
            folded: list[str] = []
            i += 1
            while i < len(fm_lines) and (fm_lines[i].startswith("  ") or not fm_lines[i].strip()):
                folded.append(fm_lines[i].strip())
                i += 1
            joiner = " " if val.startswith(">") else "\n"
            data[key] = joiner.join(p for p in folded if p).strip()
            continue

        if val == "":
            items: list[str] = []
            i += 1
            while i < len(fm_lines) and (
                fm_lines[i].startswith("  - ") or fm_lines[i].startswith("    ") or not fm_lines[i].strip()
            ):
                sline = fm_lines[i]
                if sline.startswith("  - "):
                    item_raw = sline[4:].strip()
                    i += 1
                    cont: list[str] = [item_raw]
                    while i < len(fm_lines) and fm_lines[i].startswith("    "):
                        cont.append(fm_lines[i].strip())
                        i += 1
                    joined_raw = " ".join(cont)
                    if joined_raw and joined_raw[0] not in ('"', "'") and ": " in joined_raw:
                        errors.append(
                            f"{path.relative_to(ROOT)}: unquoted ': ' in YAML list item under {key}: {joined_raw!r}"
                        )
                    items.append(strip_quotes(joined_raw))
                    continue
                i += 1
            data[key] = items
            continue

        if val[0] not in ('"', "'") and ": " in val:
            errors.append(f"{path.relative_to(ROOT)}: unquoted ': ' in YAML scalar {key}: {val!r}")
        data[key] = strip_quotes(val)
        i += 1

    return data


def parse_rule_sources(path: Path, errors: list[str]) -> OrderedDict[str, list[str]]:
    out: OrderedDict[str, list[str]] = OrderedDict()
    cur: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw[0].isspace() and raw.endswith(":"):
            cur = raw[:-1].strip()
            out[cur] = []
        elif cur is not None and raw.startswith("  - "):
            item = raw[4:].strip()
            out[cur].append(strip_quotes(item))
        else:
            errors.append(f"{path.relative_to(ROOT)}: malformed line: {raw!r}")
    return out


def _parse_iso_date(raw: str) -> date | None:
    if not ISO_DATE_RE.match(raw):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def validate_external_trials(
    entries: list[dict],
    errors: list[str],
    today: date | None = None,
    label: str = "toolkit/external.yaml",
) -> None:
    ref_date = today or date.today()
    for e in entries:
        name = e["name"] or "<unnamed>"
        status = str(e.get("status", "")).strip().lower()
        if status and status not in VALID_EXTERNAL_STATUS:
            errors.append(
                f"{label}: {name} has invalid status {e['status']!r} "
                f"(expected one of {sorted(VALID_EXTERNAL_STATUS)})"
            )
        prose_blob = " ".join(e.get("prose", []))
        raw_start = str(e.get("trial_start", "")).strip()
        raw_review = str(e.get("trial_review_by", "")).strip()
        is_trial = (
            status == "trial"
            or bool(raw_start or raw_review)
            or bool(TRIAL_PROSE_RE.search(prose_blob))
        )
        if not is_trial:
            continue

        if TRIAL_UNSTARTED_RE.search(prose_blob):
            errors.append(
                f"{label}: {name} is marked for trial but unstarted; "
                "set concrete trial_start and trial_review_by dates once started, or remove the trial entry"
            )
        if not raw_start:
            errors.append(f"{label}: {name} is marked for trial and must declare trial_start: YYYY-MM-DD")
        if not raw_review:
            errors.append(f"{label}: {name} is marked for trial and must declare trial_review_by: YYYY-MM-DD")

        start_dt = _parse_iso_date(raw_start) if raw_start else None
        review_dt = _parse_iso_date(raw_review) if raw_review else None
        if raw_start and start_dt is None:
            errors.append(f"{label}: {name} has invalid trial_start {raw_start!r} (expected YYYY-MM-DD)")
        if raw_review and review_dt is None:
            errors.append(f"{label}: {name} has invalid trial_review_by {raw_review!r} (expected YYYY-MM-DD)")
        if start_dt and review_dt:
            if review_dt < start_dt:
                errors.append(
                    f"{label}: {name} has trial_review_by ({raw_review}) earlier than trial_start ({raw_start})"
                )
            elif ref_date > review_dt:
                errors.append(
                    f"{label}: {name} trial expired on {raw_review} "
                    f"(started {raw_start}, today {ref_date.isoformat()}) — adopt, absorb into a skill, or remove"
                )


def parse_external_yaml(path: Path, errors: list[str], today: date | None = None) -> list[dict]:
    label = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    entries: list[dict] = []
    cur: dict | None = None
    in_install = False
    in_folded = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("- name:"):
            cur = {
                "name": strip_inline_comment(line.split(":", 1)[1]),
                "category": "",
                "repo": "",
                "license": "",
                "tools": [],
                "install": [],
                "optional": False,
                "status": "",
                "trial_start": "",
                "trial_review_by": "",
                "prose": [],
            }
            entries.append(cur)
            in_install = False
            in_folded = False
        elif cur is None or not line.strip() or line.lstrip().startswith("#"):
            continue
        elif in_install and re.match(r"^ {2,4}- ", line):
            cur["install"].append(re.sub(r"^ {2,4}- ", "", line).strip())
        elif in_folded and line.startswith("    "):
            cur["prose"].append(line.strip())
        elif line.startswith("  ") and not line.startswith("   "):
            in_install = False
            in_folded = False
            key, _, raw_val = line.strip().partition(":")
            val = strip_inline_comment(raw_val)
            if val in (">", ">-", "|", "|-"):
                in_folded = True
            elif key == "install":
                in_install = True
            elif key == "tools":
                cur["tools"] = [t.strip() for t in val.split(",") if t.strip()]
            elif key == "optional":
                cur["optional"] = val.lower() == "true"
            elif key in ("category", "repo", "license", "status", "trial_start", "trial_review_by"):
                cur[key] = strip_quotes(val)
            elif key in ("covers", "notes", "why_not_rewritten") and val:
                cur["prose"].append(strip_quotes(val))
    for e in entries:
        for req in ("name", "category", "repo", "license"):
            if not e[req]:
                errors.append(f"{label}: {e['name'] or '<unnamed>'} missing {req}:")
        if not e["install"]:
            errors.append(f"{label}: {e['name']} missing install commands")
        if not e["tools"] or (set(e["tools"]) - VALID_TOOLS):
            errors.append(f"{label}: {e['name']} has invalid tools: {e['tools']}")
    validate_external_trials(entries, errors, today=today, label=label)
    return entries


def extract_skill_structure(body: str) -> dict[str, set[int]]:
    clean = re.sub(r"```.*?```", "", body, flags=re.S)
    steps = {int(m.group(1)) for m in re.finditer(r"^#{2,3}\s+Step\s+(\d+)\b", clean, re.M)}
    passes = {int(m.group(1)) for m in re.finditer(r"^#{2,3}\s+Pass\s+(\d+)\b", clean, re.M)}
    sections = {int(m.group(1)) for m in re.finditer(r"^#{2,3}\s+(\d+)\.\s+", clean, re.M)}
    laws: set[int] = set()
    law_sec = re.search(r"^##\s+(?:Iron\s+)?[Ll]aws\b.*?\n(.*?)(?=^##\s+|\Z)", clean, re.M | re.S)
    if law_sec:
        laws = {int(m.group(1)) for m in re.finditer(r"^(\d+)\.\s+", law_sec.group(1), re.M)}
    return {"steps": steps, "passes": passes, "sections": sections, "laws": laws}


def validate_skill_section_refs(
    skill_bodies: dict[str, tuple[Path, str]],
    errors: list[str],
) -> None:
    structures = {name: extract_skill_structure(body) for name, (_, body) in skill_bodies.items()}
    for name, (rel, body) in skill_bodies.items():
        clean = re.sub(r"```.*?```", "", body, flags=re.S)
        own = structures[name]

        for m in re.finditer(r"(?:`([a-z0-9-]+)`\s+)?\bStep\s+(\d+)\b", clean):
            if clean[max(0, m.start() - 4) : m.start()].lstrip().startswith("#"):
                continue
            target_skill, num = m.group(1), int(m.group(2))
            target = structures.get(target_skill) if target_skill else own
            if target is None or num not in target["steps"]:
                errors.append(f"{rel}: Step {num} reference does not match any Step heading in {target_skill or name}")

        for m in re.finditer(r"(?:`([a-z0-9-]+)`\s+)?\bPass\s+(\d+)\b", clean):
            if clean[max(0, m.start() - 4) : m.start()].lstrip().startswith("#"):
                continue
            target_skill, num = m.group(1), int(m.group(2))
            target = structures.get(target_skill) if target_skill else own
            if target is None or num not in target["passes"]:
                errors.append(f"{rel}: Pass {num} reference does not match any Pass heading in {target_skill or name}")

        for m in re.finditer(r"(?:`([a-z0-9-]+)`\s+)?\b(?:Iron\s+)?[Ll]aw\s+(\d+)\b", clean):
            target_skill, num = m.group(1), int(m.group(2))
            target = structures.get(target_skill) if target_skill else own
            if target is None or num not in target["laws"]:
                errors.append(f"{rel}: law {num} reference does not match any Iron law in {target_skill or name}")

        for m in re.finditer(r"(?:`([a-z0-9-]+)`\s+)?(?:§|section\s+)(\d+)\b", clean, re.I):
            target_skill, num = m.group(1), int(m.group(2))
            target = structures.get(target_skill) if target_skill else own
            if target is None or num not in target["sections"]:
                errors.append(
                    f"{rel}: section/§{num} reference does not match any numbered section in {target_skill or name}"
                )


def validate_install_external_prefixes(
    install_sh: Path,
    externals: list[dict],
    errors: list[str],
) -> None:
    txt = install_sh.read_text(encoding="utf-8")
    m = re.search(r"BASE_EXTERNAL_PREFIXES\s*=\s*\((.*?)\)", txt, re.S)
    if not m:
        errors.append("install.sh: missing BASE_EXTERNAL_PREFIXES tuple")
        return
    prefixes = re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1))
    flat_prefixes = [a or b for a, b in prefixes]
    active_tokens = {e["name"].lower() for e in externals} | {
        sm.lower()
        for e in externals
        for cmd in e["install"]
        for sm in re.findall(r"(?:^|\s)(?:-s|--skill)\s+([A-Za-z0-9_.-]+)", cmd)
    }
    for pref in flat_prefixes:
        plow = pref.lower()
        if not any(tok == plow or tok.startswith(plow) for tok in active_tokens):
            errors.append(
                f"install.sh: BASE_EXTERNAL_PREFIXES contains stale prefix {pref!r} not backed by toolkit/external.yaml"
            )


def build_expected_credits(
    skill_sources: list[tuple[str, list[str]]],
    rule_sources: OrderedDict[str, list[str]],
    externals: list[dict],
) -> str:
    merged: OrderedDict[str, list[str]] = OrderedDict()
    for skill_name, srcs in skill_sources:
        for s in srcs:
            merged.setdefault(s, [])
            if skill_name not in merged[s]:
                merged[s].append(skill_name)
    for rule_name, srcs in rule_sources.items():
        label = f"rule {rule_name}"
        for s in srcs:
            merged.setdefault(s, [])
            if label not in merged[s]:
                merged[s].append(label)

    lines = [
        "# Credits",
        "",
        "Skills here were written from the sources below: read and rewritten, not copied.",
        "Sources under CC BY-SA or CC BY-NC-SA contributed ideas only, no wording.",
        "",
        "## Per-skill sources",
        "",
    ]
    for src, users in merged.items():
        lines.append(f"- {src} — used in: {', '.join(users)}")
    lines.extend([
        "",
        "## Adopted external projects (installed from their own source; not included)",
        "",
    ])
    for e in externals:
        lines.append(f"- {e['name']} ({e['license']}) — {e['repo']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sync-credits", action="store_true", help="Write expected CREDITS.md before checking")
    args = ap.parse_args()

    errors: list[str] = []
    skill_mds = sorted(TOOLKIT.glob("*/skills/*/SKILL.md"))
    seen_names: dict[str, Path] = {}
    skill_sources: list[tuple[str, list[str]]] = []
    skill_bodies: dict[str, tuple[Path, str]] = {}
    total_desc_chars = 0

    for smd in skill_mds:
        rel = smd.relative_to(ROOT)
        fm = parse_skill_frontmatter(smd, errors)
        if not fm:
            continue
        name = fm.get("name")
        if name != smd.parent.name:
            errors.append(f"{rel}: frontmatter name {name!r} != directory name {smd.parent.name!r}")
        if isinstance(name, str):
            if name in seen_names:
                errors.append(f"{rel}: duplicate skill name {name!r} (also at {seen_names[name]})")
            seen_names[name] = rel

        desc = fm.get("description")
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"{rel}: missing non-empty description")
        else:
            total_desc_chars += len(desc)
            if len(desc) > MAX_DESC_CHARS:
                errors.append(f"{rel}: description is {len(desc)} chars (budget cap: {MAX_DESC_CHARS})")

        ver = fm.get("version")
        if not isinstance(ver, str) or not SEMVER_RE.match(ver):
            errors.append(f"{rel}: missing/invalid semver version (got {ver!r})")

        srcs = fm.get("sources")
        if not isinstance(srcs, list) or not srcs:
            errors.append(f"{rel}: missing non-empty sources list")
        else:
            skill_sources.append((smd.parent.name, [str(s) for s in srcs]))

        body = str(fm.get("_body", ""))
        skill_bodies[smd.parent.name] = (rel, body)
        docs_to_scan = [(rel, body)] + [
            (ref_md.relative_to(ROOT), ref_md.read_text(encoding="utf-8"))
            for ref_md in sorted((smd.parent / "references").glob("*.md"))
            if (smd.parent / "references").is_dir()
        ]
        for doc_rel, doc_text in docs_to_scan:
            for m in REL_REF_RE.finditer(doc_text):
                ref_rel = m.group(1)
                if "*" in ref_rel or "<" in ref_rel:
                    continue
                if not (smd.parent / ref_rel).exists():
                    errors.append(f"{doc_rel}: referenced file {ref_rel!r} does not exist")

    validate_skill_section_refs(skill_bodies, errors)

    # Validate rules & sources.yaml
    rule_files = sorted(r for r in (TOOLKIT / "rules").glob("*.md") if not r.name.endswith(".local.md"))
    rule_stems = {r.stem for r in rule_files}
    for rf in rule_files:
        txt = rf.read_text(encoding="utf-8")
        if txt.startswith("---"):
            m = re.match(r"---\n(.*?)\n---\n(.*)", txt, re.S)
            if not m:
                errors.append(f"{rf.relative_to(ROOT)}: unclosed frontmatter")
            else:
                globs = re.findall(r'-\s*"([^"]+)"', m.group(1))
                if not globs:
                    errors.append(f"{rf.relative_to(ROOT)}: path rule has no quoted globs")
                if not m.group(2).strip().startswith("# "):
                    errors.append(f"{rf.relative_to(ROOT)}: rule body must start with '# Title'")

    rule_sources = parse_rule_sources(TOOLKIT / "rules" / "sources.yaml", errors)
    missing_rule_prov = sorted(rule_stems - set(rule_sources))
    extra_rule_prov = sorted(set(rule_sources) - rule_stems)
    if missing_rule_prov:
        errors.append(f"toolkit/rules/sources.yaml: missing provenance for rules: {missing_rule_prov}")
    if extra_rule_prov:
        errors.append(f"toolkit/rules/sources.yaml: unknown rule keys: {extra_rule_prov}")

    # Validate category READMEs don't promise personal.local.md when category has no local skills/
    for cat_readme in sorted(TOOLKIT.glob("*/README.md")):
        if "personal.local.md" in cat_readme.read_text(encoding="utf-8"):
            if not list((cat_readme.parent / "skills").glob("*/SKILL.md")):
                errors.append(
                    f"{cat_readme.relative_to(ROOT)}: mentions personal.local.md but category has no local skills/"
                )

    externals = parse_external_yaml(TOOLKIT / "external.yaml", errors)
    validate_install_external_prefixes(ROOT / "install.sh", externals, errors)
    expected_credits = build_expected_credits(skill_sources, rule_sources, externals)
    if args.sync_credits:
        CREDITS.write_text(expected_credits, encoding="utf-8")
        print(f"Synced {CREDITS.relative_to(ROOT)}")

    actual_credits = CREDITS.read_text(encoding="utf-8") if CREDITS.exists() else ""
    if actual_credits != expected_credits:
        errors.append("CREDITS.md is out of sync with skill/rule/external sources (run: python3 scripts/check.py --sync-credits)")

    # Run validator and claim-check unit tests
    for label, test_script in (
        ("check.py", ROOT / "scripts" / "test_check.py"),
        ("claim-check", TOOLKIT / "hooks" / "claim-check" / "test_claim_check.py"),
    ):
        res = subprocess.run([sys.executable, str(test_script)], capture_output=True, text=True)
        if res.returncode != 0:
            errors.append(f"{label} tests failed:\n{res.stdout}\n{res.stderr}")

    if errors:
        print(f"FAILED ({len(errors)} issue(s)):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    avg_desc = total_desc_chars // max(len(skill_mds), 1)
    print(
        f"OK: {len(skill_mds)} skills ({total_desc_chars} total description chars, avg {avg_desc}), "
        f"{len(rule_files)} rules, {len(externals)} externals, CREDITS.md in sync, unit tests green."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
