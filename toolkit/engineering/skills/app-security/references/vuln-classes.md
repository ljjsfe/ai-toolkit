# Vulnerability classes, false positives and do-not-flag

Read after the boundary map, when filling the coverage table, and again before reporting.

## Coverage table

Copy this table into the report. Mark each row **assessed** (you traced the relevant sinks or
config in scope), **not assessed** (with the reason: out of scope, no access, ran out of
budget), or **n/a** (the class cannot occur here — say why, e.g. "no outbound HTTP"). A row
left blank counts as not assessed. Coverage of these rows is not a claim of OWASP or ASVS
compliance.

| class | OWASP 2025 | where to look | what makes it real |
|---|---|---|---|
| Access control (object, function, property, tenant) | A01 | every handler, job, export and admin tool that takes an ID | user B / tenant B reaches A's resource (law 2) |
| Path traversal | A01 | file reads/writes, downloads, archive extraction, template names built from input | an attacker-controlled path escapes the intended directory after canonicalisation; zip entries with `../` (zip slip) |
| SSRF | A01 | any server-side fetch of a URL, hostname, webhook target, image/import URL, OAuth/OIDC metadata URL | attacker picks the destination; check redirects are not followed blindly, each resolved IP is checked (not just the hostname — DNS rebinding), and cloud metadata (`169.254.169.254`, `metadata.google.internal`) and private ranges are blocked |
| Security misconfiguration | A02 | debug mode, admin consoles, CORS, cookies, headers, default credentials, verbose errors in prod config | reachable in the deployed configuration, not only in a dev file |
| Dependency supply chain | A03 | manifests, lockfiles, install scripts, vendored code | a known-vulnerable version whose vulnerable function is reachable; missing lockfile or unpinned install in a build that holds secrets; post-install scripts from untrusted packages. Dev dependencies count when they run in CI with publishing credentials |
| CI/CD pipeline | A03 | `.github/workflows`, other CI config | `pull_request_target` or `workflow_run` that checks out or runs fork code, or consumes fork artefacts/caches, with secrets or a write token; `${{ github.event.* }}` interpolated into `run:` shell; broad default `permissions`; unpinned third-party actions in release jobs |
| Cryptography | A04 | password storage, token generation, encryption at rest, signature checks | password hashing with a fast hash (MD5/SHA-*) instead of bcrypt/scrypt/Argon2; security tokens from a non-CSPRNG (`Math.random`, `random.random`); ECB mode or unauthenticated encryption; hardcoded keys; non-constant-time comparison of secrets |
| Secrets in code and git history | A04 | current tree **and** history (`git log -p -S <prefix>`, a secret scanner over all commits), CI config, Dockerfiles and image layers, logs | a credential with real authority was committed, even if later deleted. Report exposure, recommend revocation and rotation; deleting it from history is not remediation. Never print the secret in the report |
| Injection (SQL, NoSQL, OS command, template, LDAP) | A05 | string-built queries, `.raw()`/`text()` with interpolation, `shell=True`, `exec`, `child_process.exec`, user input rendered as a template | attacker-controlled data changes the structure of the query or command; parameterised queries and argument arrays are not injection |
| XSS | A05 | `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, the Django `safe` filter and `mark_safe`, `{% autoescape off %}`, URL sinks (`href` with `javascript:`), `postMessage` handlers | attacker-controlled data reaches a sink in the wrong encoding context; auto-escaped template output is not XSS |
| Insecure design / business logic | A06 | money, quotas, coupons, state machines, multi-step flows | a step can be skipped, replayed, raced or reordered (double spend, negative quantity, check-then-act on balance) |
| Authentication and sessions | A07 | login, reset, MFA, session store, cookies | session ID not rotated at login (fixation); logout or password change does not revoke other sessions; cookies missing `HttpOnly`/`Secure`/`SameSite` where it matters; enumeration through different error text; no rate limit on credential guessing |
| JWT and bearer tokens | A07 | token verification code | `alg: none` or algorithm taken from the token; HS/RS confusion; signature not verified (decode-only); `exp`, `aud`, `iss` not checked; long-lived tokens with no revocation; tokens in URLs |
| Deserialisation | A08 | `pickle.loads`, `yaml.load` (not `safe_load`), `Marshal.load`, PHP `unserialize`, Java `ObjectInputStream`, .NET `BinaryFormatter`, JSON with type hints/`create_additions` | attacker-controlled bytes reach a deserialiser that can instantiate arbitrary types |
| Integrity of artefacts and state | A08 | update channels, signed URLs, webhooks, client-held state | unsigned or unverified artefacts; trust in client-supplied prices, roles or flags |
| Logging and alerting | A09 | auth failures, admin actions, payment events | security-relevant events not logged, or secrets and tokens written to logs; log injection via unescaped newlines |
| Exceptional conditions | A10 | error handlers around auth and payment checks | the check fails open (exception → allow), partial state left after an error, rollback missing |
| CSRF | — | cookie-authenticated state-changing endpoints | no token, `SameSite` or origin check on a state change |
| Open redirect | — | `next`, `return_to`, `redirect_uri` parameters | arbitrary external redirect, especially in OAuth flows |
| Mobile OAuth | — | native-app sign-in | an embedded WebView instead of the system browser or an in-app browser tab (Custom Tabs, iOS auth session); no PKCE |
| File upload | — | upload handlers and storage | executable types served from the app origin, content type trusted from the client, no size limit, user-chosen file names |
| Mass assignment | — | model binding from request bodies | see the "Where to look first" table in `SKILL.md` |

Server-controlled sources — operator settings, environment variables, config files, constants,
signed session data — are not attacker input. Attacker-controlled sources include query and
body parameters, most headers, unsigned cookies, URL path segments, uploaded file content and
names, WebSocket messages, webhook bodies, and data another user stored.

## False-positive patterns

Run every candidate through these before it reaches the report. Each describes a way a
suspicious-looking pattern turns out harmless.

- **A guard earlier on the path.** Walk backwards from the sink to the entry point and list
  every check in between — validation, allowlists, type coercion, middleware, decorators. A
  sink judged in isolation is not a finding.
- **Unreachable by construction.** The branch that reaches the sink only runs under conditions
  (a minimum length, an enum check, a feature flag that is off in production) that rule out
  the attack. Write the conditions out and see whether they can all hold with hostile input.
- **The guard is the code you flagged.** Validation and bounds-checking code looks dangerous
  because it handles hostile input; that is its job.
- **The source is not the attacker.** The value comes from operator config, an install-time
  step, a trusted internal store or another server you control.
- **The framework or API already prevents it.** Auto-escaping, parameterised ORM calls, safe
  library defaults, size-bounded APIs. Check that the escape hatch (`raw`, `safe`,
  `dangerouslySetInnerHTML`) is not in use before dismissing.
- **No concurrency, no race.** Claiming a race or TOCTOU needs two paths that really run at
  once on shared state with nothing serialising them — not single-threaded start-up code.
- **Arithmetic that cannot happen.** Overflow, underflow and off-by-one claims need input
  ranges that actually allow them after earlier checks.
- **Impact without security meaning.** A crash in a non-critical background task or a failure
  to store non-sensitive data is an operational bug; ask whether it gives code execution,
  privilege, data disclosure or money.
- **A secondary control failing while the primary holds.** Defence-in-depth gaps (a missing
  header, a token not cleaned up when tokens are single-use anyway) are hardening notes, not
  vulnerabilities, unless you can show the primary control is also bypassable.
- **Test, debug and dead code.** Only a finding if it ships or runs in production.

## Do-not-flag list

Not findings, unless a concrete attack path shows otherwise:

- Test files, fixtures, examples and documentation strings (unless the review is about them).
- Dead or commented-out code.
- Patterns fed only by constants or server-controlled configuration (`requests.get(settings.API_URL)`).
- Code reachable only after authentication, *when the authenticated actor already has the
  power the bug would give* — otherwise note the auth requirement in severity, do not drop it.
- Auto-escaped template output, React/Vue interpolation, parameterised queries and ORM filter
  methods.
- MD5/SHA-1 used for checksums, cache keys or deduplication; `random` used for non-security
  purposes (UI, sampling, jitter).
- Missing security headers, rate limits or hardening flags with no scenario in which their
  absence enables an attack here.
- Theoretical issues that need the attacker to already control the server, the build, or
  another user's session.
- Generic advice ("consider input validation", "use HTTPS") with no located sink.
- Anything a scanner flagged that you have not traced yourself (treat scanner output as
  candidates).

Do **not** blanket-exclude: development dependencies (they run in CI with secrets), denial of
service and resource exhaustion (judge by impact), old secrets in history (judge by whether they
were revoked), or prompt injection through user-controlled text (route to `agent-security`).
