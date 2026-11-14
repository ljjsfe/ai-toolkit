# Assignment checks and power sanity check

Read the assignment section when running Gate 2 (every readout); read the power section when
sizing a test in Gate 1. The gates and thresholds themselves stay in SKILL.md.

## Assignment checks — run beside SRM

Any hit can bias the readout; classify it in Gate 4.

- **Units seen in more than one variant.** Count units with exposures under two or more
  variant keys. PostHog's warning fires once that share passes 0.1% of exposed units with at
  least 5 such units; dropping them (the usual default) on an uneven split removes them
  unevenly. Look for an identity change or merge, a split edit mid-run, or a cached page
  carrying the assignment.
- **A flag shared with another running experiment.** Two live tests on one flag or
  assignment key are not independent: a pause or ship on one moves the other, and a re-run
  on the same key gives returning users their old draw. Each experiment gets its own key.
- **A filter that drops events but not units** (a numbers check, not a bias). A filter on
  metric events changes who counts as converted, not who is in the experiment — the exposed
  count stays fixed and the numbers are right for that definition. To restrict the population,
  set eligibility at exposure (targeting, an exposure-event filter or a custom exposure event),
  and say which definition the numbers used.
- **A code fallback logged as an exposure.** When the flag returns nothing and the code
  falls back to a default variant and logs it, that arm gains units the flag never
  assigned — even while the flag is off. Exposures in a variant the flag cannot serve, or
  one arm still gaining exposures while the flag is off, point here.

## SRM failure: where to look

Assignment logic that excludes some users, treatment failing to load or log for one arm,
pipeline loss, a restart or split change mid-run. A segment that fails `srm-segments` while
the total passes points at that platform's assignment or logging.

## Power: rule of thumb

From the PostHog reference: per-arm sample is about 16 × variance / (absolute effect)² — valid
for α = 0.05 two-sided, 80% power and equal arms, with variance p(1−p) for a rate. A sanity
check on the `expstats.py power-prop` / `power-mean` output only; never the reported figure.
