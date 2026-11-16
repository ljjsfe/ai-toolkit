# Red team and checker: full procedure

Read this when a run includes the red team (section 3b of SKILL.md) or when you brief the
checker (section 4). The gates, sizes and verdict table stay in SKILL.md.

## Red team brief

Runs after the draft exists and before the checker, so one check covers what the red team
adds. A fresh subagent (without subagents, a separate pass started from the brief alone) whose
job is to make the conclusion fail if it deserves to. The red team gets the bottom line and
the key findings: the draft's answer verbatim and the 3–7 findings it rests on, each with its
record number, plus the 2–4 points you are least sure of and any option the draft never
compared. It does not get the argument. It searches for:

- the strongest counter-evidence and the best-argued opposing view, stated at its strongest;
- newer data, replications, corrections or retractions that undercut a key source;
- the weakest links: a conclusion on a single origin, a source with an interest, an
  extrapolation from a different population, period or definition;
- the key assumptions the answer silently needs (each with what changes if false) and a
  premortem: a year on the answer proved wrong — the 3–5 likeliest reasons, checking the ones
  checkable now.

What it finds is admitted as records like any other (R/D, opened, verbatim). It reports the
three most serious challenges, each rated changes the conclusion / lowers confidence / minor.
If it finds nothing, it says what it tried.

## Audit script steps

Before the checker runs, run `scripts/research_audit.py` (standard-library Python):

1. `research_audit.py records records.md` — every record has its fields; origins are counted.
   Add `--since <date>` for fast-changing facts (prices, versions, statistics) to list stale sources.
2. `research_audit.py draft draft.md --records records.md --out claims.md` — fix every error: a
   cited R/D that does not exist, or a URL in the draft that no record holds (not opened this
   session, or invented). Each "uncited" sentence gets a record or is cut; a "single origin"
   section gets a second origin or a lower confidence. `claims.md` is the claims list the checker
   receives.
3. `research_audit.py links records.md` when the shell has network access — dead links and
   passages missing from their page. Re-open BLOCKED or NOT FOUND pages with a fetch tool before
   dropping them; if it reports the network is blocked, say links were not machine-checked.

If Python cannot run, do these checks by hand and say the script was not run.

## Checker: blind extraction first, comparison second

Direct records: the checker re-opens the source and quotes the passage it relied on. Derived
records: it recomputes the arithmetic from the inputs, or tests whether the step follows from
them; it does not look for a page that states the result.

For each direct record the checker first gets only the locator (URL, or title and first
author) and the subject of the claim — not the claim, the passage or the record's other
fields. It opens the source and writes what the source itself states: for a paper or report
its title, authors in order, year, venue or publisher and identifier (DOI, arXiv id); for the
subject, the figure, date, scope or qualifier, and who is said to have said or done it. Only
then does it read the claim and the record and compare field by field — same / differs (both
values written out) / absent — and assign the verdict from that comparison. Reading the claim
first anchors the checker on it, which is how a dropped author, a wrong year or a lost
qualifier survives a check. The upstream does this for bibliographic fields; applying it to
the claim's own fields is toolkit policy. Without subagents, do the extraction for all records
before opening the claims list.
