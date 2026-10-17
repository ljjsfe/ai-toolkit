---
name: valuation-audit
description: "Audit a stock valuation, yours or someone else's, for the errors that make it wrong — no price or cheap/expensive call without a dated quote and diluted share count, read what today's price implies before valuing, two independent method families, terminal value checked against growth, reinvestment and the discount rate, each peer premium stated once, and return split into fundamentals vs multiple change. Use for 'is X cheap', fair value, DCF or multiple checks; to track a thesis use thesis-ledger. Also for 估值, 贵不贵, 合理价值, \"should I buy X\" (answered as a valuation audit, never as advice)."
version: 1.2.3
sources:
  - upstream/b-m-capital-research-honeclaw/skills/valuation-audit/SKILL.md (MIT) — structure of §1 (snapshot rows, red flags); method-by-business pairings (reorganised); 3%, 5%, 25%, ±30% thresholds; same-family rule; joint-upgrade and double-count checks; DCF shown only when its inputs can be written out; return split incl. EV path; no-rerating case
  - Mauboussin and Rappaport, "Expectations Investing" (2001; rev. 2021), https://www.expectationsinvesting.com/ — §2, price-implied drivers and forecast period
  - Damodaran, valuation teaching material, https://pages.stern.nyu.edu/~adamodar/ — FCFF vs equity models for financials; g near risk-free; reinvestment = g/ROIC; ROIC fade; ROIC = WACC makes growth worthless
  - upstream/xbtlin-ai-berkshire/codex-skills/investment-research/SKILL.md (MIT) — terminal multiple from economics not peers; 5-point r−g heuristic; same-basis r and g; discrete-risk scenario
  - upstream/anthropics-financial-services/plugins/agent-plugins/model-builder/skills/dcf-model/SKILL.md (Apache-2.0) — PV(TV) share below 40% check; grid centre equals base
  - upstream/anthropics-financial-services/plugins/agent-plugins/model-builder/skills/comps-analysis/SKILL.md (Apache-2.0) — median, drop doubtful peers, quartiles, 10% source gap
  - upstream/yennanliu-investskill/prompts/dcf-valuation.md (MIT) — g below r; TV above 80% flag
  - upstream/yennanliu-investskill/prompts/stock-valuation.md (MIT) — SBC-adjusted FCF; no EV bridge for P/E price
  - upstream/tradermonty-claude-trading-skills/skills/kanchi-dividend-sop/references/valuation-and-one-off-checks.md (MIT) — REIT row; one-off profit checks
---

# Valuation Audit

The deliverable is a value range with its assumptions and a list of findings, never a
recommendation.

## Hard stops

- **No quote, no price talk.** A timestamped price and a dated diluted share count gate every
  price-dependent number: cap, multiples, range, the cheap/expensive verdict. Missing either,
  say which calculations are blocked, then give what still stands on its own (statement
  figures you confirmed, the business-type read).
- **No advice in any form:** no buy, sell, add or exit levels, no position size, no target
  dressed as a recommendation. "Where should I buy?" gets the value range and what today's
  price assumes, nothing more. Never restate either end of the range as an entry or exit level.
- **Every derived number shows its formula with values plugged in**, or comes from a script.
  Inputs are sourced and dated per `verified-research`; the risk-free rate comes from
  `macro-regime`.

## 1. Freeze the snapshot

One as-of price for the whole piece. If two prices appear anywhere, the audit stops until one
is removed. Then build this table, each row with source and date:

| row | what to check |
|---|---|
| shares | latest basic count (10-Q / 10-K cover page) plus dilution at today's price: options and warrants by the treasury stock method, unvested RSUs, in-the-money convertibles if-converted; say so if you use the reported diluted average or fully diluted instead |
| market cap | price × diluted shares, compared with the quoted cap. Over 3% apart (honeclaw's tolerance, roughly the gap stock compensation alone can open between basic and diluted counts) means explain it before going on. Example: 42.00 × 310m = 13.02bn against a quoted 12.4bn is 5% off; the quote used 296m basic shares (42.00 × 296m = 12.43bn), so the gap is explained |
| EV bridge | market cap + debt (state whether leases are in) − cash + preferred + minority interests − equity-method stakes. EV multiples pair with EV, P/E and FCF yield with market cap; a P/E-derived price is already per share and is not bridged again |
| denominators | revenue, EBIT(DA), EPS, FCF: each with period (TTM / FY1 / FY2), GAAP or adjusted, and status (reported, guided, consensus, own assumption) |
| guidance vs consensus | apart by more than about 5%: say which you use and why |
| fiscal calendar | if the year does not end in December, name the calendar months FY1 covers |

Clean the denominators before any multiple touches them:

- Negative denominator: the multiple is N/M. Do not print a negative or absolute-value multiple.
- One quarter × 4 is not TTM.
- Backlog, bookings, RPO or ARR are not revenue.
- One-offs: strip disposal gains, legal settlements and tax one-offs from earnings; charges
  called "non-recurring" in most years are recurring.
- Stock compensation: FCF is shown net of it.
- Cyclicals: show price ÷ peak earnings and price ÷ mid-cycle earnings side by side; a normal
  multiple on peak earnings is the classic trap.
- Two data sources disagreeing on an input by more than 10%: resolve or flag before use.

## 2. Read the price first

The question is not "is my value above the price" but "what must happen for today's price to
be fair, and is that more or less likely than the market assumes".

- Solve for the value the market puts on the thing your model values: today's EV against
  free cash flow to the firm for an operating company; today's market cap against equity cash
  flows, or P/TBV against return on tangible equity, for a bank or insurer.
- Growth, margin and reinvestment cannot all be solved from one price. Hold two at consensus
  or the company's history, solve for the third, then rotate which one is solved. Also state
  the multiple the market needs on the forecast denominator and how many years of
  above-cost-of-capital growth the price implies.
- Set each against the last four reported quarters, guidance and the company's own history.
  The sentence has this shape (hypothetical figures): "the price needs 14% growth for 8 years
  at a 22% margin; the last four quarters show 9% and 18%". A price needing the best stretch
  the company has ever had is a finding.
- Name the driver whose change moves value most. That is where the debate is, and where the
  rest of the audit should spend its effort.
- No-rerating case: today's multiple × the forecast denominator. It isolates what the
  forecast earns by itself; the price can still trade below it.

## 3. Two independent views

Ask which line of the accounts honestly measures what an owner gets, then value on it and
check it from a different family:

| where value sits | honest basis | second view | misleads here |
|---|---|---|---|
| bank or insurer: the balance sheet is the business | P/TBV against return on tangible equity | P/E | EV, net debt |
| REIT: cash defined by property income | P/FFO or P/AFFO | implied cap rate vs peers | P/E |
| holdco or fund: assets it owns | NAV per share | its discount to NAV vs its own history or listed peers | earnings multiples |
| several unlike segments | one line per segment, summed | consolidated multiple | one blended multiple |
| steady profits | normalised P/E | EV/EBIT or FCF yield | |
| heavy fixed assets | EV/EBIT (depreciation is a real cost) | FCF yield | EV/EBITDA on its own |
| paid largely in stock | SBC-adjusted FCF yield or EV/EBIT | DCF | EV/EBITDA |
| no profits yet | EV/Sales with a margin bridge to a target-year profit | DCF | P/E on negative EPS |

- Swapping the period or accounting basis of a denominator leaves you in the same method. Only
  a different family counts as the second view; with one family, the verdict is withheld.
  Families, by what the denominator measures: equity earnings (P/E), enterprise operating profit
  (EV/EBIT), free cash (FCF yield, DCF), assets (P/TBV, NAV, cap rate), sales (EV/Sales). For the
  business types in the table, its cross-check column is the accepted second view. P/TBV and P/E are tied through
  ROTE, so that pair counts only with ROTE taken from reported figures, not backed out.
- Peer multiples go on the target's own basis. Drop a doubtful peer rather than average it in,
  use the median, and place the target in the peer quartiles.
- **Disagreement test.** When the two midpoints sit more than about 25% apart (honeclaw's
  threshold; past it the gap is a modelling disagreement, not noise), swap the suspect
  assumption across the two methods and recompute, but only an assumption both actually use
  (growth, discount rate, normalised margin). Where the two rest on different bases, bridge
  them through their own inputs instead — P/TBV = P/E × ROTE when all three use the same
  earnings, share count and closing tangible equity (reported ROTE often uses the average;
  restate it first), so a bank whose two views disagree is carrying an implied return on
  tangible equity; test that number. Whatever
  closes most of the gap is the finding.
  Report both values; the base case uses the view whose weak input you can defend, and the
  other stays beside it. An average of the two is never the answer.

## 4. Check the terminal value

A DCF counts as a value only when its ledger is complete: the starting cash flow, growth
path, reinvestment, discount rate and terminal method each sourced. A model missing any of
them is a sensitivity sketch; label it so, and let the two-family result carry the answer. Here r is the rate matching the cash
flows: WACC for firm cash flows, cost of equity for equity cash flows.

- **g ≥ r: stop and fix.** The perpetuity formula has no meaning there. Long-run g stays near
  the risk-free rate or nominal GDP, on the same currency and inflation basis as r.
- Growth costs reinvestment: reinvestment rate = g ÷ ROIC. A terminal year that grows
  without reinvesting is free growth. Unless a durable advantage is evidenced, let terminal
  ROIC fade toward the cost of capital.
- Derive the terminal multiple from the business's own economics, keeping firm terms with firm
  terms: EV/NOPAT(next year) = (1 − g/ROIC) ÷ (WACC − g), or on an equity basis
  P/E(next year) = (1 − g/ROE) ÷ (cost of equity − g). Example: ROIC 12%, WACC 8%, g 3% gives
  (1 − 0.25) ÷ 0.05 = 15×. A peer's multiple today carries today's market mood into year ten.
- **Narrow spread (toolkit heuristic, after xbtlin, not a law).** When r − g is under about
  5 points, test how much value actually moves: recompute reinvestment for each g in the grid,
  then the value. Sensitivity depends on ROIC against r: at ROIC = WACC = 8%, g of 2% and 4%
  both give 12.5×, because growth earning only its cost adds nothing. If value does swing,
  label the result a scenario rather than an estimate and widen the grid.
- Terminal share = PV(terminal value) ÷ the same DCF's total present value (enterprise value
  for firm cash flows, equity value for equity cash flows). Above 80%: a finding;
  the answer rests on the perpetuity, so say so and widen the grid. Below 40%: check the
  terminal assumptions are not unreasonably harsh.
- Discrete risks (delisting, expropriation, a regulatory ban) go in their own
  probability-weighted scenario, not in a higher r, which would punish distant cash flows far
  more than near ones.
- Show a grid of r against g. Its centre cell must equal the base-case value; if it does not,
  the model is wrong somewhere.

## 5. Adjustment ledger

Every step away from a plain anchor (peer median, own five-year median, sector) is a ledger
line: anchor → adopted value, size in %, evidence, and what else in the model rests on the same
evidence. The checks read off the columns:

- **Evidence.** A premium and a discount each need observable evidence; neither is the default.
  A discount for uncertainty (unproven product, thin disclosure, governance) is its own line,
  separate from a discount for weaker economics, so each can be challenged on its own.
- **Size.** The evidence column sets each line's ceiling in the base case: one piece allows
  roughly ±30% off the anchor (honeclaw's threshold), two pieces with separate origins allow
  more. Whatever exceeds the ceiling is shown only in the high or low case.
- **Shared evidence.** If two lines cite the same story, it is being paid for twice. The usual
  case: a forecast above consensus for a year, plus a multiple above today's multiple measured
  on the same period and accounting basis. Show the evidence for each separately, or drop one.
  The same column catches dilution taken in EPS and again as a discount, and net debt
  subtracted in EV and again from equity.

## 6. Split the return

With e = change in EPS and m = change in the P/E, price return = (1 + e)(1 + m) − 1 =
e + m + e×m; dividends are added separately. Report the cross term: EPS +30% with the multiple
−25% gives −2.5% (−7.5 points of it from the cross term), not +5%.

For EV multiples, split in currency through the bridge, not in percentages on the price.
Example: EBITDA 10 at 10× is EV 100; with net debt 40, equity is 60. EBITDA +30% and the
multiple −25% give EV 13 × 7.5 = 97.5 and equity 57.5, a return of −4.2%, not −2.5%. With a
denominator that is not positive, use the currency bridge too.

## Auditing someone else's model

Run sections 1-6 against it. Each failure is a finding with three parts: the check, the
evidence (cell, line or figure) and the effect on value, with the corrected number. A check
that could not run because an input is missing is a gap, never a pass.

## Output

```
As-of: <price, timestamp, currency> | diluted shares <n, source, date> | cap check <±x%>
Snapshot table: <section 1 rows, each sourced and dated>; denominator fixes: <list or none>
Price implies: <growth, margin, reinvestment, multiple, years> vs <actuals, guidance>; key driver: <name>
Methods: <view 1: formula = value> | <view 2: formula = value> | gap <x%, input that closes it>
Terminal: g < r <yes / STOP> | spread <x pts, tested swing> | reinvestment <g/ROIC> | PV(TV)/DCF value <x%, finding if > 80%> | grid centre = base <yes/no>
Ledger: <anchor → value, size, evidence, shared with>; double counts: <none / list>
Value range: low <formula = value> | base <formula = value> | high <formula = value>
Price vs range: <where it sits>; no-rerating case <value>; return split e / m / e×m or currency bridge
Findings: <check — evidence — effect on value> | Gaps: <missing input — what it blocks>
Not advice: no entry, exit, target or sizing is given. Thesis tracking → thesis-ledger
```
