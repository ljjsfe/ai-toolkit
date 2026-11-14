---
name: agent-evals
description: >-
  Evaluate an agent, prompt, skill, or model change with frozen rubrics, hidden graders,
  deterministic checks, artifact-based live grading, and piloted spend caps. Use for LLM/agent
  benchmarks and regression suites; not for product A/B experiments (use experiment-readout) or
  one-change completion checks (use verification).
version: 1.2.0
sources:
  - upstream/everything-claude-code/skills/{eval-harness,agent-eval,gan-style-harness} (MIT) — pass@k and pass^k, worktree per run, cost per run [port "pass^k — all k tries succeed" "a git worktree per run" "record tokens and cost per run"]
  - upstream/everything-claude-code/{skills/agent-eval,skills/gan-style-harness,scripts/eval-harness.js} (MIT) — YAML task and judge schema, a runner, a results layout, weighted rubric with an iterate-to-threshold loop [port "Use the runner instead of ad-hoc scripts" "Results layout" "Judge contract" "Iterate to a threshold, not forever" "Iterate-to-threshold loop" "Σ(weight × score) / Σ(weight)" "pass_hat_k (chance all k pass)"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{self-improvement-loops,harness-engineering,evaluation,advanced-evaluation} (MIT) — hidden graders, raw traces to the optimiser, judge position bias [port "never sees how it is judged" "feed the optimiser raw traces" "position bias"]
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/advanced-evaluation (MIT) — length, verbosity and self-enhancement judge biases; scale calibration; justification before score [port "design out length and verbosity bias" "self-enhancement bias" "Scale calibration" "justification before the score" "Justification before score" "Length is not quality"]
  - upstream/anthropics-skills/skills/skill-creator, skills/mcp-builder/reference/evaluation.md (Apache-2.0) — trigger tuning split, tool-server question rules [port "split them 60/40" "answerable with read-only operations"]
  - upstream/gstack/eval-plan (MIT) — eval planning [idea]
  - upstream/compound-engineering-plugin/.agents/skills/ce-skill-work/references/evaluate.md (MIT) — skill evaluation [idea]
  - upstream/anthropics-skills/skills/claude-api/shared/evals/{eval-audit,build-eval,eval-hillclimb}.md (Apache-2.0) — grade the end state, start from real failures, report spread, held-out split [port "graded from artifacts, not narration" "start from real failures" "report the spread" "hold some cases out"]
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
   (An ordinary coding agent may read the tests it is fixing; it may not edit them.) A visible
   scorer gets gamed — edited, special-cased or disabled. The runner enforces this only as far
   as it can — it voids a run whose grader files changed — but it cannot stop reads or
   tampering inside the workspace; real isolation needs a sandbox or a separate OS user.
3. **Every eval has at least one deterministic check** — tests pass, exact match, schema
   validates, file exists, command exits 0. LLM judges add to it; they never replace it.
4. **Generator and evaluator are separate contexts.** An agent grading its own work is
   reliably optimistic. The evaluator critiques; it never proposes a fix and then grades it.
5. **Live behaviour is graded from artifacts, not narration.** If the behaviour under test is
   dispatching subagents, calling tools or mutating state, run it for real and grade the logs,
   diffs and files. Asking the model what it *would* do measures its description, not its
   behaviour.

## Step 1 — Pick the metric to fit the decision

| question | metric | gate |
|---|---|---|
| can it ever do this? (capability) | pass@k — at least one success in k tries | e.g. pass@3 ≥ 0.9 |
| does it always do this? (regression, release) | pass^k — all k tries succeed | pass^3 = 1.0 |
| is B better than A? | paired comparison on the same cases | decided in advance, with its n |

Size the eval to the decision: if the behaviour is decided in the first step (routing, a
gate, a refusal), stop each run at that step instead of running the whole workflow.

## Step 2 — Build the cases

- **Start from real failures.** Each case that broke in use becomes a case first.
- **Add hard negatives** — inputs that look like they should trigger the behaviour but should
  not.
- **For question-answering evals of a tool server, each question must be:** answerable with
  read-only operations; not
  solvable by keyword search (paraphrase, don't quote); stable over time (never "the current
  count"); and resolved to a single string that can be compared exactly.
- **Hold some cases out.** Anything used to tune the change is not evidence that it worked.
- **A skill that other skills or standing instructions invoke is tested the way it is called.**
  The task text is what the caller passes (a mode token, a scope, one line of context), not a
  user's request — a loose task invites extra work and the eval then measures the task text.
  Grade overreach as well as the intended result: fail runs that edit outside the scope, commit,
  or add files nobody asked for. Put pre-existing items inside the files the work touches, or a
  "change only the current work" rule passes trivially.

## Step 3 — Run it so the comparison is fair

- Run baseline and change **in the same batch**, on the same pinned commit and inputs, each in
  an isolated workspace (a git worktree per run is enough).
- **Blind the grader:** label runs `run-1…run-n`, keep the mapping private, reveal after scoring.
- **Check an LLM judge before trusting it:** compare it with 20–30 human-labelled cases, and in
  pairwise judging run both orders to cancel position bias. Also design out length and
  verbosity bias (an explicit conciseness criterion; length is not quality) and
  self-enhancement bias (judge with a different model family than the generator). Match the
  scale to the rubric — 1–5 by default, 1–10 only with a written description per level — and
  make the judge write its justification before the score. Read
  `references/judge-calibration.md` when writing or auditing a judge prompt.
- **Use the runner instead of ad-hoc scripts.** `scripts/eval_run.py run` reads a JSON task
  file (arms, deterministic checks, optional weighted-rubric judge), runs each arm N times in a
  fresh worktree or temp copy, interleaves the arms in one batch, and writes `results.json`
  with pass@k, pass^k and min/median/max of time, tokens and judge score. Read
  `references/eval-task-format.md` when writing a task file or reading results.
- **Control for spend.** Record tokens and cost per run. A change that wins only because it used
  more tokens has not been shown to be better; compare at an equal budget when possible.

## Step 4 — Price it before scaling

1. Dry run on real input shapes with a stub model — zero cost, catches plumbing bugs.
2. Pilot 3 cases per arm on the real model; read the actual usage, not an estimate.
3. Set a spend cap from the pilot; get approval for anything above it.
4. Then run the full set. Stop when the cap is reached; report what was completed.

## Step 5 — Read the result honestly

- **Small n is directional.** Three runs per arm is a floor, not proof: state results as a
  direction unless the separation is clean.
- **Report the spread (min / median / max), not just the mean.**
- **Accept a change only if no split regresses beyond a tolerance set in advance:** it improves
  the held-out split, and the held-in split gets no worse than that tolerance. A gain on one split paid for by a loss on the other is a reject.
- **Feed the optimiser raw traces, not summaries.** Summarised traces lose the signal the
  next iteration needs.
- **Iterate to a threshold, not forever.** A generator–judge loop (`eval_run.py iterate`)
  stops at the frozen weighted threshold, on a plateau (no better score for a set number of
  rounds — hand it to a human), or at a round cap. The loop's own scores are not evidence;
  evaluate the final version against the baseline on held-out cases.

## Tuning when a skill or tool triggers

Collect should-trigger and should-not-trigger prompts; split them 60/40; revise the
description from failures on the 60; choose the final wording by the score on the 40; run each
prompt more than once, because routing is noisy.
