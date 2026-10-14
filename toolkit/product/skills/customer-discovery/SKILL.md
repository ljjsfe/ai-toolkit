---
name: customer-discovery
description: "Validate an idea with real people before building — kill conditions written before evidence, interview questions about past behaviour only, an evidence ladder up to commitments, counts per segment, a build gate, and priced fake-door or concierge tests with thresholds. Use for customer interviews, discovery scripts, interview notes and \"would people pay for this\"; for where demand exists use market-scan, for what to build product-scoping. Also for 用户访谈, 验证需求."
version: 1.0.0
sources:
  - upstream/sreshtalluri-mom-test/skills/mom-test (MIT) — past-behaviour rule, reflexes for bad data, evidence ladder
  - upstream/sreshtalluri-mom-test/skills/mom-test-check-questions (MIT) — question failure tests and reframe shapes
  - upstream/sreshtalluri-mom-test/skills/mom-test-debrief (MIT) — 19-rung ladder, facts vs interpretations, assumption statuses, segment split in batch mode
  - upstream/sreshtalluri-mom-test/skills/mom-test-gate (MIT) — per-segment qualifying count, 3-interview bar, commitment needed for a solution
  - upstream/sreshtalluri-mom-test/skills/mom-test-memory/templates/assumptions.md (MIT) — assumption row with segment and kill condition
  - upstream/eltntawy-idea-discovery-playbook/skills/behavior-led-validation (MIT) — email-only waitlist does not validate; payment as strongest signal
  - upstream/eltntawy-idea-discovery-playbook/skills/validation-experiments (MIT) — technique picker, priced CTA, success and fail thresholds, sequence, ethical fake door
  - upstream/gstack/office-hours/sections/phase-2a-startup-diagnostic.md (MIT) — demand-reality and status-quo questions; waitlists and interest are not demand
  - upstream/phuryn-pm-skills/pm-product-discovery/skills/brainstorm-experiments-new (MIT) — "at least X% of Y will do Z" hypothesis line
---

# Customer Discovery

The goal is facts about the customer's past, not opinions about your future. Polite people
will tell you the idea is good; only what they already did, or now commit to, counts.

## Iron laws

1. **Write the assumption and its kill condition before collecting any evidence.** Each
   load-bearing assumption gets: one falsifiable sentence, the segment it is about, the
   observation that would kill it, and a status (untested / supported / weakened / killed).
   A kill condition written after the interviews is a rationalisation.
2. **Ask only about past and current behaviour.** Every question is about their life, in the
   past or present tense, and answerable with an event, a number or a name. Audit every
   script before use (table below); a question that fails is rewritten, not softened.
3. **Grade every fact on the ladder; opinions are zero.** Compliments, intentions,
   hypothetical prices, feature requests and agreement you prompted carry no evidence however
   enthusiastic. Weight is what producing the signal cost the customer.
4. **Count per segment, never average.** Mixed answers across people mean the segment is too
   wide. Find the attribute that splits them (role, size, tool, trigger) and count within it.
5. **The build gate holds until the evidence exists.** If the user builds anyway, record it as
   an unvalidated bet with the missing evidence named — do not describe it as validated.
6. **"Nothing validated" is a valid result.** Report it plainly. Do not upgrade weak signals
   to fill the report.

## Step 1 — Assumption ledger

| id | assumption (falsifiable) | segment | kill condition | status | evidence |
|---|---|---|---|---|---|

Order by riskiest first: the one that, if false, ends the idea. A row nothing touched after
the interviews means the question was never asked — that is a gap, not support.

## Step 2 — Audit the questions

A question fails if any of these is true; rewrite it into one of the shapes on the right.

| failure shape | rewrite toward |
|---|---|
| future or hypothetical (would, could, imagine, if) | "When did that last happen? Walk me through it." |
| asks for an opinion or rating | "How do you handle that today?" |
| your product is the subject (pitching) | "What have you tried? Why didn't it stick?" |
| leading — names the problem or suggests the answer | open broad; let them rank their problems |
| fishing for compliments, politely yes-able | "What did it cost you, in hours or money?" |
| generic — invites "always / often" | "How many times last month?" |
| "would you buy / pay?" | an ask: a dated trial, an intro, a pre-order |

Also ask the status-quo question: what do they do now, even badly, and what does that cost?
"Nothing, there's no solution" usually means the pain is not sharp enough.

## Step 3 — Debrief on the ladder

Split notes into **facts** (what the customer said or did, near-verbatim) and
**interpretations** (anyone's guess about meaning). Grade each fact:

| tier | signals | counts as |
|---|---|---|
| no evidence | compliment, opinion, "I would", a hypothetical price, feature request, generic complaint, prompted agreement | nothing |
| problem is real | dated past incident, named consequence, specific objection, active search, workaround they built, time or money already spent | support for a problem assumption |
| solution is wanted | dated time committed to you, intro to the decision-maker, resources committed, money paid, pre-order, signed letter of intent | support for a solution assumption |

Tag each qualifying fact to an assumption as supporting or contradicting, then update the
ledger status with the fact that moved it. A solution-stage meeting with no commitment or
concrete next step is a failed meeting — log it as one.

## Step 4 — The build gate

Evaluate on the mapped assumption with the weakest evidence, counted in its segment only:

1. Assumption killed and the plan only works if it were true → **do not build**; talk to more
   people or change the plan.
2. Three or more distinct interviews in the segment with a problem-tier fact, and (for a
   solution) at least one solution-tier commitment → **build**.
3. Three or more problem-tier interviews, no commitment yet → **build as an experiment** —
   the problem is real; the solution is not yet wanted.
4. Otherwise → **do not build**; run `3 − qualifying` more conversations (minimum one),
   anchored to the kill condition.

The three-interview bar comes from the mom-test gate; treat it as a floor, not proof.

## Step 5 — Behaviour tests

Write the hypothesis as "at least X% of <segment> will <action>", with success and fail
thresholds set before launch. The price must be shown for any willingness-to-pay test.

| test | proves | does not prove |
|---|---|---|
| priced fake door / landing | demand for a specific offer at a price | retention, workflow fit |
| concierge (deliver by hand, roughly 5–10 customers) | what to build, their language, will they pay | unit economics |
| wizard of oz (manual backend behind a real front) | the workflow and UX | first read on abstract demand |
| pre-sale / design partner | willingness to pay and delivery commitment | — |

Sequence: priced fake door, then concierge, then a small wizard of oz, then build. An
email-only waitlist, views, likes and unqualified clicks do not validate demand. Calibration
heuristic from the upstream (adjust per segment): 5–15% visitor-to-signup can be healthy on
warm niche traffic; under 1% on cold paid traffic is often a kill signal for that offer. After
the call to action, say honestly that it is not built yet.

Where demand might exist: market-scan. What goes in the first version: product-scoping.
Price-point evidence: pricing.

## Output

```
Ledger:     id · assumption · segment · kill condition · status · deciding fact
Questions:  original → verdict → failure shape → rewrite   (most common failure, one line)
Debrief:    facts | interpretations | per-fact tier and assumption tag
Segments:   segment · interviews · problem-tier count · commitments · contradicting
Gate:       BUILD | BUILD AS EXPERIMENT | DO NOT BUILD — because <counts>
Next:       test or conversations · hypothesis "≥X% of Y do Z" · success / fail threshold
Result:     what is validated, or "nothing validated yet" and the riskiest open assumption
```
