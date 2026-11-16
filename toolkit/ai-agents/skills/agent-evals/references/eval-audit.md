# Auditing an eval before trusting it

Read this when someone brings an existing eval, before the first full paid run of a new one,
when a result looks too good (or every arm scores zero), or when an optimisation loop stops
moving. A surprising result is more often a bug in the eval than a fact about the model.

First run the eval end to end on a handful of cases, or find a recent results file. Audit the
code, config and data, not the README.

## Cases

Do not read hundreds of cases inline. Work in three passes:

1. **Script over every case:** duplicate and near-duplicate rate, label or category balance,
   prompt and expected-answer length distributions, schema and missing-field counts.
2. **Close-read 20–50 cases**, sampled across categories. Ask the user to read a few too.
3. **One cheap model call per case** for sets of several hundred: flag ambiguous criteria, a
   suspect reference answer, answerable from memory, a grader too strict or too lenient, and a
   shortcut that passes without doing the task. Price it and ask before running it.

Per-case checks for the sample:

- Two domain experts shown the same output would agree on pass or fail.
- Each case has a reference answer that actually passes its grader; re-derive ten labels
  yourself. A case every arm fails is more often broken than hard.
- Record where each reference answer came from (human-written, human-checked, or which model).
- The expected answer, or a paraphrase of it, appears nowhere the model can read: prompt,
  few-shot examples, tool descriptions, files in the workspace, git history.
- For "can it do the work" cases about real entities, the subject is obscure or synthetic
  enough that recall alone cannot answer it.
- Diagnosis tasks give the symptom a user would report, not the log line or failing file.
- Behaviours are covered in both directions (should search / should not search) so an
  always-on policy cannot score perfectly; report the majority-class baseline beside accuracy.
- Answers tied to live facts (prices, versions, dates) carry the date they were last checked.
- Generated cases: fix the generator and regenerate rather than patching single items.

## Harness

- **Plumbing failures never land as model failures.** API errors after retries, timeouts,
  crashed tools and grader crashes are recorded with their class, outside the score. A
  response cut off at the token limit is marked truncated, not wrong. A refusal is its own
  metric. Write the handling rule before the scores exist.
- **"No answer" is not a negative answer.** An empty or unparseable output must not score the
  same as "found nothing" in detection or classification evals.
- **Check which model served the request** from the response, on a smoke case and then on
  every call; a silent substitution invalidates the comparison.
- The eval calls the application's real entry point with the production prompt, tools and
  parameters, not a re-implementation.
- Every run starts from clean state; seeds are pinned; anything order-dependent is sorted.
- A hard wall-clock ceiling per case reclaims hung runs; transient errors retry with jittered
  backoff, and the attempt count is recorded per run. A case that passes only on retry counts
  as a failure unless the user decides otherwise in advance, and every attempt's tokens count.
- A zero cost, zero latency or empty usage field is a runner bug, not a measurement.
- `scripts/eval_run.py` counts a timed-out run as failed and reports `timeouts` per arm; when
  those timeouts come from the environment rather than the agent, report the score with them
  excluded as well.

## Graders

- Run an oracle (reference answers) and a null (empty or constant output) through the whole
  pipeline: about 100% and about 0%.
- Give an LLM judge an empty string, "I don't know" and a confident answer to a different
  question; it must fail all three.
- Read a handful of outputs the grader marked wrong. If more than about one in ten are grader
  mistakes, fix the grader before any full run, then re-grade stored outputs rather than
  re-running the model.
- Grade the same output twice; if the verdict changes, measure and report grader variance.
- Grade outcomes, not the route taken; score separate properties as separate metrics; for rare
  high-stakes behaviour (deleting data, irreversible actions) fail on any occurrence rather
  than averaging.
- Penalties must not make doing nothing the best-scoring policy.

## Can it detect the change?

- **Noise floor.** For a pass rate, the 95% half-width of a paired difference is about
  1/√(cases × runs): 25 × 2 ≈ ±14 points, 100 × 2 ≈ ±7. Put it next to the headroom (ceiling
  minus baseline) and the smallest gain the user would act on. If it is larger than either,
  say so with the numbers and offer, cheapest first: more runs, more cases, a paired or
  continuous metric, or iterating on the discriminating cases with a full-set confirmation at
  the end.
- **The mechanism is wired.** Disable the thing the score should depend on (a tool, a memory
  store, an instruction file) and confirm the score drops; enable it and confirm it shows up in
  the traces.
- **Recompute the headline from per-run rows** yourself; aggregate fields hide mean-versus-sum
  and per-run-versus-per-case mistakes.
- **Split by random draw.** At baseline, the tuning and held-out means agree within noise; if
  not, redraw before round 1.

## When an optimisation loop stalls

Set the stopping delta above the noise floor, and call a plateau only after three or more
consecutive rounds inside it. When two or three rounds in a row stay within noise, stop
changing content and sort every remaining tuning-split failure by cause:

| cause | sign | next move |
|---|---|---|
| artifact gap | the model never had what it needed | keep iterating |
| grader disagreement | output looks right but is marked wrong, or prompt and rubric ask for different things | fix the grader, re-grade every round from stored outputs; if the ranking flips, restart from baseline |
| harness | errored or infra-marked zeros | fix the harness; exclude those runs until then |
| structural | the content exists but is not reached, or one dimension fails whatever you change | reorganise or fix routing instead of adding content |
| variance | identical-code runs flip as much as the round-to-round change | report best so far; raise runs or change target |

One idea per round; a change whose best case sits inside the noise floor is kept or reverted
by chance. If the tuning split improves and the held-out split does not, revert.
