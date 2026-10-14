---
name: market-scan
description: Scan a market for competitors and unmet demand with claims that survive scrutiny — label every competitor fact observed (source, date), inferred or implication; treat "not seen" as different from "absent"; rank demand signals by behaviour (posted workarounds and rejected pull requests over upvotes); score candidate opportunities on fixed bands; kill an idea only by naming what already does it; and return "nothing solid" rather than invent one. Use for competitor teardowns, market maps, positioning, unmet needs, pain points, idea mining, and "who wins here and why".
version: 1.0.0
sources:
  - upstream/marketingskills/skills/{competitor-profiling,competitors} (MIT) — observed / inferred / implication, not observed is not absent, dated snapshots, switching evidence both ways
  - upstream/geekjourneyx-github-demand-radar/references/{rice-jtbd-rubric.md,pr-scan-guide.md,negative-filters.md} (MIT) — job inference, workaround and rejected-PR signals, not-noise table, standalone-tool ease
  - upstream/mvanhorn-last30days-skill (MIT) — recency-windowed signals and the nothing-solid floor (installed tool; see toolkit/external.yaml)
  - upstream/wanshuiyin-auto-claude-code-research-in-sleep/skills/novelty-check (MIT) — name the prior work before killing an idea
---

# Market Scan

Two jobs, one discipline: **who is already here** (competitors) and **what is still missing**
(demand). Sources follow `verified-research`.

## Iron laws

1. **Three labelled layers for every competitor fact.** *Observed* — what a source says, with
   source and date. *Inferred* — your reading, with confidence when it matters. *Implication*
   — what it might mean for us, as an option or question, not a conclusion.
2. **Not observed is not absent.** "Not listed on their pricing page as of <date>" — never
   "they don't have it" unless docs or a trial confirm it. One visit cannot support "hasn't
   changed in years"; only dated history can.
3. **The request is not the need.** Write the job behind each demand signal — what the person
   is trying to get done, in what context ("export to CSV" is usually "feed my BI tool").
4. **Behaviour beats opinion.** Strongest to weakest: a posted workaround > a pull request the
   maintainer rejected > a long-open issue with steady reactions > comments and upvotes > likes.
5. **Killing an idea requires naming what already does it** for the same users. A crowded space
   with a stated, defensible difference is not a kill.
6. **"Nothing solid" is a valid result.** Never pad the list; say which sources failed or did not
   run instead of reporting them as "nothing found".

## Competitors

1. Scope: our product, the decision this feeds, the competitors (ask if a reference is
   ambiguous; discovering them is part of the job — say how they were found).
2. Per competitor: positioning and target user from their own pages, pricing and packaging,
   product surface from docs and changelog, momentum (release cadence, hiring, funding), what
   users praise and complain about.
3. **Switching evidence both ways** — why people leave them for us and us for them. It outranks
   feature tables.
4. Re-verify before reusing an old claim: current (new date), changed, or unverifiable (soften
   or remove).

## Demand

1. Collect signals: GitHub issues and closed-unmerged PRs (`gh search`), Reddit, HN, arXiv,
   Techmeme and Polymarket via `last30days` if installed (else dated web search), reviews and
   domain forums. Keep `signal · URL · quote · date · platform · type`. Do not discard silent
   reactions (reach), "won't fix" replies (confirmed gap) or issues open for years (chronic pain).
2. Cluster by job, not keyword; a job needs at least two independent authors.
3. Score each candidate 1–5 on the same bands every time:

   | factor | 1 | 3 | 5 |
   |---|---|---|---|
   | reach (distinct authors) | 1–2 | 5–15 | 30+ |
   | impact (cost to the person: time or money lost) | minor annoyance | hours a month or a real expense | blocks their work or costs significant money |
   | confidence | one platform, one signal type | two platforms or types | several platforms, incl. a rejected PR or long-open issue |
   | ease — only when the decision is a tool or wrapper | team-months | one developer, weeks | one developer, days |

   Keep candidates with no factor below 2 (ease excluded unless the decision is a tool or
   wrapper); rank by total; show all the numbers.
4. For each kept candidate, find who already serves the job and the stated difference (law 5).

## The angle

End with one sentence: where incumbents are structurally unable or unwilling to follow (pricing
model, customer base, architecture, channel), what must be true for it to matter, and the
questions that would confirm or kill it — those feed `product-scoping`'s red-team.

## Output

```
Decision this informs:
Competitors:     table — positioning · price · strengths · weaknesses, each cell observed (date) or inferred
Switching:       both directions
Demand:          up to 5 candidates — job · strongest evidence · four scores · closest existing solution
                 or "nothing solid" and what was searched (and what failed)
Angle:           one sentence · what must be true · questions to test
```
