# hooks

Safety and cost hooks are adopted from `claude-code-hooks` (see `../external.yaml`).
This folder holds only hooks that project does not provide.

| hook | event | what it does | tools |
|---|---|---|---|
| `claim-check/` | Stop | Blocks a success claim ("done", "fixed", "tests pass", "all tests passed", 已修复, 改好了…) made after editing workspace files in the turn without running any command or browser check after the last edit; asks the agent to verify or say it is unverified. Blocks once per stop; fails open. | Claude Code (`~/.claude/settings.json`), Antigravity (`~/.gemini/config/hooks.json`), Codex (transcript parser supported; register in `hooks.json` if desired) |

Tests (zero external dependencies): `python3 toolkit/hooks/claim-check/test_claim_check.py` (also compatible with `pytest -q`).
