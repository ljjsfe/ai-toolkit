---
name: pricing
description: "Set, test and change a price from evidence — require willingness-to-pay evidence (payment requests, top-box purchase intent, a priced fake door) before naming a number, pick the value metric before tiers, never average willingness to pay across segments, sort features into leaders, fillers and killers, and roll increases out to new customers first. Use for what to charge, tiers, free vs paid, raising prices and pricing-page reviews; for competitor prices use market-scan. Also for 定价, 涨价, 收费方案."
version: 1.0.0
sources:
  - upstream/wondelai-skills/monetizing-innovation/SKILL.md (MIT) — value metric before level, segment by willingness to pay, zero pushback as the under-pricing signature
  - upstream/wondelai-skills/monetizing-innovation/references/wtp-conversations.md (MIT) — top-box scoring, haircut stated numbers, curve not average, red flags in answers
  - upstream/wondelai-skills/monetizing-innovation/references/packaging-tiers.md (MIT) — leader/filler/killer thresholds, killers never inside a tier price
  - upstream/aidevgtm-gtm-cofounder/skills/12-pricing/SKILL.md (MIT) — deflected payment requests as the strongest signal, metric then packaging then number, value-multiple heuristic
  - upstream/marketingskills/skills/pricing/SKILL.md (MIT) — new-customers-first rollout, small existing cohort, grandfathering as a transition, the ultra-low-price trap
  - upstream/marketingskills/skills/pricing/references/pricing-page-teardown.md (MIT) — reviewing the page for AI agents as well as humans
---

# Pricing

A price is a claim about how much a specific customer values a specific outcome. Treat it as
a hypothesis with evidence attached, decided in a fixed order, and changed like a deploy.

## Iron laws

1. **No number without willingness-to-pay evidence.** Name the evidence before the price. An
   armchair estimate ("feels like $29", "competitors charge $30", "our cost is $8 so $12") is
   not evidence. If none exists, the output is the cheapest test that would produce some — not
   a price. Gathering it (interviews, outreach) belongs to customer-discovery.
2. **Decide in order: value metric, then packaging, then the number.** Choosing tier prices
   before deciding what you charge *per* locks in the wrong unit, and no tier design repairs it.
3. **Never average willingness to pay across segments.** Look at the distribution first. Two
   clusters (say, many near $20 and some near $120) mean two offers; a price at the mean fits
   nobody and loses both groups.
4. **Zero pushback means too cheap — once there is enough of it.** If a meaningful number of
   prospects in one segment (not two or three friendly ones) accept without hesitation and the
   win rate is near total, the price is below the value; test a higher one through Step 5
   rather than celebrating.
5. **A price increase is a staged rollout, not a switch.** New customers first, then a small
   cohort of existing ones, then waves. Grandfathering is a dated transition, never forever.

## Step 1 — Grade the evidence

| strength | evidence | how to read it |
|---|---|---|
| strongest | payment already taken, or "can we pay you for X" requests received or turned away | reply to each: what does not having it cost them, and what could they get approved |
| strong | a priced fake door, pre-order, deposit or pilot / letter of intent at a named price | behaviour at a stated price; count only completed commitments |
| medium | 1–5 purchase-probability answers at a stated price | count only 5s, and discount those; 4s are maybes; 1–3 are no. Read how the share of 5s falls across 2–3 price points, not the raw share |
| weak | stated acceptable / expensive / prohibitive prices | a ceiling, not a price: stated numbers run high, so haircut them and confirm with behaviour |
| not evidence | team opinion, a competitor's list price, cost-plus | a competitor's price is a reference point in the buyer's head (market-scan), not their valuation |

Distrust the data when answers cluster on your current or a competitor's price (they are
quoting the market back), when very different customers give identical answers (the concept
description is leading them), or when every feature is "very valuable" (switch to forced
trade-offs: ranking or allocating 100 points). Sample-size heuristic from the source: 15–25
B2B conversations per segment; under 10, treat results as directional.

## Step 2 — Value metric

Charge per the unit that grows as the customer gets more value, that they can predict, and
that fits in one sentence ("we charge per monitored endpoint").

- Value from more **people** collaborating → per seat. Value from more **usage** (calls,
  events, compute) → usage, with a floor and caps or alerts so the bill stays predictable.
  Platform fee plus usage is a normal hybrid.
- Wrong-metric test: does the metric tax the behaviour you want more of? Per-seat on a
  machine-driven product makes teams share logins; uncapped usage on a team tool makes them
  ration access.

## Step 3 — Packaging: leaders, fillers, killers

Classify each feature **per segment** — the same feature can be a leader for one and a
killer for another (on-prem: killer for small teams, leader for banks).

| class | signal (source thresholds) | what to do |
|---|---|---|
| leader | top-5 in purchase ranking for ≥40% of the segment, positive extra WTP | it is the reason a tier exists; put a taste in the lower tier, not the whole thing |
| filler | rarely ranked, near-zero extra WTP, no objection | round out and separate tiers cheaply |
| killer | ≥20% of the segment objects to paying for it | never inside a tier price: optional add-on, a tier where it leads, or cut |

Fence tiers with leaders first and quantity limits second. Free tier: give away individual value, charge for what a company needs (team, scale, and
enterprise controls such as SSO, audit logs, compliance, support). Baseline security, privacy
and data export belong in every tier.

## Step 4 — The number

Anchor on the value delivered, not your cost (cost is a floor). Heuristic from the source:
the customer should get roughly 10x the price in value; well below ~3x and the purchase
does not survive a budget review. Resist an ultra-low entry price to reduce friction: it
buys sign-ups from people who would never pay a real price and is far harder to raise
later than to start higher. If choosing the number does not make the founder slightly
uneasy, check law 4.

## Step 5 — Changing a price

1. Raise for **new sign-ups only** and watch conversion for a cycle — no anchor, no
   relationship at stake, a clean read.
2. Then move a **small existing cohort** (the source uses 5–10%); watch churn and support
   volume for a cycle before widening in waves.
3. **Price the grandfathering**: (target − current monthly price) × 12 × grandfathered accounts is what
   permanence costs per year. Set an end date; soften with notice, an annual lock-in offer or a
   one-time credit.
4. Announce the value shipped first, the number second, months ahead. Some churn is expected;
   it is usually the most price-sensitive, highest-support accounts.

## Step 6 — Review the pricing page (humans and agents)

- **Humans:** who each plan is for, how plans differ, a recommended tier, real prices
  shown, limits and overages stated, decidable quickly.
- **AI agents that shortlist tools:** prices and per-tier limits as text in the HTML, not in
  images, PDFs, JavaScript-only renders or behind a login; at least a starting price where a
  tier says "contact us"; FAQ answers (limits, cancellation, trial) in text; product/offer
  structured data; AI search crawlers not blocked. Test: fetch the rendered text and ask a
  model "what are the plans and prices?" — a wrong answer is a finding (a heuristic, not
  proof every agent fails).

## Output

```
Evidence: <items, each with its grade from Step 1> | gaps: <missing> → test: <cheapest next>
Segments: <cluster: WTP range, observable markers> (no averaged figure)
Value metric: "we charge per ___" | grows with value: y/n | predictable: y/n
Packaging: <tier: leaders | fillers> ; killers → <add-on / moved / cut>
Price: <tier: number> | basis: <value math + evidence> | pushback seen: <yes/no>
Change plan (if any): new-only from <date> → cohort <n%> → waves; grandfather ends <date>;
  cost of permanent grandfathering: <$/yr>
Page review: humans <gaps> | agents <gaps> | top fix: <one line>
Hand-offs: evidence gathering → customer-discovery; competitor prices → market-scan
```
