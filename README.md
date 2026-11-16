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
| engineering | `design-discussion` (think a design through, one question at a time) · `system-design` (numbers before boxes; design reviews) · `spec` (CLI-free proposal, SHALL/WHEN-THEN capability deltas, human sign-offs, living specs) · `debugging` · `tdd` (vertical slices, test-first) · `verification` · `code-review` · `app-security` · `production-ops` (safe changes and incidents) · `web-platform` (Baseline-checked platform features, Core Web Vitals, forms, browser security; adapted from Chrome's Modern Web Guidance) · `architecture-diagram` |
| AI agents | `agent-architecture` · `agent-orchestration` · `agent-evals` · `agent-security` · `agent-instructions` (AGENTS.md / CLAUDE.md / GEMINI.md) |
| learning | `socratic-tutor` — Socratic mastery of a codebase, paper or technical domain with 0–5 skill maps and spaced recall |
| research and market | `verified-research` · `market-scan` (competitors and unmet demand) · `macro-regime` |
| product | `customer-discovery` (validate ideas with real users) · `product-scoping` · `pricing` · `experiment-readout` (A/B tests and launches) · `analysis-design` (data analysis before querying: metric spec, data quality, plan stress-test) · `adopt-or-build` |
| investing | `thesis-ledger` · `valuation-audit` — decision support for individual investors; never buy/sell advice |
| strategy | `liu-ayi` — a strategic-analysis framework built on order-and-institution checks, base rates and calibrated decisions |
| career | `career-navigator` |
| writing | `writing` — posts, articles and social media in the writer's voice, no invented facts; de-AI pass via the vendored humanizer / humanizer-zh, then an added-facts check |
| rules | `core.md` (always loaded, ~20 lines) plus language traps that load only for matching files: Python, Java/Spring, C++, TypeScript/React/Next.js, web platform (HTML/CSS/JS), Swift, Kotlin, React Native/Expo, Flutter/Dart, SQL/containers |
| hooks | `claim-check` — blocks "done / fixed / tests pass" claims made after editing files without running anything (Claude Code, Antigravity, Codex transcript support) |

Two ways of using other people's work, besides porting it into a skill:

- **Vendored** (copied unchanged at a pinned commit, shipped in this repo; `toolkit/vendored.json`):
  three skills of [emilkowalski/skills](https://github.com/emilkowalski/skills) (motion review,
  mobile-web feel, worst-case data), de-AI prose editing from
  [humanizer](https://github.com/blader/humanizer) and [humanizer-zh](https://github.com/op7418/Humanizer-zh),
  and go-to-market execution (positioning, launch, onboarding, signup, churn, referrals) from six
  skills of [marketingskills](https://github.com/coreyhaines31/marketingskills).
- **External** (installed from their own source because they carry an installer, hooks or runtime
  code; `toolkit/external.yaml`): design taste from [impeccable](https://github.com/pbakaus/impeccable),
  trend signals from [last30days](https://github.com/mvanhorn/last30days-skill), browser UI
  verification from [webapp-testing](https://github.com/anthropics/skills) (or optional
  [agent-browser](https://github.com/vercel-labs/agent-browser)), handoff to Codex through
  [codex-plugin-cc](https://github.com/openai/codex-plugin-cc), safety hooks from
  [claude-code-hooks](https://github.com/karanb192/claude-code-hooks) (optional), and
  stack-specific vendor skills as optional, per-project installs (shadcn/ui, Vercel AI SDK,
  Playwright CLI, SwiftUI, Expo, Android, Stripe).

## Install

```bash
git clone https://github.com/ljjsfe/ai-toolkit && cd ai-toolkit
./install.sh claude|codex|agy|both|all         # dry run: prints what would change (`both` = claude+codex)
./install.sh claude --apply                    # install for Claude Code (toolkit, vendored and external skills)
./install.sh agy --apply                       # install for Google Antigravity
./install.sh claude --apply --replace-legacy   # also move your existing skills/rules to ~/.toolkit-backup/
./install.sh all --apply                       # new machine: all three harnesses
./install.sh claude --apply --no-external      # offline or toolkit-only: skip external installers
./update.sh                                    # later: git pull, review external changes, reinstall all
```

- A full install also runs each non-optional installer in `toolkit/external.yaml`, scoped to the
  selected target(s): impeccable, last30days, webapp-testing and (for Claude Code)
  codex-plugin-cc. These need network and `npx`, and impeccable registers its detector hook in
  `~/.claude/settings.json`; `--no-external` skips them (`--external` is still accepted and
  changes nothing). Entries marked `optional` — taste-skill, agent-browser, mcp-builder,
  mcp-server-dev, claude-security, claude-code-hooks and the stack-specific vendor skills — are
  printed, not installed. Any entry placed on `status: trial` must declare `trial_start` and
  `trial_review_by` dates, enforced by `scripts/check.py`.
- Vendored skills live unchanged under `toolkit/<category>/vendor/`, pinned in
  `toolkit/vendored.json`, and install like the toolkit's own skills (also with
  `--no-external`). Their descriptions are not trimmed
  to the toolkit's cap (the copies stay unchanged), so `check.py` reports them as a separate
  resident cost. If an earlier install put one of them there through the `skills` CLI, install.sh
  prints the one command that drops that record.
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
  - Full repo check (frontmatter, resident description budget, references, source coverage tags and their anchors, vendored file hashes, `external.yaml` trial review dates, `CREDITS.md` sync, unit tests, and tests of any skill `scripts/`): `python3 scripts/check.py`
  - Upstream drift: `python3 scripts/upstream_drift.py [name …]` (needs an authenticated `gh`) lists, for every credited path, whether it still exists upstream and which commits touched it since the commit recorded in `toolkit/upstreams.json`. After re-reading a change and updating the skill, move that upstream's `reviewed_sha` / `reviewed_on` forward. `check.py` fails if a credited upstream is not registered there.
  - Vendored skills: `python3 scripts/vendor_sync.py` lists upstream commits since each pin; `--update <source>` copies the new upstream folder and re-pins. Read `git diff` before committing, then `python3 scripts/check.py --sync-credits`.
  - Validator & hook tests alone: `python3 scripts/test_check.py` and `python3 toolkit/hooks/claim-check/test_claim_check.py` (also `pytest -q` compatible).
- `claim-check` is a cheap tripwire, not proof of verification: it checks that a command that is
  not purely read-only (`ls`, `cat`, `git status`… do not count) or a browser check ran after the
  last edit, not that it was the right one. File writes through the shell (`sed -i`, redirection,
  `tee`, `git apply`, a script heredoc that writes) count as edits. It ignores negated or
  conditional phrases ("not verified", "if tests pass", "还没完成").

## Principles

1. Correct first. A skill and its `references/` state the right way to do the job end to end. The
   SKILL.md body carries what changes outcomes on current models: gates, thresholds, decisions,
   the output. Procedure lives in references and loads when needed. Published evals (gstack
   retiring `/investigate` and `/plan-eng-review`, 2026-11) found ceremony alone gave Opus-class
   models no measurable gain at several times the cost, and prose steps were skipped unless a
   hook enforced them. So where a rule can be checked mechanically it gets a script or a hook
   (claim-check, the anchored credits, the skill scripts); the rest stays as short gates.
2. One owner per behaviour; skills cross-reference instead of repeating each other.
3. Rewrite or vendor, never half of each. Upstream material is read and restated; licences are
   respected; every credit is tagged and anchored, and `toolkit/upstreams.json` records what was
   read and when. An upstream skill that is good as written and is plain files (no installer,
   hook or runtime code) is vendored instead: copied unchanged at a pinned commit with its
   licence, never edited here (`check.py` verifies file hashes), refreshed only through
   `scripts/vendor_sync.py --update` after reading the diff. Guards against a vendored rule live
   in the toolkit skill that uses it.
4. Resident cost is a budget: descriptions are short, long rules load only when relevant.
5. When sources disagree, decide in this order:
   1. Check whether they answer the same question. Most conflicts are different contexts (an
      app shell vs a hero; API mechanics vs motion feel). State each one's condition instead of
      picking a winner.
   2. Take each source on what it is authoritative about: a browser vendor on platform support,
      a motion specialist on easing, a regulator on its own rule.
   3. Rank the evidence: a measured eval on current models, then dated primary specs or vendor
      docs, then practitioner consensus, then a single opinion.
   4. Keep what changes outcomes for today's models; drop what they already do unprompted.
   5. Where one side is irreversible, outward-facing or a security matter, take the safer side.
   Record the decision where both sides are visible (the rule text or `external.yaml` notes).
6. Track upstream, reviewed. Externals install their latest release, but `./update.sh` first
   lists each one's releases and commits since the last update and asks before installing
   (`--yes` skips it). That review is what makes `@latest` acceptable here; agent-security's
   rule against unreviewed `@latest` still applies to everything else. When a release conflicts
   with a toolkit law, guard it inside the toolkit instead of pinning (humanizer 4 began adding
   facts; writing now checks for them). Vendored skills follow upstream the same way, one step
   earlier: `scripts/vendor_sync.py` lists commits since each pin and `--update` brings them in
   as a diff to read before committing. `scripts/upstream_drift.py` lists what changed or was
   removed since each credited upstream was last read.

## License

MIT — see [LICENSE](LICENSE). Third-party material keeps its own licence as noted in [CREDITS.md](CREDITS.md).
