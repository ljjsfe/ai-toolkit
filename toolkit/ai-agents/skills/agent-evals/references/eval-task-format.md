# Eval task format, runner and results layout

Read this when writing a task file for `scripts/eval_run.py` or reading its results. The
runner is standard-library Python; it runs only the commands you put in the task file.

## Task file (JSON)

| field | required | meaning |
|---|---|---|
| `name` | yes | letters, digits, `._-` |
| `runs` | no (3) | runs per arm; `--runs` overrides |
| `timeout_s` | no (900) | per command; a timeout counts as a failed run |
| `workspace` | no | `{"repo": "/abs", "commit": "sha"}` → a fresh `git worktree` per run at that pinned commit; `{"fixture": "/abs/dir"}` → a fresh copy per run; `{}` → an empty temp dir |
| `arms` | yes | `[{"name", "command": [argv...]}]` — baseline and change, same task, same batch |
| `checks` | yes, ≥1 | deterministic checks, all must pass (types below) |
| `judge` | no | `{"command": [argv], "rubric": [{"name", "weight"}], "threshold": N, "scale": [lo, hi]}` — `scale` defaults to `[1, 5]`; state `[1, 10]` explicitly only with a written description per level |

Check types: `command` (argv, `expect_exit`, default 0) · `file_exists` · `file_absent`
(grade overreach: a file nobody asked for) · `file_contains` (`path`, `pattern` regex) ·
`stdout_contains` (regex over the arm's stdout). Paths are relative to the workspace.

Commands are argv lists, never shell strings. Each gets these environment variables:
`EVAL_WORKDIR`, `EVAL_ARM`, `EVAL_RUN_ID`, `EVAL_USAGE_FILE`, and in `iterate` mode
`EVAL_FEEDBACK_FILE` (the previous round's feedback; absent in round 1).

**Keep graders out of reach — the runner only detects tampering, it does not prevent it.**
Arms run with no sandbox, as your user. Put check and judge scripts outside the workspace
(absolute paths in the task file): before each arm runs, the runner hashes every existing
absolute-path file named in a check or judge command, and voids the run ("grader files changed
during the arm's run") if any changed. It cannot stop the arm *reading* those files, and it
cannot see tampering inside the workspace: a `command` check such as `pytest` runs in the
arm-controlled workspace, so a planted `conftest.py` or an edited test passes everything.
Prefer checks that run from outside the workspace against its outputs, or have the check
verify the hashes of the workspace's test files first. For real isolation, run each arm as a
separate OS user or in a container that cannot see the task file, the graders or `--out`.

**Tokens and cost** are recorded only if the arm writes
`{"input_tokens": N, "output_tokens": N, "cost_usd": X}` to `$EVAL_USAGE_FILE` — for example a
wrapper that copies the usage block from the agent CLI's JSON output. The runner never
estimates them.

## Judge contract

The judge command runs in the workspace after the checks and prints (scores here on the
default 1–5 scale):

```json
{"criteria": {"correctness": {"justification": "evidence first: what in the output shows it", "score": 4},
              "clarity":     {"justification": "...", "score": 3}}}
```

Every rubric criterion must be present, with a non-empty justification and a score on the
scale, or the judge result is invalid and the run fails. Weighted score =
Σ(weight × score) / Σ(weight). A run passes only if every deterministic check passes, the arm
exited 0, and (with a judge) the weighted score reaches the threshold. A judge prompt
template is in `references/judge-calibration.md`.

## Commands

```bash
python3 scripts/eval_run.py validate task.json
python3 scripts/eval_run.py run task.json --out evals/2026-11-14-retry --seed 7      # all arms, interleaved
python3 scripts/eval_run.py report evals/2026-11-14-retry/results.json --k 1
python3 scripts/eval_run.py iterate task.json --arm change --out evals/iter-1 --max-iter 5 --patience 3
```

`run` shuffles the arms' runs into one interleaved schedule (seeded), so drift in the
environment hits both arms. Re-running into an `--out` directory whose `results.json` came
from a different task file is refused: a changed eval is a new eval. Re-running into an
`--out` that already holds results of the same task is refused too, unless you pass
`--overwrite`, which discards the earlier `runs/`, `feedback/` and `results.json`. A command
that times out is killed with its whole process group.

## Results layout

```
<out>/
  results.json          task name, task_sha256, runs_per_arm, seed, complete, every run, per-arm summary
  mapping.json          run-NNN → arm (keep private until grading is done, to blind graders)
  runs/run-NNN/
    stdout.txt, stderr.txt   the arm's output (first 200 kB each)
    grade.json               every check's result, judge criteria + justifications, rubric
                             weights (or "void" with the grader files that changed)
    usage.json               only if the arm wrote it
```

`complete` is `false` when the batch stopped early (an error mid-run): the finished runs are
on record but the summary covers only them — do not read it as the full eval.

Per-arm summary: `n`, `passes`, `pass_rate`, `pass_at_k` (chance at least one of k tries
passes, unbiased estimate from n runs), `pass_hat_k` (chance all k pass), and min / median /
max of seconds, tokens, cost and judge score, plus the timeout count. `report --k` recomputes
for another k without re-running.

## Iterate-to-threshold loop

`iterate` keeps one workspace and repeats: run the arm → checks → judge → write
`<out>/feedback/iter-NNN.json` (failed checks and per-criterion score + justification; never
the rubric weights or the judge source) → next round with `EVAL_FEEDBACK_FILE` pointing at it.
Feedback is kept apart from `runs/iter-NNN/grade.json`, which holds the rubric weights; but
the generator runs as your user, so actually hiding `grade.json` from it needs a sandbox or a
separate user. A round whose grader files changed is void and ends the loop (`stopped: "void"`).
It stops at the first passing round (`threshold`), after `--patience` rounds with no better
weighted score (`plateau` — flag it for a human), or at `--max-iter`. Feedback goes in a file,
not inline, so the generator reads all of it each round.

The loop's own scores are not evidence that the final version is better: freeze the result
and evaluate it with `run` against the baseline on held-out cases.
