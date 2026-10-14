---
name: verified-research
description: Research a question across real sources and produce a verified, argued answer — question the question first, set a tool-call budget, cite only pages actually opened, count independent origins, have an independent verifier re-check every claim, and write an argument chain rather than a topic dump. Use as the citation and verification method behind any research, and for standalone technology, literature or investment questions where wrong citations are costly; for a settled single fact, just answer.
version: 1.0.0
sources:
  - upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — question-the-question phase, argument-chain test, subagent cap
  - upstream/jalald-verified-research/skills/verified-research/ (MIT) — opened-only citations, origin counting, independent verifier, tiered budgets, one gap-filling round
  - upstream/wanshuiyin-auto-claude-code-research-in-sleep/skills/citation-audit (MIT) — wrong-context citation check
---

# Verified Research

Research fails in three predictable ways: it answers the wrong question, it cites what it
never read, and it reports topics instead of conclusions. Each step below blocks one.

## Iron laws

1. **Question the question before searching.** Write down the decision this feeds, the
   assumption hidden in the question, what a good answer must contain, and 2–3 falsifiable
   hypotheses (at least one you expect to be wrong). Skipping this and fanning out searches
   is the most common and most expensive research failure.
2. **Cite only what was opened in this session.** A search snippet is a lead, not evidence. A
   URL enters the answer only if its page was fetched and the claim was read on it. Some fetch
   tools return a model-written summary instead of the page: for every key claim, quote
   verbatim from the raw page text (or a grep of it), never from a summary.
3. **Count independent origins, not links.** Five articles repeating one press release are
   one source. Every evidence entry records its origin.
4. **The writer does not verify the writing.** An independent verifier, working from a claims
   list rather than the draft, re-opens each cited source and marks every claim.
5. **Confidence comes from agreement, not from a self-rating** — high, moderate or low: high when several independent,
   high-quality sources agree; moderate when support is thinner or partly indirect; low when it
   rests on one origin or sources conflict.

## Step 0 — Pick a budget and stop when it is spent

| tier | when | tool calls | subagents |
|---|---|---|---|
| quick | one bounded question, sources likely agree | up to ~8 | none |
| standard | a decision with a few moving parts | up to ~70 | up to 4 |
| deep | contested, high-stakes, or many entities | up to ~120 | 4–6 |

Escalate one tier only for a named trigger: sources disagree on a material point, the trail
runs through re-reporting, or a "simple" fact hinges on a definition. Subagents follow
`agent-orchestration` (no nested spawning — one unconstrained run reported in the
seanellyjames deep-research skill grew from 3 agents to 149).

## Step 1 — Frame (no searching yet)

Produce, in a few lines: the decision · the hidden assumption · the good-answer standard ·
the hypotheses · the sub-questions · where each sub-question's primary sources are.

## Step 2 — Gather

- Read primary sources fully before broad search (the filing, the paper, the docs, the data).
- Give each subagent a distinct sub-question, so their searches do not duplicate.
- For every claim kept, write an evidence entry:
  `claim · URL opened · exact supporting sentence · origin · date`.
- One gap-filling round after the first pass, then move on: past that point more searching
  tends to add noise faster than accuracy.

## Step 3 — Verify (independent)

Give a fresh verifier the claims list (not the draft) and the evidence entries. In the quick
tier, re-open each cited page yourself after drafting, working from the claims list. For each
claim it re-opens the source and marks one of:

| verdict | meaning |
|---|---|
| supported | the quoted sentence says it |
| partial | says less, or with a qualifier the claim dropped |
| not supported | the page does not say it |
| contradicted | the page says the opposite |
| unreachable | could not be opened now |

It also checks the dangerous case: **a real source cited for something it does not support,
or in a context that reverses its meaning.** This is harder to catch than a fabricated
citation and does more damage. Drop or rewrite everything not marked supported.

## Step 4 — Write an argument, not an inventory

- **Section titles state conclusions.** If a title could have been the search query that
  produced it, the section is an inventory. Rewrite it as the judgement the section proves.
- **The prose must stand alone.** Delete the tables and bullets mentally; if what remains
  does not carry the argument, the thinking is not done.
- Lead with the answer to the decision, then the argument chain, then what would change the
  conclusion.
- State where independent sources agree, where they conflict (with the clashing sources),
  and the one question that would resolve the biggest conflict.
- Confidence per conclusion, per Iron Law 5 (high / moderate / low), with the reason.

## Output

```
Answer (for the decision):
Argument:            sections whose titles are claims
Agreement / conflict map:
What would change this:
Confidence per conclusion, with the reason:
Sources:             only opened URLs, each with its origin
Not verified:        claims dropped or downgraded by the verifier
```
