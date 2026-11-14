---
name: macro-regime
description: Read the macroeconomic regime from the latest dated official data — a fixed ten-row dashboard fetched by script (recession signals included), no classification when inputs are missing, and transmission to a specific business through named channels. Use for rates, inflation, recession risk or how macro conditions affect a business or plan.
version: 1.1.0
sources:
  - upstream/yennanliu-investskill/plugins/us-stock-analysis/skills/economics-analysis (MIT) — never use remembered readings; provenance header; memory means low confidence; conflicting sources shown, never averaged [port "remembered values are" "marked low confidence" "conflicting sources are shown, not averaged"]
  - upstream/yennanliu-investskill/plugins/us-stock-analysis/skills/economics-analysis (MIT) — recession indicators (Sahm rule, recession probability, inversion duration) [port "sahm rule real-time" "def inversion_stats"]
  - upstream/yennanliu-investskill/plugins/us-stock-analysis/skills/economics-analysis (MIT) — the NY Fed term-spread recession model and the Conference Board leading index (neither on FRED) [gap not fetched; read them from the publisher when a call depends on them]
  - upstream/anthropics-financial-services/plugins/partner-built/lseg/skills/macro-rates-monitor (Apache-2.0) — fixed dashboard; real rate = nominal − breakeven; 2s10s and 3M-10Y slopes; cycle, policy, real-rate and financial-conditions synthesis [port "same dashboard every time" "breakeven = nominal − real" "2s10s and 3m-10y slopes" "state the cycle position, the policy stance"]
  - upstream/anthropics-financial-services/plugins/partner-built/lseg/{.mcp.json,skills/macro-rates-monitor} (Apache-2.0) — a live data connector, replaced here by FRED's keyless CSV endpoint [port "fredgraph.csv?id=" "run `scripts/fred_dashboard.py dashboard`"]
  - upstream/tradermonty-claude-trading-skills/skills/macro-regime-detector (MIT) — fail closed on missing inputs; require a sustained signal before calling a regime change [port "missing inputs block the call" "persist across more than one release"]
  - upstream/tradermonty-claude-trading-skills/skills/macro-regime-detector/{references/regime_detection_methodology.md,scripts/scorer.py} (MIT) — stored prior readings to compare against [port "def compare(current" "the same reading in two consecutive saved"]
  - upstream/tradermonty-claude-trading-skills/skills/macro-regime-detector/{references/regime_detection_methodology.md,scripts/scorer.py} (MIT) — 6- and 12-month moving-average crossovers with confirmation scoring; cross-asset components incl. stock-bond correlation [gap not ported]
  - upstream/tradermonty-claude-trading-skills/skills/scenario-analyzer (MIT) — first- and second-order transmission to sectors with a confidence per link; independent second pass [port "a direction and a confidence" "what customers' customers do" "challenge the transmission links"]
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
   comparison across time is the point. Run `scripts/fred_dashboard.py dashboard` (standard-library
   Python, no API key): it fetches every US row from FRED's `fredgraph.csv?id=<SERIES>` endpoint
   with each observation's own date, prints derived values with their formula, and saves the
   snapshot to `~/.investing/macro/<date>.json` (`--dir` to change) for the next comparison. If it
   cannot run (no Python, no network), fetch each series yourself and say so.
3. **Missing inputs block the call.** If a dashboard row cannot be filled with its latest release, say which, and do not classify the regime on the remainder. A regime change needs the signal to
   persist across more than one release, not one print: the same reading in two consecutive saved
   snapshots whose underlying release dates differ (the script's `comparison` block shows it). With
   no earlier snapshot, nothing is sustained yet; say so.
4. **Conflicting sources are shown, not averaged.** Prefer the primary publisher, then the most
   recent vintage; show both values and say which was used.
5. **End at the business, not at the economy.** The output is what this regime does to the
   specific company, market or plan in question, through named channels.

## Data (free, primary)

| row | what to read | where (FRED series unless noted) |
|---|---|---|
| growth | real GDP growth (quarter on quarter, annualised), payrolls trend, manufacturing/activity PMI | `A191RL1Q225SBEA`, `PAYEMS`; ISM release (or NY/Philly Fed surveys `GACDISA066MSFRBNY`, `GACDFSA066MSFRBPHI` when ISM is gated) |
| inflation vs target | core PCE and core CPI, year on year and 3-month annualised | `PCEPILFE`, `CPILFESL`; BLS, BEA |
| labour | unemployment, openings per unemployed | `UNRATE`, `JTSJOL`, `UNEMPLOY` (BLS JOLTS) |
| policy | policy target range vs the central bank's own neutral estimate | `DFEDTARU`, `DFEDTARL` (effective rate `DFF`); FOMC statement and Summary of Economic Projections |
| real rates | 10-year real yield (TIPS); breakeven = nominal − real | `DFII10`, `DGS10`, `T10YIE` |
| curve | 2s10s and 3M-10Y slopes; shape (normal, flat, inverted, re-steepening) | `T10Y2Y`, `T10Y3M` |
| credit | high-yield option-adjusted spread | `BAMLH0A0HYM2` (FRED keeps only about three years of ICE series; longer history needs ICE directly) |
| financial conditions | Chicago Fed NFCI; Fed balance sheet trend | `NFCI`, `WALCL` |
| dollar | broad trade-weighted dollar | `DTWEXBGS` |
| recession signals | Sahm rule real-time reading (triggered at 0.50), smoothed recession probability, months the 3M-10Y curve was inverted in the last 24 and the current run | `SAHMREALTIME`, `RECPROUSM156N`, `T10Y3M` |

Outside the US, use the equivalent central bank and statistics office (ECB data portal, Bank
of England database) and follow that central bank's own reporting structure.

## Step 1 — Fill the dashboard

For each row: current value, prior value, direction, as-of date, source, and a one-word signal
(e.g. expanding / contracting; above / at / below target; tight / balanced / slack;
restrictive / neutral / accommodative; tightening / easing).

## Step 2 — Classify, only if every row has its latest release

The script exits non-zero and marks `complete: false` when any series is missing; then do not
classify. Policy neutral comes from the latest FOMC Summary of Economic Projections, which the
feed does not carry — read and date it separately.

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
the transmission links (or run a labelled self-challenge pass if subagents are unavailable); keep
the ones that survive.

Never turn the result into asset-allocation, buy/sell or market-timing recommendations.

## Output

```
Data & sources:     as-of date · sources · retrieval method · confidence (and any memory-based figures)
Dashboard:          the ten rows (script output, with the command run and its as-of dates)
Regime:             cycle · policy vs neutral · real rates · financial conditions — or "not classified" and why
Watch:              the releases that would change the call, with dates
Transmission:       channel · direction · confidence · reason
Implications:       for the decision at hand — framed as considerations, not investment advice
```
