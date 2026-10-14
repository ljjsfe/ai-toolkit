---
name: debugging
description: Find the root cause of a bug before changing code — build a fast red/green reproduction first, route by failure shape (flaky, order-dependent, race, performance), locate the failing layer (frontend, API, backend, data), cite an observation for every hypothesis, and stop after three failed fixes. Use for bugs, failing tests, regressions and "is this frontend or backend?"; for an active production outage use production-ops.
version: 1.0.0
sources:
  - upstream/superpowers/skills/systematic-debugging (MIT) — root cause first, read the full error, one change at the source, three failed fixes means stop
  - upstream/compound-engineering-plugin/skills/ce-debug/references/{investigate,fix}.md (MIT) — observation-cited hypotheses, explicit invalidation
  - upstream/mattpocock-skills/skills/engineering/diagnosing-bugs (MIT) — reproduction loop as the first deliverable
  - upstream/gstack/investigate (MIT) — failure-shape routing; rerun, timeout and skip are not hypotheses
  - upstream/compound-engineering-plugin/skills/ce-debug (MIT) — convergent vs divergent fixes
  - upstream/gstack/qa (MIT) — regression-test value bar
  - upstream/addyosmani-agent-skills/skills/debugging-and-error-recovery (MIT) — check the layer (UI, network, backend)
  - authored for this toolkit from a stated need (frontend-or-backend triage) — request/response boundary isolation steps
---

# Debugging

The bottleneck is almost never ideas about the cause. It is a fast, reliable signal that
says broken or fixed.

## Iron laws

1. **Build the reproduction before theorising.** First deliverable: one command that goes red
   now and will go green when fixed (a failing test, a curl script, a CLI call with a
   snapshot diff, a bisect script). If you are reading code to build a theory and this
   command does not exist yet, stop and build it. If no reproduction is feasible (production
   only, specific data), say so and collect observations from that environment instead — never
   fake one.
2. **Every hypothesis cites an observation** — a value, a log line, a captured request, a
   diff between a working and a broken case. "Seems off" is not evidence.
3. **A failed fix must invalidate its hypothesis out loud:** name what you saw that the old
   theory cannot explain before forming the next. Variants of the same theory are a spiral.
4. **Three failed fixes → stop.** The problem is structural or misunderstood. Report what is
   known and discuss before a fourth attempt.
5. **Rerunning, raising a timeout, retrying or skipping the test is never a hypothesis.**
6. **Do not "fix" intended behaviour.** If the fix would reverse a deliberate contract — a
   test that asserts the current behaviour on purpose, a documented limit — it is a design
   change. Stop and ask, even in an autonomous loop.

Fast path: if the cause is readable straight from the error (typo, missing import, obvious
off-by-one) state the cause with `file:line`, apply the one-line fix, and verify. When in
doubt, use the full process.

## Step 1 — Route by failure shape

| shape | do first |
|---|---|
| flaky / CI-only | run it many times in a loop to measure the rate; compare environments (versions, env vars, parallelism, time zone, clock) |
| order-dependent | run in isolation, then bisect the test order to find the polluter |
| race / timing | add timestamps at each boundary; look for shared mutable state and missing awaits |
| performance regression | measure a baseline with a profiler, then bisect commits; logs mislead here |

## Step 2 — Find the failing layer (frontend or backend?)

Capture the real request and response at the boundary, then replay the request with `curl`
to take the client out of the loop: a wrong response there is server-side, a right one moves
the fault to the client. A response that is right on replay but wrong in the app points to
caching, stale client state or a race.

## Step 3 — Fix and prove

- The reproduction from Step 1 goes green; the related test suite still passes.
- Keep the reproduction as a regression test only if existing tests would not already catch
  this, and only if it tests a real boundary rather than a seam added just for the test.
- Report: cause (with `file:line`), evidence, fix, how it was verified.
