---
name: agent-orchestration
description: Run a team of subagents inside Claude Code or Codex without losing work — keep progress in a ledger that survives compaction, pin models, assign file ownership, serialise single-writer operations, and verify every "done" against an artifact. Use when dispatching more than one subagent or delegating multi-step work.
version: 1.1.0
sources:
  - upstream/superpowers/skills/{subagent-driven-development,dispatching-parallel-agents} (MIT)
  - upstream/oh-my-claudecode/skills/team (MIT)
  - upstream/compound-engineering-plugin/skills/ce-work/references/execution-strategy.md (MIT) — exclusive file ownership, orchestrator-only git, bounded batch concurrency
  - upstream/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md — when delegation fits
  - upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — concurrency cap and no nested spawning
  - upstream/villetakanen-asdlc-io (MIT) — declared dependencies and a divergence rule in the task brief
---

# Agent Orchestration

You are the orchestrator. Subagents do the work; you own the plan, the state and the
verdict. This skill is about running the team, not about designing an agent product
(that is `agent-architecture`).

## Iron laws

1. **Progress lives in a ledger file, not in your context.** Write each task's status, owner,
   model, dependencies and result path to a file as you go. After any compaction or resume, trust the ledger
   and `git log` over your own recollection. The most expensive orchestration failure is an
   orchestrator that loses its place and re-dispatches work that was already done.
2. **Pass the model explicitly on every dispatch.** An omitted model inherits the session's,
   which is usually the most expensive one.
3. **Parallelise reading, serialise writing.** Research, review and analysis run in parallel.
   Workers that edit files run in parallel only on disjoint file sets. Single-writer
   operations — version bumps, changelog, tags, PRs, migrations, deploys, shared config — are
   done by the orchestrator, one at a time, never delegated.
4. **Assign ownership before spawning.** Each worker gets an explicit file cluster; no file
   appears in two clusters, and workers never pick their own tasks. Disjoint files are not
   enough for parallel writers: give each its own worktree (they still collide on lockfiles,
   build output, test databases and ports), and fix shared interfaces before fanning out.
5. **"Done" from a worker is a claim, not a fact.** Accept it only with an artifact you can
   check — a test run, a diff, a file at a path — or a verdict from an independent reviewer
   who did not do the work.

## Inline or delegate?

| do it inline (load a skill / instructions into this context) | delegate to a subagent |
|---|---|
| short, and you need the details afterwards | long reading or searching whose details you won't need |
| depends on what is already in your context | self-contained with a clear input and output |
| one step | independent of other in-flight steps |

Delegation costs a fresh context per worker; inline work costs your own context. Choose
deliberately.

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
Model:       explicit
```

Workers do not spawn their own subagents. Keep concurrency small: 3–5 workers if you read
each result in full, up to about 7 if workers write results to files and return only paths and
short summaries. Batch many small same-shape edits into one worker
instead of one worker each.

## Fix loop — bounded escalation

When a worker's result fails verification:

| round | action |
|---|---|
| 1–3 | send the failure evidence back to the same worker |
| 4–5 | start a fresh worker on a more capable model, with the history of failed attempts |
| after 5 | stop delegating; the orchestrator decides — fix it, re-scope, or ask the user |

Never retry with the same brief and no new information.

While workers run, do independent work or give the user a one-line status; never go silent.

## Closing a batch

Before reporting to the user: every ledger row is resolved or explicitly open; every accepted
result has its artifact named; single-writer steps are done and listed in order; anything
skipped is said, with the reason.
