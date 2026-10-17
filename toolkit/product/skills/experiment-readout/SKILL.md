---
name: experiment-readout
description: "Design and read product A/B tests and post-launch metric changes so the conclusion survives scrutiny — fix decision rules and primary and guardrail metrics before looking, halt on sample ratio mismatch, check power and progress against the planned sample, separate bias from noise, classify guardrails, and correct for many metrics or segments. Use for test design, sample size, readouts, ship decisions and 'did this launch work?'; for evaluating AI agents use agent-evals. Also for 实验结果, AB测试 读数."
version: 1.0.1
sources:
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/srm-check (MIT) — SRM as a blocking gate, per-period SRM, investigation paths
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/guardrails (MIT) — clear / trade-off / degraded verdicts, net impact in shared units
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/experiment (MIT) — pre-registered config, not-viable power checkpoint, stricter SRM threshold while monitoring, Holm correction, outcome classes
  - upstream/ai-analyst-lab-ai-analyst/.claude/skills/triangulation (MIT) — independent methods for non-randomised changes; agreement is not proof
  - upstream/posthog-experiments/products/experiments/skills/diagnosing-experiment-health (MIT, method only) — age and exposed-population checks, systematic vs statistical, mechanisms need evidence
  - upstream/posthog-experiments/products/experiments/skills/diagnosing-experiment-health/references/interpretation.md (MIT, method only) — peeking, multiple comparisons, MDE and sample arithmetic, "target reached" is not a result
---

# Experiment Readout

A readout is only as good as the decision rule written before the data arrived. Run the gates
below in order; a gate that fails stops the readout or changes what it may claim.

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

## Gate 1 — Design (before launch)

- **Power.** From the baseline rate or variance, the MDE and daily eligible traffic, compute the
  sample and the days to reach it. Rule of thumb from the PostHog reference: per-arm sample is about
  16 × variance / (absolute effect)² — valid for α = 0.05 two-sided, 80% power and equal arms,
  with variance p(1−p) for a rate; use a proper power calculation otherwise. Halving the MDE
  quadruples the sample.
- **Not viable forces a decision.** If the needed run is longer than the team will wait, do not
  launch and hope: choose a larger MDE worth shipping for, a more sensitive metric, more traffic,
  or a non-randomised method (Gate 6). Record which.
- **Pick a small set of planned metrics.** One primary; guardrails that measure a different
  dimension of value (quantity vs quality, speed vs accuracy, short- vs long-term).
- **Decide how results will be read.** Fixed horizon (read once, at the planned sample) or a
  sequential method that stays valid under repeated looks. Write it down.

## Gate 2 — Sample ratio mismatch (first step of every readout)

- Chi-squared goodness-of-fit of observed counts per arm against the **designed** allocation
  (80/20 is not 50/50). Never judge the split by eye; small skews on large samples are real.
- Threshold: the ai-analyst skills block at p ≤ 0.01 for a single final check and use
  p < 0.0005 while monitoring. **When checking many periods, days or segments, correct for the
  number of checks** (Bonferroni or Holm), or use that stricter threshold — testing every week
  at 0.05 flags a clean experiment by chance.
- On failure: stop. Report expected vs observed, then where to look — assignment logic that
  excludes some users, treatment failing to load or log for one arm, pipeline loss, a restart
  or split change mid-run. Offer a clean time window only if the per-period check shows one.

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

- **Multiple comparisons.** Reading many metrics, variants or segments, adjust p-values (Holm)
  or treat only the pre-registered primary as decisive. Per the PostHog reference, five
  independent metrics at α = 0.05 give about a 23% chance of at least one false positive. An
  unplanned metric that turns significant is a hypothesis for the next test, not a ship reason.
- **Guardrails**, each classified:
  Pass or fail on the confidence-interval bound, not the point estimate (a non-inferiority check):
  - **clear** — the harm-side bound stays within the pre-agreed tolerance and the point estimate
    shows no harm; the win stands.
  - **trade-off** — the harm-side bound stays within the tolerance but the point estimate shows
    harm; ship with both sides stated.
  - **degraded** — the bound crosses the tolerance; not a win. Investigate or keep control.
  The ai-analyst default tolerance is 10% relative — a heuristic; tighten it for churn, safety
  or margin. Then a **net-impact line**: gain and loss in the same unit (revenue, users), with
  a note on guardrails whose damage arrives late (returns, churn).
- **Outcome:** ship (primary wins, guardrails clear) · ship with trade-off stated (within tolerance) · investigate (degraded guardrail) · abort (powered null or loss) · learn (underpowered null) · invalid
  (SRM or data fault).

## Gate 6 — Post-launch changes without randomisation

A before/after metric move is not an experiment. Answer it with at least two paths that differ in
method, source or counterfactual (comparison group, interrupted time series, holdout region),
run without seeing each other. Explain disagreement by populations or assumptions; agreement
narrows the doubt but is not proof. State what would have to be true for the change to be noise.

## Output

```
Experiment: <name>   Decision rule (pre-registered): <rule, or "none — exploratory">
SRM: χ²=<x> p=<p> vs <designed split> → PASS / HALT  (periods checked: <n>, correction: <m>)
Progress: day <d>, <n> of <planned> exposed (<x>%)   Design: fixed / sequential
Population: exposed = <who>; decision covers = <who>; match: yes / no / unknown
Primary: <metric> <effect> [<interval>] p=<p> (adjusted: <p_adj>)
Guardrails: <metric> <change> → clear / trade-off / degraded  …
Net impact: +<gain> − <loss> = <net> in <unit>
Issues: <each> — bias / noise / time effect — evidence: <source>
Outcome: ship / ship with trade-off / investigate / abort / learn / invalid — <one-line reason>
```
