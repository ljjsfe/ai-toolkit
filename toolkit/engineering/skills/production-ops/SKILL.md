---
name: production-ops
description: "Make production changes that pass review and also survive live (schema and data migrations, retries, deploys, rollbacks, alerting), and run incidents in the right order: stop the harm first, capture evidence, call it resolved only when the original signal recovers. Use for changes to schema, data, retries, deploys, rollbacks or alerting, and for live incidents or outages (users affected now); for non-urgent bugs use debugging."
version: 1.0.1
sources:
  - upstream/everything-claude-code/skills/{database-migrations,docker-patterns} (MIT) — expand-migrate-contract, CONCURRENTLY, batched backfills
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/data-migration-reviewer.md (MIT) — broken dual-write transitions
  - upstream/jeffallan-claude-skills/skills/microservices-architect (MIT) — idempotency keys, idempotent saga steps, explicit retry budgets
  - upstream/gstack/{land-and-deploy,canary} (MIT) — risk-scaled verification, baseline deviation, merge-shape-aware revert
  - upstream/jeffallan-claude-skills/skills/{sre-engineer,monitoring-expert} (MIT) — multi-window burn-rate alerts, trend-based capacity alerts
  - upstream/addyosmani-agent-skills/skills/observability-and-instrumentation (MIT) — entry-point log field
  - upstream/everything-claude-code/skills/{latency-critical-systems,springboot-patterns} (MIT) — split latency signals; forwarded-header spoofing
  - upstream/jeffallan-claude-skills/skills/devops-engineer/references/incident-response.md (MIT) — evidence before state-destroying actions, routing by incident type and regulatory clock, re-check after remediation
  - upstream/axiomhq-skills/skills/sre (MIT) — discover the data's real fields before querying
---

# Production Ops

Two parts: changing production safely, and handling it when something breaks. Each item is a
mistake that looks reasonable at the time.

## Changing production — iron laws

1. **Any schema change that renames, retypes or removes something in use is expand → migrate →
   contract,** with old and new code able to run against the schema at every point. Purely
   additive changes (a new table, a nullable column) need no phases. The contract step (dropping)
   is the irreversible one.
2. **Every write that can be retried or redelivered is idempotent,** enforced by a unique
   constraint plus an atomic insert or upsert — not by checking first and then acting, which
   races under concurrent redelivery.
3. **Every deploy has a verification sized to the change,** decided before it ships.

### Schema and data

- **During a dual-write transition both the old and new columns must be populated.** If a
  release stops writing the old one early, a rollback to the previous code reads NULLs.
- Indexes on live tables: `CREATE INDEX CONCURRENTLY`, which cannot run inside a transaction
  block — and most migration runners wrap each migration in one, so use the tool's opt-out. A
  failed concurrent build leaves an `INVALID` index; drop it before retrying.
- Backfills in keyset batches — select the next ids with `WHERE id > $last ORDER BY id LIMIT n`
  and update those (Postgres `UPDATE` has no `LIMIT`), committing per batch;
  never one `UPDATE` over the whole table. `SKIP LOCKED` would silently skip rows that live
  traffic holds.

### Retries and workflows

- **Every external call has an explicit timeout, a retry budget and a degradation path** —
  never an unbounded retry loop. Every saga step is idempotent and has a compensation.

### Deploys and rollbacks

- **Scale verification to the change:** docs only → smoke check; config → health and status
  codes; backend → error rate, latency and logs against the pre-deploy baseline; frontend or
  mixed → also console errors and a visual check. Compare against baseline, not absolute
  numbers, and require two consecutive bad checks before rolling back automatically.
- **Know the merge shape before reverting.** A true merge commit reverts with `git revert -m 1`;
  a squash is one commit; a rebase-merge is a range — reverting only its last commit leaves the
  rest deployed. If the shape is unclear, stop and identify the full range.

### Observability and alerting

- **Alert on error-budget burn rate over multiple windows** (for example fast: 1h at ~14× burn;
  slow: 6h at ~6×; ticket: 3 days at ~1×), each paired with a short window (about 5 min, 30 min,
  6 h) so the alert clears once the burn stops — not on a single raw error-rate threshold.
- **Capacity alerts on projected exhaustion** (e.g. Prometheus `predict_linear` over a week),
  not a static "80% full".
- Track p50/p95/p99, queue depth, cache-hit rate and **data freshness** separately; a fast
  cache must not hide stale data.
- Logs carry a correlation ID **and an entry-point field** (scheduler, API route, replay, CLI)
  set at the start of the run and propagated across boundaries.
- Rate limiting or auditing by client IP: trust `X-Forwarded-For` only behind a configured,
  trusted proxy chain, and take the right-most address that is not one of your trusted proxies (with N trusted
  proxies, skip N−1 entries from the right); otherwise use
  the socket address.

## When something breaks — iron laws

1. **Stop the harm first, find the cause second.** Prefer the fastest reversible mitigation:
   roll back (merge shape above), turn off a feature flag, shed load, fail over, or disable
   the integration. Propose the mitigation and wait for the operator's go-ahead before running
   it, unless the user has pre-authorised that action. Root cause comes after users are safe
   (then `debugging`).
2. **Capture evidence in parallel with mitigation; never delay mitigation for it.** Restarts,
   rollbacks and redeploys erase evidence, so alongside the action save timestamped logs,
   process and container state, current database sessions and locks, and recent deploys and
   config changes into one incident folder with a timeline.
3. **Look at the data's real shape before querying it.** List the actual fields, labels and
   services in the logs or metrics first; a query built from remembered field names returns
   nothing and wastes the first minutes. Then try to disprove the leading theory.
4. **Resolved means the original signal recovered.** Wait a fixed interval and re-check the same
   metric or reproduction. Issuing a rollback is not recovery; if it has not recovered,
   escalate rather than repeating the action.
5. **One person decides, one log records** every action and observation.

### Route by incident type

| type | who | clock and first moves |
|---|---|---|
| outage or degradation | engineering on call | status updates at a fixed cadence |
| data loss or corruption | database owner + engineering lead | stop writes that spread the damage before repairing |
| security breach | security + engineering + legal | revoke or rotate exposed credentials; isolate rather than wipe. GDPR: a controller notifies the supervisory authority without undue delay and where feasible within 72 hours of becoming aware (unless unlikely to risk people's rights), and tells affected people when the risk is high; a processor — typical for B2B SaaS — notifies its controller (the customer) without undue delay. Add sector, securities and contract clocks that apply (e.g. US public companies: SEC 8-K within 4 business days of determining materiality; US state breach laws) |
| compliance | compliance + legal + leadership | per the regulation or contract |
| third-party failure | engineering + product + vendor | vendor status and contractual SLA |
| runaway or compromised AI agent | engineering + owner of spend and data | kill it in code — see `agent-security` |

### After

Review from the action log, blameless: timeline, how it was detected and how late, what
mitigated it, root cause, and one or two changes that prevent the class of incident — each with
an owner and a date.
