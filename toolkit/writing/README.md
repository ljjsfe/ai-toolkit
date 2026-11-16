# writing

- `skills/writing` — the toolkit's own writing skill.
- `vendor/humanizer`, `vendor/humanizer-zh` — the de-AI editing pass, vendored unchanged
  (`SKILL.md` only) from blader/humanizer and op7418/Humanizer-zh, pinned in `../vendored.json`.
  humanizer 4+ may add "a specific detail it knows to be true"; the writing skill runs
  `scripts/new_specifics.py` after it, so the guard lives there, never in the copy.

Personal preferences (`personal/writing.md` or `personal.local.md` here) are merged into the
installed copies of all three as `PERSONAL.md`, which is the voice sample step 6 hands to the
humanizer. Never edit `vendor/`: refresh it with `python3 scripts/vendor_sync.py --update <source>`.
