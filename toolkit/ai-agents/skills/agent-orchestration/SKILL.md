---
name: agent-orchestration
description: >-
  Coordinate subagents or parallel workers: compaction-safe ledger, Oracle-and-blast-radius
  model tiering, disjoint file ownership, single-writer git/config ops, and independent
  artifact-verified completion. Not for designing agent products (use agent-architecture).
version: 1.5.0
sources:
  - upstream/superpowers/skills/{subagent-driven-development,dispatching-parallel-agents,executing-plans} (MIT) — explicit model per worker, fix rounds, a ledger that survives compaction [port "progress lives in a ledger file" "explicit tier / model" "fix loop — bounded escalation"]
  - upstream/superpowers/skills/subagent-driven-development (MIT) — two-stage review after every task (spec compliance, then code quality) plus a final whole-branch review; the DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED worker status protocol; implementer and reviewer prompt templates and brief scripts [port "first spec compliance" "then code quality" "final whole-branch review on the Frontier tier" "DONE_WITH_CONCERNS" "NEEDS_CONTEXT" "never the same brief again" "Implementer brief" "Task reviewer brief (spec compliance, then code quality)" "Scoped re-review brief"]
  - upstream/oh-my-claudecode/skills/team (MIT) — staged plan, prd, exec, verify, fix pipeline with entry and exit gates; risk-based reviewer escalation; stuck-worker watchdog and reassignment; shutdown and resume protocol [port "an entry and exit gate per stage" "capped verify→fix loop" "Risk-based reviewer escalation" "Stuck-worker watchdog and reassignment" "check once, then reassign" "A worker fails two tasks" "Resume after a crash or compaction" "Stage handoff file" "Send each live worker a shutdown request"]
  - upstream/oh-my-claudecode/skills/{team,autopilot}/SKILL.md (MIT) — subagent nesting depth and concurrency are Claude Code settings whose defaults changed across 2.1.217–2.1.219 [port "toolkit policy, not a runtime limit" "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/long-horizon-prompting/references/mass-handoff-contracts.md (MIT) — degenerate-value rejection at handoff gates, bounded recall orders, the reviser as bottleneck [port "reject too-good-to-be-true results" "bounded recall order" "the reviser can be the bottleneck"]
  - upstream/compound-engineering-plugin/skills/ce-work/references/execution-strategy.md (MIT) — exclusive file ownership, orchestrator-only git, bounded batch concurrency [port "no file appears in two clusters" "single-writer operations" "keep concurrency small"]
  - upstream/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md — when delegation fits [port "inline or delegate"]
  - upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — concurrency cap and no nested spawning [port "workers do not spawn their own subagents"]
  - upstream/villetakanen-asdlc-io (MIT) — declared dependencies and a divergence rule in the task brief [port "declared now, not discovered at merge" "if the brief or spec turns out wrong"]
  - 'authored for this toolkit — Oracle-by-blast-radius model tiering (Fast / Workhorse / Frontier), subagent-only tier switching to preserve prompt cache, command-log redirection, two-strike escalation, and cross-family / cross-tier review order [port "route model tiers on subagent spawn" "redirect noisy commands" "a workhorse stalls twice" "prefer a different model family"]'
---

# Agent Orchestration

You are the orchestrator. Subagents do the work; you own the plan, the state and the
verdict. This skill is about running the team, not about designing an agent product
(that is `agent-architecture`).

## Iron laws

1. **Progress lives in a ledger file, not in your context.** Write each task's status, owner,
   model tier, dependencies and result path to a file as you go. After any compaction or resume, trust the ledger
   and `git log` over your own recollection. The most expensive orchestration failure is an
   orchestrator that loses its place and re-dispatches work that was already done.
2. **Route model tiers on subagent spawn, never mid-session.** Switching models inside a live
   conversation invalidates its prompt cache; tiering applies only when spawning a fresh worker
   (while honouring any host rule that keeps the session model unless asked). Match the tier to
   whether a deterministic check (Oracle) catches mistakes and how wide a mistake reaches — never
   to file extension or line count.
3. **Parallelise reading, serialise writing.** Research, review and analysis run in parallel.
   Workers that edit files run in parallel only on disjoint file sets. Single-writer
   operations — version bumps, changelog, tags, PRs, migrations, deploys, shared config — are
   done by the orchestrator, one at a time, never delegated.
4. **Assign ownership before spawning.** Each worker gets an explicit file cluster; no file
   appears in two clusters, and workers never pick their own tasks. Disjoint files are not
   enough for parallel writers: give each its own isolated workspace or git worktree (note they
   still collide on shared test databases and ports), and fix shared interfaces before fanning out.
5. **"Done" from a worker is a claim, not a fact.** Accept it only with an artifact you can
   check — a test run, a diff, a file at a path — or a verdict from a fresh, read-only reviewer
   context that did not do the work. Code-writing tasks under a plan need both review verdicts
   (below); other work is accepted on its artifact alone. For high-blast-radius changes, prefer a different model
   family when available, else a Frontier-tier fresh context, else a same-tier fresh context.

## Inline or delegate?

| do it inline (load a skill / instructions into this context) | delegate to a subagent |
|---|---|
| short, and you need the details afterwards | long reading or searching whose details you won't need |
| depends on what is already in your context | self-contained with a clear input and output |
| one step | independent of other in-flight steps |

Delegation costs a fresh context per worker; inline work costs your own context. Choose
deliberately.

## Model tier per subagent

| tier | use when | guardrails |
|---|---|---|
| **Fast** (lightweight / low-effort) | Steps are known **and** a deterministic Oracle checks the output: targeted search, log/JSON extraction, mechanical transforms, running an existing check script. Zero open-ended design. | Restrict to read-only or minimum tools; require a fixed return shape. |
| **Workhorse** (standard coding) | Bounded implementation, tests, or debugging with clear interfaces and specs. | Default for self-contained engineering slices. |
| **Frontier** (deep reasoning) | **No automatic Oracle on a high-blast-radius call** (architecture, auth/security/money boundaries, or editing tests/gates themselves), open-ended synthesis, or escalation after a Workhorse stalls twice. | Reserve for judgment gates and hard root-cause analysis. |

## Dispatch brief — every subagent gets all of these

```
Goal:        one sentence, the outcome not the activity
Inputs:      exact file paths / URLs / data to use
Owns:        files it may modify (empty for read-only work)
Must not:    files, commands and decisions that are out of bounds
Return:      the exact shape — fields, file path, max length — plus what was not done or assumed
Done when:   the checkable condition
Depends on:  tasks that must finish first — declared now, not discovered at merge
If wrong:    what to do if the brief or spec turns out wrong — stop and report, or
             continue and log each deviation; a deviation never crosses Owns or Must not
             (if it would, stop); never silently work around it
Model:       explicit tier / model
```

Workers do not spawn their own subagents — toolkit policy, not a runtime limit: Claude Code
sets nesting depth with `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` (its default changed between
2.1.217 and 2.1.219) and caps parallel subagents with `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`, so
check the host's settings before planning nested delegation. Workers must redirect noisy commands (test suites,
builds, large logs) to a file and inspect only the relevant tail or matches so raw output never
floods their own context, returning only the artifact path and a short summary. Keep concurrency
small: 3–5 workers if you read each result in full, up to about 7 if workers return only paths
and short summaries. Batch many small same-shape edits into one worker instead of one worker each.

## Worker status and review after every task

Every implementer replies with one status, and you act on it:

| status | meaning | your move |
|---|---|---|
| `DONE` | finished, tests run | package the diff (`BASE..HEAD`) and dispatch the task reviewer |
| `DONE_WITH_CONCERNS` | finished, with doubts | read the concerns first; correctness or scope doubts are resolved before review, observations are noted |
| `NEEDS_CONTEXT` | missing information | supply it and re-dispatch; do not let it guess |
| `BLOCKED` | cannot finish | change something: more context, a higher tier, a smaller task, or a ruling that corrects the plan — never the same brief again |

Each code-writing task under a plan then gets a two-stage review by a fresh read-only
reviewer: **first spec compliance** (missing, extra, misunderstood against the brief), **then
code quality** (errors, edge cases, tests that check behaviour). Such a task is complete only
with both verdicts; implementer self-review never replaces it. Other delegated work (research,
extraction, running an existing check) is accepted under iron law 5 on its checkable artifact. Minor findings go to the ledger; Critical/Important ones enter
the fix loop, each round ending with a scoped re-review of the fix diff. When all tasks are
done, run one final whole-branch review on the Frontier tier, send all its findings to one
fixer, and re-review once.

Read `references/briefs.md` when writing an implementer, reviewer, re-review or final-review
brief — the templates and the diff-package recipe.

## Multi-stage team runs

For a run with several stages, use plan → spec → exec → verify → fix with an entry and exit
gate per stage, a capped verify→fix loop, reviewers added by risk, a stuck-worker watchdog
(check once, then reassign), and an orderly shutdown and resume. Read
`references/team-pipeline.md` when running such a team.

## Fix loop — bounded escalation

This table is the single fix-round cap for every loop in this skill. `references/team-pipeline.md`
(verify→fix) and `references/briefs.md` (final review) point here and add only their
stage-specific rule for what happens at the cap.

When a worker's result fails verification:

| round | action |
|---|---|
| 1–2 | send the new failure evidence back to the same worker |
| 3–4 | stop retrying in that polluted context; start a fresh worker on a Frontier tier (or a different model family), with the failed attempts summarised |
| after 4 | stop delegating; the orchestrator decides — fix it, re-scope, or ask the user |

Never retry with the same brief and no new information.

- **Gates reject too-good-to-be-true results,** not only failures: degenerate or implausible
  values (a perfect score, NaN, an empty diff reported as DONE, metrics that should differ but
  match) usually mean something upstream broke.
- **A failed gate becomes a bounded recall order** to one worker: target, failed checks,
  narrowed scope, acceptance criteria, max retries (counted against the table above), so a
  review finding never reopens the whole artifact.
- **The reviser can be the bottleneck.** Strong feedback is wasted on a fixer that cannot act
  on it; give the fixer a tier comparable to the reviewer that found the problem.

While async workers run, do independent work or yield cleanly when the host wakes on worker
completion — never poll in a sleep loop, and give the user a one-line status before yielding.

## Closing a batch

Before reporting to the user: every ledger row is resolved or explicitly open; every accepted
result has its artifact named; single-writer steps are done and listed in order; anything
skipped is said, with the reason.
