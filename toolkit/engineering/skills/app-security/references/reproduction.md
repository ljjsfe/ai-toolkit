# Reproduction contract

Read before running any reproduction or claiming a finding is verified or a fix confirmed.

Run reproductions only in a local or disposable environment you are allowed to use — never
against production or someone else's system. A finding is **verified** when steps 1, 2 and 4
hold: the exploit is reproduced. The third step is a further check, run once a fix exists, and is
reported separately as **fix confirmed**; a verified finding does not wait for it.

1. **Unmodified app, legitimate control passes.** The app starts unchanged, and the honest
   version of the request (user A reading A's own order) succeeds. A boot failure or generic
   error is inconclusive, not proof.
2. **The attack trips a specific security assertion.** The hostile request (user B reading A's
   order) succeeds when it should not, and the test checks *that* outcome — B received A's
   data — not merely a non-zero exit or an error printed somewhere.
3. **After the fix, the same request is refused and the legitimate control still passes**,
   with the identical assertion, and the existing test suite stays green. Run it on both
   revisions: the exploit must succeed on the vulnerable base and fail on the patch — a check
   that never succeeded anywhere proves nothing. Also try other routes to the same root cause
   (another endpoint, encoding or caller reaching the same flawed check) and the behaviour the fix
   must keep. Report the evidence level reached — source reading, build, or runtime; only a
   runtime result earns **fix confirmed**.
4. **Nothing under the harness was changed to get there:** no mocks replacing the very check
   under test, no loosened assertions, no edits to fixtures or test runner config. Mocks may
   stand in for third parties, never for the boundary being tested.

Partial evidence (a static trace, or a run where step 1, 2 or 4 does not hold) is reported as
**traced** or **plausible**, not verified. Write the reproduction as the four-field claim plus
concrete values — no placeholders.
