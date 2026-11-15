# Debugging skill: pilot eval, 2026-11-14

Question: does the `debugging` skill change what a current model does on a real bug, and is
this branch's lean rewrite better than the version on `main`?

## Method

- Runner: `toolkit/ai-agents/skills/agent-evals/scripts/eval_run.py`, one fresh fixture copy per
  run, `--keep` for process metrics, seed 11.
- Task: a Python shop where `collect(codes, seen=set())` (a mutable default) makes a coupon fail
  for later orders. The ticket describes the checkout symptom only; patching checkout passes the
  ticket but not the quote path that shares the helper.
- Grader (outside the workspace): checkout and quote both accept the coupon on repeat orders,
  one code still counts once per order, the visible tests pass. Grader check before any paid
  run: the reference fix passed; the untouched start, a checkout-only patch and a decoy that
  special-cases SAVE10 all failed.
- Arms: no skill; `main`'s debugging SKILL.md; this branch's SKILL.md — injected with
  `claude -p --append-system-prompt`, installed skills disabled (`--disable-slash-commands`),
  tools limited to file edits and python/git-diff/ls/cat. Models: claude-haiku-5-5 and Sonnet
  (claude CLI aliases `haiku`, `sonnet`; the served model was confirmed in the CLI's JSON).
- Process metrics from the kept workspaces: a test was added; that test fails when copied onto
  the original buggy code; the fix touched the root cause (`shop/coupons.py`).

## Results (3 runs per arm; directional, not significant)

| model | arm | outcome | test added | test catches the bug | root cause fixed | cost (median) |
|---|---|---|---|---|---|---|
| Haiku | no skill | 3/3 | 3/3 | 3/3 | 3/3 | $0.006 |
| Haiku | main | 3/3 | 3/3 | 3/3 | 3/3 | $0.006 |
| Haiku | branch | 3/3 | 3/3 | 3/3 | 3/3 | $0.006 |
| Sonnet | no skill | 3/3 | 1/3 | 1/3 | 3/3 | $0.073 |
| Sonnet | main | 3/3 | 1/3 | 1/3 | 3/3 | $0.065 |
| Sonnet | branch | 3/3 | 3/3 | 3/3 | 3/3 | $0.094 |

Total spend for this table: $0.75. An earlier, easier task (float truncation in cents) also
passed in every arm. In a one-run smoke test, neither skill version made the model watch its
new test fail before fixing — both reports said so.

## Reading

- Outcome is at the ceiling for this bug class: every arm, both models, found and fixed the root
  cause. The skill does not make current models find bugs they would otherwise miss here.
- Process: only this branch's version changed Sonnet's behaviour (regression tests that catch the
  bug in 3/3 vs 1/3), at about 40% more cost; `main`'s version behaved like no skill.
- Wall-clock times are not comparable: denied shell commands and the user's global Stop hook
  added turns in some runs.

## Limits

One task, n = 3; the skill was appended to the system prompt rather than loaded as a skill; the
user's global rules and hooks applied to every arm. A harder task where models fail without help
is needed before claiming an outcome effect.
