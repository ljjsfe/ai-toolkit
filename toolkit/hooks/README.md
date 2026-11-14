# hooks

This folder holds cross-harness hooks shipped directly by `ai-toolkit`. For Claude Code, optional
command/secret/git/cache guards (`guard-pack`, `instructions-audit`, `cache-tax`,
`subagent-spawn-cap`) are listed in `../external.yaml` under `claude-code-hooks` (`optional: true`,
Claude Code only); cross-harness prompt-injection and tool-authority rules live in
`agent-security`.

| hook | event | what it does | tools |
|---|---|---|---|
| `claim-check/` | Stop | Blocks a success claim ("done", "fixed", "resolved", "tests pass", "everything works", 已修复, 修改完毕…) made after editing workspace files in the turn (including through the shell: `sed -i`, redirection, `tee`, `git apply`) without running a non-read-only command or a browser check after the last edit; asks the agent to verify or say it is unverified. Blocks once per stop; fails open. | Claude Code (`~/.claude/settings.json`), Antigravity (`~/.gemini/config/hooks.json`), Codex (copied to `~/.codex/hooks/toolkit/claim_check.py`; register in `hooks.json` if desired) |

Tests (zero external dependencies): `python3 toolkit/hooks/claim-check/test_claim_check.py` (also compatible with `pytest -q`).
