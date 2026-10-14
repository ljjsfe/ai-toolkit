#!/usr/bin/env bash
# Install the toolkit for Claude Code and/or Codex.
#
#   ./install.sh claude|codex|both [--apply] [--replace-legacy] [--external]
#
# Without --apply nothing is written: the plan is printed (dry run).
# --external also installs the externally maintained components in toolkit/external.yaml
# (skipping entries marked optional), using their own installers.
# --replace-legacy (Claude Code) moves previously installed skills and rules into
# ~/.toolkit-backup/<timestamp>/ before installing — except claude.ai-synced skills, names in
# KEEP below or in ~/.toolkit-keep (one per line), and anything external installers added.
# Agents are never moved; they are listed for you to decide. Skills this toolkit installed in
# an earlier run but no longer ships are removed (tracked in a manifest).
# If a personal/ folder exists next to this script (private copies only; never exported),
# personal/skills/* install alongside the toolkit and personal/external.yaml adds externals.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"
APPLY=0
REPLACE=0
EXTERNAL=0
for arg in "${@:2}"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --replace-legacy) REPLACE=1 ;;
    --external) EXTERNAL=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done
case "$TARGET" in
  claude|codex|both) ;;
  *) sed -n '2,11p' "$0"; exit 2 ;;
esac

exec python3 - "$ROOT" "$TARGET" "$APPLY" "$REPLACE" "$EXTERNAL" <<'PY'
import json, re, shlex, shutil, subprocess, sys, tempfile, time
from pathlib import Path

root, target, apply, replace = Path(sys.argv[1]), sys.argv[2], sys.argv[3] == "1", sys.argv[4] == "1"
external = sys.argv[5] == "1"
home = Path.home()
toolkit = root / "toolkit"
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = home / ".toolkit-backup" / stamp
MARK_START, MARK_END = "<!-- toolkit:start -->", "<!-- toolkit:end -->"
KEEP = {"synced"}
EXTERNAL_PREFIXES = ("impeccable", "last30days", "review-animations", "mobile-native", "break-ui")
keep_file = home / ".toolkit-keep"
if keep_file.is_file():
    KEEP |= {l.strip() for l in keep_file.read_text().splitlines() if l.strip()}
PERSONAL_NOTE = ("\n\n---\nBefore applying this skill, read `PERSONAL.md` in this folder: it holds "
                 "this user's own parameters and preferences, which override the defaults above.\n")


def say(msg):
    print(("" if apply else "[dry-run] ") + msg)


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def copytree(src, dst):
    say(f"copy {src.relative_to(root)} -> {dst}")
    if apply:
        remove(dst)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "test_*.py", "*.local.md"))


def write(path, text):
    say(f"write {path}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def move_to_backup(path):
    if not path.exists():
        return
    dest = backup / path.relative_to(home)
    say(f"backup {path} -> {dest}")
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))


# ---- collect ---------------------------------------------------------------------------
def frontmatter(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        sys.exit(f"{path}: frontmatter must open and close with a line containing only ---")
    return "\n".join(lines[1:lines[1:].index("---") + 1])


personal = root / "personal"
skills = {}
for skill_md in sorted(toolkit.glob("*/skills/*/SKILL.md")) + sorted(personal.glob("skills/*/SKILL.md")):
    frontmatter(skill_md)
    d = skill_md.parent
    if d.name in skills:
        sys.exit(f"duplicate skill name {d.name}: {skills[d.name]} and {d}")
    skills[d.name] = d

rules = sorted(r for r in (toolkit / "rules").glob("*.md") if not r.name.endswith(".local.md"))
path_rules = [r for r in rules if r.read_text().startswith("---")]
core_rules = [r for r in rules if r not in path_rules]


def personal_for(skill_dir):
    p = skill_dir.parent.parent / "personal.local.md"
    return p if p.is_file() else None


def install_skill(name, src, dest_root):
    dst = dest_root / name
    copytree(src, dst)
    p = personal_for(src)
    if p:
        say(f"merge personal preferences {p.relative_to(root)} -> {dst / 'PERSONAL.md'}")
        if apply:
            shutil.copy(p, dst / "PERSONAL.md")
            with (dst / "SKILL.md").open("a", encoding="utf-8") as f:
                f.write(PERSONAL_NOTE)


def rule_to_skill(rule):
    text = rule.read_text()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    globs = re.findall(r'-\s*"([^"]+)"', m.group(1))
    body = m.group(2).strip()
    title = body.splitlines()[0].lstrip("# ").strip()
    desc = f"{title}. Use when reading or editing files matching: {', '.join(globs)}."
    return f"---\nname: {rule.stem}-traps\ndescription: {json.dumps(desc)}\n---\n\n{body}\n"


def upsert_block(path, block):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    new_block = f"{MARK_START}\n{block.strip()}\n{MARK_END}"
    if MARK_START in old:
        new = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), lambda _: new_block, old, flags=re.S)
    else:
        new = (old.rstrip() + "\n\n" if old.strip() else "") + new_block + "\n"
    write(path, new)


def sync_manifest(base, names):
    """Remove skills this toolkit installed before but no longer ships; record the new set."""
    manifest = base / ".toolkit-manifest.json"
    old = set(json.loads(manifest.read_text())) if manifest.exists() else set()
    for stale in sorted(old - set(names)):
        target = base / "skills" / stale
        if target.exists() or target.is_symlink():
            say(f"remove stale toolkit skill {target}")
            if apply:
                remove(target)
    if apply:
        manifest.write_text(json.dumps(sorted(names), indent=2) + "\n")


# ---- Claude Code -----------------------------------------------------------------------
def install_claude():
    base = home / ".claude"
    settings = base / "settings.json"
    try:
        data = json.loads(settings.read_text()) if settings.exists() else {}
    except json.JSONDecodeError as e:
        sys.exit(f"{settings} is not valid JSON ({e}); fix it before installing")
    ours = set(skills)
    if replace:
        for sub in ("skills", "rules"):
            for p in sorted((base / sub).glob("*")) if (base / sub).exists() else []:
                if p.name in KEEP or p.name in ours or p.name == "toolkit" or p.name.startswith(EXTERNAL_PREFIXES):
                    continue
                move_to_backup(p)
        agents = sorted(p.name for p in (base / "agents").glob("*")) if (base / "agents").exists() else []
        if agents:
            print(f"note: {len(agents)} agents in {base / 'agents'} were left in place; move them yourself if unwanted")
    for name, src in skills.items():
        install_skill(name, src, base / "skills")
    sync_manifest(base, skills)
    for r in rules:
        dst = base / "rules" / "toolkit" / r.name
        say(f"copy {r.relative_to(root)} -> {dst}")
        if apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(r, dst)
    hook = toolkit / "hooks" / "claim-check" / "claim_check.py"
    hook_dst = base / "hooks" / "toolkit" / "claim_check.py"
    say(f"copy {hook.relative_to(root)} -> {hook_dst}")
    cmd = f"python3 {shlex.quote(str(hook_dst))}"
    stop = data.setdefault("hooks", {}).setdefault("Stop", [])
    changed = not any(h.get("command") == cmd for e in stop for h in e.get("hooks", []))
    if changed:
        stop.append({"hooks": [{"type": "command", "command": cmd, "timeout": 10}]})
        say(f"register Stop hook in {settings} (previous file backed up)")
    if apply:
        hook_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(hook, hook_dst)
        if changed:
            if settings.exists():
                (backup / ".claude").mkdir(parents=True, exist_ok=True)
                shutil.copy(settings, backup / ".claude" / "settings.json")
            settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# ---- Codex -----------------------------------------------------------------------------
def install_codex():
    base = home / ".codex"
    for name, src in skills.items():
        install_skill(name, src, base / "skills")
    for r in path_rules:
        write(base / "skills" / f"{r.stem}-traps" / "SKILL.md", rule_to_skill(r))
    sync_manifest(base, list(skills) + [f"{r.stem}-traps" for r in path_rules])
    core = "\n\n".join(r.read_text().strip() for r in core_rules)
    agents_md = base / "AGENTS.md"
    old = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""
    if f"{MARK_START}\n{core.strip()}\n{MARK_END}" in old:
        say(f"{agents_md} already current")
        return
    if apply and agents_md.exists():
        (backup / ".codex").mkdir(parents=True, exist_ok=True)
        shutil.copy(agents_md, backup / ".codex" / "AGENTS.md")
    upsert_block(agents_md, core)
    say("hooks: Codex Stop-hook registration not automated; claim-check is Claude-only for now")


if target in ("claude", "both"):
    install_claude()
if target in ("codex", "both"):
    install_codex()

def external_entries():
    """Parse external.yaml files (a fixed subset of YAML, so no library is needed)."""
    entries, cur, in_install = [], None, False
    files = [toolkit / "external.yaml"] + ([personal / "external.yaml"] if (personal / "external.yaml").is_file() else [])
    lines = [l for f in files for l in f.read_text(encoding="utf-8").splitlines()]
    for line in lines:
        if line.startswith("- name:"):
            cur = {"name": line.split(":", 1)[1].strip(), "install": [], "tools": [], "optional": False}
            entries.append(cur)
            in_install = False
        elif cur is None or not line.strip() or line.lstrip().startswith("#"):
            continue
        elif in_install and line.startswith("    - "):
            cur["install"].append(line[6:].strip())
        elif line.startswith("  ") and not line.startswith("   "):
            in_install = False
            key, _, val = line.strip().partition(":")
            val = val.strip()
            if key == "install":
                in_install = True
            elif key == "tools":
                cur["tools"] = [t.strip() for t in val.split(",") if t.strip()]
            elif key == "optional":
                cur["optional"] = val == "true"
    for e in entries:
        if not e["install"] or not e["tools"]:
            sys.exit(f"external.yaml: entry {e['name']} needs tools: and an install: list")
    return entries


wanted = {"claude", "codex"} if target == "both" else {target}
print("\nExternal components (external.yaml):")
failed = []
for e in external_entries():
    if not wanted & set(e["tools"]):
        continue
    run = external and not e["optional"]
    label = "optional — install yourself when decided" if e["optional"] else ("installing" if run and apply else "would install" if run else "run with --external")
    print(f"  {e['name']} ({label}):")
    for cmd in e["install"]:
        print(f"      {cmd}")
        if run and apply and e["name"] not in failed:
            # Run outside any project: some installers also write per-project hooks into the cwd.
            if subprocess.run(cmd, shell=True, cwd=tempfile.mkdtemp()).returncode != 0:
                failed.append(e["name"])
if failed:
    print(f"\nExternal installs that failed: {', '.join(failed)} — rerun their commands by hand.")
print(f"\n{len(skills)} skills, {len(rules)} rule files." + ("" if apply else "  Re-run with --apply to write."))
if apply and backup.exists():
    print(f"Backups in {backup}")
PY
