---
name: thesis-ledger
description: "Write an investment thesis as dated, falsifiable claims and track it — tie each claim to a KPI with a threshold and date, grade it intact / weakened / broken / insufficient evidence, refuse intact on stale data, treat price moves as non-evidence, split each update into fact, price and wording changes, and fix a 12-month pre-mortem and kill criteria at entry. Use to write, check or review a stock or options thesis; for valuation use valuation-audit, for macro use macro-regime. Also for 投资逻辑, 持仓复盘, 季报对照."
version: 1.2.1
sources:
  - upstream/yennanliu-investskill/prompts/thesis-tracker.md (MIT) — structure from this source;
    ledger fields, four statuses and their bars, last-confirmed vs check outcome, 3–5 KPIs,
    pre-mortem, next check
  - upstream/yennanliu-investskill/prompts/10k-digest.md (MIT) — commitment scoring; rerun after a restatement (the stale-data rule is toolkit policy)
  - upstream/yennanliu-investskill/prompts/result-validator.md (MIT) — provenance block; memory is low confidence
  - upstream/xbtlin-ai-berkshire/skills/thesis-drift.md (MIT) — fact / price / wording buckets; no baseline, no check
  - upstream/anthropics-financial-services/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md
    (Apache-2.0) — long/short side, catalysts tied to claims, trend column, track disconfirming evidence
  - upstream/tradermonty-claude-trading-skills/skills/trader-memory-core/SKILL.md (MIT) — event-history
    appends; closed vs invalidated (never editing past rows is toolkit policy)
  - upstream/b-m-capital-research-honeclaw/skills/company-thesis-ratings/SKILL.md (MIT) — fact / inference / unknown tags
  - Gary Klein, "Performing a Project Premortem", HBR 2007, https://hbr.org/2007/09/performing-a-project-premortem
    (public literature) — failure taken as certain; user's causes first (order adapted)
  - Annie Duke, Thinking in Bets (2018) (public literature) — grade the thesis apart from the P&L
  - authored for this toolkit from a stated need (options positions) — claim dates vs expiry
---

# Thesis Ledger

Records a thesis as dated, testable claims and audits it at each check; what to do with the
position stays the user's call.

## Rules that hold in every mode

1. **No advice.** Never output buy, sell, hold, trim, add, a size or a price target — not as a
   suggestion, not as a signal mapped from the status. Asked for one, give the status and its
   evidence and say the decision is the user's.
2. **The user owns the thesis.** You tighten wording, add thresholds and dates, and surface
   bear arguments; you never supply the idea. A metric with no threshold is dropped or given one.
3. **Price is not evidence.** A rally confirms no claim and a sell-off weakens none. Price
   matters only to a valuation question, which goes to valuation-audit.
4. **Sourcing follows verified-research.** In addition: a figure recalled from model memory
   never moves a status.
5. **Only fresh figures confirm.** A claim holds only on a figure dated after the previous check.
   A check without such figures does not re-confirm anything (see the two statuses below).
6. **Compute, don't estimate.** Growth, margins, deltas and distance to threshold come from a
   script, or the formula and inputs are printed so the user can redo them.

## The ledger entry

Opening a thesis means filling every field below. Ask for what is missing; do not guess it.

| field | what goes in | the check you apply |
|---|---|---|
| side and horizon | long or short; holding horizon; expiry for options | for a short, phrase each claim in the direction the short needs — deterioration, or weakness that persists (toolkit policy); every claim date lands before expiry, and a claim only testable after expiry cannot justify the option (heuristic) |
| thesis | one paragraph: the business change that has to occur, why today's price does not reflect it, and why this is the moment | hand it to an imagined bear — if they cannot point at the sentence they reject, it is still a company description; keep asking |
| claims | 3–5 statements, each with KPI, threshold and by-date | cap at five (toolkit heuristic: each extra claim adds another way for routine noise to register a breach); favour reported financials over sentiment; price is a result, never a claim |
| kill criteria | observable events or breaches that would end the thesis outright, written now, before any news tests them | sourced from the user's own "I am wrong if…" and the best bear case; a stop-loss is a trading rule the user may log separately, not a kill criterion |
| pre-mortem | dated entry + 12 months, written as if the failure already happened | the user lists causes first, then you add the bear's; pair each cause with the kill criterion that would detect it, and write a new criterion for every unpaired cause |
| catalysts | dated events that will produce evidence, each naming the claim it tests and the result that would count against it | an event that tests no claim is not listed |
| promises | management commitments from the latest filing or call, with that source and date | they are scored at the next check |
| next check | a date and its reason | whichever arrives first: next earnings, the next listed catalyst, or 90 days from this check |
| status history | date, check outcome, last confirmed status, the fact behind any change | rows are added, never edited (toolkit policy) |

## Checking an open thesis

The saved entry is the yardstick. If there is none, open one dated today and treat this as day
zero — a thesis recalled after the fact has absorbed what happened since, so it is never used
as a baseline.

1. **Admit only facts.** Split each item into single changes, then ask of every one: is it new,
   dated, checkable and about the business itself? A yes is *fact* and feeds the steps below.
   A no goes under *price* (a move in the quote or multiple) or *wording* (old evidence, new
   phrasing) — listed, and it moves nothing. Example: "shares fell 12% after the CFO left and
   guidance was cut" is two facts (the departure, the cut) and one price item (the 12%).
2. **Refresh each claim**: new value, source, as-of date, and trend since last check (better /
   flat / worse). With no newer figure, record "no new figure"; step 6
   decides whether that makes it pending or stale. A restatement or auditor change
   marks the figures it touches stale (toolkit policy).
3. **Score the saved promises** against their source and date: delivered, partial, missed, or
   not yet due. This is fact evidence about the mechanism.
4. **Assess each kill criterion**: not fired, fired, or cannot assess (give the reason).
5. **Write down the strongest fact against the thesis**, even when everything holds. If none
   exists, say what you searched.
6. **Grade each claim**: *holding* or *breached* (on a figure dated after the previous check),
   *stale* (its date has come but no fresh figure exists), or *pending* (its by-date is ahead
   and nothing can test it yet; pending claims neither help nor hurt). Report coverage, e.g.
   "tested 2/5 · pending 3 · stale 0 · kill criteria clear 3/4, unassessed 1".
7. **Set this check's outcome** — walk the list top-down and stop at the first that applies:
   1. **broken** — a kill criterion fired; two or more claims breached on current data; or a
      structural reason the mechanism cannot work.
   2. **weakened** — exactly one claim breached on current data, or the mechanism is running
      behind its dates. A single breach moves one rung, not straight to broken, and is not
      explained away.
   3. **intact** — at least one claim tested, every tested claim holding, none stale, and every
      applicable kill criterion assessed as not fired.
   4. **insufficient evidence** — everything else: stale claims, unassessed kill criteria, or
      every claim still pending (say "awaiting first test"). Name the missing figure and when
      it should be published, and make that the next check.
8. **Update the last confirmed status** only when the outcome is broken, weakened or intact.
   Insufficient evidence leaves it in place and is reported beside it, never as a fresh
   confirmation. Each change cites the claim's earlier and latest reading, its threshold, and
   where and when the reading was published. A cheaper multiple never offsets a fired kill
   criterion.

## Closing a thesis

Mark the entry *closed* (ran its course or the user chose to exit) or *invalidated* (a kill
criterion fired or the status was broken), with the user's stated reason. Grade whether the
thesis was right separately from the P&L: a sound thesis can lose money and a wrong one can profit.

## Reviewing the book

One row per thesis: ticker, side, last confirmed status, latest check outcome, last check,
next check, overdue (yes/no), what data is still missing.

## Output

```
Data & sources — as of <date> · <source per figure> · retrieval: pasted | fetched | memory
  · confidence: high | medium | low (memory ⇒ low)
<TICKER> · <long|short> · check <date>: <OUTCOME> · last confirmed: <STATUS> (<date>)
  — <the fact that moved it, or "no new facts">
Coverage: tested <n>/<N> · pending <n> · stale <n> · kill criteria clear <n>/<N>, unassessed <n>
Thesis: <change · why unpriced · why now>   Horizon / expiry: <…>
| # | claim | KPI | threshold | by | previous | current (source, as-of) | trend | holding / breached / stale / pending |
| kill criterion | not fired / fired / cannot assess | evidence |
Changes since <last check>: fact: <…> | price: <…, no effect> | wording: <…, no effect>
Promises (<source, date>): <delivered / partial / missed / not yet due>
Strongest contrary fact: <…>   Inferences (marked): <…>   Unknown: <…>
Calculations: <script output, or formula with inputs>
Pre-mortem (<entry + 12 months>): <…>
Catalysts: <date — event — claim tested — result that would count against>
Status history: <date: outcome · last confirmed old → new — fact>
Next check: <date> — <reason>   Missing evidence: <…>
Not covered here: valuation → valuation-audit; macro → macro-regime. No action is implied.
```
