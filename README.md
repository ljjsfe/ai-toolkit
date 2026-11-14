# ai-toolkit

A small, opinionated set of skills, rules and hooks for **Claude Code**, **Codex** and
**Antigravity (`agy`)**, for building full-stack products and agent systems.

Each skill states how to do its job right — a small set of tools chosen for being correct, not
for being exhaustive. Skills are prose; where an upstream ships executable pieces (scripts,
validators, templates, storage) the toolkit has not ported yet, that is listed openly as a
known gap. Every source is tagged `port` (anchored: `scripts/check.py` fails if the cited text
is missing from the skill), `idea` or `gap`; see [CREDITS.md](CREDITS.md).

## What is inside

| area | skills |
|---|---|
| engineering | `design-discussion` (think a design through, one question at a time) · `system-design` (numbers before boxes; design reviews) · `spec` (CLI-free proposal, SHALL/WHEN-THEN capability deltas, human sign-offs, living specs) · `debugging` · `tdd` (vertical slices, test-first) · `verification` · `code-review` · `app-security` · `production-ops` (safe changes and incidents) · `architecture-diagram` |
| AI agents | `agent-architecture` · `agent-orchestration` · `agent-evals` · `agent-security` · `agent-instructions` (AGENTS.md / CLAUDE.md / GEMINI.md) |
| learning | `socratic-tutor` — Socratic mastery of a codebase, paper or technical domain with 0–5 skill maps and spaced recall |
| research and market | `verified-research` · `market-scan` (competitors and unmet demand) · `macro-regime` |
| product | `customer-discovery` (validate ideas with real users) · `product-scoping` · `pricing` · `experiment-readout` (A/B tests and launches) · `adopt-or-build` |
| investing | `thesis-ledger` · `valuation-audit` — decision support for individual investors; never buy/sell advice |
| strategy | `liu-ayi` — a strategic-analysis framework built on order-and-institution checks, base rates and calibrated decisions |
| career | `career-navigator` |
| writing | `writing` — posts, articles and social media in the writer's voice, no invented facts; de-AI pass via humanizer / humanizer-zh (external) with inline fallback |
| rules | `core.md` (always loaded, ~20 lines) plus language traps that load only for matching files: Python, Java/Spring, C++, TypeScript/React/Next.js, Flutter/Dart, SQL/containers |
| hooks | `claim-check` — blocks "done / fixed / tests pass" claims made after editing files without running anything (Claude Code, Antigravity, Codex transcript support) |

Design taste is delegated to [impeccable](https://github.com/pbakaus/impeccable) plus three of
[emilkowalski/skills](https://github.com/emilkowalski/skills) (motion review, mobile-web feel, worst-case data), trend signals to
[last30days](https://github.com/mvanhorn/last30days-skill), de-AI prose editing to
[humanizer](https://github.com/blader/humanizer) and [humanizer-zh](https://github.com/op7418/Humanizer-zh), browser UI verification to
[webapp-testing](https://github.com/anthropics/skills) (or optional [agent-browser](https://github.com/vercel-labs/agent-browser)), safety hooks to
[claude-code-hooks](https://github.com/karanb192/claude-code-hooks) (optional), and handoff to Codex
to [codex-plugin-cc](https://github.com/openai/codex-plugin-cc) — installed from their own
sources (see `toolkit/external.yaml`).

## Install

```bash
git clone https://github.com/ljjsfe/ai-toolkit && cd ai-toolkit
./install.sh claude|codex|agy|both|all         # dry run: prints what would change (`both` = claude+codex)
./install.sh claude --apply                    # install for Claude Code
./install.sh agy --apply                       # install for Google Antigravity
./install.sh claude --apply --replace-legacy   # also move your existing skills/rules to ~/.toolkit-backup/
./install.sh all --apply --external            # new machine: all three harnesses + external components
./update.sh                                    # later: git pull, then reinstall all + external at latest
```

- `--external` runs each non-optional installer listed in `toolkit/external.yaml` scoped to the
  selected target(s): impeccable, last30days, emilkowalski/skills, humanizer, humanizer-zh,
  webapp-testing, and (for Claude Code) codex-plugin-cc. Entries marked `optional` — currently
  taste-skill, agent-browser, mcp-builder, mcp-server-dev, claude-security and claude-code-hooks —
  are printed, not installed. Any entry placed on `status: trial` must declare `trial_start` and
  `trial_review_by` dates, enforced by `scripts/check.py`.
- Skills are stored once in `~/.agents/skills/`, which Codex reads directly; Claude Code gets
  symlinks in `~/.claude/skills/` and Antigravity gets symlinks in `~/.gemini/config/skills/`
  (including any external skills installed in `~/.agents/skills/`, excluding `*-traps`, since both
  Claude Code and Antigravity receive native path/glob-scoped rules).
- `--replace-legacy` never touches claude.ai-synced skills, externally installed ones, your
  agents, or names listed in `~/.toolkit-keep`.
- Personal parameters: put them in `toolkit/<category>/personal.local.md` (gitignored; e.g. a
  writing voice profile in `toolkit/writing/`); they are merged into that category's skills as
  `PERSONAL.md` at install time.
- Validation and tests (zero external dependencies):
  - Full repo check (frontmatter, resident description budget, references, source coverage tags and their anchors, `external.yaml` trial review dates, `CREDITS.md` sync, unit tests, and tests of any skill `scripts/`): `python3 scripts/check.py`
  - Validator & hook tests alone: `python3 scripts/test_check.py` and `python3 toolkit/hooks/claim-check/test_claim_check.py` (also `pytest -q` compatible).
- `claim-check` is a cheap tripwire, not proof of verification: it checks that a command that is
  not purely read-only (`ls`, `cat`, `git status`… do not count) or a browser check ran after the
  last edit, not that it was the right one. File writes through the shell (`sed -i`, redirection,
  `tee`, `git apply`, a script heredoc that writes) count as edits. It ignores negated or
  conditional phrases ("not verified", "if tests pass", "还没完成").

## Principles

1. Correct first. A skill states the right way to do its job end to end; it is not trimmed to
   what today's model happens to skip. Few tools, each one right, and right together.
2. One owner per behaviour; skills cross-reference instead of repeating each other.
3. Rewrite, don't copy — upstream material is read and restated; licences are respected.
4. Resident cost is a budget: descriptions are short, long rules load only when relevant.

## License

MIT — see [LICENSE](LICENSE). Third-party material keeps its own licence as noted in [CREDITS.md](CREDITS.md).
