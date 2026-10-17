---
name: code-review
description: Review a diff, pull request or branch with findings you can defend — grade spec and standards separately, find what is missing as well as what is wrong, sweep siblings of each issue, flag weakened tests or CI, read the history of changed lines, gate findings on file:line plus a failure scenario, and have an independent checker try to refute serious ones. Use when asked to review code, a PR or a branch, or before merging.
version: 1.2.1
sources:
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/{personas/*,action-class-rubric.md,subagent-template.md} (MIT) — correctness, security, performance and reliability lenses; P0–P3; check callers, guards and framework defaults
  - upstream/compound-engineering-plugin/skills/ce-simplify-code/references/personas/efficiency-reviewer.md (MIT) — unbounded structures, listener leaks
  - upstream/gstack/review (MIT) — sideways sweep, gate-integrity inventory, quote-or-cap confidence
  - upstream/villetakanen-asdlc-io (MIT) — the repo's own instruction files as a review contract; stale specs as missing work
  - upstream/mattpocock-skills/skills/engineering/code-review (MIT) — spec and standards as separate axes, smell vocabulary as fallback, repo conventions override
  - upstream/claude-plugins-official/plugins/code-review/commands/code-review.md (Apache-2.0) — independent per-finding verification; untouched-line, pre-existing, tool-catchable and explicitly silenced issues are not findings; git history, earlier PR comments and in-code guidance as review lenses
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
5. **Review the change, not the file.** A real problem that this change neither introduced nor
   made reachable goes in the appendix marked `pre-existing`. "Made reachable" means the diff
   adds a caller or an input source, or removes a guard — cite that changed line as the
   finding's `file:line`. This law does not demote law 3's siblings of a finding in the change,
   or Pass 2's stale docs. Not findings at all: what the compiler, type checker, linter or CI
   already reports — unless the diff disables or loosens that check (law 4) — and anything
   silenced by an ignore comment that existed before this change; an ignore this diff adds is a
   gate change (law 4).
6. **Serious findings survive an independent refutation.** Give every P0/P1 — and every finding
   that rests on a repo rule — to a fresh subagent that did not produce it: the finding, the cited
   rule from the base branch, and the repository at the change's head (so it can read callers,
   guards and history), but not the reviewer's reasoning; tell it to disprove the finding. It
   must confirm a rule-based finding against the rule's actual wording. Drop what it refutes;
   move what it cannot confirm to the appendix at low confidence. Where no subagent is
   available, re-check in a separate pass and label those findings `self-checked`.

## Pass 1 — What is present

The usual correctness, security and performance lenses, plus the one most often skipped —
**lifecycle**, the bugs that pass tests and fail later: collections that only grow, handles not
released on every error path, listeners never removed — and authorisation on every new entry
point. When the change touches auth, tenancy, payments or webhooks, also apply `app-security`.

## Pass 2 — What is missing

Check the spec for requirements that are missing or only partly implemented, and the change
for what its own code paths need but lack (validation on a new input, a test for a new branch).
If a spec or doc already describes behaviour the change alters, and the change leaves it
stale, report `MISSING:` citing that doc's `file:line` — the description should change in the
same PR. P2 at most, unless the stale doc is a public API contract. If no such doc exists,
there is no finding.
Report as `MISSING: <what> — <why it matters>`, citing the requirement or rule it comes from.

## Pass 3 — What the history says

- **Blame and log of the changed lines:** was this code written this way to fix something? A
  change that undoes an earlier fix, or reintroduces a reverted pattern, is a finding.
- **Earlier pull requests touching these files** — find them with
  `git log --format='%h %s' -- <path>`, then read `gh pr view <n> --comments` and the inline
  review comments (`gh api repos/<owner>/<repo>/pulls/<n>/comments`): objections raised there
  often apply again.
- **Comments in the modified files** that state an invariant ("must be called before…", "not
  thread-safe"): check the change still honours them.

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
