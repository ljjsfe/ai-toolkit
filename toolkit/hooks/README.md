# hooks

Safety and cost hooks are adopted from `claude-code-hooks` (see `../external.yaml`).
This folder holds only hooks that project does not provide.

| hook | event | what it does | tools |
|---|---|---|---|
| `claim-check/` | Stop | Blocks a success claim ("done", "fixed", "tests pass", 已修复…) made after editing files in the turn without running any command after the last edit; asks the agent to verify or say it is unverified. Blocks once per stop; fails open. | Claude Code (Codex: register if its Stop hook is available — advisory) |

Tests: `cd claim-check && python3 -m pytest -q`.
