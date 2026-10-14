---
name: valuation-audit
description: "Audit a stock valuation, yours or someone else's, for the errors that make it wrong — no price or cheap/expensive call without a dated quote and diluted share count, two independent method families, a mandatory market-implied (reverse) valuation, DCF terminal sanity flags, each peer premium stated once, and return split into fundamentals vs multiple change. Use for 'is X cheap', fair value, DCF or multiple checks; to track a thesis use thesis-ledger. Also for 估值, 贵不贵, 合理价值, \"should I buy X\" (answered as a valuation audit, never as advice)."
version: 1.0.0
sources:
  - upstream/b-m-capital-research-honeclaw/skills/valuation-audit/SKILL.md (MIT) — reconciliation table, 3% market-cap tolerance, no quote no price, two method families, divergence handling, market-implied valuation, premium counted once, ±30% anchor rule, e + r + e×r return split, no-rerating case
  - upstream/yennanliu-investskill/prompts/dcf-valuation.md (MIT) — terminal growth below the discount rate; flag terminal value above 80% of enterprise value
---

# Valuation Audit

A valuation is only as good as its weakest input, and the usual failures are clerical, not
conceptual: a stale price, the wrong share count, one reason counted twice. This skill checks
for them and returns a value range with its assumptions. It is decision support, not advice.

## Iron laws

1. **No dated quote and diluted share count, no price conclusion.** Without both, write no
   price, market cap, multiple, value range or "cheap/expensive". Give only the qualitative
   read, the figures you did verify, and what becomes computable once the quote arrives.
2. **Never output buy, sell, entry or add prices, price targets as advice, or position sizes.**
   The deliverable is a value range, the assumptions behind each end, and the audit findings.
   If asked "where should I buy", give the range and the market-implied assumptions and stop.
   Never restate either end of the range as an entry or exit level.
3. **Two independent method families before any cheap/expensive call.** TTM and forward P/E,
   or GAAP and adjusted P/E, are one ruler read twice. The second must be a different family
   (EV/EBIT, EV/EBITDA, FCF yield, EV/Sales, P/B, DCF). One multiple alone is unfinished work.
4. **The reverse valuation is mandatory:** state what growth and margins today's price
   requires, and set them beside the last four quarters' actuals and company guidance.
5. **Every premium or discount to peers appears in one explicit sentence and is counted once.**
   A reason already in the growth rate or the earnings forecast cannot also lift the multiple.
6. **Every input carries a source and a date; every number can be recomputed.** Show each
   formula with its values substituted, or run it as a script. Source and date inputs with the
   `verified-research` method; take the risk-free rate and rate regime from `macro-regime`.

## Step 1 — Reconcile the inputs (before any multiple)

| row | rule |
|---|---|
| as-of | one timestamped price for the whole analysis; a second price anywhere means fix it |
| diluted shares | latest reported diluted count; say if fully diluted is used instead |
| market cap | price × diluted shares; if it differs from the quoted cap by more than 3%, explain why (quoted caps usually use basic shares, so heavy stock compensation is an expected cause) |
| net debt / EV | cash, total debt (state whether leases count); EV = market cap + net debt + preferred + minority interests − equity-method stakes |
| denominators | revenue, EBIT(DA), EPS, FCF — each with period (TTM, FY1, FY2), GAAP or adjusted, and nature (actual / guidance / consensus / own assumption) |
| guidance vs consensus | gap above about 5%: name it, say which one is used and why |
| fiscal year | if the year does not end in December, state which calendar months FY1 covers |

Red flags to clear before moving on: price and statements in different currencies (convert
and show the rate); units mixed (millions vs billions); a negative denominator (write N/M,
never a negative or absolute-value multiple); a single quarter × 4 presented as TTM; backlog,
orders or ARR used as revenue; for a cyclical, peak earnings × a normal multiple — show
price ÷ peak and price ÷ mid-cycle earnings side by side.

## Step 2 — Pick methods by business model

| business | primary | independent check |
|---|---|---|
| mature, profitable | normalised P/E | EV/EBIT or FCF yield |
| loss-making growth | EV/Sales plus a margin bridge to target-year profit | DCF |
| capital-heavy | EV/EBIT (depreciation is a real cost) | FCF yield; never EV/EBITDA alone |
| conglomerate | sum of the parts, one line per segment | consolidated multiple |
| asset holder (holdco, fund) | NAV per share, then the premium or discount to it | none of the earnings multiples |
| bank or insurer | P/TBV against return on tangible equity | P/E; no EV-based multiples or net debt |

If the two families' midpoints differ by more than about 25%, do not average them. Name the
input causing the gap (denominator basis, anchor multiple, growth, net debt), say which result
you trust more and why, and keep the other beside it as a cross-check.

## Step 3 — DCF sanity flags

Show a DCF only when the starting free cash flow, growth path, capex, discount rate and
terminal method can each be written out; otherwise use multiples and say so.

- **Terminal growth must be below the discount rate.** g ≥ k (k = discount rate) makes the
  terminal formula meaningless, so stop and fix the input.
- **Flag a terminal value above 80% of enterprise value** (the threshold in the cited source).
  The answer then rests on a perpetuity assumption more than on the forecast; say that.
- Show sensitivity of value to discount rate and terminal growth, not one point estimate.

## Step 4 — Peer premium, stated once

Write one sentence: "Multiple moves from <named anchor: peer median, own history or sector>
to <value> because <observable evidence>." Rules:

- An adjustment of more than about ±30% from the anchor needs two independent pieces of
  evidence (source heuristic); with one, shrink it or move the excess to the upside case.
- Discounts are stated too: a commodity product with no proven edge does not get the leader's
  multiple by default.
- Double-count check: forecast above consensus **and** a target multiple above today's
  same-basis multiple is a joint dependency — list the evidence for each separately.
  Dilution already in EPS is not applied again as a discount; net debt already in EV is not
  deducted twice.

## Step 5 — Market-implied view and return split

- At today's price, back out the revenue growth, margin and multiple the market needs, and
  compare each with verified actuals and guidance ("needs <x>% growth vs <y>% over the last
  four quarters").
- Split expected return into fundamentals and multiple. With e = earnings-per-share change and m = multiple change,
  P₁/P₀ − 1 = e + m + e×m (price return only; add dividends separately); report the
  interaction term (20% and 50% compound to 80%, not 70%). If the denominator is not positive, report the bridge in
  currency instead.
- Report the no-rerating case: today's multiple × the forecast denominator. It is a
  diagnostic, not a floor.

## Auditing someone else's valuation

Run Steps 1-5 against their model and report each failed check as a finding: the check, the
evidence (the cell, line or figure), and its effect on value with the corrected number shown.
A check you could not run because an input is missing is a gap, not a pass.

## Output

```
As-of: <price, timestamp, currency> | diluted shares <n, source, date> | cap check <±x%>
Reconciliation table: <rows from Step 1, each with source and date>
Methods: <family 1: formula = value> | <family 2: formula = value> | divergence <x%, cause>
DCF flags: g < k <yes/no> | terminal share of EV <x%> <flag if > 80%>
Premium sentence: <anchor → value because evidence>; double counts found: <none / list>
Market-implied: <growth, margin, multiple required vs actuals and guidance>
Value range: low <formula = value> | base <formula = value> | high <formula = value>
Price vs range: <position>; return split: fundamentals e / multiple r / interaction e×r
Findings: <check — evidence — effect on value>  |  Gaps: <missing input — what it blocks>
Not advice: no entry, exit, target or sizing is given. Thesis tracking → thesis-ledger
```
