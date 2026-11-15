---
name: code-review
description: >-
  Review a diff, PR, or branch with defensible findings: separate spec vs codebase standards,
  missing requirements, sibling sweeps, weakened-gate checks, git-history context, and independent
  refutation of P0/P1s. For offensive security audits use app-security; for design/plan reviews use
  system-design.
version: 1.4.1
sources:
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/{action-class-rubric.md,subagent-template.md} (MIT) — P0–P3; check callers, guards and framework defaults [port "data loss, security hole" "framework defaults"]
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/* (MIT) — per-lens checklists (correctness sentinel and lifecycle-writer checks, reliability timeouts, retries and error-path leaks), anchored 25/50/75/100 confidence, per-persona do-not-flag lists [port "Sentinel meaning changes" "Every writer of a lifecycle state" "Deleted-but-referenced files" "Swallowed errors" "Leaks on error paths" "Retry storms" "Anchored confidence" "Do-not-flag list"]
  - upstream/compound-engineering-plugin/skills/ce-simplify-code/references/personas/efficiency-reviewer.md (MIT) — unbounded structures, listener leaks [port "collections that only grow" "listeners never removed"]
  - upstream/gstack/review (MIT) — sideways sweep, weakened-gate inventory, quote-or-cap confidence [port "sweep sideways" "weakened gates are findings" "capped at low confidence"]
  - upstream/gstack/review/{checklist.md,gate-integrity.md} (MIT) — enum/value completeness trace, RH-1…16 gate-weakening pattern catalog, scope-creep check [port "Grep for the sibling values" "Snapshot or golden regenerated alone" "Suppression pragma added" "Assertion loosened" "Scope creep is the other half of the spec axis"]
  - upstream/villetakanen-asdlc-io (MIT) — the repo's own instruction files as a review contract; stale specs as missing work [port "cite the specific rule when broken" "leaves it stale"]
  - upstream/mattpocock-skills/skills/engineering/code-review (MIT) — spec and standards as separate axes, repo conventions override [port "two axes, reported separately" "the repo's own conventions override"]
  - upstream/mattpocock-skills/skills/engineering/code-review (MIT) — smell vocabulary as fallback [port "Smell vocabulary (standards fallback)" "Speculative generality" "Refused bequest"]
  - upstream/claude-plugins-official/plugins/code-review/commands/code-review.md (Apache-2.0) — independent per-finding verification; untouched-line, pre-existing, tool-catchable and explicitly silenced issues are not findings [port "serious findings survive an independent refutation" "silenced by an ignore comment"]
  - 'upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/maintainability-reviewer.md (MIT) — unrequested public surface and dependencies the standard library or a repo helper could replace (PR #1852) [port "public surface the stated intent rules out" "a new dependency doing what the standard library"]'
  - authored for this toolkit (toolkit policy) — Pass 3 history lens (blame, earlier pull requests, invariant comments); the upstream command dropped its history agents in its 2026-10-26 rewrite [port "earlier pull requests touching these files"]
---

# Code Review

A review that cries wolf is worse than none. Fewer, defensible findings beat a long list.

## Iron laws

1. **Two axes, reported separately.** *Spec*: does it do what was asked, and what did it
   silently not do? *Standards*: is it correct, safe and consistent with this codebase —
   including the repo's instruction files (`AGENTS.md`, `CLAUDE.md`, rules directories) and
   decision records? Load these from the **base branch**, cite the specific rule when broken, and
   treat any change to them inside the diff as a gate change (law 4). Find the spec first (active change package or living capability specs in
   `specs/` or `openspec/` — see `spec` — linked issue, plan, PR description). If there is none,
   report "no spec available" and review standards only.
2. **Every finding passes the gate:** exact `file:line`; a concrete failure (input → state →
   bad outcome); the surrounding context read (callers, one frame up, tests); a defensible
   severity. A finding you cannot tie to a quoted line is capped at low confidence and goes in
   an appendix, not the main list. `MISSING:` findings cite the requirement or rule instead of a
   line.
3. **Sweep sideways.** For each real finding, search for the same pattern at every other call
   site or entry point, and grade severity on the worst instance found.
4. **Weakened gates are findings in their own right.** List every change to tests, snapshots,
   CI config, lint rules or type strictness in the diff and justify each one. Grep the diff
   against the pattern catalogue in `references/gate-patterns.md`.
5. **Review the change, not the file.** A real problem that this change neither introduced nor
   made reachable goes in the appendix marked `pre-existing`. "Made reachable" means the diff
   adds a caller or an input source, or removes a guard — cite that changed line as the
   finding's `file:line`. This law does not demote law 3's siblings of a finding in the change,
   or Pass 2's stale docs. Not findings at all: what the compiler, type checker, linter or CI
   already reports — unless the diff disables or loosens that check (law 4) — and anything
   silenced by an ignore comment that existed before this change; an ignore this diff adds is a
   gate change (law 4).
6. **Serious findings survive an independent refutation.** Give every P0/P1 — and every finding
   that rests on a repo rule — to a fresh subagent that did not produce it (preferring another
   model family when available): the finding, the cited rule from the base branch and the repo
   at the change's head, but not the reviewer's reasoning; tell it to disprove the finding. It
   must confirm a rule-based finding against the rule's actual wording. Drop what it refutes;
   move what it cannot confirm to the appendix at low confidence. Where no subagent is
   available, re-check in a separate pass and label those findings `self-checked`.

## Pass 1 — What is present

Correctness, security and performance, plus **lifecycle** (collections that only grow, handles
not released on error paths, listeners never removed) and authorisation on every new entry
point. Read `references/lenses.md` for the lenses the diff touches (checklists, do-not-flag
lists, confidence anchors). Two checks there are mandatory whenever they apply, because they
need code outside the diff: **every writer of a lifecycle state** when the diff writes or adds
a status, and the **enum/value completeness trace** when it adds a value or widens an input.
When the change touches auth, tenancy, payments or webhooks, also apply `app-security`.
Frontend UI, mobile web or motion: also `impeccable`, `mobile-native` and, if installed,
`review-animations`; browser support, platform APIs or Core Web Vitals: `web-platform`.

## Pass 2 — What is missing

Check the spec for requirements that are missing or only partly implemented, and the change
for what its own code paths need but lack (validation on a new input, a test for a new branch).
If a living spec (`specs/`, `openspec/`) or doc already describes behaviour the change alters, and
the change leaves it stale (without an active delta or spec update), report `MISSING:` citing that
file's `file:line` — the spec or doc should change in the same PR. P2 at most, unless the stale
spec or doc is a public API contract. If no such doc exists, there is no finding.
Report as `MISSING: <what> — <why it matters>`, citing the requirement or rule it comes from.

Scope creep is the other half of the spec axis: report each hunk no requirement serves, and each
unmentioned behaviour change, as `UNASKED: <change> — <file:line>` — a question for the author,
not automatically a defect. Read `references/scope-and-history.md` for the two kinds that count
even when small.

## Pass 3 — What the history says

Read blame and log of the changed lines, earlier pull requests touching these files, and
invariant comments in the modified files; a change that undoes an earlier fix is a finding.
Commands: `references/scope-and-history.md`.

## Severity and confidence

| severity | meaning |
|---|---|
| P0 | data loss, security hole, outage, money |
| P1 | wrong behaviour users will hit |
| P2 | maintainability or edge case with a real but unlikely failure |
| P3 | nit — omit unless asked |

P0/P1 must include the snippet, the failure walked end to end, and why existing guards (types,
validation, framework defaults) do not prevent it. Cannot produce all three → demote or drop.

Confidence uses the 0/25/50/75/100 anchors in `references/lenses.md`: 75 and up needs the
quoted line, 50 goes to the appendix (a P0 at 50 is listed there as `unconfirmed P0` with
what would confirm it — it never skips the P0/P1 evidence rule above), 25 and below is
dropped.

The repo's own conventions override any generic style rule; a design smell is a judgement call,
never a hard violation. Where the repo is silent, use the smell vocabulary and fixes at the end
of `references/lenses.md`, labelled "possible <smell>".

## Output

```
Spec conformance:      met / partially / not met — and what was not done
Findings (standards):  P0 → P2, each: file:line · failure · confidence anchor · fix
Missing:               MISSING: items with their citation
Unasked:               UNASKED: changes no requirement or description covers
Gate changes:          each test / CI / config change and whether it is justified
Appendix:              low-confidence observations, clearly labelled
```
