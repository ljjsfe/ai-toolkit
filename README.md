# ai-toolkit

A small, opinionated set of skills, rules and hooks for **Claude Code** and **Codex**, for building
full-stack products and agent systems.

Every skill exists because a current frontier model skips the behaviour it enforces, or does not
know it. Generic advice the model already follows was left out. Each skill lists its sources;
see [CREDITS.md](CREDITS.md).

## What is inside

| area | skills |
|---|---|
| engineering | `system-design` (numbers before boxes; design reviews) · `debugging` · `verification` · `code-review` · `app-security` · `production-ops` (safe changes and incidents) · `architecture-diagram` |
| AI agents | `agent-architecture` · `agent-orchestration` · `agent-evals` · `agent-security` |
| research and market | `verified-research` · `market-scan` (competitors and unmet demand) · `macro-regime` |
| product | `adopt-or-build` · `product-scoping` |
| strategy | `liu-ayi` — a strategic-analysis framework built on order-and-institution checks, base rates and calibrated decisions |
| career | `career-navigator` |
| rules | `core.md` (always loaded, ~20 lines) plus language traps that load only for matching files: Python, Java/Spring, C++, TypeScript/React/Next.js, Flutter/Dart, SQL/containers |
| hooks | `claim-check` — blocks "done / fixed / tests pass" claims made after editing files without running anything |

Design taste is delegated to [impeccable](https://github.com/pbakaus/impeccable), trend signals to
[last30days](https://github.com/mvanhorn/last30days-skill), and safety hooks to
[claude-code-hooks](https://github.com/karanb192/claude-code-hooks) — installed from their own
sources (see `toolkit/external.yaml`).

## Install

```bash
git clone https://github.com/ljjsfe/ai-toolkit && cd ai-toolkit
./install.sh claude|codex|both                 # dry run: prints what would change
./install.sh claude --apply                    # install for Claude Code
./install.sh claude --apply --replace-legacy   # also move your existing skills/rules to ~/.toolkit-backup/
```

- Skills install to `~/.claude/skills/` (Claude Code) and `~/.codex/skills/` (Codex).
- `--replace-legacy` never touches claude.ai-synced skills, externally installed ones, your
  agents, or names listed in `~/.toolkit-keep`.
- Personal parameters: put them in `toolkit/<category>/personal.local.md` (gitignored); they are
  merged into that category's skills as `PERSONAL.md` at install time.
- Hook tests: `cd toolkit/hooks/claim-check && python3 -m pytest -q`.

## Principles

1. Only what the model would not do on its own.
2. One owner per behaviour; skills cross-reference instead of repeating each other.
3. Rewrite, don't copy — upstream material is read and restated; licences are respected.
4. Resident cost is a budget: descriptions are short, long rules load only when relevant.


## License

MIT — see [LICENSE](LICENSE). Third-party material keeps its own licence as noted in CREDITS.md.
