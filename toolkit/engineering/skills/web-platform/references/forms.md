# Forms and autofill

Client-side validation is for the user; the server validates for security.

## Autofill only works if the browser can recognise the form

- Each flow (sign-in, sign-up, checkout) in its own `<form>` with a `<button type="submit">`.
  Browsers store autofill data only for inputs with a stable `name` or `id` (not regenerated per
  page load or deploy) inside a form with a submit button.
- Every control has a `name` and a `<label for>`; placeholder text is not a label.
- Secondary buttons get `type="button"`, or they submit the form.

## Tokens that change the outcome

| field | attributes |
|---|---|
| sign-in username / email | `autocomplete="username"` (add `webauthn` for passkey autofill, see `security.md`) |
| sign-in password | `type="password" autocomplete="current-password" required` |
| sign-up password | `autocomplete="new-password"` (lets the browser suggest a strong one) |
| one-time code | `type="text" inputmode="numeric" autocomplete="one-time-code"` |
| card | `autocomplete="cc-number"`, `cc-exp`, `cc-csc`; one field per value |
| address | `street-address` in a `<textarea>` for international users, or `address-line1`/`address-line2` when split; prefix `shipping` / `billing` when both appear |
| name | one field, not first/last; no Latin-only pattern |

- Never block paste, and never turn `autocomplete` off, on passwords and codes.
- Identifiers (username, email, URL, codes, search): `autocorrect="off"`, `autocapitalize="none"`,
  `spellcheck="false"`. `autocorrect` became Newly available on 2026-09-11; older browsers ignore it.
- `enterkeyhint` (`next`, `done`, …) and `inputmode` are Widely available.
- Do not mask the card security code. Make postal codes optional.

## One-time codes

- One input, never one box per digit: split boxes break `one-time-code` autofill and paste and
  confuse screen readers. Need the look? Style a single input with `letter-spacing` and a
  monospace font.
- Never `type="number"` (spinners, lost leading zeros, scroll-wheel changes) and not `type="tel"`.
- SMS body: a human sentence with the code first; last line `@example.com #123456` — host only,
  one space, nothing after it.
- WebOTP is limited (Chrome 93, Edge 93, Safari 27; no Firefox). Call
  `navigator.credentials.get({ otp: { transport: ['sms'] } })` only when `'OTPCredential' in window`,
  with an `AbortController` aborted on manual submit, on resend and on unmount. On success set the
  value and call `form.requestSubmit()`, not `form.submit()`, which skips submit handlers and
  validation.

## Enter-to-submit with IME input

A custom `keydown` handler that submits on Enter (chat boxes, rename fields, command palettes)
must return early when `event.isComposing || event.keyCode === 229`, and call
`event.preventDefault()` when it does submit. Safari delivers `compositionend` before the
confirming Enter, so `isComposing` alone is already false there; the `229` check catches it.
Migrating a legacy `keyCode === 13` check to `key === 'Enter'` without these checks introduces
the bug. Plain implicit form submission with no custom handler needs nothing. Keep a visible
submit button.

## Validation timing

| event | do |
|---|---|
| `input` | only clear errors that are now fixed |
| `blur` (if edited) | check and show the error |
| `submit` | block, then move focus to the first invalid field or an error summary |

- Style with `:user-invalid` / `:user-valid` (Widely available since 2023-11-02), not `:invalid`,
  which marks empty required fields before the user touches them.
- Native constraints first (`required`, `minlength`, `pattern`), custom messages via
  `setCustomValidity()`.
- Set `aria-invalid="false"` until the field is invalid, then `true`. Add the error's id to
  `aria-describedby` only while the error shows. Announce errors through one polite live region,
  not a live region per message.
- Do not disable submit to prevent invalid submission; disable it only after a valid submit, to
  stop double posts.
- Inputs that zoom the page on focus in iOS: see mobile-native (font size 16px minimum).

## Newer form features

- `field-sizing: content` (auto-growing inputs and textareas) is Newly available since 2026-06-16;
  older browsers keep the fixed size.
- `:autofill` styling is limited (Chrome 110, Edge 110, Safari 15; Firefox matches only
  username and password fields).
- `<input type="checkbox" switch>` is limited (Safari 17.4 only); load `input-switch-polyfill`
  only when `'switch' in HTMLInputElement.prototype` is false.
- Customizable `<select>`: see `components.md`.
