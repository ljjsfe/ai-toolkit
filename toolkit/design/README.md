# design

Adopted from upstream rather than rewritten:

- **impeccable** (external, see `../external.yaml`) — visual design taste end to end (surface
  modes, direction, craft floor, audit, polish, motion, and edit-time detector hook). Put
  per-project context and visual tokens in the project's `PRODUCT.md` and `DESIGN.md`.
- **emilkowalski/skills** (vendored in `vendor/`, pinned in `../vendored.json`) — three focused
  companions: `review-animations` (motion standards; sets `disable-model-invocation: true`, so in
  Claude Code a model cannot call it: toolkit skills read its `SKILL.md` and `STANDARDS.md`), `mobile-native`
  (viewport, touch, scroll and safe-area traps on real phones), and `break-ui` (realistic
  worst-case data toggle). The copies name sibling skills that are not installed (`animate`,
  `animate-expo`, `emil-design-eng`, `prototype`, `choreograph`); impeccable covers those jobs.
  Never edit `vendor/`: refresh it with `python3 scripts/vendor_sync.py --update emilkowalski-skills`.
- **taste-skill** (`design-taste-frontend`, optional external) — alternative art-direction
  workflow for landing pages, apps and film modes; use one design system per project because its
  house rules conflict with impeccable's.

This folder holds only what those projects do not cover. Currently: nothing of our own.
Personal design preferences (`personal/design.md`) are merged into the installed copies of the
vendored skills as `PERSONAL.md`; the copies in this repo stay unchanged.

If a gap shows up in real use, add a small skill under `skills/` that covers exactly that gap and
cross-references `impeccable` — never a second design system.
