---
name: agent-orchestration
description: >-
  Coordinate subagents or parallel workers: compaction-safe ledger, Oracle-and-blast-radius
  model tiering, disjoint file ownership, single-writer git/config ops, and independent
  artifact-verified completion. Not for designing agent products (use agent-architecture).
version: 1.6.0
sources:
  - upstream/superpowers/skills/{subagent-driven-development,dispatching-parallel-agents,executing-plans} (MIT) — explicit model per worker, fix rounds, a ledger that survives compaction [port "progress lives in a ledger file" "explicit tier / model" "fix loop — bounded escalation"]
  - upstream/superpowers/skills/subagent-driven-development (MIT) — two-stage review after every task (spec compliance, then code quality) plus a final whole-branch review; the DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED worker status protocol; implementer and reviewer prompt templates and brief scripts [port "first spec compliance" "then code quality" "final whole-branch review on the Frontier tier" "DONE_WITH_CONCERNS" "NEEDS_CONTEXT" "never the same brief again" "Implementer brief" "Task reviewer brief (spec compliance, then code quality)" "Scoped re-review brief"]
  - upstream/oh-my-claudecode/skills/team (MIT) — staged plan, prd, exec, verify, fix pipeline with entry and exit gates; risk-based reviewer escalation; stuck-worker watchdog and reassignment; shutdown and resume protocol [port "an entry and exit gate per stage" "capped verify→fix loop" "Risk-based reviewer escalation" "Stuck-worker watchdog and reassignment" "check once, then reassign" "A worker fails two tasks" "Resume after a crash or compaction" "Stage handoff file" "Send each live worker a shutdown request"]
  - upstream/oh-my-claudecode/skills/{team,autopilot}/SKILL.md (MIT) — subagent nesting depth and concurrency are Claude Code settings whose defaults changed across 2.1.217–2.1.219 [port "toolkit policy, not a runtime limit" "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/long-horizon-prompting/references/mass-handoff-contracts.md (MIT) — degenerate-value rejection at handoff gates, bounded recall orders, the reviser as bottleneck [port "reject degenerate results" "bounded recall order" "the reviser can be the bottleneck"]
  - upstream/compound-engineering-plugin/skills/ce-work/references/execution-strategy.md (MIT) — exclusive file ownership, orchestrator-only git, bounded batch concurrency [port "no file appears in two clusters" "single-writer operations" "keep concurrency small"]
  - upstream/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md (Apache-2.0) — when delegation fits; in a many-item fan-out, failed items listed as uncovered and a second pass over every item when misses are costly [port "inline or delegate" "reported as not covered" "not only the flagged ones"]
  - upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — concurrency cap and no nested spawning [port "workers do not spawn their own subagents"]
  - upstream/villetakanen-asdlc-io (MIT) — declared dependencies and a divergence rule in the task brief [port "declared now, not discovered at merge" "if the brief or spec turns out wrong"]
  - 'authored for this toolkit — Oracle-by-blast-radius model tiering (Fast / Workhorse / Frontier), subagent-only tier switching to preserve prompt cache, command-log redirection, two-strike escalation, and cross-family / cross-tier review order [port "route model tiers on subagent spawn" "redirect noisy commands" "a workhorse stalls twice" "prefer a different model family"]'
---

# Agent Orchestration

You own the plan, the state and the verdict; subagents do the work. Agent products: `agent-architecture`.

## Iron laws

1. **Progress lives in a ledger file, not in your context.** Record each task's status, owner,
   model tier, dependencies and result path as you go. After compaction or resume, trust the
   ledger and `git log` over recollection.
2. **Route model tiers on subagent spawn, never mid-session** (a switch invalidates the prompt
   cache; honour host rules that keep the session model). Match the tier to
   whether a deterministic check (Oracle) catches mistakes and how wide a mistake reaches —
   never to file extension or line count.
3. **Parallelise reading, serialise writing.** Editing workers run in parallel only on disjoint
   file sets. Single-writer operations — version bumps, changelog, tags, PRs, migrations,
   deploys, shared config — are done by the orchestrator, one at a time, never delegated.
4. **Assign ownership before spawning.** Each worker gets an explicit file cluster; no file
   appears in two clusters, and workers never pick their own tasks. Parallel writers also get
   their own workspace or git worktree (they still share test databases and ports); fix shared
   interfaces before fanning out.
5. **"Done" from a worker is a claim, not a fact.** Accept it only with a checkable artifact
   (test run, diff, file at a path) or a verdict from a fresh, read-only reviewer that did
   not do the work. Code-writing tasks under a plan need both review verdicts (below); other
   work is accepted on its artifact alone. For high-blast-radius changes, prefer a different
   model family when available, else a Frontier-tier fresh context, else a same-tier one.

## Inline or delegate?

| do it inline | delegate to a subagent |
|---|---|
| short, and you need the details afterwards | long reading or searching whose details you won't need |
| depends on what is already in your context | self-contained with a clear input and output |
| one step | independent of other in-flight steps |

Fanning one step out over many items (a review or audit of dozens of files or sources): a
worker that fails leaves its items reported as not covered, never silently dropped; when a
miss is costly, a second worker re-reads every item, not only the flagged ones (about one extra
agent per item: say so to the user before choosing it).

## Model tier per subagent

| tier | use when | guardrails |
|---|---|---|
| **Fast** | Steps are known **and** a deterministic Oracle checks the output: search, extraction, mechanical transforms, running an existing check script. No open-ended design. | Read-only or minimum tools; fixed return shape. |
| **Workhorse** | Bounded implementation, tests or debugging with clear interfaces and specs. | Default for self-contained slices. |
| **Frontier** | **No automatic Oracle on a high-blast-radius call** (architecture, auth/security/money, editing tests or gates), open-ended synthesis, or escalation after a Workhorse stalls twice. | Judgment gates and hard root-cause analysis. |

## Dispatch brief — every subagent gets all of these

```
Goal:        one sentence, the outcome not the activity
Inputs:      exact file paths / URLs / data to use
Owns:        files it may modify (empty for read-only work)
Must not:    files, commands and decisions that are out of bounds
Return:      the exact shape — fields, file path, max length — plus what was not done or assumed
Done when:   the checkable condition
Depends on:  tasks that must finish first — declared now, not discovered at merge
If wrong:    if the brief or spec turns out wrong — stop and report, or continue and log
             each deviation; never cross Owns or Must not, never silently work around it
Model:       explicit tier / model
```

Workers do not spawn their own subagents (toolkit policy, not a runtime limit — read
`references/team-pipeline.md` § Host limits before planning nested delegation). Workers redirect
noisy commands (tests, builds, logs) to a file and return the path plus a short summary. Keep concurrency small: 3–5 workers if you read each result in full, up to about 7 if
they return only paths and summaries. Batch many small same-shape edits into one worker.

## Worker status and review after every task

| status | your move |
|---|---|
| `DONE` | package the diff (`BASE..HEAD`) and dispatch the task reviewer |
| `DONE_WITH_CONCERNS` | read the concerns; resolve correctness or scope doubts before review, note observations |
| `NEEDS_CONTEXT` | supply it and re-dispatch; do not let it guess |
| `BLOCKED` | change something — more context, a higher tier, a smaller task, or a plan ruling — never the same brief again |

Each code-writing task under a plan gets a fresh read-only reviewer: **first spec
compliance** (missing, extra, misunderstood), **then code quality** (errors, edge cases,
behaviour-checking tests); both verdicts are required, and the implementer's self-review never
replaces either. Minor findings go to the ledger; Critical/Important ones enter the fix loop,
each round ending with a scoped re-review of the fix diff. When all tasks are done, run one
final whole-branch review on the Frontier tier, send all its findings to one fixer, and
re-review once. Read `references/briefs.md` when writing any implementer or reviewer brief.

## Multi-stage team runs

Read `references/team-pipeline.md` when running several stages (plan → spec → exec → verify
→ fix): an entry and exit gate per stage, a capped verify→fix loop, risk-based reviewers, a
stuck-worker watchdog (check once, then reassign), shutdown and resume.

## Fix loop — bounded escalation

The single fix-round cap for every loop in this skill (the references add only their
at-the-cap rule):

| round | action |
|---|---|
| 1–2 | send the new failure evidence back to the same worker |
| 3–4 | start a fresh worker on a Frontier tier (or a different model family), with the failed attempts summarised |
| after 4 | stop delegating; the orchestrator fixes, re-scopes, or asks the user |

Never retry with the same brief and no new information.

- **Gates reject degenerate results:** NaN, an empty diff reported as DONE, metrics that
  should differ but match. A too-good result (a perfect score, accuracy 1.0, an implausible
  metric) triggers an inspection of how it was produced before it is accepted, never automatic
  rejection: a release gate may rightly require pass^3 = 1.0 (agent-evals).
- **A failed gate becomes a bounded recall order** to one worker: target, failed checks,
  narrowed scope, acceptance criteria, max retries (counted above).
- **The reviser can be the bottleneck:** give the fixer a tier comparable to the reviewer.

Never poll async workers in a sleep loop; do independent work or yield with a one-line status.

## Closing a batch

Before reporting: every ledger row resolved or explicitly open; every accepted result's
artifact named; single-writer steps listed in order; anything skipped stated with the reason.
