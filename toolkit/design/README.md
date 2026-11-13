# design

Adopted, not rewritten: **impeccable** (see `../external.yaml`). It owns visual design taste.
**taste-skill** v2 is listed there as optional (originally landing pages; v2.5+ also adds `--app`
and `--film`), but install only one design system per project because their house rules conflict.

This folder holds only what impeccable does not cover. Currently: nothing public.
Put per-project visual tokens in the project's own `.impeccable.md` or `DESIGN.md`. (Because no
local skill lives in `toolkit/design/skills/` yet, category preferences are only merged if you add
a local gap skill here first.)

If a gap in impeccable shows up in real use, add a small skill under `skills/` that covers
exactly that gap and cross-references impeccable — never a second design system.
