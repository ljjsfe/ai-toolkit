#!/usr/bin/env bash
# Install the toolkit for Claude Code, Codex, and/or Antigravity (agy).
#
#   ./install.sh claude|codex|agy|both|all [--apply] [--replace-legacy] [--external]
#
# Targets: `both` means claude+codex (backwards-compatible); `all` means claude+codex+agy.
# Skills are stored once in ~/.agents/skills/ (read directly by Codex and used by the `skills`
# CLI); Claude Code gets symlinks in ~/.claude/skills/ and Antigravity gets symlinks in
# ~/.gemini/config/skills/ (plus skills.json discovery for external skills). Rules and Stop
# hooks stay tool-specific.
# Without --apply nothing is written: the plan is printed (dry run).
# --external also installs the externally maintained components in toolkit/external.yaml
# (skipping entries marked optional), scoped to the selected tool(s).
# --replace-legacy (Claude Code / Antigravity) moves previously installed skills and rules into
# ~/.toolkit-backup/<timestamp>/ before installing — except claude.ai-synced skills, names in
# KEEP below or in ~/.toolkit-keep (one per line), and anything external installers added.
# Agents are never moved; they are listed for you to decide. Skills and rules this toolkit
# installed in an earlier run but no longer ships are removed (tracked in a manifest).
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
  claude|codex|agy|both|all) ;;
  *) sed -n '2,14p' "$0"; exit 2 ;;
esac

exec python3 - "$ROOT" "$TARGET" "$APPLY" "$REPLACE" "$EXTERNAL" <<'PY'
import json, os, re, shlex, shutil, subprocess, sys, tempfile, time
from pathlib import Path

root, target, apply, replace = Path(sys.argv[1]), sys.argv[2], sys.argv[3] == "1", sys.argv[4] == "1"
external = sys.argv[5] == "1"
home = Path.home()
toolkit = root / "toolkit"
personal = root / "personal"
stamp = time.strftime("%Y%m%d-%H%M%S")
backup = home / ".toolkit-backup" / stamp
MARK_START, MARK_END = "<!-- toolkit:start -->", "<!-- toolkit:end -->"
VALID_TOOLS = {"claude", "codex", "agy"}
WANTED_BY_TARGET = {
    "claude": {"claude"},
    "codex": {"codex"},
    "agy": {"agy"},
    "both": {"claude", "codex"},
    "all": {"claude", "codex", "agy"},
}
wanted = WANTED_BY_TARGET[target]
KEEP = {"synced"}
BASE_EXTERNAL_PREFIXES = (
    "impeccable",
    "design-taste-frontend",
    "openspec-",
    "last30days",
    "review-animations",
    "mobile-native",
    "break-ui",
    "humanizer",
    "webapp-testing",
    "mcp-builder",
)
keep_file = home / ".toolkit-keep"
if keep_file.is_file():
    KEEP |= {l.strip() for l in keep_file.read_text(encoding="utf-8").splitlines() if l.strip()}
PERSONAL_NOTE = (
    "\n\n---\nBefore applying this skill, read `PERSONAL.md` in this folder: it holds "
    "this user's own parameters and preferences, which override the defaults above.\n"
)


def say(msg):
    print(("" if apply else "[dry-run] ") + msg)


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def real_nonexistent(path: Path) -> Path:
    """Resolve symlinks on existing ancestors even when the leaf path does not exist yet."""
    missing = []
    cur = path
    while not cur.exists() and cur != cur.parent:
        missing.append(cur.name)
        cur = cur.parent
    resolved = cur.resolve()
    for part in reversed(missing):
        resolved = resolved / part
    return resolved


def copytree(src, dst):
    say(f"copy {src.relative_to(root)} -> {dst}")
    if apply:
        remove(dst)
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", "test_*.py", "*.local.md"),
        )


def write(path, text):
    say(f"write {path}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def backup_file(path):
    if not apply or not path.exists():
        return
    dest = backup / path.relative_to(home)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(path, dest)


def move_to_backup(path):
    if not path.exists() and not path.is_symlink():
        return
    dest = backup / path.relative_to(home)
    say(f"backup {path} -> {dest}")
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))


def strip_inline_comment(val: str) -> str:
    in_quote = None
    for i, ch in enumerate(val):
        if ch in ('"', "'"):
            in_quote = None if in_quote == ch else (ch if in_quote is None else in_quote)
        elif ch == "#" and in_quote is None and (i == 0 or val[i - 1].isspace()):
            return val[:i].strip()
    return val.strip()


def external_entries():
    """Parse external.yaml files (a fixed subset of YAML, so no library is needed)."""
    entries, cur, in_install = [], None, False
    files = [toolkit / "external.yaml"] + (
        [personal / "external.yaml"] if (personal / "external.yaml").is_file() else []
    )
    lines = [l for f in files for l in f.read_text(encoding="utf-8").splitlines()]
    for line in lines:
        if line.startswith("- name:"):
            name = strip_inline_comment(line.split(":", 1)[1])
            cur = {"name": name, "install": [], "tools": [], "optional": False}
            entries.append(cur)
            in_install = False
        elif cur is None or not line.strip() or line.lstrip().startswith("#"):
            continue
        elif in_install and re.match(r"^ {2,4}- ", line):
            cur["install"].append(re.sub(r"^ {2,4}- ", "", line).strip())
        elif line.startswith("  ") and not line.startswith("   "):
            in_install = False
            key, _, raw_val = line.strip().partition(":")
            val = strip_inline_comment(raw_val)
            if key == "install":
                in_install = True
            elif key == "tools":
                cur["tools"] = [t.strip() for t in val.split(",") if t.strip()]
                unknown = set(cur["tools"]) - VALID_TOOLS
                if unknown:
                    sys.exit(f"external.yaml: entry {cur['name']} has unknown tools: {sorted(unknown)}")
            elif key == "optional":
                cur["optional"] = val.lower() == "true"
    for e in entries:
        if not e["install"] or not e["tools"]:
            sys.exit(f"external.yaml: entry {e['name']} needs tools: and an install: list")
    return entries


externals = external_entries()
dynamic_skill_flags = {
    m
    for e in externals
    for cmd in e["install"]
    for m in re.findall(r"(?:^|\s)(?:-s|--skill)\s+([A-Za-z0-9_.-]+)", cmd)
}
EXTERNAL_PREFIXES = tuple(sorted(set(BASE_EXTERNAL_PREFIXES) | dynamic_skill_flags | {e["name"] for e in externals}))


# ---- collect ---------------------------------------------------------------------------
def frontmatter(path):
    lines = path.read_text(encoding="utf-8").split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        sys.exit(f"{path}: frontmatter must open and close with a line containing only ---")
    return "\n".join(lines[1 : lines[1:].index("---") + 1])


skills = {}
for skill_md in sorted(toolkit.glob("*/skills/*/SKILL.md")) + sorted(personal.glob("skills/*/SKILL.md")):
    frontmatter(skill_md)
    d = skill_md.parent
    if d.name in skills:
        sys.exit(f"duplicate skill name {d.name}: {skills[d.name]} and {d}")
    skills[d.name] = d

rules = sorted(r for r in (toolkit / "rules").glob("*.md") if not r.name.endswith(".local.md"))
path_rules = [r for r in rules if r.read_text(encoding="utf-8").startswith("---")]
core_rules = [r for r in rules if r not in path_rules]


def personal_for(skill_dir):
    """Personal preferences for a category: personal/<category>.md (private, portable) or
    toolkit/<category>/personal.local.md (machine-local)."""
    category = skill_dir.parent.parent
    if category == personal:
        return None
    found = [p for p in (personal / f"{category.name}.md", category / "personal.local.md") if p.is_file()]
    if len(found) > 1:
        print(f"warning: both {found[0]} and {found[1]} exist; using the first")
    return found[0] if found else None


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


def link(path, target_path):
    """Point path at target_path (relative symlink, safe when parent dirs are symlinks)."""
    rel = Path(os.path.relpath(real_nonexistent(target_path), real_nonexistent(path.parent)))
    if path.is_symlink() and Path(os.readlink(path)) == rel:
        return
    say(f"link {path} -> {rel}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        remove(path)
        path.symlink_to(rel)


def parse_path_rule(rule):
    text = rule.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    if not m:
        sys.exit(f"{rule}: malformed frontmatter")
    globs = re.findall(r'-\s*"([^"]+)"', m.group(1))
    body = m.group(2).strip()
    title = body.splitlines()[0].lstrip("# ").strip()
    return globs, title, body


def rule_to_skill(rule):
    globs, title, body = parse_path_rule(rule)
    desc = f"{title}. Use when reading or editing files matching: {', '.join(globs)}."
    return f"---\nname: {rule.stem}-traps\ndescription: {json.dumps(desc)}\n---\n\n{body}\n"


def rule_to_agy(rule):
    if rule not in path_rules:
        body = rule.read_text(encoding="utf-8").strip()
        return f"---\ntrigger: always_on\n---\n\n{body}\n"
    globs, title, body = parse_path_rule(rule)
    return (
        f"---\ntrigger: glob\nglobs: {json.dumps(', '.join(globs))}\n"
        f"description: {json.dumps(title)}\n---\n\n{body}\n"
    )


def upsert_block(path, block):
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    new_block = f"{MARK_START}\n{block.strip()}\n{MARK_END}"
    if MARK_START in old:
        new = re.sub(re.escape(MARK_START) + r".*?" + re.escape(MARK_END), lambda _: new_block, old, flags=re.S)
    else:
        new = (old.rstrip() + "\n\n" if old.strip() else "") + new_block + "\n"
    write(path, new)


def sync_manifest(base, skill_names, rule_rel_paths=None):
    """Remove skills and rules this toolkit installed before but no longer ships; record the new set."""
    manifest = base / ".toolkit-manifest.json"
    old_skills, old_rules = set(), set()
    if manifest.exists():
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            old_skills = set(raw)
        elif isinstance(raw, dict):
            old_skills = set(raw.get("skills", []))
            old_rules = set(raw.get("rules", []))
    for stale in sorted(old_skills - set(skill_names)):
        p = base / "skills" / stale
        if p.exists() or p.is_symlink():
            say(f"remove stale toolkit skill {p}")
            if apply:
                remove(p)
    new_rules = set(rule_rel_paths or [])
    for stale_rel in sorted(old_rules - new_rules):
        p = base / stale_rel
        if p.exists() or p.is_symlink():
            say(f"remove stale toolkit rule {p}")
            if apply:
                remove(p)
    if apply:
        base.mkdir(parents=True, exist_ok=True)
        payload = (
            {"skills": sorted(skill_names), "rules": sorted(new_rules)}
            if rule_rel_paths is not None
            else sorted(skill_names)
        )
        manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


# ---- shared skill store ----------------------------------------------------------------
store = home / ".agents" / "skills"
trap_names = [f"{r.stem}-traps" for r in path_rules]


def install_store():
    for name, src in skills.items():
        install_skill(name, src, store)
    for r in path_rules:
        write(store / f"{r.stem}-traps" / "SKILL.md", rule_to_skill(r))
    sync_manifest(store.parent, list(skills) + trap_names)


# ---- Claude Code -----------------------------------------------------------------------
def install_claude():
    base = home / ".claude"
    settings = base / "settings.json"
    try:
        data = json.loads(settings.read_text(encoding="utf-8")) if settings.exists() else {}
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
    for name in skills:
        link(base / "skills" / name, store / name)
    claude_rule_rels = [f"rules/toolkit/{r.name}" for r in rules]
    sync_manifest(base, skills, claude_rule_rels)
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
            backup_file(settings)
            settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---- Codex -----------------------------------------------------------------------------
def install_codex():
    base = home / ".codex"
    # Codex reads skills from the shared store; remove copies older runs put in ~/.codex/skills.
    sync_manifest(base, [])
    core = "\n\n".join(r.read_text(encoding="utf-8").strip() for r in core_rules)
    agents_md = base / "AGENTS.md"
    old = agents_md.read_text(encoding="utf-8") if agents_md.exists() else ""
    if f"{MARK_START}\n{core.strip()}\n{MARK_END}" in old:
        say(f"{agents_md} already current")
    else:
        backup_file(agents_md)
        upsert_block(agents_md, core)
    say("hooks: Codex Stop-hook registration left manual (claim_check.py supports Codex transcripts when enabled)")


# ---- Antigravity (agy) -----------------------------------------------------------------
def install_agy():
    base = home / ".gemini" / "config"
    hooks_json = base / "hooks.json"
    skills_json = base / "skills.json"
    for cfg in (hooks_json, skills_json):
        if cfg.exists():
            try:
                json.loads(cfg.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                sys.exit(f"{cfg} is not valid JSON ({e}); fix it before installing")

    ours = set(skills)
    agy_rule_names = {f"toolkit-{r.stem}.md" for r in rules}
    if replace:
        for p in sorted((base / "skills").glob("*")) if (base / "skills").exists() else []:
            if p.name in KEEP or p.name in ours or p.name.startswith(EXTERNAL_PREFIXES):
                continue
            move_to_backup(p)
        for p in sorted((base / "rules").glob("*")) if (base / "rules").exists() else []:
            if p.name in KEEP or p.name in agy_rule_names or p.name.startswith("toolkit-"):
                continue
            move_to_backup(p)

    for name in skills:
        link(base / "skills" / name, store / name)

    agy_rule_rels = [f"rules/toolkit-{r.stem}.md" for r in rules]
    sync_manifest(base, skills, agy_rule_rels)
    for r in rules:
        write(base / "rules" / f"toolkit-{r.stem}.md", rule_to_agy(r))

    # Expose ~/.agents/skills (excluding *-traps, since AGY has native glob rules above)
    # so external skills installed by `npx skills` or `impeccable` are also discovered.
    sdata = json.loads(skills_json.read_text(encoding="utf-8")) if skills_json.exists() else {}
    entries_list = sdata.setdefault("entries", [])
    shared_entry = {"path": "~/.agents/skills", "exclude": [".*-traps"]}
    has_shared = any(
        isinstance(it, dict) and it.get("path") in ("~/.agents/skills", str(store))
        for it in entries_list
    )
    if not has_shared:
        entries_list.append(shared_entry)
        say(f"register shared ~/.agents/skills discovery in {skills_json}")
        if apply:
            backup_file(skills_json)
            skills_json.parent.mkdir(parents=True, exist_ok=True)
            skills_json.write_text(json.dumps(sdata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    hook = toolkit / "hooks" / "claim-check" / "claim_check.py"
    hook_dst = base / "hooks" / "toolkit" / "claim_check.py"
    say(f"copy {hook.relative_to(root)} -> {hook_dst}")
    cmd = f"python3 {shlex.quote(str(hook_dst))}"
    hdata = json.loads(hooks_json.read_text(encoding="utf-8")) if hooks_json.exists() else {}
    desired = {"Stop": [{"type": "command", "command": cmd, "timeout": 10}]}
    changed = hdata.get("toolkit-claim-check") != desired
    if changed:
        hdata["toolkit-claim-check"] = desired
        say(f"register Stop hook in {hooks_json} (previous file backed up)")
    if apply:
        hook_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(hook, hook_dst)
        if changed:
            backup_file(hooks_json)
            hooks_json.write_text(json.dumps(hdata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


PROVIDER_FOR_TOOL = {"claude": "claude", "codex": "codex", "agy": "antigravity"}
SKILLS_AGENT_FOR_TOOL = {"claude": "claude-code", "codex": "codex", "agy": "antigravity"}
KNOWN_SKILL_AGENTS = set(SKILLS_AGENT_FOR_TOOL.values())


def adapt_external_cmd(cmd: str, active_tools: set[str]) -> str:
    """Scope multi-provider external install commands to only the target tool(s) requested."""
    wanted_providers = {PROVIDER_FOR_TOOL[t] for t in active_tools}
    m = re.search(r"--providers=([A-Za-z0-9_,-]+)", cmd)
    if m:
        listed = [p for p in m.group(1).split(",") if p]
        scoped = [p for p in listed if p in wanted_providers or p not in PROVIDER_FOR_TOOL.values()]
        if scoped:
            cmd = cmd[: m.start()] + f"--providers={','.join(scoped)}" + cmd[m.end() :]

    wanted_agents = {SKILLS_AGENT_FOR_TOOL[t] for t in active_tools}

    def _keep_agent(match):
        agent = match.group(1)
        if agent in KNOWN_SKILL_AGENTS and agent not in wanted_agents:
            return ""
        return match.group(0)

    cmd = re.sub(r"\s+(?:-a|--agent)\s+([A-Za-z0-9_-]+)", _keep_agent, cmd)
    return cmd


install_store()
if "claude" in wanted:
    install_claude()
if "codex" in wanted:
    install_codex()
if "agy" in wanted:
    install_agy()

print("\nExternal components (external.yaml):")
failed = []
for e in externals:
    active_tools = wanted & set(e["tools"])
    if not active_tools:
        continue
    run = external and not e["optional"]
    label = (
        "optional — install yourself when decided"
        if e["optional"]
        else ("installing" if run and apply else "would install" if run else "run with --external")
    )
    print(f"  {e['name']} ({label}):")
    for raw_cmd in e["install"]:
        cmd = adapt_external_cmd(raw_cmd, active_tools)
        print(f"      {cmd}")
        if run and apply and e["name"] not in failed:
            # Run outside any project: some installers also write per-project hooks into the cwd.
            with tempfile.TemporaryDirectory() as tmp:
                if subprocess.run(cmd, shell=True, cwd=tmp).returncode != 0:
                    failed.append(e["name"])
if failed:
    print(f"\nExternal installs that failed: {', '.join(failed)} — rerun their commands by hand.")
print(f"\n{len(skills)} skills, {len(rules)} rule files." + ("" if apply else "  Re-run with --apply to write."))
if apply and backup.exists():
    print(f"Backups in {backup}")
PY
