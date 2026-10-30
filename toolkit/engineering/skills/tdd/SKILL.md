---
name: tdd
description: Build test-first in thin end-to-end slices — cut a plan into vertical slices with real blocking edges, agree the test seams before the first test, go red before green one slice at a time, mock only at system boundaries, and reject tests coupled to internals or that recompute their own expected value. Use for test-first or TDD work, red-green-refactor, and breaking a plan or spec into slices, tickets or tasks; for a bug without a reproduction start with debugging, and for a diff's tests use code-review.
version: 1.0.0
sources:
  - upstream/mattpocock-skills/skills/engineering/tdd (MIT, commit 5beb35b) — tests at agreed seams, implementation-coupled and tautological tests, horizontal slicing as an anti-pattern, mock only at system boundaries, no refactoring mid-cycle
  - upstream/mattpocock-skills/skills/engineering/to-tickets (MIT, commit 5beb35b) — tracer-bullet vertical slices, blocking edges and the frontier, expand–contract sequencing for wide refactors, no file paths in tickets
  - authored for this toolkit from a stated need (green suites that test nothing) — a test never seen red is not evidence
---

# Test-Driven Development

A test is worth keeping when it fails for a real reason and still passes after a refactor that
keeps behaviour. Get there by slicing the work thin and agreeing where tests go before writing
any.

Scale it to the change: a small change is one slice, and its seams are stated, not negotiated.

## Iron laws

1. **Slice vertically.** Each slice is a narrow path through every layer it touches (data, API,
   UI, tests) and can be demonstrated or verified on its own. Never all the schema, then all
   the API.
2. **Agree the seams first.** Before the first test, list the public interfaces you will test
   through, with one line each on what a test there catches and misses, and get the user's
   agreement. In an unattended run, record them as assumptions in the plan instead; under
   `agent-orchestration` the orchestrator settles them before dispatch and puts them in the
   brief. No test at a seam that is neither agreed nor recorded.
3. **Red before green.** Write one failing test, watch it fail for the expected reason, then
   write only the code that makes it pass. One test and one minimal implementation per cycle.
4. **Expected values come from outside the code:** a known literal, a worked example, the spec.
   Never a recomputation done the way the code does it.
5. **No refactoring mid-cycle.** Tidy only once the slice is green, with the suite green before
   and after. Planning a larger restructure goes to `system-design`; its diff goes to
   `code-review`.

## 1. Slice the work

- Draft the slices as a numbered list. Each has a title, what it delivers end to end from the
  caller's or user's view, what blocks it, and acceptance items as `- [ ]`.
- Put prefactoring first, as its own slice: make the change easy, then make the easy change.
- Size each slice to fit one fresh agent context.
- Add a blocking edge only where one slice truly gates another. The slices whose blockers are
  all done form the frontier: free to start in any order, but run in parallel only once
  `agent-orchestration` has given each one a disjoint set of files to own.
- **Wide refactors** (one mechanical change that breaks every call site at once) cannot land as
  a green vertical slice. Sequence them as expand, migrate, contract: add the new form beside
  the old; migrate callers in batches sized by blast radius, each blocked by the expand and
  each leaving CI green; remove the old form in a slice blocked by every batch. If a batch
  cannot be green on its own, put the batches on one integration branch that is only promised
  green at a final integrate-and-verify slice. For schema or data, `production-ops` owns the
  phases.
- Describe behaviour, not file paths or code, which go stale. The exception is a type, schema
  or state machine that pins a decision more precisely than prose.
- Show the breakdown and ask whether the granularity is right, whether each edge really gates,
  and what to merge or split; iterate until the user approves it. Unattended, record the
  breakdown as an assumption, as in law 2.
- A slice is done when every acceptance item is covered, in `verification`'s requirement
  coverage terms.

## 2. Where tests go

- Test through the public interface: what a caller can observe. Use the highest seam that
  still runs fast and deterministically, and prefer existing seams to new ones.
- Mock only at system boundaries: external APIs, time and randomness; a database or file system
  only when a real test instance is impractical. Never mock your own modules.
- Make boundaries easy to fake: pass the dependency in rather than constructing it inside, and
  give each external operation its own function rather than one generic fetcher.
- For a bug, turn the reproduction from `debugging` into the first red test at an agreed seam.

## 3. Tests to reject

| smell | tell | fix |
|---|---|---|
| implementation-coupled | mocks an internal collaborator, tests a private method, asserts call counts or order on your own code; breaks on a refactor that keeps behaviour | assert on the observable result at the seam (call counts are fine at a system boundary: charged exactly once) |
| side channel | checks by querying the database or reading internal state | read back through the interface (create, then get) |
| tautological | expected value computed the way the code computes it, a snapshot derived the same way, a constant asserted equal to itself | a known literal or worked example |
| horizontal | every test written before any code | one test per cycle |
| never seen red | written after the code and never observed failing | break the code or revert it, watch the test fail, restore |

## Output

Per slice:

```
Slice:       NN title — blocked by …
Seams:       interfaces under test (agreed | assumed)
Cycles:      test name → why it went red → green (command and result)
Acceptance:  each item covered · not covered · not verified · not applicable, with its evidence
```
