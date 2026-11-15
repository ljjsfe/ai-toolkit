# Performance: INP, LCP, CLS

Measure first (iron law 2). Field data decides; a lab trace explains the mechanism.

## Get the field number and its attribution

- If no RUM tool exists, use the `web-vitals` library's attribution build
  (`import { onINP } from 'web-vitals/attribution'`) and beacon the attribution to your analytics
  with `navigator.sendBeacon`. A console log is not field data.
- INP is built on Event Timing, Newly available since 2025-12-12 (Safari 26.2 was last). Browsers
  without it cannot report INP at all, so a missing value is not a good value.
- Long Animation Frames (LoAF) adds which script ran (`sourceURL`, `sourceFunctionName`) and
  style vs layout time. Chrome 123 and Edge 123 only, but safe without a fallback: it is extra
  detail, and what it finds usually applies in other browsers too. Prefer it to the JS
  Self-Profiling API, which costs more at runtime.

## INP: find the subpart, then fix it

Split the slow interaction into its three subparts before reading handler code:

| subpart is largest | meaning | look at |
|---|---|---|
| input delay | other work was already running when the user acted | long tasks from timers, third-party scripts, hydration |
| processing duration | the interaction's own handlers | the longest script LoAF names |
| presentation delay | rendering the next frame | style and layout cost after the handler |

High style duration points to expensive selectors or broad invalidation (narrow the rules). High
layout duration points to DOM size or forced reflow (batch reads before writes, add containment).
Forced work inside scripts shows as `forcedStyleDuration` / `forcedLayoutDuration`; where the split
fields are missing, use the combined `forcedStyleAndLayoutDuration`.

Task budget:

| work | do |
|---|---|
| under 50ms | run it synchronously |
| 50–250ms | slice it and yield between slices |
| over 250ms | move it to a Web Worker |

- **Yield on a deadline, not a counter:** check `performance.now()` against a deadline 50ms out;
  when passed, `await scheduler.yield()` if `'scheduler' in window && 'yield' in scheduler`, else
  `await new Promise(r => setTimeout(r, 0))`, then reset the deadline. Scheduler API is limited:
  Chrome 129, Edge 129, Firefox 142; no Safari.
- `setTimeout(…, 0)` puts the continuation at the back of the task queue; `scheduler.yield()` puts
  it at the front. That is why the fallback is a fallback, not the default.
- Background work (analytics, prefetch) goes through `scheduler.postTask(fn, { priority:
  'background' })`; load `scheduler-polyfill` only when `postTask` is missing.
- Paint feedback first (pressed state, spinner), then do the heavy work.
- Never interleave DOM reads (`offsetHeight`, `getBoundingClientRect()`) and writes in one loop.
- Debounce or throttle `scroll`, `resize` and rapid `input` handlers; no heavy `setInterval` polling.
- Large, complex regions that mutate on interaction: `content-visibility: auto` (with
  `contain-intrinsic-size`) or `contain: layout style paint` keeps the reflow inside the region.

## LCP

- The LCP image must be discoverable in the HTML response: an `<img>` (preferred), or a
  `<link rel="preload" as="image">` when CSS or JS loads it. A hero rendered by client-side JS adds
  an HTML → JS → execute → image chain.
- `fetchpriority="high"` on the LCP image (and its preload). One or two resources per page at
  most; prioritisation is zero-sum. Never combine it with `loading="lazy"`. Fetch priority is
  Newly available since 2024-10-29 and is ignored where unsupported.
- Never `loading="lazy"` on an above-the-fold image. Use `loading="lazy"` alone for ordinary
  below-the-fold images, without `fetchpriority="low"`.
- `fetchpriority="low"` is for images that are above the fold but hidden: later carousel slides,
  mega-menu and modal images.
- Omit `fetchpriority="auto"`. `importance` and `loading="auto"` do nothing in any browser.
- `srcset` without `sizes` makes the browser assume `100vw` and fetch the largest file.
- Preload at most 2 images and 2–3 fonts. Font preloads always carry `crossorigin`, even
  same-origin; fonts are already high priority, so no `fetchpriority="high"` on them.
- Scripts: `defer` (or `type="module"`) for anything not needed to paint; `fetchpriority="low"` on
  analytics and ads; no CSS `@import` chains; inline critical CSS.
- Next-page loads in a multi-page site: speculation rules (`<script type="speculationrules">`) are
  limited (Chrome 109, Edge 109; no Firefox or Safari) and ignored elsewhere. Prefer document
  rules, exclude state-changing URLs such as `/logout` and `/add-to-cart`, and do not use them in
  single-page apps.
- `Cache-Control: no-store` can keep the page out of the back/forward cache. Chrome has admitted
  no-store pages since its April 2025 rollout, but evicts them on cookie or auth changes, when the
  page uses WebSocket, WebTransport or WebRTC, or when a fetch/XHR response is itself no-store, and
  caps their stay at 3 minutes; other browsers may still refuse them (Chrome for Developers,
  "Enabling bfcache for Cache-Control: no-store", checked 2026-11-14). Reserve it for private data
  and use `no-cache` or `max-age=0` for pages that just need to be fresh.

## CLS

- `width` and `height` attributes (or CSS `aspect-ratio`) on every `<img>`, `<video>` and `<iframe>`.
- `content-visibility: auto` (Newly available since 2025-09-15; Safari 26 was last) goes only on
  sections below the initial viewport of long, complex pages. Always pair it with
  `contain-intrinsic-size: auto <estimate>`, estimating from the content in `lh`, `rem` or `ch`;
  without it the element collapses to 0 and the scrollbar jumps. Not worth it on small pages.
  Check that keyboard navigation still reaches content inside it.
- `content-visibility: hidden` for fast view switching; where unsupported the content shows, so
  default to `display: none` and switch inside `@supports (content-visibility: hidden)`.
- `scrollbar-gutter: stable` (Newly available since 2024-12-11) reserves scrollbar space so
  content does not shift when it starts to overflow.

## Media

- `loading="lazy"` on `<video>` and `<audio>` is limited (Chrome 150, Edge 150). Pair it with
  `preload="none"` or `preload="metadata"` so other browsers still skip the file; the poster is
  still fetched there. If the poster must wait too, detect
  `Object.hasOwn(HTMLMediaElement.prototype, 'loading')` and fall back to `IntersectionObserver`.
- A video that is the LCP element: preload its poster with `fetchpriority="high"`.
