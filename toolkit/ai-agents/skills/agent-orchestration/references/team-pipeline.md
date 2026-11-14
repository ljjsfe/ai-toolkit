# Staged team pipeline

Read this when a team of workers runs a multi-stage job (more than a single batch of tasks):
the stages, the gates between them, who reviews, how stuck workers are handled, and how the
run stops and resumes.

## Stages and gates

`plan → spec (only when needed) → exec → verify → fix → (exec → verify)…`

| stage | entry gate | work | exit gate |
|---|---|---|---|
| plan | the request is parsed | read-only explorers map the code; a planner writes the task graph with owners and dependencies | every task has an owner cluster, a done-when check and declared dependencies |
| spec | scope is ambiguous or acceptance criteria are missing (skip otherwise) | an analyst writes acceptance criteria; optionally a critic challenges scope | criteria and boundaries are explicit and written to a file |
| exec | tasks assigned and workers spawned | workers implement in their clusters/worktrees | every task in this pass is in a terminal state (done, failed, blocked) |
| verify | the exec pass finished | a verifier runs the checks; reviewers chosen by risk (below) | pass → done; fail → fix tasks written, move to fix |
| fix | verify found defects or unmet criteria | workers fix, routed by defect type (build/type errors → a debugging worker) | fixes committed; return to verify |

The verify→fix loop is capped by the fix-loop table in `SKILL.md` (same worker for rounds 1–2,
a fresh higher-tier worker for 3–4). Team-run rule at the cap: the orchestrator's decision is
recorded in the run state, and unless it re-scopes into a new run, the run ends as `failed`
with the evidence; it does not loop again. Terminal
states are `complete`, `failed` and `cancelled`.

## Stage handoff file

Each stage writes a short handoff (10–20 lines) to `<ledger-dir>/handoff-<stage>.md` before
the next stage starts, and the next stage's briefs include it:

```
## Handoff: <stage> → <next stage>
Decided:   key decisions
Rejected:  alternatives and why
Risks:     what the next stage must watch
Files:     files created or changed
Remaining: what the next stage still has to do
```

Handoffs accumulate: verify reads all of them. They survive cancellation, for resume.

## Risk-based reviewer escalation (verify stage)

| change | reviewers |
|---|---|
| any | one verifier that runs the deterministic checks |
| touches auth, crypto, secrets, money, permissions | + a security reviewer |
| more than ~20 files, or an architectural/interface change | + a Frontier-tier code reviewer (or another model family) |
| edits tests, gates or CI (toolkit policy, not in the upstream team skill) | + a Frontier-tier reviewer; never the worker that wrote it |

Cost-saving downgrades never apply to the verify stage below the Workhorse tier.

## Stuck-worker watchdog and reassignment

Track, per task in the ledger: owner, started-at, last-heard-at, attempt count.

- **No word for ~5 minutes on an in-progress task** → send one status check.
- **No word for ~10 minutes after the check** (or the worker crashed) → treat it as dead,
  reassign the task to another worker with the brief, the report file and any partial commits,
  and record the reassignment in the ledger.
- **A worker fails two tasks** → stop assigning it new work.
- **A blocking task fails** → decide explicitly: retry it, remove the dependency, or skip the
  dependants; tell the affected workers and ledger the decision.

Adjust the minutes to the task's expected length; the rule is "check once, then reassign",
never "wait indefinitely" and never a tight polling loop.

## Shutdown

1. Confirm in the ledger that every real task is complete or failed.
2. Send each live worker a shutdown request with a request id.
3. Wait a bounded time per worker for an acknowledgement that echoes that id; mark
   non-responders as unresponsive rather than waiting on them.
4. Only then clear run state (worktrees, temp branches, process handles). Stop only orphaned
   processes this run started — PIDs recorded in the run state, or the team's own named
   sessions — never by a process-name match: send SIGTERM, wait ~5 s, then SIGKILL survivors.
5. Append at most three factual lines on what broke or dragged to the run's notes file; append,
   never overwrite. For a `failed` run, write an incident note with the failure signature and
   evidence paths.
6. Report to the user.

## Resume after a crash or compaction

1. Read the run state (current stage, fix-round count, workers, task owners) and the handoff
   files before doing anything else.
2. If the state names a non-terminal stage, resume that stage: monitor existing workers, do not
   re-plan, do not create duplicate tasks, do not spawn duplicate workers.
3. If the state is unreadable or corrupt, stop, report it and keep the original bytes; never
   reinitialise over it.
4. Only a run with no active state starts from the plan stage.
