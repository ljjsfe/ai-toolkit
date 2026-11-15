---
paths:
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.jsx"
  - "**/*.tsx"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*.astro"
  - "**/*.js"
  - "**/*.mjs"
---
# Web platform traps

Check the project's browser support matrix (browserslist, AGENTS.md) before using a feature
that is not Baseline Widely available; "limited" below means ship the fallback. Detail and
fallback code: the `web-platform` skill.

- Modals are `<dialog>` + `showModal()` (Widely available since 2022): no `role="dialog"`,
  `aria-modal`, hand-made focus trap or Esc handler, and never lock scroll with `overflow: hidden`
  on `html`/`body`. `closedby="any"` has no Safari yet: keep a backdrop-click fallback.
- Menus, tooltips and toasts use the `popover` attribute (Baseline 2025) instead of an overlay
  library; load `@oddbird/popover-polyfill` only when `"popover" in HTMLElement.prototype` is false.
- Open and close from HTML with invokers, `commandfor` + `command="show-modal"`/`"toggle-popover"`
  (Baseline Dec 2025). Keeping `popovertarget` on the same button is a safe fallback for browsers
  with popover but no invokers: where `commandfor` resolves, the button runs the command instead.
- Anchor positioning's core is Baseline (Newly available 2026-01-13: Chrome 125, Firefox 147,
  Safari 26); the full feature needs Chrome 157 / Safari 27 and is not in Firefox, so gate newer
  parts inside `@supports` and keep an absolute-position fallback.
- `appearance: base-select` has no Firefox; keep each `<option>`'s text readable alone, because
  older browsers drop the markup inside it.
- View transitions: same-document `startViewTransition()` is Baseline 2025, cross-document
  `@view-transition` has no Firefox. Easing and duration come from the motion rules (ease-out,
  under ~300ms for in-page UI), not from the guide samples' `ease-in` exits.
- Viewport units follow mobile-native: `100dvh` for app shells, `100svh` for heroes and first
  screens, which must not jump as the URL bar moves.
- Never `loading="lazy"` on the LCP image; it must be in the server HTML and is the one (at most
  two) `fetchpriority="high"` resource. A `srcset` with `w` descriptors needs `sizes`.
- INP: split work longer than 50ms with `scheduler.yield()` behind a feature check (no Safari),
  falling back to `setTimeout`; move work over ~250ms to a worker.
- `content-visibility: auto` only on below-the-fold sections of long pages, always paired with
  `contain-intrinsic-size: auto <estimate>`, or the page jumps on scroll.
- `Cache-Control: no-store` can keep a page out of the back/forward cache: Chrome (since Apr 2025)
  admits it but evicts on cookie changes or WebSocket/WebTransport/WebRTC use, and other browsers
  may refuse it; on a non-private page use `no-cache` (checked 2026-11-14).
- A one-time code is one `type="text" inputmode="numeric" autocomplete="one-time-code"` field,
  never `type="number"` or split boxes; never block paste.
- A custom Enter-to-submit handler must skip `event.isComposing || event.keyCode === 229`, or IME
  users (Japanese, Chinese, Korean) send half-composed text.
- Style errors with `:user-invalid`, not `:invalid`, so untouched required fields stay clean.
- Where `innerHTML`/`outerHTML`/`document.write` receives non-constant HTML: `setHTML()` (no Safari:
  load DOMPurify on demand) or a named Trusted Types policy, never a pass-through
  `createHTML: (s) => s`.
- CSP: per-request nonce + `'strict-dynamic'`, `object-src 'none'`, `base-uri 'none'`, shipped as
  `Content-Security-Policy-Report-Only` first; a domain allowlist is not a `script-src` defence.
- Dates: calendar dates and wall-clock times are `Temporal.Plain*`, real events `ZonedDateTime`
  with IANA zone names; Temporal has no Safari, so load `temporal-polyfill` behind a check.
