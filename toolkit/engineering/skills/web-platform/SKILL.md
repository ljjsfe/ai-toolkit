---
name: web-platform
description: >-
  Web-platform work checked against Baseline: support and fallbacks, native
  dialog/popover/invokers/anchor/select over JS libraries, INP/LCP/CLS and long tasks, forms and
  autofill, passkeys, CSP/Trusted Types, Temporal dates, legacy modernising. Not for visual design
  (impeccable), mobile feel (mobile-native), React/Next (typescript-web rule), webapp-testing.
version: 1.0.2
sources:
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/SKILL.md (CC-BY-4.0, adapted) — Baseline policy (Widely available needs no fallback, otherwise follow the fallback unless the project states a policy; Baseline-year targets), conditional polyfills, verify legacy-scan findings before modernising [port "a Baseline YYYY target" "keep the library as the fallback" "drop false positives"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/performance/{performance,identify-inp-causes,identify-heavy-scripts,break-up-long-tasks,schedule-tasks-by-priority}.md (CC-BY-4.0, adapted) — field attribution with web-vitals, INP subparts, LoAF style vs layout split, deadline-based yielding with a setTimeout fallback, task budget [port "Split the slow interaction into its three subparts" "Yield on a deadline, not a counter" "puts it at the front" "A console log is not field data"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/performance/{optimize-image-priority,optimize-preload-priority,optimize-script-priority,improve-next-page-load-performance,defer-rendering-heavy-content,interactions-in-complex-layouts,lazy-load-video-and-audio}.md (CC-BY-4.0, adapted) — LCP discovery and fetchpriority rules, preload limits, speculation rules, content-visibility with contain-intrinsic-size, lazy media fallback [port "The LCP image must be discoverable in the HTML response" "is for images that are above the fold but hidden" "Preload at most 2 images" "exclude state-changing URLs" "without it the element collapses to 0"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/{ui-components/dialog,ui-behaviors/light-dismiss-a-dialog,ui-behaviors/prevent-page-scroll-under-modal-dialog,ui-behaviors/declarative-dialog-popover-control,ui-behaviors/custom-button-actions}.md (CC-BY-4.0, adapted) — dialog type choice, closedby values and fallback, backdrop scroll containment, popover polyfill caveats, invoker commands [port "Pick the first case that fits" "the backdrop is not a scroll container" "makes older browsers discard the whole rule" "The `command` event does not bubble"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/{css/css-layout,ui-atoms/viewport-aware-dropdowns,ui-atoms/position-aware-tooltips,ui-behaviors/interest-triggered-tooltips,forms/branded-select-styling}.md (CC-BY-4.0, adapted) — anchor positioning status, polyfill limits and @supports gating, interest invokers, customizable select [port "strand the popover at the top-left corner" "needs an explicit unique" "gives up the native mobile picker"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/ui-behaviors/{animate-element-entry-exit,animate-to-from-top-layer,same-document-transitions,cross-document-transitions}.md (CC-BY-4.0, adapted) — starting-style and allow-discrete pitfalls, Firefox display-transition detection bug, view-transition naming, focus and support split [port "makes older browsers drop the whole" "returns true there" "two elements with the same name cancel the transition" "Transitions do not move focus"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/forms/{forms,autofill-sign-in-form,autofill-sign-up-form,autofill-payment-form,autofill-address-form,sms-otp-form,ime-safe-enter-submit,validate-input-after-interaction}.md (CC-BY-4.0, adapted) — autofill prerequisites and tokens, single-field OTP and WebOTP, IME-safe Enter, validation timing [port "Browsers store autofill data only for inputs with a stable" "One input, never one box per digit" "the `229` check catches it" "only clear errors that are now fixed"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/security/{security,trusted-types,sanitize-untrusted-html,validate-origins}.md (CC-BY-4.0, adapted) — sink hygiene, Sanitizer with DOMPurify fallback, Trusted Types rollout, nonce-based CSP rollout, companion headers, origin comparison [port "reopens mutation XSS" "Never create a pass-through policy" "Never stamp nonces onto every" "reject `'null'`, compare `.origin`"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/security/{passkeys,passkey-registration,passkey-authentication,passkey-conditional-create,passkey-management,passkey-reauthentication}.md (CC-BY-4.0, adapted) — server-provided rpId, conditional mediation, conditional create after full sign-in, Signal API gating [port "never from `window.location.hostname`" "after every MFA factor" "never an access decision"]
  - upstream/googlechrome-modern-web-guidance/skills/modern-web-guidance/guides/js/{capture-location-agnostic-data,coordinate-global-events,calculate-event-differentials,sort-high-precision-timestamps,support-global-calendar-systems}.md (CC-BY-4.0, adapted) — Temporal type choice, DST disambiguation, durations, instants, calendars [port "Pick the type by what the value means" "never a fixed offset" "relativeTo` is required" "Loop to `monthsInYear`"]
  - authored for this toolkit (cross-source resolution with the vendored mobile-native and review-animations) — motion values come from the motion rules, not from the view-transition samples [port "keep the API usage, not those timings"]
---

# Web Platform

Most front-end mistakes a strong model still makes are dated ones: a library for something the
browser now does, a feature used where a target browser lacks it, or a "fix" to a Web Vital
nobody measured.

## Iron laws

1. **Check Baseline and the project's support matrix before using a feature.** Find the matrix
   first: `browserslist`, `package.json`, a "Browser Support" line in `AGENTS.md` / `CLAUDE.md`.
   With none stated, Baseline Widely available needs no fallback; Newly available and limited
   features need the fallback in the reference. Under a Baseline YYYY target, a feature qualifies
   when its Baseline-since date falls in or before that year. The support data here is the guides'
   data at v1.0.0 (2026-11-10); "limited" changes month to month, so re-check MDN or
   webstatus.dev when a decision depends on it.
2. **Measure a Web Vital before and after the change; field data over lab.** Lab tools reproduce
   one device and one path; INP in particular depends on real interactions. No baseline number, no
   claim of improvement. Say where each number came from.
3. **Prefer the platform feature over a dependency when it is Baseline for the matrix.** Name what
   the removed library did and confirm the native feature covers it, including keyboard and
   screen-reader behaviour.
4. **A limited feature ships with a fallback or as progressive enhancement.** Detect on the
   interface (`'popover' in HTMLElement.prototype`, `CSS.supports(…)`), never the user agent, and
   load any polyfill conditionally, never unconditionally.

## Route

Read the file for the matching row before answering.

| task | read |
|---|---|
| slow taps, INP, long tasks, LCP, layout shift, heavy pages | `references/performance.md` |
| modal, menu, tooltip, dropdown, select, enter/exit animation, page transitions | `references/components.md` |
| sign-in, sign-up, checkout, address, one-time code, validation, IME input | `references/forms.md` |
| `innerHTML`, CSP, Trusted Types, security headers, `postMessage`, passkeys | `references/security.md` |
| dates, time zones, durations, timestamps, calendars | `references/dates.md` |

Hand-offs: visual design → `impeccable`; phone feel and viewport units → `mobile-native`; motion
values → `review-animations` (user-invoked only in Claude Code: read `../review-animations/STANDARDS.md`
rather than calling it); React and Next.js → `rules/typescript-web.md`;
server-side authorisation → `app-security`; proving it in a browser → `webapp-testing`.

## Support snapshot (guides' data, v1.0.0)

| feature | status | missing in |
|---|---|---|
| `<dialog>`, `:user-invalid`, `dvh`/`svh`, container size queries, `:has()` | Widely available | — |
| `popover` | Newly available, 2025-01-27 | — |
| invoker commands (`commandfor`) | Newly available, 2025-12-12 | — |
| same-document view transitions | Newly available, 2025-10-14 | — |
| `content-visibility` | Newly available, 2025-09-15 | — |
| `fetchpriority` | Newly available, 2024-10-29 | — |
| `@starting-style`, `transition-behavior` | Newly available, 2024-08-06 | — |
| Trusted Types | Newly available, 2026-02-24 | — |
| `closedby` on `<dialog>` | limited | Safari |
| customizable `<select>` (`base-select`) | limited | Firefox |
| cross-document view transitions | limited | Firefox |
| `scheduler.yield()` / `postTask()` | limited | Safari |
| Sanitizer API (`setHTML`) | limited | Safari |
| `Temporal` | limited | Safari |
| anchor positioning | core Newly available 2026-01-13; full feature limited | Firefox (full feature) |
| interest invokers (`interestfor`), Long Animation Frames, speculation rules | limited | Firefox, Safari |
| `overlay` property | limited | Firefox, Safari |

Anything not listed: look it up before claiming support.

## Modernising legacy front-end code

1. Search for the legacy pattern and list each hit with `file:line`:

   | legacy | replacement | keep the old code as fallback? |
   |---|---|---|
   | modal library, focus-trap, body scroll lock | `<dialog>` + `showModal()`, overscroll containment | no |
   | dropdown/tooltip overlay library | `popover` + invokers | no, polyfill if the matrix predates 2025 |
   | Popper / Floating UI | anchor positioning | yes, until it is Baseline |
   | custom select component | `appearance: base-select` | only if Firefox must match the design |
   | click-outside handler on a modal | `closedby="any"` | yes, for Safari |
   | DOMPurify + `innerHTML` | `setHTML()` | yes, DOMPurify loaded on demand |
   | `setTimeout` chunking | `scheduler.yield()` | yes, as the fallback branch |
   | moment / date-fns-tz | `Temporal` | polyfill, for Safari |

2. Verify each hit before changing it: drop false positives — code that already is a fallback,
   vendor bundles, look-alikes.
3. Replace, and where the feature is limited for the matrix keep the library as the fallback
   behind feature detection (law 4).
4. Re-run the tests and re-scan the touched files; report what was left and why.

## Output

```
Support matrix:  source (browserslist / stated policy / assumed Widely available)
Features:        feature — Baseline status and date — fallback shipped, or "none needed"
Dependencies:    removed / kept as fallback / added — reason
Vitals:          metric — before → after — field or lab, and where measured
Handed off:      what belongs to another skill, and which
```
