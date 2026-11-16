---
name: customer-discovery
description: >-
  Validate demand with real users before building: pre-written kill conditions, past-behaviour-only
  interview scripts, commitment-graded evidence per segment, and priced fake-door/concierge tests.
  Trigger on 用户访谈, 验证需求, "would people pay?". Market map: market-scan; scope: product-scoping.
version: 1.2.1
sources:
  - upstream/sreshtalluri-mom-test/skills/mom-test (MIT) — past-behaviour rule, reflexes for bad data, evidence ladder [port "ask only about past and current behaviour" "grade every fact on the ladder"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-check-questions (MIT) — question failure tests and reframe shapes [port "rewrite it into one of the shapes"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-debrief (MIT) — 19-rung ladder, facts vs interpretations, assumption statuses, segment split in batch mode [port "split notes into **facts**" "tag each qualifying fact" "find the attribute that splits them"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-debrief (MIT) — the full 19-rung ladder (collapsed here to three tiers) and the 15-row interview scorecard [port "emotional recounting of that incident" "where the scorecard changes the grading" "does not count toward the three-interview bar"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-gate (MIT) — per-segment qualifying count, 3-interview bar, commitment needed for a solution [port "three or more distinct interviews in the segment" "count per segment, never average"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-memory/templates/assumptions.md (MIT) — assumption row with segment and kill condition [port "write the assumption and its kill condition"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-memory (MIT) — a persistent discovery folder with append-only interview files, rung tags and status merge rules, so the ledger survives across sessions [port "killed is sticky; within one call weakened beats supported" "interviews/ and decisions.md are append-only" "re-derives evidence from the"]
  - upstream/eltntawy-idea-discovery-playbook/skills/behavior-led-validation (MIT) — email-only waitlist does not validate; payment as strongest signal [port "an email-only waitlist"]
  - upstream/eltntawy-idea-discovery-playbook/skills/validation-experiments (MIT) — technique picker, priced CTA, success and fail thresholds, sequence, ethical fake door [port "then concierge, then a small wizard of oz" "5–15% visitor-to-signup" "say honestly that it is not built yet"]
  - upstream/gstack/office-hours/sections/phase-2a-startup-diagnostic.md (MIT) — demand-reality and status-quo questions; waitlists and interest are not demand [port "also ask the status-quo question"]
  - upstream/phuryn-pm-skills/pm-product-discovery/skills/brainstorm-experiments-new (MIT) — "at least X% of Y will do Z" hypothesis line [port "will <action>"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-roleplay (MIT) — practice mode with a hidden persona sheet, difficulty 1–5, answer rules that reward past-behaviour questions, debrief on the scorecard [port "build a persona sheet privately" "has no real problem, is warm, does not decide" "asked about a specific past instance, current behaviour, cost or what they tried" "mark each hidden fact found or missed"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-prep (MIT) — one-page prep sheet (riskiest assumption, scary question first, broad opener, commitment to ask for) [port "scary question (ask in the first five minutes)" "commitment to ask for, with a date"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-next-question (MIT) — classify the statement, list the gaps, rank follow-ups by stage [port "classify the statement" "rank the follow-ups by stage" "never from its topic"]
  - upstream/sreshtalluri-mom-test/skills/mom-test-outreach (MIT) — five-part cold message, no product link, intro, follow-up, one-attempt revival [port "never link to or describe the product" "one honest unknown" "one attempt only"]
  - upstream/phuryn-pm-skills/pm-market-research/skills/survey-design (MIT) — is a survey the right tool, start from the decision, behaviour questions, pilot, honest sample and non-response reporting [port "a survey counts; it does not explain" "every survey question maps to one research question" "send it to a small group first" "how many answered (the response rate)"]
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

The ledger lives on disk so it survives sessions: `./discovery/` when the repo has one (shared
with the team), else `~/.discovery/<idea>/`, or `$DISCOVERY_DIR`. `scripts/discovery.py`
(standard library) owns it: `init`, `assume` (new id, never renumbered), `interview` (one file
per conversation, named date-role, never a person's name, never overwritten), `verdict`
(applies the merge rule), `decide` (append-only gate log) and `status` (counts, riskiest open
row, and every evidence cell that disagrees with the `[A<n>+]` / `[A<n>-]` tags in the
interview files). Merge rule: killed stays killed; inside one debrief weakened beats
supported; a later debrief overrides an earlier one; an untouched assumption keeps its status.
Ask before keeping the folder in git — it holds real quotes.

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
**interpretations** (anyone's guess about meaning). Before grading, read
`references/ladder-and-scorecard.md` (its 19 rungs break ties; its 15-row interview scorecard
can disqualify a leading or pitched interview from the count), then grade each fact on a tier
here and on its rung there:

| tier | signals | counts as |
|---|---|---|
| no evidence | compliment, opinion, "I would", a hypothetical price, feature request, generic complaint, prompted agreement | nothing |
| problem is real | dated past incident, named consequence, specific objection, active search, workaround they built, time or money already spent | support for a problem assumption |
| solution is wanted | dated time committed to you, intro to the decision-maker, resources committed, money paid, pre-order, signed letter of intent | support for a solution assumption |

Tag each qualifying fact to an assumption as supporting or contradicting (in the interview
file as `[A3+] rung 13 "quote"`), then update the
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

A survey counts how common something is; it does not explain why. When a survey is proposed,
or before writing, reading or reporting one, read `references/survey-design.md`.

## Step 6 — Practice, prep and outreach

- **Practice:** the agent plays a customer with hidden facts at difficulty 1–5, then grades
  the founder on the 15-row scorecard. A practice run is never evidence for the ledger.
- **Prep:** a one-page sheet per conversation — riskiest assumption, the scary question asked
  first, a broad opener, and (solution stage) the commitment to ask for, with a date.
- **Next question:** classify what the customer just said, list what is still missing, and
  rank follow-ups by stage.

Before rehearsing, preparing a call or choosing a follow-up, read `references/practice.md`
(persona rules, prep sheet, ranking table). Before writing cold outreach, an intro or a
follow-up message, read `references/outreach.md` (message rules).

Where demand might exist: market-scan. What goes in the first version: product-scoping.
Price-point evidence: pricing.

## Output

```
Ledger:     id · assumption · segment · kill condition · status · deciding fact
Questions:  original → verdict → failure shape → rewrite   (most common failure, one line)
Debrief:    facts | interpretations | per-fact tier, rung, assumption tag | scorecard /75, two lowest rows
Stored:     folder path · files written · status mismatches (none / list)
Segments:   segment · interviews · problem-tier count · commitments · contradicting
Gate:       BUILD | BUILD AS EXPERIMENT | DO NOT BUILD — because <counts>
Next:       test or conversations · hypothesis "≥X% of Y do Z" · success / fail threshold
Result:     what is validated, or "nothing validated yet" and the riskiest open assumption
```
