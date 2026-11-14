---
name: thesis-ledger
description: >-
  Write and track stock or options theses as dated, falsifiable KPI claims: status bars (intact /
  weakened / broken / insufficient evidence), stale-data blocks, price != evidence, fact/price/wording
  drift split, and 12m pre-mortem. Trigger on 投资逻辑, 持仓复盘, 季报对照. Valuation: valuation-audit.
version: 1.3.1
sources:
  - upstream/yennanliu-investskill/prompts/thesis-tracker.md (MIT) — structure from this source;
    ledger fields, four statuses and their bars, last-confirmed vs check outcome, 3–5 KPIs,
    pre-mortem, next check [port "3–5 statements, each with kpi" "insufficient evidence" "last confirmed status" "dated entry + 12 months"]
  - upstream/yennanliu-investskill/prompts/thesis-tracker.md (MIT) — a parseable saved-entry format and location, with a fenced-block fallback the user stores [port "~/.investing/theses/<ticker>.md" "paste it back to resume"]
  - upstream/yennanliu-investskill/prompts/10k-digest.md (MIT) — commitment scoring; rerun after a restatement (the stale-data rule is toolkit policy) [port "score the saved promises" "a restatement or auditor change"]
  - upstream/yennanliu-investskill/prompts/result-validator.md (MIT) — provenance block; memory is low confidence [port "memory ⇒ low"]
  - upstream/xbtlin-ai-berkshire/skills/thesis-drift.md (MIT) — fact / price / wording buckets; no baseline, no check [port "is it new, dated, checkable" "a thesis recalled after the fact"]
  - upstream/xbtlin-ai-berkshire/tools/financial_rigor.py (MIT) — growth, margin and distance-to-threshold computed by script with the formula printed [port "def cmd_calc"]
  - upstream/anthropics-financial-services/plugins/vertical-plugins/equity-research/skills/thesis-tracker/SKILL.md
    (Apache-2.0) — long/short side, catalysts tied to claims, trend column, track disconfirming evidence [port "long or short; holding horizon" "an event that tests no claim" "strongest fact against the thesis"]
  - upstream/tradermonty-claude-trading-skills/skills/trader-memory-core/SKILL.md (MIT) — event-history
    appends; closed vs invalidated (never editing past rows is toolkit policy) [port "rows are added, never edited" "*invalidated*"]
  - upstream/tradermonty-claude-trading-skills/skills/trader-memory-core/{scripts/thesis_store.py,schemas/thesis.schema.json} (MIT) — validated thesis state and due-date queries; append-only history enforced in code here by a hash chain [port "def verify_text" "def cmd_book" "chained to the row before it"]
  - upstream/tradermonty-claude-trading-skills/skills/trader-memory-core/scripts/thesis_review.py (MIT) — MAE/MFE postmortem from price history and recorded lessons [gap needs a price feed; not ported]
  - upstream/b-m-capital-research-honeclaw/skills/company-thesis-ratings/SKILL.md (MIT) — fact / inference / unknown tags [port "inferences (marked)"]
  - Gary Klein, "Performing a Project Premortem", HBR 2007, https://hbr.org/2007/09/performing-a-project-premortem
    (public literature) — failure taken as certain; user's causes first (order adapted) [port "the user lists causes first"]
  - Annie Duke, Thinking in Bets (2018) (public literature) — grade the thesis apart from the P&L [port "separately from the p&l"]
  - authored for this toolkit from a stated need (options positions) — claim dates vs expiry [port "every claim date lands before expiry"]
---

# Thesis Ledger

Records a thesis as dated, testable claims and audits it at each check; the position stays
the user's call.

## Rules that hold in every mode

1. **No advice.** Never output buy, sell, hold, trim, add, a size or a price target — not as a
   suggestion, not as a signal mapped from the status. Asked for one, give the status and its
   evidence and say the decision is the user's.
2. **The user owns the thesis.** You tighten wording, add thresholds and dates, and surface
   bear arguments; you never supply the idea. A metric with no threshold is dropped or given one.
3. **Price is not evidence.** A rally confirms no claim and a sell-off weakens none; valuation
   questions go to valuation-audit.
4. **Sourcing follows verified-research.** In addition: a figure recalled from model memory
   never moves a status.
5. **Only fresh figures confirm.** A claim holds only on a figure dated after the previous check.
   A check without such figures does not re-confirm anything (see the two statuses below).
6. **Compute, don't estimate.** Growth, margins, deltas and distance to threshold come from
   `scripts/ledger.py calc growth|margin|distance` (or another script run this session), or the
   formula and inputs are printed so the user can redo them.

## Where the ledger lives

One file per thesis at `~/.investing/theses/<TICKER>.md` (`$THESIS_DIR` overrides), managed by
`scripts/ledger.py` (standard-library Python):

- `ledger.py new <TICKER> --side long|short [--expiry <date>]` creates the file with every
  section below; fill them by editing it. It refuses to overwrite an existing thesis.
- `ledger.py log <TICKER> --outcome intact|weakened|broken|insufficient --fact "…" --next <date>
  --reason "…"` appends the check to the Status history and updates the header; `insufficient`
  leaves last confirmed in place (step 8). Each history row is hash-chained to the row before it.
- `ledger.py verify <TICKER>` before every check: an edited or deleted row, or a header that
  disagrees with the history, fails it, and `log` refuses to append until fixed.
- `ledger.py close <TICKER> --as closed|invalidated --reason "…"`; `ledger.py book` for the
  review table with overdue checks.

Without file access (a chat session), emit the full entry as one fenced Markdown block in the
same layout and tell the user to save it and paste it back to resume; never rebuild it from
memory.

## The ledger entry

Opening a thesis means filling every field below. Ask for what is missing; do not guess it.

| field | what goes in | the check you apply |
|---|---|---|
| side and horizon | long or short; holding horizon; expiry for options | for a short, phrase each claim in the direction the short needs — deterioration, or weakness that persists (toolkit policy); every claim date lands before expiry, and a claim only testable after expiry cannot justify the option (heuristic) |
| thesis | one paragraph: the business change that has to occur, why today's price does not reflect it, and why this is the moment | hand it to an imagined bear — if they cannot point at the sentence they reject, it is still a company description; keep asking |
| claims | 3–5 statements, each with KPI, threshold and by-date | cap at five (toolkit heuristic: each extra claim is another way for noise to read as a breach); favour reported financials over sentiment; price is a result, never a claim |
| kill criteria | observable events or breaches that would end the thesis outright, written now, before any news tests them | sourced from the user's own "I am wrong if…" and the best bear case; a stop-loss is a trading rule the user may log separately, not a kill criterion |
| pre-mortem | dated entry + 12 months, written as if the failure already happened | the user lists causes first, then you add the bear's; pair each cause with the kill criterion that would detect it, and write a new criterion for every unpaired cause |
| catalysts | dated events that will produce evidence, each naming the claim it tests and the result that would count against it | an event that tests no claim is not listed |
| promises | management commitments from the latest filing or call, with that source and date | they are scored at the next check |
| next check | a date and its reason | whichever arrives first: next earnings, the next listed catalyst, or 90 days from this check |
| status history | date, check outcome, last confirmed status, the fact behind any change | rows are added, never edited (toolkit policy) |

## Checking an open thesis

The saved entry is the yardstick: open it (or the pasted block) and run `ledger.py verify`
first. If there is none, open one dated today as day zero — a thesis recalled after the fact has absorbed what happened since, so it is never used
as a baseline.

1. **Admit only facts.** Split each item into single changes, then ask of every one: is it new,
   dated, checkable and about the business itself? A yes is *fact* and feeds the steps below.
   A no goes under *price* (a move in the quote or multiple), *wording* (old evidence, new
   phrasing) or *unverified* (a claim about the business with no date or source yet, held
   until it is sourced) — listed, and it moves nothing. "Shares fell 12% after the CFO left and
   guidance was cut" is two facts and one price item.
2. **Refresh each claim**: new value, source, as-of date, trend (better / flat / worse), or
   "no new figure". A restatement or auditor change marks the figures it touches stale
   (toolkit policy).
3. **Score the saved promises** against their source and date: delivered, partial, missed, or
   not yet due. This is fact evidence about the mechanism.
4. **Assess each kill criterion**: not fired, fired, or cannot assess (give the reason).
5. **Write down the strongest fact against the thesis**, even when everything holds, or say
   what you searched.
6. **Grade each claim**: *holding* or *breached* (on a figure dated after the previous check),
   *stale* (it has been testable, by an earlier figure or a passed date, and no fresh figure
   exists now), or *pending* (it has never yet been testable and its by-date is ahead; pending
   claims neither help nor hurt). Report coverage, e.g.
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
   confirmation. Each change cites earlier and latest reading, threshold, and source with date.
   A cheaper multiple never offsets a fired kill criterion.

## Closing a thesis

Mark the entry *closed* (ran its course or the user chose to exit) or *invalidated* (a kill
criterion fired or the status was broken), with the user's stated reason. Grade whether the
thesis was right separately from the P&L: a sound thesis can lose money and a wrong one can profit.
The ledger holds no prices or position size; ask for the realised result if the user wants it
beside the grade.

## Reviewing the book

`ledger.py book` prints one row per thesis (side, statuses, last and next check, overdue);
add a column for the data each file still lacks.

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
Changes since <last check>: fact: <…> | price: <…, no effect> | wording: <…, no effect> | unverified: <…, held until sourced>
Promises (<source, date>): <delivered / partial / missed / not yet due>
Strongest contrary fact: <…>   Inferences (marked): <…>   Unknown: <…>
Calculations: <script output, or formula with inputs>
Pre-mortem (<entry + 12 months>): <…>
Catalysts: <date — event — claim tested — result that would count against>
Status history: <date: outcome · last confirmed old → new — fact>
Next check: <date> — <reason>   Missing evidence: <…>
Not covered here: valuation → valuation-audit; macro → macro-regime. No action is implied.
```
