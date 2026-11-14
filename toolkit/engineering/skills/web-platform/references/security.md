# Browser-side security

Browser defences only. Authorisation, tenancy, webhooks and server input validation belong to
`app-security`.

## DOM XSS sinks

- Grep for `innerHTML`, `outerHTML`, `document.write`, `eval`, string `setTimeout`, and
  assignments to `script.src`. Text goes in through `textContent`; structure through
  `document.createElement` or `DOMParser`, never string concatenation.
- Untrusted HTML that must render: `element.setHTML(html)` (Sanitizer API) parses, sanitises and
  inserts in one step, and its default config cannot be loosened into allowing XSS-unsafe markup.
  Limited: Chrome 146, Edge 146, Firefox 148; no Safari.
  - Fallback: detect with `'setHTML' in Element.prototype` and load DOMPurify only when it is
    missing. To match the native behaviour, set `ALLOW_ARIA_ATTR: false`, `ALLOW_DATA_ATTR: false`,
    `KEEP_CONTENT: false`.
  - To inspect before inserting, use `Document.parseHTML()` and move the nodes; serialising back to
    a string and re-parsing with `innerHTML` reopens mutation XSS.
  - Content that is also rendered on the server, in email or in other clients is sanitised on the
    server too.

## Trusted Types

Status: Newly available since 2026-02-24 (Firefox 148 was last).

- Enforcement is a CSP directive, `require-trusted-types-for 'script'`; after that, string writes
  to sinks throw unless they come from a named `trustedTypes.createPolicy()` that sanitises.
- Never create a pass-through policy (`createHTML: (s) => s`); it disables the protection.
- Roll out with `Content-Security-Policy-Report-Only` first; a temporary `default` policy that logs
  string writes finds the remaining sinks. Enforce once reports reach zero.
- Restrict policy names with `trusted-types <names>`; add `dompurify` if DOMPurify is used with
  `RETURN_TRUSTED_TYPE: true`, and `default` while migrating.
- First check that the framework and third-party libraries produce Trusted Types; if they write raw
  strings to sinks, enforcement breaks them.
- Older browsers: a "tinyfill" (`if (!window.trustedTypes)` define `createPolicy` to return the
  rules object) lets the same code run there, and your policy's sanitiser still runs.

## Content Security Policy

1. Inventory first: existing headers (server, middleware, CDN, `<meta>`), inline scripts, third-party
   script origins, popup flows (OAuth, payments), embeds.
2. Ship as `Content-Security-Policy-Report-Only` with `Reporting-Endpoints` + `report-to`, for days
   to weeks of real traffic. Filter extension and crawler noise; strip PII and tokens from reports.
3. Enforce:
   - `script-src 'nonce-{random per request}' 'strict-dynamic' 'report-sample'` (static sites: script
     hashes instead of a nonce). `https:` and `'unsafe-inline'` may follow as fallbacks for old
     browsers; modern ones ignore them when `'strict-dynamic'` is present.
   - `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'` (or `'self'`), and keep
     `report-to` on the enforced header.
   - Generate the nonce in server middleware per request and pass it to the template. Never stamp
     nonces onto every `<script>` in rendered HTML with a regex; that authorises injected scripts
     too.
4. A domain allowlist in `script-src` is not a defence: open redirects, JSONP and other scripts on
   the allowed origin bypass it. No inline `onclick=` handlers under a strict CSP.

## Companion headers (low breakage risk, deploy alongside)

| header | value |
|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains`, starting near 300s and raising it; add `preload` only when every subdomain is HTTPS for good — preload-list removal takes months, so it is the user's call |
| `X-Content-Type-Options` | `nosniff`, with correct `Content-Type` on every response |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `X-Frame-Options` | `DENY` / `SAMEORIGIN` alongside `frame-ancestors`; omit it when specific cross-origin framing is allowed |
| `Cross-Origin-Opener-Policy` | `same-origin-allow-popups` unless you are an OAuth or payment provider |
| `Cross-Origin-Resource-Policy` | `same-origin` for app-internal responses |
| `Permissions-Policy` | disable unused camera, microphone, geolocation; delegate with iframe `allow` too |
| `Clear-Site-Data` | `"cookies", "storage", "cache"` on logout |

Cookies: `__Host-` prefix (`Secure`, `Path=/`, no `Domain`), `HttpOnly`, explicit `SameSite=Lax`;
embedded third-party contexts need `SameSite=None; Secure; Partitioned`. SRI only for immutable,
versioned files. COOP + COEP cross-origin isolation only if you need `SharedArrayBuffer`.

## Origins and postMessage

- Send with an explicit target origin, never `*`, when the data is sensitive.
- Never compare origins with `startsWith` or substring checks (`https://app.example.com.attacker.example`
  passes), and never split hostnames on `.` to decide same-site (`.co.uk`, `.github.io`).
- `Origin.from(event).isSameOrigin(trusted)` / `isSameSite()` do this properly but are limited
  (Chrome 145, Edge 145, Safari 26.5; no Firefox). Fallback: parse both sides with `new URL()`,
  reject `'null'`, compare `.origin`. For a known sandboxed iframe, check
  `event.source === expectedWindow` instead, because its origin serialises as `"null"`.

## Passkeys (WebAuthn)

- Needs a secure context (`https://`, or `http://localhost` in development).
- Read `rpId` from the server's options (`publicKey.rp.id` / `publicKey.rpId`), never from
  `window.location.hostname`; the RP ID may be a parent domain or a related origin.
- Server-side verification with a maintained library (SimpleWebAuthn, py_webauthn, java-webauthn-server,
  go-webauthn…); on the client call the native API directly.
- Parse server JSON with `PublicKeyCredential.parseCreationOptionsFromJSON()` /
  `parseRequestOptionsFromJSON()` (Newly available since 2025-03-31); load `webauthn-polyfills`
  for older browsers.
- Sign-in page: passkey autofill via `navigator.credentials.get({ mediation: 'conditional', … })`
  plus `autocomplete="username webauthn"` on the username input, and a separate explicit
  "Sign in with a passkey" button. Store the requested `userVerification` in the server session,
  not in a query parameter.
- Offer passkey creation after a full password sign-in (after every MFA factor) with
  `mediation: 'conditional'` on `create()`; swallow `InvalidStateError`, `NotAllowedError` and
  `AbortError` silently. Relax the user-presence check on the server only for those conditional
  creations.
- Gate "Create passkey" UI on `PublicKeyCredential.getClientCapabilities()` (Newly available since
  2025-02-06).
- Signal API (`signalUnknownCredential`, `signalAllAcceptedCredentials`,
  `signalCurrentUserDetails`) keeps password managers in sync; limited (Chrome 132, Edge 132,
  Safari 26; no Firefox), no polyfill, so feature-detect each method, wrap in `try`, and log
  failures with `console.warn`.
- Re-authentication must check that the returned credential belongs to the signed-in user.
- The AAGUID is a UX hint (provider name and icon), never an access decision.
