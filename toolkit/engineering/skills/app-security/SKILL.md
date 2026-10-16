---
name: app-security
description: Security-review a web, mobile or backend application the way attackers find real bugs — map actors, assets, trust and tenant boundaries and invariants before hunting, test authorisation with a second user or tenant, sweep every sibling route once a gap is found, trace webhooks end to end, and gate findings on a concrete attack path with severity, confidence and evidence kept separate. Use for security reviews, audits, or before shipping auth, payments, multi-tenant or integration code; for agents and LLM tools use agent-security.
version: 1.0.2
sources:
  - upstream/gstack/cso (MIT) — boundary and invariant census first, sibling propagation, exploitability gating, three separate judgements, independent re-derivation, webhook review order, two-user and two-tenant negative controls
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/security-reviewer.md (MIT) — confidence tied to attack-path traceability with a critical-impact override; feature-gate leaks
  - upstream/trailofbits-skills/plugins/{fp-check,differential-review} (CC BY-SA 4.0 — ideas only, no wording) — restate the claim before verifying, trace the validation chain, risk not size, git blame on removed security code, counted blast radius, exploit chains across rejected findings
  - upstream/getsentry-skills/skills/security-review (Apache-2.0) — attacker-controlled vs server-controlled input; do-not-flag list
---

# App Security

Most serious application bugs are authorisation and boundary bugs that match no textbook
pattern. Find the boundaries first, then attack them.

## Iron laws

1. **Map before you hunt.** List actors (anonymous, user, admin, other tenant, service, webhook
   sender), assets (data, money, permissions), entry points, **tenant boundaries**, sensitive
   operations, and the invariants that must hold ("a user only reads their own orders"). Check
   each claim in comments or docs against the actual callers and config.
2. **Authorisation is tested with a second identity.** For every object, function and property
   access that matters, construct the negative control: user B (or tenant B) tries user A's
   resource. An unguessable ID is not authorisation.
3. **One gap means look for its siblings** (as in `code-review`): search the same pattern at
   every other route, handler, job and command in scope; severity follows the worst sibling.
4. **A finding needs an attack path from attacker-controlled input.** Before verifying, write
   each suspected bug as four fields — claim, trigger, impact, and what the attacker can
   already do; a large share of false alarms cannot be written that way and end there. Then
   follow the input from where it enters to where it is used, through every check between. Values set by
   operators (settings, environment, config, constants) are not attacker-controlled; a pattern
   the framework already neutralises is not a finding; a missing header or rate limit needs a
   concrete scenario. A suspicious-looking pattern proves nothing by itself — models
   over-report and over-rate severity. Unknown reachability stays "unknown", never "unreachable".
5. **Severity, confidence and evidence are separate judgements.** A critical-impact issue with
   unconfirmed exploitability is still reported as critical, labelled unconfirmed; a confirmed
   trivial issue stays trivial.

## Where to look first

| area | check |
|---|---|
| object access | every read, update and delete scopes by owner or tenant in the query itself, not only in the UI or route guard |
| mass assignment | request bodies bound to models cannot set role, owner, tenant, price or status fields |
| tenant isolation | background jobs, exports, search indexes, caches and admin tools respect the tenant boundary too |
| webhooks and integrations | trace the whole middleware and handler chain before calling a signature missing; verify the signature over the **raw** body with a constant-time comparison, enforce a timestamp or replay window, make handling idempotent, bind the event to the right tenant, and ask what a forged event could change (money, ownership, access) |
| feature gates | a diff that makes a gated, internal or unreleased feature reachable without its gate (flipped default, guard dropped on one path, route registered outside the gated block) |

## Reviewing a change

Order the files by what they can break, not by how much changed: authentication, tenant
scoping, payments, cryptography and calls to other systems come first — a two-line change can
be the critical one. For removed or loosened security code, read the
history (`git blame`, the commit that added it) to learn why it existed. Count the callers of
changed security-relevant functions instead of guessing the blast radius, and treat untested
changes to them as higher risk.

## Confirm before reporting

Give a second reviewer the location, the invariant and the rubric — not your conclusion — and
have it re-derive the result from the callers, middleware and config. If no second reviewer is
available, do a labelled challenge pass against your own finding. After triage, ask whether two
or more of the findings you dropped would together give an attacker a path none gives alone.

## Confidence

| level | meaning | report? |
|---|---|---|
| verified | literally visible in code or reproduced | yes |
| traced | the full attack path is traceable | yes |
| plausible | pattern present, exploitability unconfirmed | only if impact is critical — label it |
| speculative | — | no |

## Output

```
Scope and boundary map:   actors · assets · entry points · tenant boundaries · invariants
Findings:                 severity · confidence · evidence · attack path · siblings checked · fix
Unconfirmed (critical):   labelled hypotheses, with what would confirm them
Not reviewed:             areas out of scope or not reachable in this review
```

For an automated scan alongside this review in Claude Code, the optional `claude-security`
plugin (see `toolkit/external.yaml`) runs one; treat its output as candidates for the gate
above, not as findings.
