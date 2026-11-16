# WACC build and DCF validation

Read when a DCF enters the answer, as a method or as the model under audit.

## Build the discount rate line by line

Each line is sourced and dated; `scripts/dcf_check.py wacc` prints every step with values in.

| input | how | trap |
|---|---|---|
| risk-free rate | 10-year government yield in the cash flows' currency, from `macro-regime` | a US yield on euro cash flows |
| beta | regression of monthly returns over five years against the broad local index, or the median unlevered peer beta relevered at the target's market debt/equity: βL = βU × (1 + (1 − tax) × D/E) | a two-year daily beta for a thinly traded stock; an equity beta from a peer with a different leverage used as-is |
| equity risk premium | one named, dated source (Damodaran's implied ERP, or a stated house figure); 4.5–6% is the usual mature-market band | adding a country premium on top of a beta already measured against that country's index |
| cost of equity | CAPM: ke = rf + β × ERP | |
| pre-tax cost of debt | yield to maturity on the company's traded bonds; failing that, the rating's spread over rf; interest expense ÷ average debt only as a last resort, labelled so | book coupon on old debt when rates have moved |
| after-tax cost of debt | kd × (1 − marginal tax rate); use zero tax when the company has no taxable profit to shield | effective rate inflated by one-off tax items |
| weights | market value of equity (price × diluted shares, the snapshot row) and debt (market value if traded, book otherwise; leases in or out, same choice as the EV bridge) | target weights silently used instead of today's without saying so |

WACC = ke × E/(E+D) + kd(1 − t) × D/(E+D). Debt is gross by default; weighting on net debt is a
stated choice, and with net cash the script falls back to gross rather than produce a negative
debt weight. A WACC outside 5–20% is not wrong by itself but gets its inputs read again.

Example (hypothetical): rf 4%, β 1.2, ERP 5% → ke = 0.04 + 1.2 × 0.05 = 10%; kd 5%, tax 20% →
4%; E 800, D 200 → WACC = 10% × 0.8 + 4% × 0.2 = 8.8%.

## Validate the DCF before reading its value

Write the model's inputs to JSON (`fcf` per year, `r`, `g`, `net_debt`, `shares`,
`base_value`, optional `terminal_fcf` and the r × g `grid`) and run
`scripts/dcf_check.py check model.json`. It recomputes the value with end-of-year discounting
(or, with `"mid_year": true` in the JSON, the mid-year convention: explicit years discounted at
0.5, 1.5, … and the terminal value at n − 0.5) and fails when:

- g ≥ r;
- the recomputed per-share value differs from the model's stated value by more than 0.5% (the
  answer does not follow from its own inputs);
- PV(terminal value) is above 80% of the DCF total (below 40% is a note to check the terminal is
  not unreasonably harsh);
- the grid's middle row and column are not the model's r and g, or its centre cell differs from
  the base value.

A model built on the mid-year convention differs from end-of-year discounting by roughly half
a year of r (about 4% at r = 8%), far outside the 0.5% tolerance: set `"mid_year": true` to
match the model's convention, and say which convention was used. Do not loosen the tolerance
to force a match. Exit code 1 means a finding for the audit, with the
script's line as its evidence.
