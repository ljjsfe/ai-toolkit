# Property-based checks

Read when a slice touches a parser, serializer, codec, normaliser, comparator, numeric type,
data structure or state machine. Example tests pin points you thought of; a property states a
rule for every input and lets a generator search for the input that breaks it. Use the
project's existing library (Hypothesis, fast-check, proptest, jqwik, rapid…). A project
without one gets a new dependency only if the user agrees: name the library and show the rule
you want to check, then leave the decision with them.

Not every unit has a property. If the honest answer is "only examples fit here", say so and
write examples.

## Catalogue, weakest to strongest

Write the strongest one the code supports; add weaker ones only where they catch something the
stronger one does not.

| strength | property | rule | typical home |
|---|---|---|---|
| 1 (weakest) | survives | `f(x)` returns or raises only its documented error type, never hangs | decoders fed arbitrary bytes, input validators |
| 2 | shape holds | output has the promised type, length, range or schema | formatters, mappers |
| 3 | invariant kept | a fact true of the input is true of the output (sum preserved, count unchanged, balanced tree stays balanced, a sorted list stays sorted after insert) | collection operations, state transitions, ledgers |
| 3 | cheap checker | the output is hard to compute but easy to check (`is_sorted(sort(xs))` and same multiset; a found path really connects the nodes) | search, sort, solvers |
| 3 | metamorphic | changing the input in a known way changes the output in a known way (adding a non-matching row leaves a filter's result alone; scaling all prices scales the total) | queries, search ranking, numeric code with no oracle |
| 3 | algebraic laws | order of arguments does not matter; grouping does not matter; a neutral element changes nothing | merges, set operations, money addition |
| 4 | idempotent | applying it twice equals applying it once: `norm(norm(x)) == norm(x)` | normalisers, formatters, deduplication, upserts |
| 5 | roundtrip / inverse | `parse(render(x)) == x`, `decompress(compress(b)) == b` | codecs, serializers, encryption pairs |
| 5 (strongest) | oracle / differential | new implementation equals a trusted reference on every input | rewrites, optimisations, a fast path beside a simple slow path |
| 5 | model-based | a sequence of generated operations on the real system matches the same sequence on a simple in-memory model | stateful APIs, caches, queues, state machines |

Roundtrip direction matters: `parse(render(x)) == x` generates valid values and is the usual
one; `render(parse(s)) == s` only holds for canonical strings, so generate canonical input
or compare after normalising.

## Properties that test nothing

- **Restating the code.** If the expected value is computed the same way the code computes
  it — `assert total(items) == sum(i.price for i in items)` when `total` is that sum — a shared
  bug passes both sides. Assert something that limits the answer without rebuilding it (the
  total never drops when an item is added; it equals the sum of totals of two halves). Calling
  a function twice on the same input and comparing is not always empty, though: it catches
  output that drifts between calls, such as JSON written from an unordered set, a cache key
  built from object identity, or a timestamp baked into an ID.
- **Vacuous through over-filtering.** Discarding generated inputs with a filter (`assume`,
  `fc.pre`, `prop_assume!`) has two failure modes. When the filter rejects everything (say
  `x > 100` together with `x < 50`), most libraries stop with an error rather than a pass —
  Hypothesis raises `Unsatisfiable` or fails the `filter_too_much` health check, fast-check and
  proptest abort after too many rejections — so the danger is someone silencing that error.
  The quieter case is a filter that keeps a small slice: the run passes, but against far fewer
  or far narrower inputs than the configured count suggests. Check the library's statistics
  or health output (Hypothesis `--hypothesis-show-statistics`, fast-check `verbose`, proptest
  rejection counts) for the number of inputs actually tried, and generate valid inputs
  directly (see below) instead of filtering.
- **Assertion-free.** The body calls the function and stops; only "survives" is being
  tested, and probably by accident.
- **Weaker than available.** Checks length when ordering could be checked too; checks "no
  crash" on a codec that has a roundtrip.

A new property must be seen red like any other test: break the code (swap a comparison,
drop a field from the encoder) and watch the generator find a counterexample.

## Generator design

- **Build valid inputs directly.** Bound ranges in the generator (`integers(min_value=1)`),
  build records from their field generators, and draw dependent values from earlier draws (pick
  a list, then pick an index within it) instead of generating both freely and filtering.
  Reserve filters for relations you cannot construct, and keep them rare.
- **Cover the edges deliberately.** Make sure empty, single-element, all-duplicate, zero,
  negative, maximum/minimum representable, NaN and infinities (where the type allows),
  empty string, non-ASCII and combining characters, and very long inputs can be generated.
  Pin the ones you already know matter as explicit examples so every run includes them.
- **Match the real input domain.** If production sees nested JSON up to depth 5, generate that,
  not flat dicts. Weight generators towards the shapes that reach the interesting code; a
  generator that almost never produces a valid header never tests the body parser.
- **Keep it shrinkable.** Prefer the library's combinators over hand-rolled randomness
  (`random.choice` inside a test) so failures shrink to a minimal counterexample. Never seed
  randomness from the clock inside the property.
- **Error paths too.** Feed arbitrary bytes to decoders and assert they either succeed or raise
  the documented error; catch only that error so anything else fails the test.
- **Budget per context.** Few examples while iterating locally, the library default or more in
  CI, a large run nightly. Disable or raise per-example deadlines for work that is legitimately
  slow, so a slow runner does not turn the property flaky.
- **Keep counterexamples.** When a property fails, decide first whether the property or the
  code is wrong; then commit the shrunk counterexample as an explicit example so it stays in
  every future run.
