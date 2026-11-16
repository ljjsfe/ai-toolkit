# Cleaning the inputs, and the EV return split

Read when section 1 of the skill hits one of these cases, or section 6 splits an EV-multiple return. The gates stay in `SKILL.md`; this
file holds the procedure behind them.

## Market-cap check, worked

Over 3% apart is honeclaw's tolerance, roughly the gap stock compensation alone can open
between basic and diluted counts. Example: 42.00 × 310m = 13.02bn against a quoted 12.4bn is
5% off; the quote used 296m basic shares (42.00 × 296m = 12.43bn), so the gap is explained.

## Currency and units

ADRs and foreign issuers: convert EPS and every denominator into the price currency at a dated
rate written in the snapshot table, and per ADR multiply by the ADR ratio (ordinary shares per
ADS). A dollar price over euro EPS is not a P/E.

One unit style for the whole piece (m or bn, never both, never 亿 mixed with $bn); check the
magnitude before writing a figure: 8.1bn written as 81bn or 16.7bn as 1.67bn is the common
slip. Recompute every per-share result from the formula in the same sentence.

## One-off checks

Strip disposal gains, legal settlements and tax one-offs from earnings; charges called
"non-recurring" in most years are recurring. Also flag margin expansion that revenue quality
does not explain (price, mix and volume flat or worse while margin jumps: cost capitalised,
reserves released, a cut that will not repeat) and a dividend paid from new debt or asset sales
(dividends above FCF while net debt rises). Count over these five checks: disposal gains, legal
or tax one-offs, recurring "non-recurring" charges, unexplained margin expansion, debt-funded
dividend. Two or more of these one-off flags (any two of the five): the earnings base is not
clean enough for a base case; use the cleaned figure or withhold.

## Cyclicals

Show price ÷ peak earnings and price ÷ mid-cycle earnings side by side; a normal multiple on
peak earnings is the classic trap. Mid-cycle EPS = median net margin over a full cycle (5–10
years of annual figures) × current revenue ÷ diluted shares; say where today's margin sits in
that range (peak, trough, middle).

Current revenue can itself be at a price peak (commodity or memory pricing): then mid-cycle
margin × current revenue still overstates normal earnings; also show it on mid-cycle revenue
(or volume × mid-cycle price) and say which one the range uses.

Before normalising, look for contract coverage (long-term agreements, take-or-pay, capacity
reserved by customers) in filings and transcripts: value the contract-locked part at contract
price and term, and normalise only the spot-exposed part. Coverage not found: say the estimate
treats the business as fully spot and is conservative if coverage is high.

## Forward revenue beyond FY1

Grade each block of forward revenue (project, product batch, repeat customer group):

| grade | evidence | where it enters |
|---|---|---|
| A | operating and checkable, or contracted with delivery, customer qualification, funding and permits in place | base case, on its delivery curve |
| B | demand evidenced and the remaining conditions have a checkable path (list them with timing) | base case only in part, with the condition named |
| C | roadmap, TAM, framework agreement not exercised, permits or funding unresolved | high case only |

Guidance and consensus are source types, not grades. Per block write gross size, size that can
execute this period, size in the base case and why the rest is out.

## Two sources disagree on an input by more than 10%

Resolve in this order: the primary record (filing, company release, exchange data) wins over
an aggregator or data vendor; between sources of the same rank, the most recently dated one
wins. Write both values with source and date, say which one the model uses and why, and never
take the midpoint of the two. If neither rule decides it, flag the input and run the value on
both (toolkit policy).

## Return split through the EV bridge, worked

EBITDA 10 at 10× is EV 100; with net debt 40, equity is 60. EBITDA +30% and the multiple −25%
give EV 13 × 7.5 = 97.5 and equity 57.5, a return of −4.2%, not the −2.5% the percentage split
on the price gives.
