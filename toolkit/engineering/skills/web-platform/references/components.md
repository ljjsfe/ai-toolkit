# Components: platform features that replace JS libraries

Support data is from the guides' Baseline data at v1.0.0 (2026-11-10). "Limited" means at least
one core browser lacks it, so ship the fallback unless the project's matrix excludes that browser.
Motion values (easing, duration) are not set here; take them from `review-animations` (if
installed) or the project's motion rules.

## Dialog — replaces modal libraries and focus-trap code

Status: `<dialog>` Widely available since 2022-03-14.

Pick the first case that fits:

| need | use |
|---|---|
| blocks the page (confirm, form, sign-in, destructive action) | `<dialog>` + `dialog.showModal()` |
| panel the user works beside (find bar, inspector, palette) | `<dialog popover>`, or `dialog.show()` if it must stay out of the top layer |
| menu, dropdown, tooltip, hovercard, toast | a semantic element with `popover`, not `<dialog>` |

`showModal()` already gives an inert page, focus containment, top layer, `::backdrop`, Esc and
back-gesture close, and focus return to the opener. So:

- Do not add `role="dialog"`, `aria-modal`, a manual focus trap, `inert` toggling, an Esc handler
  or focus-return code. Do not open a modal with `show()` or the `open` attribute.
- Name it: `aria-labelledby` on its heading (or `aria-label`); `autofocus` on the first field, or on
  the safe button (Cancel / Keep) in a destructive confirmation.
- Close with `<form method="dialog">` buttons or `command="close"`. Read `dialog.returnValue` in the
  `close` listener, then reset it to `''`; Esc sets no value, so a stale one can leak.
- Do not set `display` on `dialog` unconditionally; scope it to `dialog[open]`.
- Non-modal dialogs always get a visible close button.

**Dismissal (`closedby`).** `any` = backdrop click + Esc; `closerequest` = Esc only (the modal
default); `none` = only your code closes it. Limited: Chrome 134, Edge 134, Firefox 141; no Safari.
Without it a modal still closes on Esc and back gesture, so it degrades gracefully. If light
dismiss is required, add a click listener that closes the dialog when the click falls outside
`dialog.getBoundingClientRect()`. Put an unsaved-changes guard in the `cancel` handler, not in
`closedby="none"` alone, so it also holds where `closedby` is missing. Cancel buttons that must
run that guard use `requestClose()` / `command="request-close"`, which fire `cancel` first.

**Scroll under a modal.** Set `overscroll-behavior: contain` on `dialog:modal`, and
`overflow: hidden` + `overscroll-behavior: contain` on `dialog::backdrop` (the backdrop is not a
scroll container until you give it `overflow`). Containment on non-scrolling containers is
limited (Chrome 144, Edge 144, Firefox 150; no Safari) and `@supports` cannot detect it — it
always reports true — so treat it as progressive enhancement. Never fall back to
`overflow: hidden` or `position: fixed` on `html`/`body`: it removes the root scrollbar, shifts
layout, can jump the scroll position and breaks `position: sticky`.

## Popover — replaces dropdown / tooltip / toast overlay libraries

Status: Newly available since 2025-01-27 (Safari iOS 18.3 was last). `popover="auto"`
light-dismisses, `manual` does not. `popover="hint"` is limited (Chrome 151, Edge 151,
Firefox 153; no Safari).

- Lives in the top layer, so no `z-index` management. Never combine `popover` and `showModal()`
  on one element.
- Fallback: load `@oddbird/popover-polyfill` only when `'popover' in HTMLElement.prototype` is
  false. Before it loads, set the attribute with `setAttribute()`, not the `popover` property, and
  write state selectors as `:is(:popover-open, .\:popover-open)` — a bare `:popover-open` makes
  older browsers discard the whole rule.

## Invoker commands — replaces click-handler wiring for open/close

Status: Newly available since 2025-12-12 (Chrome 135, Firefox 144, Safari 26.2).

- `<button commandfor="id" command="…">` with `show-modal`, `close`, `request-close`,
  `toggle-popover`, `show-popover`, `hide-popover`, or a custom `--name` (custom names must start
  with `--`). The browser sets `aria-expanded` for built-in commands.
- Never put `popovertarget` and `commandfor` on the same button for the same popover: it toggles
  twice.
- The `command` event does not bubble: listen on the target, or on an ancestor with
  `{ capture: true }`. Custom commands carry no semantics; set `aria-pressed` / `aria-expanded`
  yourself.
- Hiding a popover from a button inside it drops focus; send focus back to the trigger.
- Fallback: detect `commandForElement` on `HTMLButtonElement.prototype` and import
  `invokers-polyfill` only when it is missing. The polyfill does not manage ARIA states.
- Interest invokers (`interestfor`, hover/focus-triggered tooltips) are limited: Chrome 149 and
  Edge 149 only. Detect `interestForElement` and load the `interestfor` polyfill conditionally.

## Anchor positioning — replaces Popper / Floating UI

Status (web-features, checked 2026-11-14): the core is Baseline Newly available since
2026-01-13 (Chrome 125, Firefox 147, Safari 26). The feature as a whole is limited: Chrome 157 and
Safari 27 support it fully, Firefox not yet. The guides' v1.0.0 snapshot lists Chrome, Edge and
Firefox as unsupported, which does not match web-features; check MDN for the part you use, gate
newer parts with `@supports`, and keep an absolute-position fallback.

- Use `position-area` (logical keywords such as `block-end`, `span-inline-end`) or `anchor()` on
  insets, `anchor-size()` for sizing, and `position-try-fallbacks: flip-block` for edge flipping.
  Do not mix physical and logical keywords in one `position-area`.
- A `popover` opened by `popovertarget`, `commandfor` or `interestfor` has an implicit anchor, so
  native support needs no `anchor-name`.
- **Fallback A, polyfill** (when the overlay must stay tethered): load
  `@oddbird/css-anchor-positioning` only when `CSS.supports("anchor-name: --a")` is false. It
  needs an explicit unique `anchor-name` on each trigger and matching `position-anchor`; it does
  not support `position-area` together with `position-try-fallbacks` (use `anchor()` insets with
  `inset: auto` instead); do not wrap polyfilled rules in `@supports`, which hides them from it.
- **Fallback B, no polyfill:** put `inset: auto` and `margin: 0` inside
  `@supports (position-area: block-end)` (or the feature you use). Set unconditionally, they
  override the default centring and strand the popover at the top-left corner in browsers without
  anchor positioning.
- Arrow flipping with `container-type: anchored` + `@container anchored(fallback: flip-block)` is
  also limited; hide the arrow unless `@supports (container-type: anchored)`.

## Customizable select — replaces custom select components

Status: limited — Chrome 135, Edge 135, Safari 27; no Firefox.

- Opt in with `appearance: base-select` on both `select` and `::picker(select)`. Optional
  `<button><selectedcontent></selectedcontent></button>` inside the `select` replaces the trigger;
  style `select::picker-icon` and `option::checkmark`.
- Fallback is the native control. Older parsers strip markup inside `<option>`, so its text must
  make sense alone.
- `base-select` gives up the native mobile picker and the automatic width from the longest
  option; set a width. Keep `name`, `value` and a `<label>` so forms and screen readers still work.

## Entry and exit animation of top-layer elements

- `@starting-style` (Newly available since 2024-08-06) defines where an entry transition starts.
  It does nothing for exits.
- Transition `display` with a separate `transition-behavior: allow-discrete` declaration; putting
  `allow-discrete` inside the `transition` shorthand makes older browsers drop the whole
  declaration. Add `overlay` to the transitioned properties for `<dialog>` and popovers.
- `overlay` is limited (Chrome 117, Edge 117 only). Discrete `display` transitions do not run in
  Firefox, yet `CSS.supports('transition-behavior', 'allow-discrete')` returns true there (bug
  1882408). Exit fallback: set a `data-closing` attribute that applies the exit styles, wait for
  `element.getAnimations()` to finish, then call `close()` / `hidePopover()`. Light dismiss cannot
  be intercepted that way, so those exits stay instant.

## View transitions

Status: same-document `document.startViewTransition()` Newly available since 2025-10-14
(Firefox 144, Safari 18). Cross-document is limited: Chrome 126, Edge 126, Safari 18.2; no
Firefox. Element-scoped transitions are limited to Chrome 147 and Edge 147.

- Both are progressive enhancement: unsupported browsers update or navigate instantly. Feature
  detect and run the DOM update directly when absent.
- A `view-transition-name` must be unique on each side of the transition; two elements with the
  same name cancel the transition. Remove names you assigned for one transition after its
  `finished` promise resolves.
- Cross-document: both pages opt in with `@view-transition { navigation: auto; }`, wrapped in
  `@media (prefers-reduced-motion: no-preference)`. Direction types via `types` in that rule or a
  `pagereveal` listener, styled with `:active-view-transition-type()`.
- Transitions do not move focus. After the update, move focus to the new heading or view
  container (`tabindex="-1"`).
- Morph only what the user is tracking (hero image, heading). Elements with running animations
  appear frozen, because the transition animates snapshots.
- Motion values: the guide samples use exits such as `0.4s ease-in`. In-page UI here uses
  ease-out and stays under ~300ms (`review-animations`); keep the API usage, not those timings.
- React apps: `ViewTransition` is covered in `rules/typescript-web.md`.
