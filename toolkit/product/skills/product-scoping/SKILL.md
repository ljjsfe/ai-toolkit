---
name: product-scoping
description: Scope a feature or product decision before building — choose an explicit ambition level, frame needs as opportunities rather than features, generate at least three solutions before picking one, name what users would use instead, and red-team the plan's load-bearing assumptions into "fails if" conditions with this week's cheapest test. Use when deciding what to build, what goes into a first version, prioritising features, writing a lean PRD, or stress-testing a product plan.
version: 1.0.0
sources:
  - upstream/gstack/plan-ceo-review (MIT) — four explicit scope modes chosen before review
  - upstream/phuryn-pm-skills/pm-product-discovery/skills/opportunity-solution-tree (MIT) — opportunities not features, three solutions per opportunity, opportunity score
  - upstream/phuryn-pm-skills/pm-execution/skills/create-prd (MIT) — value proposition with an explicit alternatives slot; findings enter the PRD only if they change a decision
  - upstream/phuryn-pm-skills/pm-execution/skills/strategy-red-team (MIT) — load-bearing claims, steelman then attack, "fails if", ranked cheapest tests, no manufactured doubt
---

# Product Scoping

Most scoping failures are one of three: the scope level was never chosen, the first idea was
built, or the plan rested on an assumption nobody tested.

## Iron laws

1. **Choose the ambition level out loud before reviewing scope:**

   | mode | when | what it means |
   |---|---|---|
   | expand | new product or system | describe the 10× version, then cut back to what the first version must prove |
   | selective | adding a capability | keep the core; offer each extension with its cost and risk |
   | hold | a fix or refactor | no additions; go deep on failure paths and edge cases |
   | reduce | too big for the time or team | strip to the smallest version that proves the point |

   Every scope change after that is an explicit decision, not drift.
2. **Opportunities before features.** State the need from the user's side ("I struggle to…",
   "I wish I could…") and the outcome it moves. A requested feature is one possible solution.
3. **At least three solutions per opportunity** before choosing one — including the cheapest
   non-software option and "do nothing".
4. **Name the alternative.** For each target user: what they use today without this, and why
   they would switch. If you cannot say why they would switch, the scope is not ready.

## Step 1 — Map

One measurable outcome → 3–7 opportunities → rank them (a heuristic such as importance ×
(1 − current satisfaction), or an honest qualitative ranking) → top 2–3 → three or more
solutions each.

## Step 2 — Cut the first version

For the chosen solution: what is in, what is explicitly out ("not in scope" list), what the
first version must prove, and how you will know (the metric and the threshold).

## Step 3 — Red-team the plan

1. List what the plan asserts about users, market, mechanism, constraints and timeline. Keep
   only **load-bearing** claims — if false, the plan fails.
2. For each, write the strongest case that it is true, then attack that version.
3. Write each surviving risk as **"Fails if …"**, concrete and falsifiable.
4. Rank by impact × likelihood of being wrong × cheapness to test. The top one is what to
   test this week.
5. If a claim is well supported, say so. Do not invent weaknesses to look rigorous.

## Output — lean PRD

```
Outcome and metric:
Mode:                     expand / selective / hold / reduce — and why
Users and alternatives:   who · what they use now · why they would switch
Opportunities (ranked):
Chosen solution:          and the two it beat, with why
In / out of scope:
Kill-assumptions (3–5):   claim · fails if · evidence to get this week · kill criterion · cheapest test
What holds up:
```

Research that does not change a decision stays out of the PRD; put it in notes. Assumptions
that need evidence from real people go to `customer-discovery`.
