---
name: analysis-design
description: >-
  Design a data analysis before querying: decision-first questions, a written metric spec, data
  coverage and quality checks, a plan stress-test (survivorship, baselines, Simpson's), tracking
  gaps. Trigger on 数据分析, 指标口径, "why did X drop?" (no launch behind it), "is this data
  clean?". A/B tests or post-launch shifts: experiment-readout.
version: 1.0.0
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

An analysis goes wrong before the first query: the question has no decision behind it, the
metric means two things, the data misses part of the population, or the plan compares against
the wrong thing. Work through the five parts below in order and write each down. For a quick
number pull, one line per part is enough; never let the design outgrow the question.

## Iron laws

1. **Decision before data.** Name the decision the answer will change before touching data.
   If nothing would change, say that it is reporting, not analysis, and offer a quick number
   instead of a design.
2. **A written metric spec before any query.** Definition, unit, numerator and denominator,
   filters and exclusions, time window, grain, and known gotchas. A metric used without a spec
   is a guess at what the requester meant.
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

## 1. Frame — the question ladder

Climb four rungs; stop and ask when one is missing.

| rung | question to ask | weak | strong |
|---|---|---|---|
| goal | what outcome does the business want? | "retention" | "cut 90-day churn of new self-serve accounts" |
| decision | what will you do differently with the answer? | "understand users" | "fund the onboarding fix or the pricing change" |
| metric | what number informs that choice? | "engagement" | "share of week-1 accounts that create a second project" (spec in part 2) |
| hypothesis | what do you expect, and why? | "something is off" | "mobile accounts stall at the import step since the redesign" |

- **The decision test.** Ask "what will you do differently" for each plausible answer. If every
  answer leads to the same action, that is reporting, not analysis.
- **Reframe loaded questions.** "Prove feature X works" becomes "what did feature X change in
  metric M?" A question with the answer built in invites confirmation bias.
- **Dimensions are chosen, not exhaustive:** each dimension needs a reason (what would a
  difference between its values tell you?).
- **Success criteria must be falsifiable:** "find the segment that explains more than half of
  the drop", not "understand the drop".
- **Several questions compete:** do first the one that informs a decision due soon and that the
  current data can answer; new instrumentation or another team's data moves it later.

## 2. Metric spec

Write one spec per metric in the brief (template in `references/templates.md`). The test is
that two analysts would write the same query from it.

- **Definition** in one plain sentence, then the exact formula.
- **Unit of analysis** (what one row is) and the **grain** it is reported at; the randomisation
  or sampling unit if different.
- **Numerator and denominator** separately, each with its source column. Ratios hide moves: the
  denominator moves on its own, so a rate can "improve" because low-intent traffic left.
- **Filters and exclusions:** test accounts, internal users, bots, refunds, guest sessions.
- **Time window** and how it is anchored (calendar day in which timezone, rolling 7 days,
  N days after signup).
- **Known gotchas:** late-arriving data, definition changes, tracking outages, partial last
  period.
- **One name, two meanings, two specs.** If marketing's "conversion" and product's differ,
  name them differently instead of picking one.
- For a key business metric, decompose into drivers (multiplicative such as users × orders per
  user × order value, or additive by segment) and check them in order of likelihood.

## 3. Data check — coverage and quality

First the minimum probe on the exact slice you will analyse: row count, null rate per column,
date range of the main timestamp, duplicates on the key. For a CSV extract:

`python3 scripts/profile_csv.py extract.csv --key order_id [--date created_at] [--json]`

Then the checklist, each item marked BLOCKER / WARNING / INFO:

| check | what to look for | blocker when (toolkit policy where not upstream) |
|---|---|---|
| coverage | the population and period the decision is about are in the data (all platforms, regions, plans; whole period) | a needed segment or period is absent |
| freshness | latest timestamp vs expected cadence; partial last day or week | the analysis window ends after the data does |
| completeness | null rates (flag above 5%), missing days, unexpected zeros | key or critical metric column mostly null; whole days missing |
| duplicates | repeated primary keys, double-logged events | any duplicate on the metric's unit |
| join fan-out | rows per grain key before and after each join; orphan rows after a join | a join multiplies rows the metric then sums |
| timezone | mixed offsets, naive vs UTC, day buckets around midnight | days are bucketed in a timezone other than the spec's |
| bot / test traffic | internal accounts, test orders, crawler user agents, implausible activity rates | an exclusion flag the spec relies on is missing |
| impossible values | negative revenue, rates above 100%, dates in the future | present in a metric column |

- **Severity, then a call:** blocker / warning / info for each finding, then proceed / proceed
  with caution / blocked. Blockers stop the analysis; warnings travel into the findings as
  caveats.
- **Never fix data silently.** Every dedupe, exclusion or imputation is written down with the
  row count it touched.
- The profiler cannot see coverage of the right population, bots, upstream fan-out or business
  rules; those stay manual.

## 4. Tracking gaps — instrumentation requests

List what the analysis needs before looking at what exists, or the gaps go unseen.

1. Requirements table: each event or field, the part of the plan it serves, grain, period.
2. Mark each one available / partial / missing / derivable. Derivable is not available: a
   proxy (billing country for user country, page view time for feature time) carries a stated
   confidence and what it gets wrong.
3. For each partial or missing item, try a workaround first; a workaround can make the request
   unnecessary. Say what the analysis can still conclude with it.
4. Otherwise write an instrumentation request: event name, exact trigger, properties with type
   and required flag, priority (P0-Critical, P1-High, P2-Medium, P3-Low), the question it
   unblocks, dependencies. Template in `references/templates.md`.
5. State feasibility: full, partial (which questions are deferred), or blocked.

## 5. Stress-test the plan

Check the data exists before the method: if a required field is missing, the plan fails on
that alone. Then give each check pass / warn / fail with a one-line reason:

| check | fails when |
|---|---|
| hypothesis | no claim that data could falsify; "explore and see" |
| baseline | a naive baseline: last week with a holiday, campaign, outage or deploy in it; before/after with no comparison; a seasonal metric against last month |
| survivorship | only completed, active or surveyed entities are counted; say who is excluded from the denominator and why |
| segment mix (Simpson's) | only totals are reported; the total can reverse inside a segment when the mix shifts, so break down by the dimensions that changed composition and report the mix |
| confounds | no list of what else changed in the same window (releases, pricing, campaigns, tracking, new markets) or no way to separate it |
| kill criteria | no written answer to what result would reject the hypothesis, and no smallest effect worth acting on |
| output fit | the deliverable does not answer the decision (a description where a recommendation is needed, percentages where money is) |

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
