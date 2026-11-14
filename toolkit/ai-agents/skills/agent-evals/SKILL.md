---
name: agent-evals
description: >-
  Evaluate an agent, prompt, skill, or model change with frozen rubrics, hidden graders,
  deterministic checks, artifact-based live grading, and piloted spend caps. Use for LLM/agent
  benchmarks and regression suites; not for product A/B experiments (use experiment-readout) or
  one-change completion checks (use verification).
version: 1.4.0
sources:
  - upstream/everything-claude-code/skills/{eval-harness,agent-eval,gan-style-harness} (MIT) — pass@k and pass^k, worktree per run, cost per run [port "pass^k — all k tries succeed" "a git worktree per run" "record tokens and cost per run"]
  - upstream/everything-claude-code/{skills/agent-eval,skills/gan-style-harness,scripts/eval-harness.js} (MIT) — YAML task and judge schema, a runner, a results layout, weighted rubric with an iterate-to-threshold loop [port "Use the runner instead of ad-hoc scripts" "Results layout" "Judge contract" "Iterate to a threshold, not forever" "Iterate-to-threshold loop" "Σ(weight × score) / Σ(weight)" "pass_hat_k (chance all k pass)"]
  - upstream/everything-claude-code/{docker/gateguard-effectiveness,docs/gateguard/question-effectiveness.md} (MIT) — grader check against reference, naive and decoy overlays before billing; placebo and ablated arms; the all-pass pilot as a ceiling that measured nothing [port "grade the graders before any paid run" "right shape, wrong content" "add a placebo arm" "the eval measured nothing" "Grader check before a paid run"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{self-improvement-loops,harness-engineering,evaluation,advanced-evaluation} (MIT) — hidden graders, raw traces to the optimiser, judge position bias [port "never sees how it is judged" "feed the optimiser raw traces" "position bias"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/advanced-evaluation (MIT) — length, verbosity and self-enhancement judge biases; scale calibration; justification before score [port "design out length and verbosity bias" "self-enhancement bias" "Scale calibration" "justification before the score" "Justification before score" "Length is not quality"]
  - upstream/anthropics-skills/skills/skill-creator, skills/mcp-builder/reference/evaluation.md (Apache-2.0) — trigger tuning split, tool-server question rules [port "split them 60/40" "answerable with read-only operations"]
  - upstream/gstack/eval-plan (MIT) — eval planning [idea]
  - upstream/compound-engineering-plugin/.agents/skills/ce-skill-work/references/evaluate.md (MIT) — skill evaluation [idea]
  - upstream/anthropics-skills/skills/claude-api/shared/evals/{eval-audit,build-eval,eval-hillclimb}.md (Apache-2.0) — grade the end state, start from real failures, report spread, held-out split drawn at random, gold never from a compared model, noise floor before the full run, failure classes kept out of the score, judge agreement bar, the eval-audit checklist and stall categorisation [port "graded from artifacts, not narration" "start from real failures" "report the spread" "hold some cases out" "never by baseline score" "never come from a model under comparison" "noise floor before the full run" "classify every failed run" "recommend not shipping" "90% agreement on clear-cut cases" "Plumbing failures never land as model failures" "Check which model served the request" "When an optimisation loop stalls"]
  - upstream/compound-engineering-plugin/docs (MIT) — blinded arms, small-n paired evals [port "blind the grader" "small n is directional"]
  - upstream/compound-engineering-plugin/docs/solutions/skill-design/callee-skill-evals-need-caller-shaped-tasks.md (MIT) — caller-shaped tasks, overreach grading, pre-existing items in touched files [port "tested the way it is called" "grade overreach" "put pre-existing items inside the files"]
---

# Agent Evals

An eval answers one decision. Decide what you will do with each possible result before you
run anything.

## Iron laws

1. **Define the eval before building the change, and freeze it before the first paid run.**
   Changing a criterion, case or threshold after seeing results makes it a new eval; say so.
2. **In an optimisation or self-improvement loop, the optimiser never sees how it is judged.**
   It gets scores and traces, never the rubric or evaluator source, and may not write to them.
   (An ordinary coding agent may read the tests it is fixing, never edit them.) The runner voids
   a run whose grader files changed but cannot stop reads or tampering inside the workspace;
   real isolation needs a sandbox or a separate OS user.
3. **Every eval has at least one deterministic check** — tests pass, exact match, schema
   validates, file exists, command exits 0. LLM judges add to it; they never replace it.
4. **Generator and evaluator are separate contexts.** The evaluator critiques; it never
   proposes a fix and then grades it.
5. **Live behaviour is graded from artifacts, not narration.** If the behaviour is dispatching
   subagents, calling tools or mutating state, run it for real and grade the logs, diffs and
   files, not what the model says it *would* do.

## Step 1 — Pick the metric to fit the decision

| question | metric | gate |
|---|---|---|
| can it ever do this? (capability) | pass@k — at least one success in k tries | e.g. pass@3 ≥ 0.9 |
| does it always do this? (regression, release) | pass^k — all k tries succeed | pass^3 = 1.0 |
| is B better than A? | paired comparison on the same cases | decided in advance, with its n |

If the behaviour is decided in the first step (routing, a gate, a refusal), stop each run at
that step.

## Step 2 — Build the cases

- **Start from real failures.** Each case that broke in use becomes a case first.
- **Add hard negatives** — inputs that look like they should trigger the behaviour but should not.
- **Hold some cases out.** Anything used to tune the change is not evidence that it worked.
  Draw the split at random (stratified by category), never by baseline score: cases picked
  for failing improve on re-run by chance.
- **Reference answers never come from a model under comparison**; gold taken from one arm's
  outputs rewards imitating that arm.
- Read `references/case-design.md` when testing a tool server's question answering (questions
  answerable with read-only operations), a skill other skills call (tested the way it is
  called; grade overreach; put pre-existing items inside the files it touches), or trigger
  wording (split them 60/40).

## Step 3 — Run it so the comparison is fair

- Run baseline and change **in the same batch**, on the same pinned commit and inputs, each in
  an isolated workspace (a git worktree per run is enough).
- **Blind the grader:** label runs `run-1…run-n`, keep the mapping private, reveal after scoring.
- **Check an LLM judge before trusting it** against 20–30 human-labelled cases (below about
  90% agreement on clear-cut cases, revise the judge before its scores steer anything); run pairwise
  judging in both orders (position bias); design out length and verbosity bias and
  self-enhancement bias (a different model family judges); 1–5 scale unless each of 1–10 is
  described; justification before the score. Read `references/judge-calibration.md` when
  writing or auditing a judge prompt.
- **Use the runner instead of ad-hoc scripts:** `scripts/eval_run.py run` on a JSON task file
  (arms, deterministic checks, optional weighted-rubric judge) runs interleaved arms in fresh
  worktrees and writes `results.json` with pass@k, pass^k and min/median/max time, tokens and
  score. Read `references/eval-task-format.md` when writing a task file or reading results.
- **Record tokens and cost per run.** A change that wins only by using more tokens has not been
  shown better; compare at an equal budget when possible.

## Step 4 — Price it before scaling

0. **Grade the graders before any paid run.** Every grader must pass a reference solution and
   fail the untouched start state, a naive answer and decoys (right shape, wrong content). When
   testing a hook, skill or prompt, add a placebo arm (same cost and shape, no real content) and
   ablated arms (one part removed) so a win can be attributed.
1. Dry run on real input shapes with a stub model — zero cost, catches plumbing bugs.
2. Pilot 3 cases per arm on the real model; read the actual usage, not an estimate.
3. Set a spend cap from the pilot; get approval for anything above it.
4. **Know the noise floor before the full run:** for the paired difference between two arms the
   95% half-width is roughly 1/√(cases × runs) (25 × 2 ≈ ±14 points) — a floor, not the true
   width: repeats of one case are correlated, so a new case narrows it more than a new run. If
   it exceeds the headroom or the smallest change you would act on, add cases first.
5. Then run the full set. Stop when the cap is reached; report what was completed.

Read `references/eval-audit.md` when auditing an existing eval, before the first full paid
run, when a result looks too good, or when an optimisation loop stalls.

## Step 5 — Read the result honestly

- **If every arm passes every run, the eval measured nothing** (a ceiling; all failing is a
  floor): redesign the tasks so they can fail before reading cost or turn differences.
- **Classify every failed run before reading the score:** harness or infrastructure error,
  timeout, refusal, or genuine failure. Fix how each class counts in advance (a pass only on
  retry is a failure by default); report the score with and without non-model failures.
- **Small n is directional.** Three runs per arm is a floor, not proof. If the held-out
  difference is within noise, say so and recommend not shipping.
- **Report the spread (min / median / max), not just the mean.**
- **Accept a change only if no split regresses beyond a tolerance set in advance:** it improves
  the held-out split and the held-in split gets no worse than that tolerance.
- **Feed the optimiser raw traces, not summaries.**
- **Iterate to a threshold, not forever.** `eval_run.py iterate` stops at the frozen weighted
  threshold, on a plateau (hand it to a human), or at a round cap. The loop's own scores are not
  evidence; evaluate the final version against the baseline on held-out cases.
