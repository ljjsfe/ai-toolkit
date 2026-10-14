---
name: thesis-ledger
description: "Write an investment thesis as dated, falsifiable claims and track it — tie each claim to a KPI with a threshold and date, grade it intact / weakened / broken / insufficient evidence, refuse intact on stale data, treat price moves as non-evidence, split each update into fact, price and wording changes, and fix a 12-month pre-mortem and kill criteria at entry. Use to write, check or review a stock or options thesis; for valuation use valuation-audit, for macro use macro-regime. Also for 投资逻辑, 持仓复盘, 季报对照."
version: 1.0.0
sources:
  - upstream/yennanliu-investskill/prompts/thesis-tracker.md (MIT) — mechanism / mispricing /
    why-now test, 3–5 KPIs with thresholds, ordered status rules, stale data cannot support
    intact, next-check timing, dated pre-mortem, memory figures low confidence
  - upstream/yennanliu-investskill/prompts/10k-digest.md (MIT) — prior commitments scored
    delivered / partial / missed; restatement or auditor change makes earlier figures stale
  - upstream/yennanliu-investskill/prompts/result-validator.md (MIT) — provenance header
    first; memory figures above low confidence are a red flag
  - upstream/xbtlin-ai-berkshire/skills/thesis-drift.md (MIT) — fact / price / wording
    separation, compare evidence not prose, no change without new evidence, no mental
    arithmetic, kill criteria outrank a cheap multiple, no baseline means no drift check
  - authored for this toolkit from a stated need (options positions) — claim dates vs expiry
---

# Thesis Ledger

A thesis is a contract with your later self: what has to be true, by when, and what would
prove it wrong. This skill keeps that contract honest; it never tells you what to do with
the position.

## Iron laws

1. **No advice.** Output is claim status and evidence only — never buy, sell, hold, trim, add,
   a position size or a price target, not even as a "suggestion" or a mapped signal. If asked,
   restate the status and the evidence and say the decision is the user's.
2. **Every claim is falsifiable, measured and dated.** Each claim names a KPI, a threshold and
   the date by which it must hold. A KPI without a threshold is a curiosity — drop it or give
   it one. The user states the thesis; you sharpen it, never invent it.
3. **Price movement is never evidence about the thesis.** A rise does not confirm a claim and a
   fall does not weaken one. Price can only change a valuation question (valuation-audit).
4. **Stale data cannot support "intact".** A claim is intact only on a figure dated after the
   last check. Otherwise it is insufficient evidence — the previous status is not carried over.
5. **Every figure carries source and as-of date.** A figure from model memory is low
   confidence and cannot move a status; sourcing method lives in verified-research.
6. **No arithmetic in the head.** Growth rates, margins, deltas and distances to threshold are
   computed by a script, or the formula and inputs are shown so the user can recompute.

## Open — writing the thesis at entry

1. **Sharpen to one paragraph** answering in order: what has to happen to the business (the
   mechanism, not "the stock goes up"); why the market currently misprices it; why now. Test:
   could a bear read it and know exactly what to disagree with? If not, ask until they could.
2. **Turn it into 3–5 claims** (beyond that, routine noise breaches some claim most quarters and the status loses meaning). Prefer financial-statement KPIs over sentiment; price is an output.
3. **Write kill criteria now, while calm**: observable events or KPI breaches that would break
   the thesis — from the user's own "I'd be wrong if…" and the strongest bear arguments.
   A stop-loss is a separate trading rule the user may record; it is not a kill criterion.
4. **Write the pre-mortem**, dated 12 months out, past tense: "It is <date>. This failed
   because…". If it names a cause no kill criterion would catch, add that criterion.
5. **Options:** every claim date must fall before expiry. A claim that can only be tested after
   expiry cannot be the reason for the option; say so (heuristic).
6. **Set the next check**: the earliest of the next earnings release, the next dated catalyst,
   or 90 days.

## Update — re-testing against new evidence

Requires a saved baseline. With none, say a drift check is impossible and offer to open one;
never reconstruct an old thesis from memory.

1. **Sort every difference** since the last check into exactly one bucket, and compare only
   the first:

| bucket | what it is | effect on status |
|---|---|---|
| fact changed | a new dated figure, filing, event or management action | can move a claim |
| price changed | quote, multiple or sentiment moved; the business did not | none — note it only |
| wording changed | the new write-up phrases or orders things differently | none — not drift |

2. **Refresh each claim's KPI** with its new value, source and date; mark it `stale` if no
   newer figure exists. A restatement or auditor change marks the affected history stale.
3. **Score management's prior commitments** (from the last filing or call) as delivered,
   partial, missed or too early — this is fact evidence for the mechanism.
4. **Re-test each kill criterion**: fired / not fired / cannot assess (say why).
5. **Grade each claim, then the thesis, top-down — first match wins:**

| status | rule |
|---|---|
| broken | two or more claims breached on current data, or any kill criterion fired, or the mechanism is shown structurally false |
| weakened | one claim breached, or the mechanism is behind its dates |
| intact | every claim within threshold on post-check data; no kill criterion fired |
| insufficient evidence | anything else (e.g. some claims stale, none breached); name the missing data and when it will exist |

A cheaper multiple never offsets a fired kill criterion. Any status change cites the exact
fact that moved it — old value, new value, threshold, source, date. A change with no new
fact behind it is not a change.

## Review — the whole book

One row per thesis: ticker, status, last check, next check, overdue, data still missing.

## Output

```
Data & sources — as of <date> · <source per figure> · retrieval: pasted | fetched | memory
  · confidence: high | medium | low (memory ⇒ low)
<TICKER> · <STATUS> · <date> — <the one fact that moved it, or "no new facts">
Thesis: <mechanism · mispricing · why now>   Horizon / expiry: <…>
| # | claim | KPI | threshold | by | previous | current (source, as-of) | status |
| kill criterion | fired / not fired / cannot assess | evidence |
Changes since <last check>: fact: <…> | price: <…, no effect> | wording: <…, no effect>
Calculations: <script output, or formula with inputs>
Pre-mortem (<entry date + 12 months>): <…>
Next check: <date> — <reason>   Missing evidence: <…>
Not covered here: valuation → valuation-audit; macro → macro-regime. No action is implied.
```
