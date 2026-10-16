---
name: adopt-or-build
description: Decide whether to adopt, trial, wait on, reject, migrate to or build instead of a technology, library or open-source project — size the cost of being wrong from the code, ground the verdict in this project and in outside evidence, price building and operating it, keep "keep what we have" and "do nothing" as real options, and return Incomplete rather than guess. Use for "should we use X", "is X better than what we built", build-vs-buy and migration questions.
version: 1.2.0
sources:
  - upstream/compound-engineering-plugin/skills/ce-pov (MIT) — two evidence floors, reversibility-tiered effort with a consequence override, precedent first, keep-incumbent and do-nothing skepticism, Hold / Reject / Not-our-problem vocabulary, frozen view before a second opinion, "either is viable"
  - Thoughtworks Technology Radar, https://www.thoughtworks.com/radar/faq — Radar-inspired labels; eligibility and production gates adapted for this toolkit
  - upstream/wondelai-skills/pragmatic-programmer/references/reversibility.md (MIT) — switching cost measured from fan-out, coupling, tests and config
  - upstream/optimnow-cloud-finops-skills/plugins/cloud-finops/skills/cloud-finops/references/finops-ai-self-hosted-vs-managed.md (CC BY-SA 4.0 — ideas only, no wording) — readiness factors for self-hosting, generalised here as toolkit policy
---

# Adopt or Build

## 1. Precedent, then size

Spend a few minutes looking for a decision already made here: ADR, design doc, issue, an
earlier attempt. One found either settles the question or becomes its starting point.

Then measure how expensive a wrong call is. For the incumbent (or for where X would plug in),
count files that import it, layers it reaches through, tests that would break on a swap, and
config keys and infra that name it:

| switching cost | typical case | depth of check |
|---|---|---|
| hours | a library behind one interface, few importers | quick: maintained and licensed |
| days | an SDK or vendor API used in several modules | add security record and exit path |
| weeks or more | database, framework, language, cloud or model vendor, live-data migration | deep: licence history, bus factor, advisory fix speed, exit path and its cost |

**Consequence override.** If X touches authentication, cryptography, personal data or
telemetry, a legal or licence obligation, a public API or contract, or changes data in a way
that cannot be undone, run the deep check whatever its switching-cost tier.

## 2. Two floors, checked separately

- **Project floor.** A prior decision from step 1 can carry the verdict. Otherwise it needs
  something you opened in this repo: for a replacement, where the current tool is wired in
  (`file:line`, manifest entry, issue); for something net-new, proof nothing does the job
  today and the spot and conventions X would have to fit. Nothing opened → **Incomplete —
  project not inspected**, listing what to open.
- **Outside floor.** Every external claim the verdict leans on (maturity, maintenance, licence,
  performance, security) is backed by a source you read, per `verified-research`. Missing →
  **Incomplete — external evidence unavailable**. Never a lower-confidence guess.
- Neither floor offsets the other. Excellent docs do not excuse an unread codebase.
- Anything asserted in the conversation ("X is 10x faster", "we tried that") is a lead to
  check, and goes under Unverified until checked.

## 3. Put every option on the table

- **Keep what we have** and **do nothing** are always listed; first write how the current
  stack would solve the problem, and how badly.
- **Self-hosting stateful infrastructure** (a database, queue or model serving) at the weeks
  tier — toolkit policy: assess operational readiness before recommending it. Is there a named
  owner; has anyone run this kind of system in production; do monitoring, backup and upgrade
  tooling exist; is the load steady enough to justify it; do the savings survive the staff
  time? Each gap goes under Cost; weigh them together rather than letting one decide.
- How many unfamiliar technologies the stack already carries is `system-design`'s call (boring
  by default); cite it rather than redo it.
- **Migration** verdicts name the incremental path and the step after which going back stops
  being cheap.
- If you want a second model or reviewer, write your grade down first and give them the
  evidence, not your grade.

## 4. Grade

| grade | requires | next step it commits to |
|---|---|---|
| Adopt | both floors and fit shown here: a passed Trial, use in another of our services, or — for hours-tier only — X wired into our code with its tests passing | use it as the default for this need |
| Trial | both floors; a slice where failure is contained | a time-boxed spike with pass/fail criteria and a named owner |
| Assess | both floors; fit plausible, not yet worth a Trial | a time-boxed investigation; no production dependency |
| Hold | both floors; X is unstable, the category is churning, or migration costs more than today's pain | start nothing new on it; existing use may stay; revisit date |
| Reject | both floors; an option in section 3 beats it | say which option won and why |
| Not our problem | an exposure question (CVE, deprecation, licence change) whose path does not reach this project | show the path that was checked |
| Incomplete | a floor failed; this is not a verdict | the list of what to check |

A cheap switching cost lowers how much fit evidence Adopt needs; it never removes the need.

Before sending, check the answer against the table:
- The grade matches its "requires" cell; the way the question was asked played no part.
- A Reject stands on its own: Options names the winner, and nothing more is owed.
- An Adopt at weeks tier names the Trial or production use it rests on.
- If Why cannot separate two options that both pass, the Grade line reads "either is viable"
  and Options gives the trade-off — no invented weights or totals.

## Output

```
Grade:        first line, from the table above
Size:         switching-cost tier, the counts behind it, and any consequence override
Why:          2–4 deciding facts — project ones with file:line, outside ones with sources
Options:      keep / do nothing / build / X — one line each on why it lost or won
Cost:         migration effort, running cost incl. people and on-call, lock-in, exit path
Conditions:   what would move the grade, and the revisit date
Unverified:   conversation claims not yet checked
```
