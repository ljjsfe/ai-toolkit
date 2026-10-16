---
name: adopt-or-build
description: Decide whether to adopt, trial, wait on, reject, migrate to or build instead of a technology, library or open-source project — size the cost of being wrong from the code, ground the verdict in this project and in outside evidence, price building and operating it, keep "keep what we have" and "do nothing" as real options, and return Incomplete rather than guess. Use for "should we use X", "is X better than what we built", build-vs-buy and migration questions.
version: 1.1.0
sources:
  - upstream/compound-engineering-plugin/skills/ce-pov (MIT) — two evidence floors, reversibility-tiered effort, keep-incumbent and do-nothing skepticism, Hold / Reject / Not-our-problem vocabulary, frozen view before a second opinion, "either is viable"
  - Thoughtworks Technology Radar, https://www.thoughtworks.com/radar/faq — four-ring ladder, Assess as a learn-only step
  - upstream/wondelai-skills/pragmatic-programmer/references/reversibility.md (MIT) — switching cost measured from fan-out, coupling, tests and config
  - upstream/optimnow-cloud-finops-skills/plugins/cloud-finops/skills/cloud-finops/references/finops-ai-self-hosted-vs-managed.md (CC BY-SA 4.0 — ideas only, no wording) — operating cost and team maturity as the self-hosting risk
---

# Adopt or Build

The question is never "is X good" but "is X right for this codebase and team now". An answer
that would read the same for any project is not an answer.

## 1. Size the cost of being wrong — from the code

Measure before choosing how deep to go. For the incumbent (or for where X would plug in), count:
files that import it, layers it reaches through, tests that would break on a swap, and config
keys and infra that name it. Then place it:

| switching cost | typical case | depth of check |
|---|---|---|
| hours | a library behind one interface, few importers | quick: one maintained-and-licensed check |
| days | an SDK or vendor API used in several modules | standard: add security record and exit path |
| weeks or more | database, framework, language, cloud or model vendor, live-data migration | deep: all rows of the list below |

Deep check: licence (and its change history); release cadence, open-issue trend and bus factor;
security advisories and how fast they were fixed; the concrete exit path and what it costs;
the running cost the team inherits.

## 2. Two floors, checked separately

- **Project floor.** Search first for a decision already made here (ADR, design doc, issue, a
  past attempt); one found can carry the verdict. Otherwise the verdict needs something you
  opened in this repo: for a replacement, where the current tool is wired in (`file:line`,
  manifest entry, issue); for something net-new, proof nothing does the job today and the spot
  and conventions X would have to fit. Nothing opened → **Incomplete — project not
  inspected**, listing what to open.
- **Outside floor.** Every external claim the verdict leans on (maturity, maintenance, licence,
  performance, security) is backed by a source you read, per `verified-research`. Missing →
  **Incomplete — external evidence unavailable**. Never a lower-confidence guess.
- Neither floor offsets the other. Excellent docs do not excuse an unread codebase.
- Anything asserted in the conversation ("X is 10x faster", "we tried that") is a lead to
  check, and goes under Unverified until checked.

## 3. Put every option on the table

- **Keep what we have** and **do nothing** are always listed; first write how the current
  stack would solve the problem, and how badly.
- **Build** is priced with what it costs to run, not just to write: maintenance, upgrades,
  on-call, incident time.
- **Self-hosting stateful infrastructure** (a database, queue or model serving) at the weeks
  tier: name in Why whether the team has run that kind of system in production. If it has not,
  that is the deciding risk, stated as such.
- How many unfamiliar technologies the stack already carries is `system-design`'s call (boring
  by default); cite it rather than redo it.
- **Migration** verdicts name the incremental path and the step after which going back stops
  being cheap.
- If you want a second model or reviewer, write your grade down first and give them the
  evidence, not your grade.

## 4. Grade

| grade | requires | next step it commits to |
|---|---|---|
| Adopt | both floors; and either switching cost in hours, or X already ran in production here (a Trial, another service) | use it as the default for this need |
| Trial | both floors; a slice where failure is contained | a time-boxed spike with pass/fail criteria and a named owner |
| Assess | both floors; fit plausible but untested | learning only — read, prototype off the main branch; no production code |
| Hold | both floors; X is unstable, the category is churning, or migration costs more than today's pain | start nothing new on it; existing use may stay; revisit date |
| Reject | both floors; an option in section 3 beats it | say which option won and why |
| Not our problem | an exposure question (CVE, deprecation, licence change) whose path does not reach this project | show the path that was checked |
| Incomplete | a floor failed; this is not a verdict | the list of what to check |

Reject is a complete answer, not a failure to decide, and an enthusiastic question does not
raise the grade. Weeks-tier switching cost never goes
straight to Adopt. When two worked-out options are both sound, answer **"either is viable"**
with the trade-offs instead of a weighted score that hides the tie.

## Output

```
Grade:        first line, from the table above
Size:         switching-cost tier and the counts behind it (importers, layers, tests, config)
Why:          2–4 deciding facts — project ones with file:line, outside ones with sources
Options:      keep / do nothing / build / X — one line each on why it lost or won
Cost:         migration effort, running cost incl. people and on-call, lock-in, exit path
Conditions:   what would move the grade, and the revisit date
Unverified:   conversation claims not yet checked
```
