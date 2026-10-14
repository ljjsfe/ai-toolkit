---
name: system-design
description: "Design a new system or re-size one with numbers before boxes, and review an existing design or plan without inventing findings — state load, growth, an uptime target and separate RPO and RTO; estimate capacity and cost per request; choose stores and services against those numbers and grade their lock-in; name failure domains and hot spots. In review mode: check it does not already exist, apply named complexity tests (boring by default, essential vs accidental, deletion and seam tests), and allow \"fine as is\". Use for system design, architecture, capacity, cloud cost, and technical design or implementation-plan reviews such as \"is this over-complicated?\"; for a diff use code-review; for an open-ended design conversation use design-discussion."
version: 1.0.0
sources:
  - upstream/jeffallan-claude-skills/skills/architecture-designer/references/nfr-checklist.md (MIT) — numeric non-functional requirements before design; RPO and RTO as separate targets
  - upstream/everything-claude-code/skills/redis-patterns (MIT) — cache stampede named with a concrete fix
  - upstream/jeffallan-claude-skills/skills/cloud-architect/references/multi-cloud.md (MIT) — lock-in tier per service type; multi-cloud only for a named exit scenario
  - upstream/gstack/{plan-eng-review,review} (MIT) — named review battery; two-real-callers rule for extraction
  - upstream/compound-engineering-plugin/skills/ce-doc-review (MIT) — adequate needs no change; name the downstream cost
  - upstream/mattpocock-skills/skills/engineering/{domain-modeling,triage,codebase-design} (MIT) — decision-record gate, prior-solution search, deletion and seam tests
  - upstream/optimnow-cloud-finops-skills (CC BY-SA 4.0 — ideas only, no wording) — find waste from billing data per resource type
  - authored for this toolkit from a stated need (capacity and unit-cost estimation) — the estimation worksheet and the hot-spot checklist
---

# System Design

Two modes. **Design** (new system, new load): numbers first, the boxes follow from them.
**Review** (existing design, plan or refactor): find what will hurt later — see the review
section at the end.

## Iron laws

1. **Numbers before boxes.** Before any component: users (total, daily active, concurrent),
   requests per second (average and peak, and the peak-to-average ratio), data volume now and
   its growth rate, read/write mix, latency target (p95/p99), and resilience as **three numbers**: an uptime target (SLO), RPO (how
   much data may be lost in a disaster) and RTO (how long recovery may take). An uptime
   figure alone says nothing about data loss or recovery.
2. **Every major choice cites the number that drove it.** "Postgres, because 400 writes/s and
   200 GB in two years fit one primary with replicas" — not "Postgres, because it is reliable".
3. **Cost is a design output.** Produce cost per request (or per user, per tenant) and per
   month at today's load and at the growth target, before recommending the design.
4. **Unknown numbers are assumptions, written as such,** with the value used and what would
   change if it is off by 10×.

## Step 1 — Estimate (show the arithmetic)

| quantity | how |
|---|---|
| peak RPS | daily requests ÷ 86,400 × peak ratio |
| storage | records/day × bytes/record × retention × replication factor (+ indexes, backups) |
| bandwidth and egress | responses/s × response size; egress to the internet and across regions is billed — often the surprise line item |
| LLM cost | requests × (uncached input × input price + cache-read tokens × read price + cache-write tokens × write price + output × output price); turns and retries per request multiply it; take cache rates from measured usage (see `agent-architecture`) |
| monthly total | sum per component at current load and at the 12-month target |

Use current published prices for the chosen provider and region, dated. For an existing
system, start from the billing export (e.g. the AWS Cost and Usage Report) grouped by resource
and usage type — data-transfer and NAT-gateway processing charges are common hidden waste —
rather than from the architecture diagram.

## Step 2 — Choose against the numbers

For each store, queue, cache and compute option: the requirement it meets, the number it is
sized for, and when it stops fitting (the next threshold). Prefer managed services, and grade
each one's lock-in:

| lock-in | examples | require |
|---|---|---|
| low | VMs, Kubernetes, object storage, standard Postgres/MySQL | nothing extra |
| medium | managed proprietary databases, queues with proprietary APIs | an abstraction only where switching is plausible |
| high | proprietary serverless platforms, proprietary AI/ML services | a named exit scenario if portability is claimed (data residency, a specific better service, acquisition, cross-provider DR) |

"Avoid lock-in" with no exit scenario is not a reason for multi-cloud — portability has a
real cost.

## Step 3 — Break it on paper

- **Failure domains:** what fails together (one zone, one region, one provider dependency, one
  shared database). Does the design meet the uptime target, RPO and RTO when each fails?
- **Hot spots:** hot partition keys (one tenant, one celebrity, one time bucket); cache
  stampede when a hot key expires — name the fix (a lock with re-check after acquiring it, or
  early probabilistic refresh); thundering herd on restart or deploy; retry storms.
- **Limits:** provider quotas and rate limits (API, LLM tokens per minute, connections), cold
  starts on serverless paths with a latency target, connection pool sizes against instance
  counts.

## Review mode — an existing design, plan or refactor

1. **"This is fine" is a valid outcome.** Judge whether the document would guide correct work,
   not how detailed it is; do not invent findings.
2. **Check it does not already exist** — in this codebase, a dependency, or a prior rejected
   proposal — searching by concept, not by the proposal's wording.
3. **Every finding names its cost:** what breaks, slows or becomes hard, and when.
4. **Most consequential first.** In an interactive session raise them one at a time; otherwise
   list them in that order. Never finalise a plan that silently resolves open findings.
5. Check the numbers the design states, if any; review mode does not demand a full estimate.

| test | ask |
|---|---|
| boring by default | new technology where known technology would do? A team affords about three innovations — which is this spending? |
| essential vs accidental | which complexity comes from the problem, which from the solution? Cut the second |
| deletion test | if this layer or module were deleted, would complexity vanish or move into callers? |
| seam test | one adapter behind an interface is a hypothetical seam; two (often production + a test fake) make it real |
| depth | does each module hide a lot behind a small interface, or expose nearly as much as it implements? |
| extraction | shared code needs at least two verified real callers today, not code that looks similar |

Record a decision only when it is hard to reverse, would surprise a future reader, and involved
a real trade-off.

## Output

Review mode: verdict (proceed / proceed with changes / rethink) · findings by consequence ·
what already exists · open questions that change the design. Design mode:

```
Requirements:     the numbers, with assumptions marked
Estimate:         the arithmetic table and monthly cost now / at target, cost per request
Design:           components, each with the number it is sized for and its next threshold
Lock-in:          per managed service, with exit scenario where claimed
Failure analysis: failure domains vs RPO/RTO · hot spots and fixes · limits hit first
Open questions:   numbers that would change the design
```
