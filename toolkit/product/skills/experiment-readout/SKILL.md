---
name: experiment-readout
description: >-
  Design and read product A/B tests and launch metric shifts: pre-registered primary/guardrail
  rules, SRM halt gate, power/sample arithmetic, bias-vs-noise separation, and multiple-comparison
  correction. Trigger on 实验结果, AB测试读数, "did this launch work?". For AI evals use agent-evals.
version: 1.2.2
sources:
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/srm-check (MIT) — SRM as a blocking gate, per-period SRM, investigation paths [port "sample ratio mismatch halts the readout" "per-period check" "where to look"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/guardrails (MIT) — clear / trade-off / degraded verdicts, net impact in shared units [port "the bound crosses the tolerance" "net-impact line"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/experiment (MIT) — pre-registered config, not-viable power checkpoint, stricter SRM threshold while monitoring, Holm correction, outcome classes [port "pre-register before looking" "not viable forces a decision" "p < 0.0005 while monitoring" "adjust p-values (holm," "learn (underpowered null)"]
  - upstream/ai-analyst-lab-ai-analyst/helpers/stats/experiment_stats/{srm.py,power.py,corrections.py,ab_tests.py} (MIT; rewritten in the standard library, checked against SciPy and statsmodels) — SRM chi-squared incl. per segment, power and duration incl. uneven splits, two-proportion and Welch tests, ratio metrics by the delta method, Holm [port "def srm_segments" "def power_prop" "def welch(mc" "def ratio_test" "def holm(pvalues" "every statistic comes from executed code"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/experiment/SKILL.md (MIT) — the Simpson's-paradox segment check [port "the total can reverse inside every segment"]
  - upstream/ai-analyst-lab-ai-analyst/helpers/stats/experiment_stats/{sequential.py,variance_reduction.py} (MIT) — always-valid confidence sequences for repeated looks; CUPED variance reduction [gap not ported; a sequential design needs an external tool]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/triangulation (MIT) — independent methods for non-randomised changes; agreement is not proof [port "at least two paths that differ in" "agreement narrows the doubt"]
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/triangulation (MIT) — paths run in isolated subagents with per-path record fields [gap independence is asked for in one line with no mechanism]
  - upstream/posthog-experiments/products/experiments/skills/diagnosing-experiment-health (MIT, method only) — age and exposed-population checks, systematic vs statistical, mechanisms need evidence [port "how far through the run" "who is exposed vs who the decision is about" "name a mechanism only with evidence" "waiting fixes noise, not bias"]
  - upstream/posthog-experiments/products/experiments/skills/diagnosing-experiment-health/references/interpretation.md (MIT, method only) — peeking, multiple comparisons, MDE and sample arithmetic, "target reached" is not a result [port "stopping when the result first looks significant" "about a 23% chance" "halving the mde quadruples" "an effect of mde size would likely have shown"]
  - upstream/posthog-experiments/products/experiments/skills/diagnosing-experiment-health/references/{bias-and-skew.md,mid-run-changes.md,numbers-vs-sql.md} (MIT, method only) — assignment checks (multi-variant units above 0.1% with at least 5, a flag shared by running experiments, metric filters that leave the denominator fixed, a code fallback logged as a variant) [port "units seen in more than one variant" "passes 0.1% of exposed units with at least 5" "two live tests on one flag" "changes who counts as converted, not who is in the experiment" "a code fallback logged as an exposure"]
---

# Experiment Readout

Run the gates in order; a gate that fails stops the readout or changes what it may claim.

## Iron laws

1. **Pre-register before looking.** Primary metric, guardrails, minimum detectable effect,
   planned sample and the ship / no-ship rule are written down before the first result is read.
   A metric or rule added after seeing data is exploration, labelled as such, never the verdict.
2. **Sample ratio mismatch halts the readout.** If the observed split fails the SRM test, no
   effect, segment or recommendation is reported — only the mismatch and where to look.
3. **A degraded guardrail is never presented as a win**, whatever the primary metric did.
4. **Name a mechanism only with evidence.** Every cause you state (bias, novelty, a bug, a
   segment) points to a config, a count or a log that shows it. No source, no mechanism.
5. **Waiting fixes noise, not bias.** Say which one you are looking at before advising "run
   longer".
6. **Every statistic comes from executed code.** χ², p-values, intervals, sample sizes, days and
   adjusted p-values come from `scripts/expstats.py` (standard library) or another tool run this
   session; show the command with its inputs. No figure worked out in your head.

## Gate 1 — Design (before launch)

- **Power.** From the baseline rate or variance, the MDE and daily eligible traffic, compute the
  sample and the days to reach it with `expstats.py power-prop --baseline <rate> --mde-rel <lift> --daily <eligible/day>` (or
  `power-mean --sd <sd> --mde-abs <effect>`), adding `--ratio <treatment/control>` for an
  uneven split. Halving the MDE quadruples the sample. To sanity-check by hand, read
  `references/assignment-and-power.md` first.
- **Not viable forces a decision.** If the needed run is longer than the team will wait, do not
  launch and hope: choose a larger MDE worth shipping for, a more sensitive metric, more traffic,
  or a non-randomised method (Gate 6). Record which.
- **Pick a small set of planned metrics.** One primary; guardrails that measure a different
  dimension of value (quantity vs quality, speed vs accuracy, short- vs long-term).
- **Write down how results will be read:** fixed horizon (once, at the planned sample) or a
  sequential method valid under repeated looks.

## Gate 2 — Sample ratio mismatch (first step of every readout)

- Chi-squared goodness-of-fit of observed counts per arm against the **designed** allocation
  (80/20 is not 50/50): `expstats.py srm --counts <per arm> --ratios <designed>`, with
  `--monitoring` while the test runs and `--checks <n>` for n periods. Never judge the split by
  eye; small skews on large samples are real.
- Check SRM per segment too (`expstats.py srm-segments --csv`, one row per segment).
- Threshold: the ai-analyst skills block at p ≤ 0.01 for a single final check and use
  p < 0.0005 while monitoring. **When checking many periods, days or segments, correct for the
  number of checks** (Bonferroni or Holm), or use that stricter threshold.
- On failure: stop. Report expected vs observed and where to look (read
  `references/assignment-and-power.md` first: it keeps the per-period check). Offer a clean time
  window only if the per-period check shows one.
- **Assignment checks, beside SRM** — read `references/assignment-and-power.md` and run all
  four: units in more than one variant (flag above 0.1% of exposed with at least 5), a flag
  shared with another live test, metric filters that drop events but not units, and code
  fallbacks logged as exposures. Any hit is classified in Gate 4.

## Gate 3 — Progress and population

State both before any number:
- **How far through the run:** age in days and exposed total as a share of the planned sample.
  Below plan, on a fixed-horizon design, the honest first line is that the result is not yet
  readable — still give the current estimate, labelled early, and when it becomes readable.
- **Who is exposed vs who the decision is about.** Compare exposure criteria and targeting with
  the population the ship decision covers. Default settings are not evidence they match; if
  nothing says who the decision is about, ask.

## Gate 4 — Bias or noise

Classify every oddity, each on its own line — never bundle them into one "wait" or "fix":

| kind | examples | what helps |
|---|---|---|
| systematic bias | SRM cause, users in both arms dropped unevenly, exposure logged differently per arm, mid-run split or metric change | fix the cause or re-run; waiting will not |
| statistical noise | small sample per arm, early flips in significance, one unusual day carrying the effect | reach the planned sample; read the time series |
| time effects | novelty (lift decays as users habituate), primacy (dip that recovers), seasonality | compare early vs late cohorts; run full weekly cycles |

**Peeking:** stopping when the result first looks significant inflates false positives unless
the design is sequential. "Target sample reached" says an effect of MDE size would likely have
shown; it is not significance.

## Gate 5 — Result, guardrails, multiplicity

- **Pick the test by metric shape.** Rates: `expstats.py prop-test`. Continuous metrics
  (revenue per user): `welch` from mean, sd and n per arm. **Ratio metrics** whose unit is not
  the randomisation unit (revenue per session, clicks per page view, users randomised): `ratio`
  (delta method); a per-row test understates the variance.
- **Segment check:** the total can reverse inside every segment when the segment mix differs
  between arms (Simpson's paradox). If it does, report the per-segment effects and the mix, not the total.
- **Multiple comparisons.** Reading many metrics, variants or segments, adjust p-values (Holm,
  `expstats.py holm`) or treat only the pre-registered primary as decisive. Five independent
  metrics at α = 0.05 give about a 23% chance of at least one false positive. An unplanned metric that turns significant is a hypothesis for the next test, not a ship reason.
- **Guardrails**, each classified:
  Pass or fail on the confidence-interval bound, not the point estimate (a non-inferiority check):
  - **clear** — the harm-side bound stays within the pre-agreed tolerance and the point estimate
    shows no harm; the win stands.
  - **trade-off** — the harm-side bound stays within the tolerance but the point estimate shows
    harm; ship with both sides stated.
  - **degraded** — the bound crosses the tolerance; not a win. Investigate or keep control.
  Default tolerance 10% relative (ai-analyst heuristic); tighten it for churn, safety or margin.
  Then a **net-impact line**: gain and loss in the same unit (revenue, users), with a note on guardrails whose damage arrives late (returns, churn).
- **Outcome:** ship (primary wins, guardrails clear) · ship with trade-off stated (within tolerance) · investigate (degraded guardrail) · abort (powered null or loss) · learn (underpowered null) · invalid
  (SRM or data fault).

## Gate 6 — Post-launch changes without randomisation

A before/after metric move is not an experiment. Answer it with at least two paths that differ in
method, source or counterfactual (comparison group, interrupted time series, holdout region),
run without seeing each other. Agreement
narrows the doubt but is not proof. State what would have to be true for the change to be noise.

## Output

```
Experiment: <name>   Decision rule (pre-registered): <rule, or "none — exploratory">
SRM: χ²=<x> p=<p> vs <designed split> → PASS / HALT  (periods checked: <n>, correction: <m>, segments: <pass/fail>)
Assignment: multi-variant <n> (<x>%) · shared flag y/n · metric-only filters y/n · fallback exposures y/n
Progress: day <d>, <n> of <planned> exposed (<x>%)   Design: fixed / sequential
Population: exposed = <who>; decision covers = <who>; match: yes / no / unknown
Primary: <metric> <effect> [<interval>] p=<p> (adjusted: <p_adj>) — test: <prop-test | welch | ratio>
Commands: <each expstats.py call with its inputs>
Guardrails: <metric> <change> → clear / trade-off / degraded  …
Net impact: +<gain> − <loss> = <net> in <unit>
Issues: <each> — bias / noise / time effect — evidence: <source>
Outcome: ship / ship with trade-off / investigate / abort / learn / invalid — <one-line reason>
```
