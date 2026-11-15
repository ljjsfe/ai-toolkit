---
name: production-ops
description: >-
  Ship safe production changes (expand-migrate-contract schema/data migrations, idempotent retries,
  deploys, rollbacks, burn-rate alerts) and run live incidents (mitigate first, capture evidence,
  confirm signal recovery). For non-urgent bugs use debugging.
version: 1.2.2
sources:
  - upstream/everything-claude-code/skills/{database-migrations,docker-patterns} (MIT) — expand-migrate-contract, CONCURRENTLY, batched backfills [port "expand → migrate → contract" "create index concurrently" "backfills in keyset batches"]
  - upstream/everything-claude-code/skills/database-migrations (MIT) — forward-only migrations in production; no NOT NULL column without a default on a live table [port "migrations are forward-only in production" "never add a not null column without a default"]
  - upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/data-migration-reviewer.md (MIT) — broken dual-write transitions [port "during a dual-write transition"]
  - upstream/supabase-agent-skills/skills/supabase-postgres-best-practices (MIT) — SET lock_timeout before lock-taking ALTER TABLE on live tables [port "set a short lock_timeout"]
  - upstream/jeffallan-claude-skills/skills/microservices-architect (MIT) — idempotency keys, idempotent saga steps, explicit retry budgets [port "unique constraint plus an atomic insert" "every saga step is idempotent" "a retry budget"]
  - upstream/gstack/{land-and-deploy,canary} (MIT) — risk-scaled verification, baseline deviation, merge-shape-aware revert [port "scale verification to the change" "compare against baseline" "know the merge shape before reverting"]
  - upstream/gstack/{land-and-deploy,canary} (MIT) — baseline captured before the deploy, a fixed monitoring window with numeric thresholds, unknown scope is not docs-only, bounded deploy waits, a revert PR when branch protection blocks a push [port "capture the baseline before the deploy" "a fixed monitoring window" "unknown scope is not docs-only" "bound every deploy wait" "open a revert pr instead"]
  - upstream/jeffallan-claude-skills/skills/{sre-engineer,monitoring-expert} (MIT) — multi-window burn-rate alerts, trend-based capacity alerts [port "burn rate over multiple windows" "predict_linear"]
  - upstream/jeffallan-claude-skills/skills/sre-engineer/references/error-budget-policy.md (MIT) — what happens when the error budget runs out [port "when the error budget runs out" "only security patches and fixes that restore reliability"]
  - upstream/addyosmani-agent-skills/skills/observability-and-instrumentation (MIT) — entry-point log field [port "an entry-point field"]
  - upstream/everything-claude-code/skills/{latency-critical-systems,springboot-patterns} (MIT) — split latency signals; forwarded-header spoofing [port "data freshness" "trust x-forwarded-for only behind"]
  - upstream/jeffallan-claude-skills/skills/devops-engineer/references/incident-response.md (MIT) — evidence before state-destroying actions, routing by incident type and regulatory clock, re-check after remediation [port "capture evidence in parallel with mitigation" "route by incident type" "resolved means the original signal recovered"]
  - upstream/axiomhq-skills/skills/axiom-sre (MIT; renamed from skills/sre on 2026-11-09) — discover the data's real fields before querying [port "look at the data's real shape"]
---

# Production Ops

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

- **Migrations are forward-only in production.** Once a migration has run there, undo it with a
  new forward migration, never by editing the applied file or running its down script against
  live data; down scripts are for local and test databases.
- **Never add a NOT NULL column without a default to a live table.** Add it with a default, or
  nullable → backfill in batches → `CHECK … NOT VALID`, validated separately, then `SET NOT NULL`.
- **Set a short `lock_timeout` (e.g. `SET lock_timeout = '2s'`) before any lock-taking `ALTER
  TABLE` on a live table;** a queued `ACCESS EXCLUSIVE` lock blocks every later read and write.
- **During a dual-write transition both the old and new columns must be populated.** If a
  release stops writing the old one early, a rollback to the previous code reads NULLs.
- Indexes on live tables: `CREATE INDEX CONCURRENTLY`, outside a transaction (use the runner's
  opt-out); drop an `INVALID` index from a failed build before retrying.
- Backfills in keyset batches (`WHERE id > $last ORDER BY id LIMIT n`), committing per batch;
  never one `UPDATE` over the whole table, and not `SKIP LOCKED`, which skips live rows.

### Retries and workflows

- **Every external call has an explicit timeout, a retry budget and a degradation path** —
  never an unbounded retry loop. Every saga step is idempotent and has a compensation.

### Deploys and rollbacks

Read `references/deploys-and-alerting.md` before a deploy or a revert. The gates:

- **Scale verification to the change:** docs only → smoke check; config → health and status
  codes; backend → error rate, latency and logs; frontend or mixed → also console errors and a
  visual check. Unknown scope is not docs-only: verify as for backend.
- **Capture the baseline before the deploy** and compare against baseline, not absolute
  numbers; watch a fixed monitoring window with numeric thresholds (default every 60 s for 10
  minutes, latency above 2× baseline); two consecutive bad checks raise the alarm.
- **Bound every deploy wait** (about 20 minutes), then ask; a failed status query is unknown,
  never success.
- **Know the merge shape before reverting.** If branch protection blocks the push, open a revert
  PR instead and report the rollback as pending. Rolling back is an incident mitigation:
  propose it and wait for the go-ahead unless an automated rollback was agreed beforehand.

### Observability and alerting

Alert on error-budget burn rate over multiple windows, not a raw error-rate threshold; agree in
writing what happens when the error budget runs out (exhausted: only security patches and fixes
that restore reliability ship); capacity alerts on projected exhaustion (`predict_linear`);
track data freshness apart from latency; logs carry a correlation ID and an entry-point field;
trust `X-Forwarded-For` only behind a configured trusted proxy chain. Before setting alerts
or budgets, read `references/deploys-and-alerting.md` (windows, budget table, proxy arithmetic).

## When something breaks — iron laws

1. **Stop the harm first, find the cause second.** Prefer the fastest reversible mitigation:
   roll back (merge shape above), turn off a feature flag, shed load, fail over, or disable
   the integration. Propose the mitigation and wait for the operator's go-ahead before running
   it, unless the user has pre-authorised that action. Root cause comes after users are safe
   (then `debugging`).
2. **Capture evidence in parallel with mitigation; never delay mitigation for it.** Save
   timestamped logs, process state, database sessions and locks, and recent deploys and config
   changes into one incident folder with a timeline before restarts erase them.
3. **Look at the data's real shape before querying it.** List the actual fields, labels and
   services first. Then try to disprove the leading theory.
4. **Resolved means the original signal recovered.** Wait a fixed interval and re-check the same
   metric or reproduction. Issuing a rollback is not recovery; if it has not recovered,
   escalate rather than repeating the action.
5. **One person decides, one log records** every action and observation.

### Route by incident type

| type | who | clock and first moves |
|---|---|---|
| outage or degradation | engineering on call | status updates at a fixed cadence |
| data loss or corruption | database owner + engineering lead | stop writes that spread the damage before repairing |
| security breach | security + engineering + legal | revoke or rotate exposed credentials; isolate rather than wipe; start the legal clocks (GDPR 72 h for a controller — read `references/incident-clocks.md` first) |
| compliance | compliance + legal + leadership | per the regulation or contract |
| third-party failure | engineering + product + vendor | vendor status and contractual SLA |
| runaway or compromised AI agent | engineering + owner of spend and data | kill it in code — see `agent-security` |

### After

Review from the action log, blameless: timeline, how it was detected and how late, what
mitigated it, root cause, and one or two changes that prevent the class of incident — each with
an owner and a date.
