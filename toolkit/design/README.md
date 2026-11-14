# design

Adopted from upstream rather than rewritten (see `../external.yaml`):

- **impeccable** — visual design taste end to end (surface modes, direction, craft floor, audit,
  polish, motion, and edit-time detector hook). Put per-project context and visual tokens in the
  project's `PRODUCT.md` and `DESIGN.md`.
- **emil-design-engineering** — three focused companions: `review-animations` (motion standards;
  sets `disable-model-invocation: true`, so invoke it explicitly or from `code-review`),
  `mobile-native` (viewport, touch, scroll and safe-area traps on real phones), and `break-ui`
  (realistic worst-case data toggle).
- **taste-skill** (`design-taste-frontend`, optional) — alternative art-direction workflow for
  landing pages, apps and film modes; use one design system per project because its house rules
  conflict with impeccable's.

This folder holds only what those projects do not cover. Currently: nothing public. (Because no
local skill lives in `toolkit/design/skills/` yet, category preferences are only merged if you add
a local gap skill here first.)

If a gap shows up in real use, add a small skill under `skills/` that covers exactly that gap and
cross-references `impeccable` — never a second design system.
