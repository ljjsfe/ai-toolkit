# Review lenses

Read in Pass 1, once per lens the diff touches. Each lens lists what to hunt for and what it
never flags. A hit here is a candidate: it still passes the finding gate (law 2) and, at P0/P1,
the refutation (law 6).

## Correctness

Read the code by running it in your head with concrete values at the boundaries.

- **Boundaries:** loop bounds, slices, pagination when the total is an exact multiple of the
  page size, empty and single-element inputs. Write the values out; do not eyeball.
- **Null propagation:** a function that returns null/None on failure, a caller that does not
  check, a later dereference — or a missing value that silently becomes `"undefined"`, `NaN`
  or an empty string downstream.
- **Sentinel meaning changes:** the diff adds a return path that reuses an existing sentinel
  (`null`, empty list, `-1`, a fallback enum value) for a new situation. Open every consumer
  and ask what it now shows or does: if "no results" and "query failed" are the same value, the
  user is told something false. "Does not crash" is not the bar; the fix is a richer return
  shape or an explicit state.
- **Every writer of a lifecycle state.** Applies when the diff adds a status value, writes
  one, or changes the condition a write checks. Lifecycle state is anything code branches on
  to decide what happens next: a status column, a claim or lease stamp, a nullable
  `processed_at`, a counter that triggers work. Search the whole repository — including SQL
  functions, triggers and background workers — for every place that writes it, and tabulate
  one row per writer: what it read before deciding, what condition its write actually checks,
  what state it leaves. Test the changed transition against the other rows for three cases:
  the same event delivered twice; a slow or stale writer acting after a newer one; another
  writer changing the state between this writer's read and its write. The usual bug is a write
  that checks less than the decision relied on (decides from a lease stamp, updates on status
  alone). Every early return or throw after a claim must either finish the work or release
  the claim.
- **Partial state on error:** a flag set on the success path and never cleared on the error
  path; some fields updated, their partners not.
- **Races and ordering:** two paths that can interleave with nothing serialising them (no
  lock, transaction, unique constraint or single-instance schedule); check-then-act gaps.
- **Deleted-but-referenced files:** a whole-file deletion shows only as a header. For each one,
  search the surviving tree for readers — imports, but also string references (asset paths,
  config and plugin names), routes derived from file names, and registrations the file made
  on import. The finding quotes the surviving line that still uses it. A deleted test is a
  separate question: does the code it covered still ship?
- **Swallowed errors** (owner of this check; `gate-patterns.md` points here): `catch {}`,
  `catch (e) {}`, `except: pass`, `except Exception` returning a default, `rescue nil`,
  `.catch(() => {})`, `_ = err`, a handler that logs and carries
  on, a fallback value (empty list, default object) that hides a failure so the caller reports
  "nothing found" when the truth is "lookup failed". Also errors re-thrown without context and
  error codes routed to the wrong handler.
- **Stand-in checks:** a CI step, smoke test or dry run that is meant to mirror the real
  build or deploy but runs in a different working directory, build context or environment —
  it can pass while production fails.

Do not flag: naming and style; defensive null checks for values that cannot be null on the
traced path; slow-but-correct code (performance lens).

## Reliability

A gap is a finding only if the failure it allows costs something where this code runs: a hung
or crashed service, a caller acting on a wrong result, or work left half-done that a rerun does
not repair.

- **Timeouts:** every HTTP client, database connection, RPC and queue call made in the diff has
  an explicit timeout, or a framework default you have located and quoted. A call with no
  timeout holds a thread or connection for as long as the dependency is slow.
- **Retry storms:** retries have a maximum attempt count, exponential backoff and jitter, and
  retry only errors that can succeed on retry. Immediate unbounded retry turns a blip into a
  self-inflicted outage; retries at two layers multiply.
- **Leaks on error paths:** a connection, file handle, lock, temp file or subscription acquired
  in the diff is released on *every* exit — `finally`, `defer`, `with`/`using`, or the
  language equivalent — not only on the happy path.
- **Error handling at I/O boundaries:** network, disk and queue calls whose failure is neither
  handled nor propagated.
- **Cascades:** name the chain only when you can point at each link — slow dependency → queue
  fills → health check fails → restart storm.

Do not flag: pure in-memory functions; error handling inside test helpers; wording of error
messages; cascades that need several unevidenced conditions at once.

## Performance

Higher bar than the other lenses: a miss is cheap to measure and fix later, a false alarm costs
engineering time now.

- Query or remote call inside a loop over user-sized data (count the expected iterations — a
  loop over three config items is not N+1).
- Whole table or collection loaded into memory; endpoint with no limit or cursor.
- Blocking I/O or heavy CPU on an event loop or async handler.
- Regex compilation, allocation or recomputation per request that could be hoisted.

Do not flag: cold paths (startup, migrations, admin scripts); "should cache this" without
evidence the path is hot; scale problems beyond the expected near-term load; micro-style
choices (`for` vs `forEach`).

## Tests

- New branches, error paths and early returns with no test that drives them.
- A reused sentinel (above) with no test proving consumers act truthfully on the new meaning.
- Tests that would pass with the code broken: only "does not throw", truthiness instead of a
  value, expected value from the same helper as the code, a mock that supplies the result the
  code should produce, a negative case rejected by a different guard than the one named.
- An export, flag or hook added only so a test can reach an internal.
- Real time, real network, shared mutable fixtures, or run-order dependence in new tests.
- Behaviour changed and no test file touched at all.

Do not flag: missing tests for trivial accessors; test style conventions; coverage
percentages; untested code the diff did not touch or make riskier.

## Enum and value completeness

Run whenever the diff adds an enum member, status string, tier, type constant or feature flag
value, **or** widens what an input accepts (a new MIME type, extension, flag; a looser
validator, parser or guard).

1. Grep for the *sibling* values (the existing members), not the new one — that finds every
   consumer, including the ones that do not know the new value exists yet.
2. Open and read each hit: every `switch`/`match`/`if-elif` chain, allowlist array, filter,
   serializer, database check constraint, display mapping and analytics bucket.
3. For each, record whether the new value is handled, falls to a wrong default, or is
   silently dropped. Common miss: added to the UI dropdown but not persisted by the backend.
4. For a widened input, confirm every consumer of that field copes with the newly accepted
   shape; the breakage is usually in files the diff never touched.

This step requires reading outside the diff; a review that only greps the new value has not
done it.

## Anchored confidence

Pick the anchor whose *behaviour* you can truthfully claim, never a value between them.

| anchor | what you did | goes to |
|---|---|---|
| 100 | the defect is mechanical from the code alone: wrong return type, swapped arguments, compile or type error, a quoted repo rule plainly broken | main list |
| 75 | you traced input → branch → line → wrong result, quoted the motivating line, and normal use hits it | main list |
| 50 | the concern is real but depends on something you could not see (caller outside the diff, a framework default elsewhere) | appendix; a P0 here is labelled `unconfirmed P0` with what would confirm it |
| 25 | could be real, could be noise; not verified | drop |
| 0 | does not survive a second look | drop |

Severity and anchor are independent: a P2 can be 100, a P0 can be 50. 75 and 100 require the
quoted line — no quote, step down to 50. For a race, quote both paths and show nothing
serialises them; that is 75 when both paths run in normal operation, 50 otherwise. For a
symbol generated by a framework (ORM model, decorator, migration), quote the construct that
generates it; a failed grep for the name proves nothing.

## Do-not-flag list

Across all lenses, these are not findings:

- Style, formatting, naming, import order, comment presence — unless a repo rule says
  otherwise, then cite the rule.
- Anything the compiler, type checker, linter or CI already reports (law 5), unless the diff
  loosens that check.
- Pre-existing problems the diff neither introduced nor made reachable (appendix,
  `pre-existing`).
- Lines silenced by an ignore comment that predates the change.
- Hypothetical failures that need several unevidenced runtime conditions at once.
- Defensive checks for impossible values; "consider adding logging"; premature caching or
  abstraction suggestions.
- Missing tests for trivial code; coverage numbers.
- A design smell stated as a violation (it is always a labelled judgement; see below).

## Smell vocabulary (standards fallback)

Use only where the repo documents nothing on the point; a documented repo convention always
wins and suppresses the smell. Report each as "possible <smell>" with the hunk quoted, at P2
or below, never as a hard violation. Skip what tooling enforces.

| smell | what you see in the diff | usual fix |
|---|---|---|
| Mysterious name | a name that does not say what the thing does or holds | rename; if no honest name exists, the design is unclear |
| Duplicated code | the same logic shape in two hunks or files | extract the shared shape, call it from both |
| Feature envy | a function that uses another object's data more than its own | move it next to the data it uses |
| Data clump | the same few fields or parameters always travel together | give them one type and pass that |
| Primitive obsession | a string or number standing in for a domain concept | a small dedicated type |
| Repeated switch | the same branch-on-type cascade in several places | polymorphism, or one shared lookup table |
| Shotgun surgery | one logical change forces edits scattered across many files | gather what changes together into one module |
| Divergent change | one module edited for several unrelated reasons | split it so each part changes for one reason |
| Speculative generality | hooks, parameters or layers no requirement asks for | delete; inline until a real need appears |
| Message chain | `a.b().c().d()` navigation the caller should not know about | one method on the first object that hides the walk |
| Middle man | a class or function that only forwards | remove it; call the target directly |
| Refused bequest | a subclass ignoring or overriding most of what it inherits | composition instead of inheritance |
