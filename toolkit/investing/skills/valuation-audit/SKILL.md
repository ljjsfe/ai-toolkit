---
name: valuation-audit
description: "Audit a stock valuation, yours or someone else's, for the errors that make it wrong — no price or cheap/expensive call without a dated quote and diluted share count, read what today's price implies before valuing, two independent method families, terminal value checked against growth, reinvestment and the discount rate, each peer premium stated once, and return split into fundamentals vs multiple change. Use for 'is X cheap', fair value, DCF or multiple checks; to track a thesis use thesis-ledger. Also for 估值, 贵不贵, 合理价值, \"should I buy X\" (answered as a valuation audit, never as advice)."
version: 1.1.0
sources:
  - upstream/b-m-capital-research-honeclaw/skills/valuation-audit/SKILL.md (MIT) — structure of §1 (snapshot rows, red flags); 3%, 5%, 25%, ±30% thresholds; same-family rule; return split; no-rerating case
  - Mauboussin and Rappaport, "Expectations Investing" (2001; rev. 2021), https://www.expectationsinvesting.com/ — §2, price-implied drivers and forecast period
  - Damodaran, valuation teaching material, https://pages.stern.nyu.edu/~adamodar/ — g near risk-free, reinvestment = g/ROIC, ROIC fade
  - upstream/xbtlin-ai-berkshire/codex-skills/investment-research/SKILL.md (MIT) — terminal multiple from economics not peers; r−g spread; same-basis r and g; discrete-risk scenario
  - upstream/anthropics-financial-services/plugins/agent-plugins/model-builder/skills/dcf-model/SKILL.md (Apache-2.0) — TV below 40% check; grid centre equals base
  - upstream/anthropics-financial-services/plugins/agent-plugins/model-builder/skills/comps-analysis/SKILL.md (Apache-2.0) — median, drop doubtful peers, quartiles, 10% source gap
  - upstream/yennanliu-investskill/prompts/dcf-valuation.md (MIT) — g below r; TV above 80% flag
  - upstream/yennanliu-investskill/prompts/stock-valuation.md (MIT) — SBC-adjusted FCF; no EV bridge for P/E price
  - upstream/tradermonty-claude-trading-skills/skills/kanchi-dividend-sop/references/valuation-and-one-off-checks.md (MIT) — REIT row; one-off profit checks
---

# Valuation Audit

Most wrong valuations are wrong for boring reasons: a stale price, basic instead of diluted
shares, a one-off gain in the denominator, a terminal value doing all the work, or one story
paid for twice. The audit finds those, then answers the question the price is actually asking.
Output is a value range with its assumptions and a list of findings, never a recommendation.

## Hard stops

- **No quote, no price talk.** A timestamped price and a dated diluted share count gate every
  price-dependent number: cap, multiples, range, the cheap/expensive verdict. Missing either,
  say which calculations are blocked, then give what still stands on its own (statement
  figures you confirmed, the business-type read).
- **No advice in any form:** no buy, sell, add or exit levels, no position size, no target
  dressed as a recommendation. "Where should I buy?" gets the value range and what today's
  price assumes, nothing more. Never restate either end of the range as an entry or exit level.
- **Every figure is traceable and recomputable.** Each input carries source and date; each
  derived number shows its formula with values plugged in, or comes from a script. Gather
  inputs with the `verified-research` method; take the risk-free rate and rate backdrop from
  `macro-regime`.

## 1. Freeze the snapshot

One as-of price for the whole piece. If two prices appear anywhere, the audit stops until one
is removed. Then build this table, each row with source and date:

| row | what to check |
|---|---|
| shares | latest diluted count (options, RSUs, convertibles in the money); say so if you use fully diluted instead |
| market cap | price × diluted shares, compared with the quoted cap. Over 3% apart (honeclaw's tolerance, roughly the gap stock compensation alone can open between basic and diluted counts) means explain it before going on. Example: 42.00 × 310m = 13.0bn against a quoted 12.4bn is 5% off; the quote used 296m basic shares, so the gap is explained |
| EV bridge | market cap + debt (state whether leases are in) − cash + preferred + minority interests − equity-method stakes. EV multiples pair with EV, P/E and FCF yield with market cap; a P/E-derived price is already per share and is not bridged again |
| denominators | revenue, EBIT(DA), EPS, FCF: each with period (TTM / FY1 / FY2), GAAP or adjusted, and status (reported, guided, consensus, own assumption) |
| guidance vs consensus | apart by more than about 5%: say which you use and why |
| fiscal calendar | if the year does not end in December, name the calendar months FY1 covers |

Clean the denominators before any multiple touches them:

- Currency: price and statements in different currencies get converted first, rate shown.
- Units: millions vs billions checked on every row.
- Negative denominator: the multiple is N/M. Do not print a negative or absolute-value multiple.
- One quarter × 4 is not TTM.
- Backlog, bookings, RPO or ARR are not revenue.
- One-offs: strip disposal gains, legal settlements and tax one-offs from earnings; charges
  called "non-recurring" in most years are recurring.
- Stock compensation: FCF is shown net of it. For a business that pays heavily in stock,
  EBITDA-based multiples flatter it, so prefer EBIT or SBC-adjusted FCF.
- Cyclicals: show price ÷ peak earnings and price ÷ mid-cycle earnings side by side; a normal
  multiple on peak earnings is the classic trap.
- Two data sources disagreeing on an input by more than 10%: resolve or flag before use.

## 2. Read the price before valuing

The question is not "is my value above the price" but "what must happen for today's price to
be fair, and is that more or less likely than the market assumes".

- Growth, margin and reinvestment cannot all be solved from one price. Hold two at consensus
  or the company's history, solve today's EV for the third, then rotate which one is solved.
  Also state the multiple the market needs on the forecast denominator and how many years of
  above-cost-of-capital growth the price implies.
- Set each against the last four reported quarters, guidance and the company's own history:
  "the price needs 14% growth for 8 years at a 22% margin; the last four quarters show 9% and
  18%". A price needing the best stretch the company has ever had is a finding.
- Name the driver whose change moves value most. That is where the debate is, and where the
  rest of the audit should spend its effort.
- No-rerating case: today's multiple × the forecast denominator. It isolates what the
  forecast earns by itself; the price can still trade below it.

## 3. Value it two independent ways

Pick the primary method by how the business makes money, and the check from a different family:

| business | primary | check | avoid |
|---|---|---|---|
| mature, profitable | normalised P/E | EV/EBIT or FCF yield | |
| loss-making growth | EV/Sales with a margin bridge to a target-year profit | DCF | P/E on negative EPS |
| capital-heavy | EV/EBIT (depreciation is a real cost) | FCF yield | EV/EBITDA on its own |
| asset-light, stock-paid | SBC-adjusted FCF yield or EV/EBIT | DCF | EV/EBITDA |
| conglomerate | sum of the parts, one line per segment | consolidated multiple | one blended multiple |
| holdco or fund | NAV per share and the premium or discount to it | that discount vs its own history or listed peers | earnings multiples |
| bank or insurer | P/TBV against return on tangible equity | P/E | EV, net debt |
| REIT | P/FFO or P/AFFO | implied cap rate vs peers | P/E |

- Swapping the period or accounting basis of a denominator leaves you in the same method. Only
  a different family counts as the second view; with one family, the verdict is withheld.
- Peer multiples go on the target's own basis. Drop a doubtful peer rather than average it in,
  use the median, and place the target in the peer quartiles.
- Midpoints more than about 25% apart (honeclaw's threshold; past it the gap is a modelling
  disagreement, not noise) are never blended. Trace the gap to the input responsible, pick the
  result you have more faith in with the reason, and show the other as a cross-check.

## 4. Check the terminal value

Show a DCF only if starting FCF, growth path, capex, discount rate and terminal method can each
be written out; otherwise stay with multiples and say why.

Here r is the rate matching the cash flows: WACC for firm cash flows, cost of equity for
equity cash flows.

- g stays below r, near the risk-free rate or nominal GDP, on the same currency and inflation
  basis as r. If r − g is under about 5 points, small moves in g swing the value: label the
  result a scenario rather than an estimate, and widen the grid.
- Growth costs reinvestment: reinvestment rate = g ÷ ROIC. A terminal year that grows
  without reinvesting is free growth. Unless a durable advantage is evidenced, let terminal
  ROIC fade toward the cost of capital.
- Derive the terminal multiple from the business's own economics, keeping firm terms with firm
  terms: EV/NOPAT(next year) = (1 − g/ROIC) ÷ (WACC − g), or on an equity basis
  P/E(next year) = (1 − g/ROE) ÷ (cost of equity − g). A peer's multiple today carries today's
  market mood into year ten.
- Terminal value above 80% of EV: the answer rests on the perpetuity, so say so and widen the
  sensitivity. Below 40%: check the terminal assumptions are not unreasonably harsh.
- Discrete risks (delisting, expropriation, a regulatory ban) go in their own
  probability-weighted scenario, not in a higher r, which would punish distant cash flows far
  more than near ones.
- Show a grid of r against g. Its centre cell must equal the base-case value; if it does not,
  the model is wrong somewhere.

## 5. Premiums, stated once

Any multiple above or below the anchor gets one sentence: "From <named anchor: peer median,
own five-year median, sector> to <value> because <observable evidence>."

- Two pieces of evidence that do not lean on each other are the price of a move beyond about
  ±30% from the anchor (honeclaw's threshold). One piece buys a smaller base-case move; the
  rest belongs to the high case.
- Discounts get the same sentence. A business with no demonstrated edge starts below the peer
  median, not at it.
- Count each reason once. Above-consensus earnings and an above-today multiple resting on the
  same story is one bet taken twice; list the evidence for each separately or drop one.
  Dilution already in EPS is not deducted again; net debt already in EV is not subtracted
  twice.

## 6. Split the return

With e = change in EPS (or the chosen denominator per share) and m = change in the multiple,
price return = (1 + e)(1 + m) − 1 = e + m + e×m; dividends are added separately. Report the
cross term: earnings +30% with the multiple −25% gives −2.5%, not +5%. With a denominator that
is not positive, bridge in currency instead. For EV multiples, the rerating acts on EV, so
carry it through net debt to equity in currency rather than applying e and m to the price.

## Auditing someone else's model

Run sections 1-5 against it. Each failure is a finding with three parts: the check, the
evidence (cell, line or figure) and the effect on value, with the corrected number. A check
that could not run because an input is missing is a gap, never a pass.

## Output

```
As-of: <price, timestamp, currency> | diluted shares <n, source, date> | cap check <±x%>
Snapshot table: <section 1 rows, each sourced and dated>; denominator fixes: <list or none>
Price implies: <growth, margin, reinvestment, multiple, years> vs <actuals, guidance>; key driver: <name>
Methods: <family 1: formula = value> | <family 2: formula = value> | divergence <x%, cause>
Terminal: g < r by <x pts> | reinvestment <g/ROIC> | TV share of EV <x%> | grid centre = base <yes/no>
Premium: <anchor → value because evidence>; double counts: <none / list>
Value range: low <formula = value> | base <formula = value> | high <formula = value>
Price vs range: <where it sits>; no-rerating case <value>; return split e / m / e×m
Findings: <check — evidence — effect on value> | Gaps: <missing input — what it blocks>
Not advice: no entry, exit, target or sizing is given. Thesis tracking → thesis-ledger
```
