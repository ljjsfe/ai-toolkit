---
name: agent-orchestration
description: >-
  Coordinate subagents or parallel workers: compaction-safe ledger, Oracle-and-blast-radius
  model tiering, disjoint file ownership, single-writer git/config ops, and independent
  artifact-verified completion. Not for designing agent products (use agent-architecture).
version: 1.3.0
sources:
  - upstream/superpowers/skills/{subagent-driven-development,dispatching-parallel-agents,executing-plans} (MIT) — explicit model per worker, fix rounds, a ledger that survives compaction
  - upstream/oh-my-claudecode/skills/team (MIT)
  - upstream/compound-engineering-plugin/skills/ce-work/references/execution-strategy.md (MIT) — exclusive file ownership, orchestrator-only git, bounded batch concurrency
  - upstream/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md — when delegation fits
  - upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — concurrency cap and no nested spawning
  - upstream/villetakanen-asdlc-io (MIT) — declared dependencies and a divergence rule in the task brief
  - "authored for this toolkit — Oracle-by-blast-radius model tiering (Fast / Workhorse / Frontier), subagent-only tier switching to preserve prompt cache, command-log redirection, two-strike escalation, and cross-family / cross-tier review order"
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
   context that did not do the work. For high-blast-radius changes, prefer a different model
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

Workers do not spawn their own subagents. Workers must redirect noisy commands (test suites,
builds, large logs) to a file and inspect only the relevant tail or matches so raw output never
floods their own context, returning only the artifact path and a short summary. Keep concurrency
small: 3–5 workers if you read each result in full, up to about 7 if workers return only paths
and short summaries. Batch many small same-shape edits into one worker instead of one worker each.

## Fix loop — bounded escalation

When a worker's result fails verification:

| round | action |
|---|---|
| 1–2 | send the new failure evidence back to the same worker |
| 3–4 | stop retrying in that polluted context; start a fresh worker on a Frontier tier (or a different model family), with the failed attempts summarised |
| after 4 | stop delegating; the orchestrator decides — fix it, re-scope, or ask the user |

Never retry with the same brief and no new information.

While async workers run, do independent work or yield cleanly when the host wakes on worker
completion — never poll in a sleep loop, and give the user a one-line status before yielding.

## Closing a batch

Before reporting to the user: every ledger row is resolved or explicitly open; every accepted
result has its artifact named; single-writer steps are done and listed in order; anything
skipped is said, with the reason.
