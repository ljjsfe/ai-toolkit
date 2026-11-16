---
name: analysis-design
description: >-
  Design a data analysis before querying: decision-first questions, a written metric spec, data
  coverage and quality checks, a plan stress-test (survivorship, baselines, Simpson's), tracking
  gaps. Trigger on 数据分析, 指标口径, "why did X drop?" (no launch behind it), "is this data
  clean?". A/B tests or post-launch shifts: experiment-readout.
version: 1.0.2
sources:
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/question-framing (MIT) — goal, decision, metric, hypothesis ladder; the "what would you do differently" test; reporting vs analysis; justified dimensions; falsifiable success criteria; impact and feasibility ordering [port "what will you do differently" "that is reporting, not analysis" "each dimension needs a reason" "success criteria must be falsifiable" "informs a decision due soon"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/stress-test (MIT) — data availability before method, hypothesis, baseline, survivorship, segment reversal, concurrent changes, kill criteria, output fit, each with a pass/warn/fail verdict [port "check the data exists before the method" "a naive baseline" "who is excluded from the denominator" "reverse inside a segment" "what else changed in the same window" "what result would reject the hypothesis" "pass / warn / fail"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/stress-test (MIT) — the A to F letter grade over the seven verdicts [gap the plan gets per-check verdicts and a go / fix / redesign call, no letter grade]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/metric-spec (MIT) — unambiguous definition, explicit denominator, window and exclusions, one name per meaning, ratio parts moving on their own, grain key, driver decomposition, limitations [port "two analysts would write the same query" "one name, two meanings, two specs" "the denominator moves on its own" "rows per grain key" "decompose into drivers"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/metric-spec (MIT) — registering specs in a metrics store and compiling single-aggregate metrics into deterministic queries [gap specs live in the analysis brief; no registry or metric compiler]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/data-quality-check (MIT) — minimum probe, severity classes, freshness, completeness, duplicates, referential integrity, impossible values, the proceed decision, no silent fixes [port "row count, null rate per column" "blocker / warning / info" "proceed / proceed with caution / blocked" "never fix data silently" "orphan rows after a join"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/data-quality-check (MIT) — outlier tests and a rolling time-series anomaly scan run as tested helpers [gap the profiler covers nulls, keys, dates and timezones only; outliers and anomalies are checked by hand]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/tracking-gaps (MIT) — requirements before inventory, four availability statuses, workarounds with confidence, prioritised instrumentation requests [port "list what the analysis needs before" "available / partial / missing / derivable" "derivable is not available" "p0-critical, p1-high" "a workaround can make the request unnecessary"]
---

# Analysis Design

An analysis goes wrong before the first query. For a quick number pull, one line per part is
enough; never let the design outgrow the question.

## Iron laws

1. **Decision before data.** Name the decision the answer will change before touching data.
   If nothing would change, say that it is reporting, not analysis, and offer a quick number
   instead of a design.
2. **A written metric spec before any query** (part 2). A metric used without one is a guess
   at what the requester meant.
3. **Coverage before analysis.** Check that the data covers the population and the period the
   decision is about, and run the data check, before computing anything you will report.
4. **Stress-test the plan before running it.** Survivorship, baseline, segment mix and kill
   criteria are checked on the written plan; a FAIL is fixed first.
5. **Separate observation from inference.** Every finding line is tagged *observed* (a count or
   chart you produced, with the query) or *inferred* (a cause or explanation, with what would
   confirm it). An anomaly is a place to look, not a conclusion.
6. **Profile figures come from executed code** (toolkit policy). Row counts, null rates,
   duplicate counts and date gaps come from `scripts/profile_csv.py` or a query run this
   session, with the command shown.

Work through the five parts in order and write each down; read the matching section of
`references/procedure.md` for the full checklist of any part you have not done before this
session. Before writing the brief, spec, data report or a request, read `references/templates.md`.

## 1. Frame — the question ladder

Climb goal → decision → metric → hypothesis; stop and ask when a rung is missing. Ask "what will
you do differently" for each plausible answer; if every answer leads to the same action, that is
reporting, not analysis. Reframe loaded questions ("prove X works" → "what did X change in M?").
Each dimension needs a reason; success criteria must be falsifiable. Of competing questions, do
first the one that informs a decision due soon and the current data can answer.

## 2. Metric spec

One spec per metric, passing the test that two analysts would write the same query from it:
definition and formula, unit and grain, numerator and denominator with source columns, filters,
anchored time window (timezone), known gotchas. The denominator moves on its own, so check both
parts of a ratio. One name, two meanings, two specs. For a key business metric, decompose into
drivers and check them in order of likelihood.

## 3. Data check — coverage and quality

Run the minimum probe on the exact slice: row count, null rate per column, date range, duplicates
on the key. For a CSV extract:

`python3 scripts/profile_csv.py extract.csv --key order_id [--date created_at] [--json]`

Then check coverage, freshness, completeness (flag nulls above 5%), duplicates, join fan-out
(rows per grain key before and after each join), timezone, bot/test traffic and impossible values
— read the blocker conditions per check in `references/procedure.md` first. Mark each finding blocker / warning /
info, then call proceed / proceed with caution / blocked: blockers stop the analysis; warnings
travel into the findings as caveats. Never fix data silently: every dedupe, exclusion or
imputation is written down with the rows it touched. Coverage, bots, upstream fan-out and
business rules stay manual; the profiler cannot see them.

## 4. Tracking gaps

List what the analysis needs before looking at what exists. Mark each item available / partial /
missing / derivable; derivable is not available, so a proxy carries a stated confidence. Try a
workaround before any instrumentation request (P0–P3; read the steps in `references/procedure.md` first), then
state feasibility: full, partial (which questions are deferred) or blocked.

## 5. Stress-test the plan

Check the data exists before the method. Then give each check pass / warn / fail with a one-line
reason: hypothesis, baseline, survivorship, segment mix (Simpson's), confounds, kill criteria,
output fit (read the fail conditions in `references/procedure.md` first).

Verdict (toolkit policy): any fail → fix before running; two or more fails → redesign from the
ladder; warns only → run and carry them as caveats.

## Hand-offs

- Randomised A/B tests, and a metric that moved after a launch → `experiment-readout`.
- Facts from external sources (market sizes, benchmarks, papers) → `verified-research`.
- What to build from the result → `product-scoping`.
- Building or resizing the pipeline, warehouse or event system → `system-design`.

## Output

```
Question: <sharpened question>        Decision it informs: <action>   (or: reporting only)
Ladder: goal <…> · decision <…> · metric <…> · hypothesis <…>
Success criterion: <falsifiable condition>   Kill: <result that rejects the hypothesis>
Metric spec: <name> = <numerator> / <denominator>; unit <…>; grain <…>; window <…>; excludes <…>; gotchas <…>
Data: <source, slice>  probe: <command>  → rows <n>, period <min..max>, gaps <…>, dup keys <n>
Checks: coverage / freshness / completeness / duplicates / fan-out / timezone / bots / impossible → each BLOCKER/WARNING/INFO
Data call: proceed / proceed with caution / blocked — <reason>
Tracking gaps: <item> available/partial/missing/derivable … ; requests: <event> P<n>
Stress test: hypothesis / baseline / survivorship / segment mix / confounds / kill / output → pass/warn/fail
Plan: <dimensions with reasons, comparison, period, deliverable>
Findings (after running): <observed | inferred> <line> — evidence: <query or chart>
```
