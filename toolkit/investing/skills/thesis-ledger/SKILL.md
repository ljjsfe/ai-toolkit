---
name: thesis-ledger
description: "Write an investment thesis as dated, falsifiable claims and track it — tie each claim to a KPI with a threshold and date, grade it intact / weakened / broken / insufficient evidence, refuse intact on stale data, treat price moves as non-evidence, split each update into fact, price and wording changes, and fix a 12-month pre-mortem and kill criteria at entry. Use to write, check or review a stock or options thesis; for valuation use valuation-audit, for macro use macro-regime. Also for 投资逻辑, 持仓复盘, 季报对照."
version: 1.1.0
sources:
  - upstream/yennanliu-investskill/prompts/thesis-tracker.md (MIT) — structure from this source;
    ledger fields, four statuses and their bars, 3–5 KPIs, pre-mortem, next check
  - upstream/yennanliu-investskill/prompts/10k-digest.md (MIT) — commitment scoring; restatements stale data
  - upstream/yennanliu-investskill/prompts/result-validator.md (MIT) — provenance block; memory is low confidence
  - upstream/xbtlin-ai-berkshire/skills/thesis-drift.md (MIT) — fact / price / wording buckets; no baseline, no check
  - upstream/anthropics-financial-services/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md
    (Apache-2.0) — long/short side, catalysts tied to claims, trend column, track disconfirming evidence
  - upstream/tradermonty-claude-trading-skills/skills/trader-memory-core/SKILL.md (MIT) — append-only
    status history; closed vs invalidated
  - upstream/b-m-capital-research-honeclaw/skills/company-thesis-ratings/SKILL.md (MIT) — fact / inference / unknown tags
  - Gary Klein, "Performing a Project Premortem", HBR 2007, https://hbr.org/2007/09/performing-a-project-premortem
    (public literature) — failure taken as certain; user's causes first (order adapted)
  - Annie Duke, Thinking in Bets (2018) (public literature) — grade the thesis apart from the P&L
  - authored for this toolkit from a stated need (options positions) — claim dates vs expiry
---

# Thesis Ledger

Written down before the news arrives, a thesis can be audited later: which business change it
bets on, the date it must show up by, and the evidence that would refute it. This skill keeps
that record and checks it; what to do with the position stays the user's call.

## Rules that hold in every mode

1. **No advice.** Never output buy, sell, hold, trim, add, a size or a price target — not as a
   suggestion, not as a signal mapped from the status. Asked for one, give the status and its
   evidence and say the decision is the user's.
2. **The user owns the thesis.** You tighten wording, add thresholds and dates, and surface
   bear arguments; you never supply the idea. A metric with no threshold is dropped or given one.
3. **Price is not evidence.** A rally confirms no claim and a sell-off weakens none. Price
   matters only to a valuation question, which goes to valuation-audit.
4. **Each line says what it is:** a sourced fact (source and as-of date), your inference
   (marked as such), or unknown. A figure recalled from model memory is low confidence and can
   never move a status; how to source figures is verified-research's job.
5. **Freshness gates "intact".** Only figures dated after the previous check can hold a claim
   up. An old status is never rolled forward because nothing new arrived.
6. **Compute, don't estimate.** Growth, margins, deltas and distance to threshold come from a
   script, or the formula and inputs are printed so the user can redo them.

## The ledger entry

Opening a thesis means filling every field below. Ask for what is missing; do not guess it.

| field | what goes in | the check you apply |
|---|---|---|
| side and horizon | long or short; holding horizon; expiry for options | for a short, each claim states what must deteriorate; every claim date lands before expiry, and a claim only testable after expiry cannot justify the option (heuristic) |
| thesis | one paragraph: the business change that has to occur, why today's price does not reflect it, and why this is the moment | hand it to an imagined bear — if they cannot point at the sentence they reject, it is still a company description; keep asking |
| claims | 3–5 statements, each with KPI, threshold and by-date | more than five and ordinary quarterly noise trips one in most quarters, so the status stops meaning anything; favour reported financials over sentiment; price is a result, never a claim |
| kill criteria | observable events or breaches that would end the thesis outright | sourced from the user's own "I am wrong if…" and the best bear case; a stop-loss is a trading rule the user may log separately, not a kill criterion |
| pre-mortem | dated entry + 12 months, written as if the failure already happened | the user lists causes first, then you add the bear's; any cause no kill criterion would catch becomes one |
| catalysts | dated events that will produce evidence, each naming the claim it tests and the result that would count against it | an event that tests no claim is not listed |
| next check | a date and its reason | whichever arrives first: next earnings, the next listed catalyst, or 90 days from this check |
| status history | append-only: date, old → new status, the fact that moved it | never rewritten, only appended |

## Checking an open thesis

No saved entry, no check: say a drift comparison is impossible and offer to open one. Never
rebuild the original thesis from memory.

1. **Classify every difference since the last check.** Only the first kind is admitted as
   evidence:
   - *fact* — a new dated figure, filing, event or management action
   - *price* — the quote, multiple or mood moved while the business did not; log it, no effect
   - *wording* — the new write-up says the same evidence differently; not drift
2. **Refresh each claim**: new value, source, as-of date, and trend since last check (better /
   flat / worse). With no newer figure the claim is `stale`. A restatement or auditor change
   stales the history it touches.
3. **Score what management promised last time** — delivered, partial, missed, or not yet due.
   This is fact evidence about the mechanism.
4. **Test each kill criterion**: fired, not fired, or cannot assess (give the reason).
5. **Write down the strongest fact against the thesis**, even when everything holds. If none
   exists, say what you searched.
6. **Grade each claim**: *holding* (within threshold on post-check data), *breached*, *stale*,
   or *not yet testable* (its by-date is still ahead and no figure can answer it yet — such
   claims sit outside the intact test until their date passes, so an early thesis or an
   option can be intact). Then tally kill criteria fired (K) and breached claims (B):
   - K ≥ 1, B ≥ 2, or a structural reason the mechanism cannot work → **broken**;
   - B = 1, or the mechanism lagging its dates → **weakened**. A single breached claim moves
     the thesis one rung, not straight to broken, and is not explained away;
   - K = 0, B = 0 and no testable claim stale → **intact**;
   - otherwise → **insufficient evidence**: say which figure is missing and when it should be
     published, and make that the next check.
7. **Every status change carries its receipt**: the claim's earlier and latest reading, the
   threshold it was measured against, and where and when that reading was published. Without
   new evidence the status stays put, and a cheaper multiple never offsets a fired kill criterion.

## Closing a thesis

Mark the entry *closed* (ran its course or the user chose to exit) or *invalidated* (a kill
criterion fired or the status was broken), with the user's stated reason. Grade whether the
thesis was right separately from the P&L: a sound thesis can lose money and a wrong one can profit.

## Reviewing the book

One row per thesis: ticker, side, status, last check, next check, overdue (yes/no), what data
is still missing.

## Output

```
Data & sources — as of <date> · <source per figure> · retrieval: pasted | fetched | memory
  · confidence: high | medium | low (memory ⇒ low)
<TICKER> · <long|short> · <STATUS> · <date> — <the fact that moved it, or "no new facts">
Thesis: <change · why unpriced · why now>   Horizon / expiry: <…>
| # | claim | KPI | threshold | by | previous | current (source, as-of) | trend | status |
| kill criterion | fired / not fired / cannot assess | evidence |
Changes since <last check>: fact: <…> | price: <…, no effect> | wording: <…, no effect>
Management commitments: <delivered / partial / missed / not yet due>
Strongest contrary fact: <…>   Inferences (marked): <…>   Unknown: <…>
Calculations: <script output, or formula with inputs>
Pre-mortem (<entry + 12 months>): <…>
Catalysts: <date — event — claim tested — result that would count against>
Status history: <date: old → new — fact>
Next check: <date> — <reason>   Missing evidence: <…>
Not covered here: valuation → valuation-audit; macro → macro-regime. No action is implied.
```
