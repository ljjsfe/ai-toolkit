---
name: code-review
description: Review a diff, pull request or branch with findings you can defend — grade spec conformance and standards separately, look for what is missing as well as what is wrong, sweep every sibling of a found issue, flag weakened tests or CI as findings, and gate each finding on file:line plus a concrete failure scenario. Use when asked to review code, a PR or a branch, or before merging.
version: 1.1.0
sources:
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/{personas/*,action-class-rubric.md,subagent-template.md} (MIT) — correctness, security, performance and reliability lenses; P0–P3; check callers, guards and framework defaults
  - upstream/compound-engineering-plugin/skills/ce-simplify-code/references/personas/efficiency-reviewer.md (MIT) — unbounded structures, listener leaks
  - upstream/gstack/review (MIT) — sideways sweep, gate-integrity inventory, quote-or-cap confidence
  - upstream/villetakanen-asdlc-io (MIT) — the repo's own instruction files as a review contract; stale specs as missing work
  - upstream/mattpocock-skills/skills/engineering/code-review (MIT) — spec and standards as separate axes, smell vocabulary as fallback, repo conventions override
---

# Code Review

A review that cries wolf is worse than none. Fewer, defensible findings beat a long list.

## Iron laws

1. **Two axes, reported separately.** *Spec*: does it do what was asked, and what did it
   silently not do? *Standards*: is it correct, safe and consistent with this codebase —
   including the code rules in the repo's `CLAUDE.md` / `AGENTS.md`, rule files and decision
   records? Load these from the **base branch**, cite the specific rule when broken, and treat
   any change to them inside the diff as a gate change (law 4) — a PR does not get to set the
   rules it is judged by. Find
   the spec first (linked issue, plan, PR description). If there is none, report "no spec
   available" and review standards only.
2. **Every finding passes the gate:** exact `file:line`; a concrete failure (input → state →
   bad outcome); the surrounding context read (callers, one frame up, tests); a defensible
   severity. A finding you cannot tie to a quoted line is capped at low confidence and goes in
   an appendix, not the main list. `MISSING:` findings cite the requirement or rule instead of a
   line.
3. **Sweep sideways.** For each real finding, search for the same pattern at every other call
   site or entry point, and grade severity on the worst instance found.
4. **Weakened gates are findings in their own right.** List every change to tests, snapshots,
   CI config, lint rules or type strictness in the diff and justify each one. A loosened
   assertion that makes the build pass is the most important line in the review.

## Pass 1 — What is present

The usual correctness, security and performance lenses, plus the one most often skipped —
**lifecycle**, the bugs that pass tests and fail later: collections that only grow, handles not
released on every error path, listeners never removed — and authorisation on every new entry
point.

## Pass 2 — What is missing

Check the spec for requirements that are missing or only partly implemented, and the change
for what its own code paths need but lack (validation on a new input, a test for a new branch).
If a spec or doc already describes behaviour the change alters, and the change leaves it
stale, report `MISSING:` citing that doc's `file:line` — the description should change in the
same PR. P2 at most, unless the stale doc is a public API contract. If no such doc exists,
there is no finding.
Report as `MISSING: <what> — <why it matters>`, citing the requirement or rule it comes from.

## Severity and confidence

| severity | meaning |
|---|---|
| P0 | data loss, security hole, outage, money |
| P1 | wrong behaviour users will hit |
| P2 | maintainability or edge case with a real but unlikely failure |
| P3 | nit — omit unless asked |

P0/P1 must include the snippet, the failure walked end to end, and why existing guards (types,
validation, framework defaults) do not prevent it. Cannot produce all three → demote or drop.

The repo's own conventions override any generic style rule; a design smell is a judgement call,
never a hard violation.

## Output

```
Spec conformance:      met / partially / not met — and what was not done
Findings (standards):  P0 → P2, each: file:line · failure · fix
Missing:               MISSING: items with their citation
Gate changes:          each test / CI / config change and whether it is justified
Appendix:              low-confidence observations, clearly labelled
```
