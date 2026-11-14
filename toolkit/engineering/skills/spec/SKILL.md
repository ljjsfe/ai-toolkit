---
name: spec
description: >-
  Author and maintain behavioral specs without a CLI: proposal, capability delta specs (SHALL +
  WHEN/THEN scenarios with stable IDs), conditional design, and vertical tasks; surface human-gated
  decisions; merge deltas into timeless living specs after verification. Not for open framing
  (design-discussion) or sizing (system-design).
version: 1.0.0
sources:
  - "upstream/fission-ai-openspec v2.0.0 schemas/spec-driven/{schema.yaml,templates/*} (MIT, https://github.com/Fission-AI/OpenSpec) — proposal/specs/design/tasks artifact DAG, capability-named layout, normative SHALL/MUST requirements with WHEN/THEN scenarios, conditional design, zero-delta escape hatch"
  - "upstream/fission-ai-openspec v2.0.0 src/core/{specs-apply,archive,validation/validator}.ts and skills/openspec-{propose,apply-change,sync-specs,update-change,archive-change} (MIT, https://github.com/Fission-AI/OpenSpec) — full-block MODIFIED anti-loss rule, RENAMED/REMOVED/MODIFIED/ADDED merge order, capability retirement guard, bi-directional change reconciliation"
  - "authored for this toolkit from a stated need (CLI-free spec-driven engineering) — stable requirement IDs for item-by-item verification, explicit human-sign-off decision block, timeless living specs with zero inline changelog"
---

# Behavioral Specifications (`spec`)

A spec pins externally observable behaviour in plain Markdown so design, test-first slices (`tdd`),
completion checks (`verification`), and review (`code-review`) judge against one contract — with
no CLI dependency.

Scale to the change: use a change package for multi-slice features, public API/schema/permission
changes, cross-agent hand-offs (`agent-orchestration`), or any repository that already keeps
`specs/` or `openspec/`. A one-line bug fix or local tidy goes straight to `debugging` / `tdd`
unless repo instructions require a change folder.

## Layout discovery

Inspect the repository before creating directories:

- If `openspec/` exists, follow `openspec/specs/<capability-path>/spec.md` and
  `openspec/changes/<change-slug>/`.
- If `specs/` exists, follow `specs/<capability-path>/spec.md` and
  `specs/changes/<change-slug>/`.
- If neither exists, ask the user before initializing a repo-wide `specs/` tree.

`<capability-path>` names a cohesive capability in `kebab-case` (`auth-session`,
`billing/invoices`), never a task verb (`add-login-endpoint`) and never a single flat
`specs/spec.md`.

## Iron laws

1. **Observable behaviour only.** State inputs, outputs, state transitions, permissions, failure
   modes and invariants — never internal class/function names, library choices or code recipes.
   Test: if internals can be refactored without breaking any caller or user expectation, it stays
   out of `spec.md` (put non-obvious mechanisms in `design.md`).
2. **Stable ID + uppercase `SHALL`/`MUST` + at least one `WHEN`/`THEN` scenario per requirement.**
   Keep each requirement to one behaviour (roughly ≤2 sentences); put edge cases and concrete
   values into `#### Scenario:` blocks rather than prose walls. Avoid `should` or `may`. (When
   modifying an existing ID-less `openspec/` file, keep legacy headers verbatim on
   `MODIFIED`/`REMOVED`/`RENAMED` so exact-header matching holds, and assign IDs to new `ADDED`
   requirements unless repo conventions forbid them.)
3. **Call out human-gated decisions explicitly; never self-settle them.** Breaking contract
   changes, product scope cuts, auth/billing/privacy trade-offs, and irreversible migrations go in
   `proposal.md` under `## Decisions needing sign-off` with options, recommendation and blast
   radius. Stop after writing or updating the change artifacts whenever any sign-off item or scope
   ambiguity is open; write product code only after approval (or on explicitly requested
   assumptions).
4. **`MODIFIED` copies the entire requirement block.** Paste the existing `### Requirement:`
   header, updated `SHALL` statement, and *every* surviving `#### Scenario:` block before editing.
   A partial snippet silently drops omitted scenarios when merged into the living spec.
5. **Living specs hold timeless current behaviour — zero changelog.** `specs/<capability-path>/spec.md`
   contains only `# <Capability>`, `## Purpose`, and `## Requirements`. Never leave delta headers,
   "Added in…", dates, PR numbers, or change logs inside a living spec; `changes/archive/` and
   `git log` own the history.
6. **Archive only after `verification` passes.** Merging a delta into living specs declares that
   behaviour live. Check every requirement ID and scenario via `verification` first; strip or
   split any user-descoped item out of the delta before merging so living specs never claim
   unbuilt behaviour.

## 1. Change package (`changes/<change-slug>/`)

Draft artifacts in dependency order (`proposal` → delta `specs` + `design` → `tasks`):

| file | when | contents |
|---|---|---|
| `proposal.md` | always | `## Why` (1–2 sentences: problem and trigger) · `## What changes` (capabilities added/modified/removed; prefix breaking changes with **`BREAKING`**) · `## Non-goals` · `## Decisions needing sign-off` (`- [ ] [DEC-01] <choice> — options, recommendation, impact`, or `None`) |
| `specs/<capability-path>/spec.md` | whenever observable behaviour changes | Delta spec (`ADDED` / `MODIFIED` / `REMOVED` / `RENAMED`) for that capability. If observable behaviour is unchanged (pure refactor, CI, tooling), omit `specs/` and write `No spec delta: observable behaviour unchanged` in `proposal.md` |
| `design.md` | conditional | Write only when cross-cutting multiple modules/services, adding external dependencies or schema/state migrations, meeting numeric capacity/SLO/cost targets (from `system-design` or `agent-architecture`), or recording non-obvious trade-offs (`## Context`, `## Decisions` with rejected alternatives, `## Risks & rollout`). Skip when `proposal` + delta specs make the code obvious |
| `tasks.md` | always | Vertical-slice checkboxes ordered by real blocking edges (`tdd`): `- [ ] 1.1 <behaviour delivered> [REQ-AUTH-001] — verify: <seam test or command>`. Each slice lands its own code, seam tests and doc updates; never push all tests or docs to a final phase |

## 2. Delta spec format

Include `## Purpose` (1–2 sentences defining capability scope) **only** when introducing a
brand-new capability; omit `## Purpose` on deltas for existing capabilities. Include only the
delta sections needed, and never place the same requirement in two conflicting sections (`ADDED` +
`MODIFIED`, or `MODIFIED` + `REMOVED`):

```markdown
# Auth Session (Delta)

## Purpose
Manages interactive user session lifecycle, rotation, and revocation across devices.

## ADDED Requirements

### Requirement: [REQ-AUTH-001] Session revocation on password change
The system SHALL revoke every active session of a user other than the initiating session when that user changes their password.

#### Scenario: Concurrent device session is rejected after password change
- **WHEN** an authenticated user changes their password from session A while session B is active
- **THEN** the next request authenticated with session B fails with HTTP 401
- **AND** session A remains authenticated

## MODIFIED Requirements

### Requirement: [REQ-AUTH-002] Idle session expiration
The system SHALL expire an interactive session after 24 hours of inactivity.
<!-- Full block required: include ALL surviving scenarios alongside any edited or new ones -->

#### Scenario: Request within idle window extends activity timestamp
- **WHEN** an authenticated request arrives 23 hours after the prior request
- **THEN** the request succeeds and the idle window resets to 24 hours

## REMOVED Requirements

### Requirement: [REQ-AUTH-003] Legacy query-string session token
**Reason**: Query-string tokens leak through referrer headers and access logs.
**Migration**: Clients send bearer tokens in the `Authorization` header or `HttpOnly` cookies.

## RENAMED Requirements

- FROM: `### Requirement: [REQ-AUTH-004] Login rate throttle`
- TO: `### Requirement: [REQ-AUTH-004] Credential-stuffing rate limit`
```

If a requirement is both renamed and behaviourally changed in the same change, list the rename in
`## RENAMED Requirements` and use the **new (`TO`)** header in `## MODIFIED Requirements`.

## 3. Reconciling discoveries mid-implementation

When `tdd` implementation or `debugging` reveals an unhandled edge case, an impossible constraint,
or a cleaner mechanism, **pause before letting code drift from the artifacts**:

- Reconcile in whichever direction restores truth (`design.md` ↔ delta `spec.md` ↔ `tasks.md` ↔
  `proposal.md`).
- Technical adjustments inside agreed behaviour update `design.md` / `tasks.md` directly; changes
  that alter observable behaviour, public contracts, or a settled `[DEC-NN]` go back through
  `## Decisions needing sign-off` for user approval before coding past them.

## 4. Archive — merge deltas into living specs

Run only after `verification` confirms every requirement ID and scenario is **covered** (and
any descoped item has been removed from the delta or split into a follow-up change):

1. For each delta `changes/<slug>/specs/<capability-path>/spec.md`, open or create the living
   `specs/<capability-path>/spec.md` (`# <Capability>`, `## Purpose`, `## Requirements`). When
   creating a new capability spec, only `## Purpose` + `## ADDED Requirements` are valid.
2. Apply operations in strict order so renames and edits compose without collision:
   - **`RENAMED`** — replace matching `### Requirement:` headers in place.
   - **`REMOVED`** — delete matching requirement blocks. If removing the last requirement retires
     the capability, confirm retirement intent and delete the capability's `spec.md` rather than
     leaving an empty `## Requirements` section.
   - **`MODIFIED`** — replace the entire matching requirement block with the delta's full block.
   - **`ADDED`** — append new requirement blocks after checking no duplicate ID or header exists.
3. Audit each touched living spec: single `## Purpose` and `## Requirements`, zero leftover delta
   headers (`ADDED`/`MODIFIED`/`REMOVED`/`RENAMED`), zero changelog or date annotations, unique
   requirement IDs/headers, and ≥1 `#### Scenario:` (`WHEN`/`THEN`) under every requirement.
4. Move `changes/<slug>/` to `changes/archive/YYYY-MM-DD-<slug>/` (do not double-prefix if `<slug>`
   already starts with `YYYY-MM-DD-`).

## Hand-offs

| stage | owner |
|---|---|
| Open-ended framing when problem or mechanism is unsettled | `design-discussion` |
| Opportunity framing, ambition level and v1 scope cuts | `product-scoping` |
| RPS/storage/cost arithmetic, SLO/RPO/RTO and design review | `system-design` (or `agent-architecture` for LLM loops) |
| Seam agreement and red-green vertical slice implementation | `tdd` |
| Fresh session proof and item-by-item `[REQ-...]` check pre-archive | `verification` |
| Independent two-axis diff and spec-conformance review | `code-review` |
