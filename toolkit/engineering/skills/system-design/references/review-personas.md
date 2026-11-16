# Persona review passes

Read when reviewing a design or plan that is large (several components or more than a few pages),
touches money, auth, data migration or a public contract, or when the user asks for a thorough
review. A short, low-risk plan gets the single pass in SKILL.md.

One reader looking for everything finds the obvious things and stops. Three readers, each told to
look for one kind of failure and to ignore the rest, find different things. Run them as separate
subagents with no conversation history, so each is independent of the others and of you.

## The three lenses

| lens | looks for | does not flag |
|---|---|---|
| **coherence** | the document disagreeing with itself: a section contradicting another, a non-goal that a requirement builds anyway, the same thing called two names or one name meaning two things, references to sections or IDs that do not exist, counts that do not match their lists, statements two careful readers would build differently ("after the migration": started? finished? verified?) | style, formatting, vagueness that is not ambiguity, anything explicitly deferred |
| **feasibility** | whether it can be built as written on this codebase and platform: interfaces that do not fit, dependencies or services that do not exist, migration order that cannot work, a stated performance or scale target the approach cannot meet; traces the happy, missing-input, empty-input and failure path of each main data flow; reads the actual code alongside the plan | theoretical scale worries with no current number behind them, "it would be nicer to", implementation detail the plan rightly leaves to the builder |
| **adversarial** | whether it is *right*: a goal the requirements do not actually serve, success criteria that could all pass with the problem unsolved, unstated assumptions about environment, scale (what at 10× and at 0.1×?), timing or user behaviour, decisions that do not survive a concrete counter-example, an obviously simpler alternative never considered | premises already settled upstream (a design discussion or approved proposal), unless new evidence contradicts them |

Skip the adversarial lens's premise checks when the plan links an approved design or proposal;
keep its assumption and decision checks.

## Prompt (one per lens)

```
You are reviewing the document at <path> as the <lens> reviewer only. <one-line lens brief from
the table above, plus its "does not flag" list>. Other reviewers cover everything else; ignore it.

For each finding give: the passage (quote it), what goes wrong and when, and your confidence:
certain (you can quote the evidence) / likely (will be hit in practice) / advisory (real but
minor). Do not report anything you cannot tie to a quoted passage or a file you read.
If the document is fine for your lens, say "nothing for <lens>".
```

## Verify before reporting

A reviewer's claim is a lead, not a finding. Before anything goes in the review:

1. **Check it yourself** against the document and the code. Establish the problem independently
   of the fix the reviewer suggested; a plausible addition does not prove anything is missing.
2. **Drop** what you cannot confirm. Speculative or unverifiable claims are not shown at all.
3. **Merge** duplicates across lenses. Two lenses that independently found the same problem
   raise confidence; your own agreement does not count as a second reviewer.
4. **Keep the smallest correction** that fixes the actual consequence, and check it does not
   break an agreed outcome or add requirements nobody asked for.
5. Report in three groups: corrections you can safely make (wording, a count, a broken
   reference), proposed changes needing approval, and decisions only the user can make. Advisory
   items go in a short FYI list. "Adequate, no changes" stays a valid result for every lens.
