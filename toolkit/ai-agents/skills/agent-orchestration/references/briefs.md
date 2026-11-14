# Implementer and reviewer briefs

Read this when dispatching an implementer or a task reviewer. Fill the bracketed fields; leave
nothing as "see above" — the worker has not seen above.

## Preparing the inputs (orchestrator, before dispatch)

1. Record `BASE=$(git rev-parse HEAD)` before the implementer starts. The review diff is
   `BASE..HEAD`, never `HEAD~1` (that silently drops all but the last commit of a multi-commit
   task).
2. Extract the task's full text from the plan into its own file (`<ledger-dir>/task-N-brief.md`).
   The brief file is the only place exact values (numbers, strings, signatures, test cases)
   appear; the dispatch prompt points at it and never asks the worker to read the whole plan.
3. Name the report file after the brief (`task-N-report.md`).
4. After the implementer returns DONE, write the review package to one file:
   `git log --oneline BASE..HEAD; git diff --stat BASE..HEAD; git diff -U10 BASE..HEAD`
   redirected to `<ledger-dir>/task-N-review.diff`. The reviewer reads that file; the diff never
   enters your own context.
5. Do not paste earlier tasks' history into a dispatch. Pass only interfaces and decisions from
   earlier tasks that this task depends on.

## Implementer brief

```
You are implementing Task N: [name].

Read first — this is your requirements, with exact values to use verbatim: [BRIEF_FILE]

Where this fits: [one line]
Interfaces from earlier tasks you depend on: [signatures, file paths]
Ambiguities already resolved: [your rulings on anything unclear in the brief]
Work in: [worktree path]     Owns: [files]     Must not: [files, commands]
Model: [explicit tier]

Ask questions before starting if the requirements, approach or dependencies are unclear.

Do the work yourself. Do not spawn subagents — not helpers and not a reviewer; review is
scheduled after you report.

Steps: implement exactly what the brief says (no extras) → write or update tests → run the
focused tests while iterating and the full relevant suite once before committing → commit →
self-review your own diff for missed requirements, overbuilding, names, and tests that test
mocks instead of behaviour → fix what you find.

Stop and report BLOCKED or NEEDS_CONTEXT instead of guessing when: the task needs an
architectural choice with several valid answers; you need code you were not given and cannot
locate; you keep reading files without progress; the brief turns out wrong.

Write the full report to [REPORT_FILE]: what you built, files changed, commands run and their
output (red then green if test-first), self-review findings, concerns.

Reply with at most 15 lines:
  Status: DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
  Commits: [short sha + subject]
  Tests: [one line, e.g. "14/14 passing, no warnings"]
  Concerns: [if any]
  Report: [REPORT_FILE]
For NEEDS_CONTEXT or BLOCKED put the specifics in the reply itself.

If you are resumed with review findings: fix them, re-run the tests covering the changed
code, append a fix section (change, tests, command, output) to the same report, and reply in
the same shape.
```

## Task reviewer brief (spec compliance, then code quality)

```
Review one task. This is a task-scoped gate; a whole-branch review happens later.
Read-only: do not modify the working tree, index or branch. Do not spawn subagents.

Requested: [BRIEF_FILE]
Binding constraints copied verbatim from the spec: [exact values, formats, relationships]
Implementer's report (unverified claims, including its design rationales): [REPORT_FILE]
Diff package (commit list, stat, full diff with context): [DIFF_FILE]   BASE [sha] HEAD [sha]
Model: [explicit tier]

Read the diff file once. Look outside it only to check a named risk (a changed contract, lock
order or shared state), and name the risk and the check. Do not re-run the suite the
implementer already ran; run one focused test only for a specific doubt.

Part 1 — spec compliance, against the brief:
  Missing (skipped or claimed but not done) · Extra (not requested) · Misunderstood.
  For a batched brief, every listed file must have its hunk.
  Requirements that live outside the diff → list under "cannot verify from diff".
Part 2 — code quality: error handling, edge cases, duplication, one responsibility per file,
  tests that check behaviour (not mocks), noise or warnings in test output.

Severity: Critical (wrong or unsafe) · Important (a missed requirement, fragile behaviour,
swallowed errors, tests that assert nothing — you would block a merge) · Minor (polish).
Something the brief mandates that this rubric calls a defect is reported as Important and
labelled plan-mandated.

Reply, starting with the verdict, no preamble:
  Spec: COMPLIANT | ISSUES [file:line each]   Cannot verify: [items]
  Issues: Critical / Important / Minor, each with file:line, what, why, fix
  Quality: APPROVED | NEEDS_FIXES
```

The orchestrator must not tell a reviewer what not to flag. If a finding looks wrong, let it be
raised and rule on it at the fix-loop cap, recording the ruling in the ledger.

## Scoped re-review brief (after each fix round)

```
Re-review fix round R of Task N. Inputs: the open findings list, [BRIEF_FILE], [REPORT_FILE],
and the fix diff [DIFF_FILE] covering FIX_BASE..HEAD (FIX_BASE = the head the last review saw).
For each finding answer ADDRESSED or NOT ADDRESSED with file:line. Flag new Critical or
Important breakage inside the fix diff only. Anything else you notice goes in a short
"out of scope" list for the ledger; it does not reopen the task.
```

## Final whole-branch review

Package `$(git merge-base main HEAD)..HEAD` the same way and dispatch one reviewer on the
Frontier tier (or a different model family) with: the spec, the ledger's deferred-minor and
parked lines, and the package. If it returns findings, send the whole list to one fixer (not
one fixer per finding), then run exactly one scoped re-review of that fix range. Residual
findings go to the user with your rulings. This is the final-review rule at the cap of the
fix-loop table in `SKILL.md`: one fix wave and one re-review, then the user decides — there
is no second fix wave.
