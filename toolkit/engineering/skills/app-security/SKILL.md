---
name: app-security
description: >-
  Security-review a web, mobile, or backend application: map trust and tenant boundaries first,
  test authorisation with a second identity/tenant, and report only findings with a concrete
  attack path. Use before shipping auth, tenancy, payments, or webhooks (diff review: code-review;
  LLM/tool agents: agent-security).
version: 1.3.1
sources:
  - upstream/gstack/cso (MIT) — boundary and invariant census first, sibling propagation, exploitability gating, three separate judgements, independent re-derivation, webhook review order, two-user and two-tenant negative controls [port "map before you hunt" "tested with a second identity" "look for its siblings" "are separate judgements" "re-derive the result" "trace the whole middleware and handler chain"]
  - upstream/gstack/cso/{SKILL.md,sections/audit-phases.md} (MIT) — OWASP Top 10 coverage map, secrets in git history, dependency supply chain, CI pull_request_target, reproduction contract, complete / partial / not-assessed report header [port "Copy this table into the report" "Secrets in code and git history" "Dependency supply chain" "pull_request_target or workflow_run" "Reproduction contract" "the same request is refused" "complete, partial or not assessed"]
  - upstream/gstack/cso/sections/audit-phases.md (MIT) — ASVS 5.0 requirement mapping, STRIDE pass, data classification, infrastructure and skill supply-chain phases [gap not carried over; the coverage table covers OWASP Top 10 classes only]
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/security-reviewer.md (MIT) — confidence tied to attack-path traceability with a critical-impact override; feature-gate leaks [port "only if impact is critical" "gated, internal or unreleased feature"]
  - upstream/trailofbits-skills/plugins/{fp-check,differential-review} (CC BY-SA 4.0 — ideas only, no wording) — restate the claim before verifying, trace the validation chain, risk not size, git blame on removed security code, counted blast radius, exploit chains across rejected findings [port "each suspected bug as four fields" "order the files by what they can break" "count the callers" "two or more of the findings you dropped"]
  - upstream/trailofbits-skills/plugins/fp-check (CC BY-SA 4.0 — ideas only, no wording) — catalogue of false-positive patterns and exploitability/PoC passes [port "False-positive patterns" "A guard earlier on the path" "No concurrency, no race"]
  - upstream/getsentry-skills/skills/security-review (Apache-2.0) — attacker-controlled vs server-controlled input [port "values set by operators"]
  - upstream/getsentry-skills/skills/security-review/references (Apache-2.0) — per-class references (injection, XSS, SSRF, deserialization, path traversal, session and JWT, crypto) and the full do-not-flag list [port "Path traversal" "JWT and bearer tokens" "Deserialisation" "Do-not-flag list" "Server-controlled sources"]
  - upstream/getsentry-skills/skills/security-model (Apache-2.0, commit d04211a) — optional persistent SECURITY_MODEL.md (boundaries, invariants with IDs, reportable classes, narrow exclusions) read from the base revision by later reviews; owner confirms anything that suppresses findings; suspected gaps stay out of it [port "SECURITY_MODEL.md" "read it from the base branch" "only the owner can confirm"]
  - upstream/trailofbits-skills/plugins/post-patch-validation (CC BY-SA 4.0 — ideas only, no wording) — fix validation against the vulnerable base and the patch, root-cause variants, preserved behaviour, stated evidence level [port "on the vulnerable base" "other routes to the same root cause" "the evidence level reached"]
  - upstream/stripe-ai/skills/stripe-best-practices (MIT) — verify settled payment status before fulfillment on async payment webhooks [port "settled payment status"]
---

# App Security

## Iron laws

1. **Map before you hunt.** List actors (anonymous, user, admin, other tenant, service, webhook
   sender), assets (data, money, permissions), entry points, **tenant boundaries**, sensitive
   operations, and the invariants that must hold ("a user only reads their own orders"). Check
   each claim in comments or docs against the actual callers and config.
2. **Authorisation is tested with a second identity.** For every object, function and property
   access that matters, construct the negative control: user B (or tenant B) tries user A's
   resource. An unguessable ID is not authorisation.
3. **One gap means look for its siblings:** search the same pattern at every other route,
   handler, job and command in scope; severity follows the worst sibling.
4. **A finding needs an attack path from attacker-controlled input.** Before verifying, write
   each suspected bug as four fields — claim, trigger, impact, and what the attacker can
   already do; most false alarms cannot be written that way. Then follow the input from entry
   to use through every check between. Values set by operators (settings, environment, config,
   constants) are not attacker-controlled; a pattern the framework already neutralises is not a
   finding; a missing header or rate limit needs a concrete scenario. Models over-report and
   over-rate severity, so a suspicious pattern alone proves nothing. Unknown reachability stays
   "unknown", never "unreachable".
5. **Severity, confidence and evidence are separate judgements.** A critical-impact issue with
   unconfirmed exploitability is still reported as critical, labelled unconfirmed; a confirmed
   trivial issue stays trivial.

## Coverage beyond authorisation

After the map, walk the OWASP Top 10 class table in `references/vuln-classes.md` and mark
every row assessed, not assessed (with the reason) or n/a in the report. Read its
false-positive patterns and do-not-flag list before any candidate goes in the findings.

## Where to look first

| area | check |
|---|---|
| object access | every read, update and delete scopes by owner or tenant in the query, not only the route guard |
| mass assignment | request bodies cannot set role, owner, tenant, price or status fields |
| tenant isolation | jobs, exports, search indexes, caches and admin tools respect it too |
| webhooks and integrations | trace the whole middleware and handler chain before calling a signature missing; signature over the **raw** body, constant-time compare, replay window, idempotent handling, event bound to the right tenant; verify **settled payment status** before fulfillment (checkout-completed is not cleared funds on async methods) |
| feature gates | a diff that makes a gated, internal or unreleased feature reachable without its gate (flipped default, guard dropped on one path, route registered outside the gated block) |

## Reviewing a change

Order the files by what they can break, not by how much changed (auth, tenant scoping,
payments, crypto, outbound calls first). For removed or loosened security code, read why it
existed (`git blame`). Count the callers of changed security-relevant functions instead of
guessing the blast radius.

## Confirm before reporting

Give a second reviewer the location, the invariant and the rubric — not your conclusion — and
have it re-derive the result; with none available, run a labelled challenge pass. After triage, ask whether two
or more of the findings you dropped would together give an attacker a path none gives alone.

## Reproduction contract

Only in a local or disposable environment you are allowed to use, never production. **Verified**
needs all three: the unmodified app passes the legitimate control (user A reads A's order); the
attack trips a specific security assertion (B received A's data), not just a non-zero exit;
nothing under the harness was changed to get there. Once a fix exists, **fix confirmed** means
the same request is refused and the legitimate control still passes, run on the vulnerable base
and on the patch, with the evidence level reached stated. Anything less is **traced** or
**plausible**. Steps and rules: `references/reproduction.md` — read before running one.

## Optional output — SECURITY_MODEL.md

When the user wants the map kept, or the repo has a `SECURITY_MODEL.md`, read
`references/security-model.md`: later reviews read it from the base branch, and anything in it
that suppresses findings is a decision only the owner can confirm.

## Confidence

| level | meaning | report? |
|---|---|---|
| verified | reproduced: steps 1, 2 and 4 of the reproduction contract hold (step 3, once a fix exists, adds **fix confirmed**) | yes |
| traced | the full attack path is traceable | yes |
| plausible | pattern present, exploitability unconfirmed | only if impact is critical — label it |
| speculative | — | no |

## Output

```
Status:                   complete / partial / not assessed — then scope and material gaps
Scope and boundary map:   actors · assets · entry points · tenant boundaries · invariants
Coverage:                 the class table, each row assessed / not assessed (why) / n/a
Findings:                 severity · confidence · evidence · attack path · siblings checked · fix
Unconfirmed (critical):   labelled hypotheses, with what would confirm them
Not reviewed:             areas out of scope or not reachable in this review
```

The report opens with complete, partial or not assessed; a run that hit its budget or missed
part of the code is partial even with zero findings. With no supported findings, write "No supported findings in the
assessed scope." — never "secure" or "no vulnerabilities". A failed tool or empty scanner output
is a coverage gap, not a clean result.

Output from the optional `claude-security` scanner plugin (`toolkit/external.yaml`) is candidates
for the gate above, not findings.
