---
name: adopt-or-build
description: Decide whether to adopt, trial, wait on, reject, migrate to or build instead of a technology, library or open-source project — ground the verdict in this project's actual code and constraints, require outside evidence, keep "keep what we have" and "do nothing" as real options, and return Incomplete rather than guess when evidence is missing. Use for "should we use X", "is X better than what we built", build-vs-buy and migration questions.
version: 1.0.0
sources:
  - upstream/compound-engineering-plugin/skills/ce-pov (MIT) — project floor and external floor, grade vocabulary, skeptic stance, reversibility-tiered effort, freeze-before-panel, "either is viable"
---

# Adopt or Build

A verdict about a technology is a verdict about *this* project. Generic opinions about the
technology are not an answer.

## Iron laws

1. **Project floor.** The verdict rests on a verified fact about this project: the incumbent
   it would replace and where it is used (`file:line`, dependency, issue), or — for something
   new — confirmed absence of an incumbent plus where it would plug in and what conventions it
   must match, or a prior decision on the question. If the project was not inspected, the answer is **Incomplete — project not inspected**, with the list of what to inspect.
2. **External floor.** At least one outside source, actually read, supports each external claim
   the verdict depends on (maturity, maintenance, licence, performance, security record). If none can be checked, the answer is **Incomplete — external evidence unavailable**, not a
   guess at lower confidence.
3. **The two floors are independent.** Strong outside evidence never compensates for an
   uninspected project, and the reverse.
4. **"Keep what we have" and "do nothing" are always candidates,** and Reject is a complete
   answer, not a failure to decide. Do not let the enthusiasm of the question raise the grade.
5. **Claims made in the conversation are leads, not evidence,** until checked against the
   source.

## Effort follows reversibility

Decide first how expensive being wrong would be. A library behind one interface is cheap to
reverse — check quickly. A database, framework, language, vendor with lock-in, or a migration
of live data is expensive — check deeply: licence, maintenance activity and bus factor,
security history, migration path out, and the operating cost the team will carry.

## Steps

1. **Precedent first:** search for prior decisions — ADRs, design docs, issues, earlier attempts.
2. **Ground both sides** (project and outside), using `verified-research` rules for citations.
3. **Form your verdict before asking anyone else.** If a second model or reviewer is consulted,
   fix your own position first and do not show it to them, so their view is independent.
4. **Grade.**

## Grades

| grade | meaning |
|---|---|
| Adopt | proven fit for us; use it |
| Trial | promising; use it on a low-risk slice first; next step is a scoped spike |
| Hold | a deliberate decision to wait — unstable, migration cost exceeds current pain, or the category is moving fast |
| Incomplete | not a verdict: one of the two floors failed; lists what to check |
| Reject | not worth it for us |
| Not our problem | for an exposure question (vulnerability, deprecation) that does not reach this project |

When comparing two developed options that are both genuinely fine, say **"either is viable"**
and give the trade-offs. Do not manufacture certainty with a weighted scorecard.

## Output

```
Grade:              one of the grades above, in the first line
Why:                the 2–4 facts that decide it — project facts with file:line, outside facts with sources
Cost:               migration effort, running cost, lock-in, and the exit path
Conditions:         what would change the grade, and when to revisit
Unverified:         claims from the conversation that were not checked
```
