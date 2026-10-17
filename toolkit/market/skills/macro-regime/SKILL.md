---
name: macro-regime
description: Read the macroeconomic regime from the latest dated official data — a fixed nine-row dashboard, no classification when inputs are missing, and transmission to a specific business through named channels. Use for rates, inflation, recession risk or how macro conditions affect a business or plan.
version: 1.0.1
sources:
  - upstream/yennanliu-investskill/plugins/us-stock-analysis/skills/economics-analysis (MIT) — never use remembered readings; provenance header; memory means low confidence; conflicting sources shown, never averaged
  - upstream/anthropics-financial-services/plugins/partner-built/lseg/skills/macro-rates-monitor (Apache-2.0) — fixed dashboard; real rate = nominal − breakeven; 2s10s and 3M-10Y slopes; cycle, policy, real-rate and financial-conditions synthesis
  - upstream/tradermonty-claude-trading-skills/skills/macro-regime-detector (MIT) — fail closed on missing inputs; require a sustained signal before calling a regime change
  - upstream/tradermonty-claude-trading-skills/skills/scenario-analyzer (MIT) — first- and second-order transmission to sectors with a confidence per link; independent second pass
---

# Macro Regime

Macro analysis fails in two ways: stale numbers stated as current, and a correct regime call
that never reaches the decision it was meant to inform.

## Iron laws

1. **Every number is the latest official release, fetched now and dated** (citation rules as in
   `verified-research`). "Latest" means the most recent publication, whatever its frequency —
   GDP is quarterly, JOLTS lags about six weeks. Economic data is revised; remembered values are
   wrong more often than they look. A figure from model memory is marked **low confidence** and
   flagged at the top; it counts as missing for rule 3.
2. **Same dashboard every time.** Fill every row below, even when a row is unremarkable — the
   comparison across time is the point.
3. **Missing inputs block the call.** If a dashboard row cannot be filled with its latest release, say which, and do not classify the regime on the remainder. A regime change needs the signal to
   persist across more than one release, not one print.
4. **Conflicting sources are shown, not averaged.** Prefer the primary publisher, then the most
   recent vintage; show both values and say which was used.
5. **End at the business, not at the economy.** The output is what this regime does to the
   specific company, market or plan in question, through named channels.

## Data (free, primary)

| row | what to read | where (FRED series unless noted) |
|---|---|---|
| growth | real GDP growth (quarter on quarter, annualised), payrolls trend, ISM PMIs | `A191RL1Q225SBEA`, `PAYEMS`; ISM releases |
| inflation vs target | core PCE and core CPI, year on year and 3-month annualised | `PCEPILFE`, `CPILFESL`; BLS, BEA |
| labour | unemployment, openings per unemployed | `UNRATE`; BLS JOLTS |
| policy | policy target range vs the central bank's own neutral estimate | `DFEDTARU`, `DFEDTARL` (effective rate `DFF`); FOMC statement and Summary of Economic Projections |
| real rates | 10-year real yield (TIPS); breakeven = nominal − real | `DFII10`, `DGS10`, `T10YIE` |
| curve | 2s10s and 3M-10Y slopes; shape (normal, flat, inverted, re-steepening) | `T10Y2Y`, `T10Y3M` |
| credit | high-yield option-adjusted spread | `BAMLH0A0HYM2` (FRED keeps only about three years of ICE series; longer history needs ICE directly) |
| financial conditions | Chicago Fed NFCI; Fed balance sheet trend | `NFCI`, `WALCL` |
| dollar | broad trade-weighted dollar | `DTWEXBGS` |

Outside the US, use the equivalent central bank and statistics office (ECB data portal, Bank
of England database) and follow that central bank's own reporting structure.

## Step 1 — Fill the dashboard

For each row: current value, prior value, direction, as-of date, source, and a one-word signal
(e.g. expanding / contracting; above / at / below target; tight / balanced / slack;
restrictive / neutral / accommodative; tightening / easing).

## Step 2 — Classify, only if every row has its latest release

State the cycle position, the policy stance relative to neutral, whether real rates are
restrictive, and whether financial conditions are tightening or easing — each tied to the rows
that support it. Name what would change the call and which release would show it.

## Step 3 — Transmit to the business

For the company, market or plan in question, go channel by channel and mark each impact with a
direction and a confidence (high / medium / low) and the reason:

- **cost of capital** — funding, valuation multiples, appetite for long-payback projects;
- **customer budgets** — which buyer segments cut or grow first in this regime;
- **sales cycle** — approval layers and deal length when budgets tighten;
- **input and wage costs** — labour market tightness, cloud and hardware pricing;
- **FX** — revenue or cost in other currencies;
- **second order** — what customers' customers do, and what competitors with different
  balance sheets can afford that this company cannot (or the reverse).

Then have a fresh reviewer, given only the dashboard and the business description, challenge
the transmission links; keep the ones that survive.

Never turn the result into asset-allocation, buy/sell or market-timing recommendations.

## Output

```
Data & sources:     as-of date · sources · retrieval method · confidence (and any memory-based figures)
Dashboard:          the nine rows
Regime:             cycle · policy vs neutral · real rates · financial conditions — or "not classified" and why
Watch:              the releases that would change the call, with dates
Transmission:       channel · direction · confidence · reason
Implications:       for the decision at hand — framed as considerations, not investment advice
```
