# Deploys, rollbacks and alerting

Read before verifying or rolling back a deploy, or when setting alerts, error-budget policy or
observability fields. Thresholds here are the defaults the `SKILL.md` laws refer to.

## Deploys and rollbacks

- **Scale verification to the change:** docs only → smoke check; config → health and status
  codes; backend → error rate, latency and logs against the pre-deploy baseline; frontend or
  mixed → also console errors and a visual check. Compare against baseline, not absolute
  numbers, and require two consecutive bad checks before raising the alarm. Rolling back is then
  an incident mitigation: propose it and wait for the go-ahead (see "When something breaks") unless an
  automated rollback was agreed before the deploy.
- **Capture the baseline before the deploy,** not after: error rate, p95 latency, the key pages
  or endpoints with their status codes, load time and console errors. A snapshot taken after the
  deploy is a starting point, not proof the old version was healthy; say which one you have.
- **Watch a fixed monitoring window with numeric thresholds** set before shipping — for example
  check every 60 s for 10 minutes; alert on a page or endpoint that fails to load, on a backend
  error rate above the baseline rate, on page console errors whose message was not in the
  baseline (for console errors compare by message, not count), on latency or load time above 2×
  the baseline, and on new 404s. The two-consecutive-checks rule above applies to each.
- **Unknown scope is not docs-only.** Skip deploy verification only when every changed file is
  documentation; if the diff could not be read or classified, verify as for backend.
- **Bound every deploy wait.** Poll the pipeline with progress updates and stop at a fixed
  deadline (about 20 minutes), then ask: wait one more bounded period, or report the deploy as
  unverified. A failed status query is unknown, never success; a later green health check does
  not erase a failed deploy run.
- **Know the merge shape before reverting.** A true merge commit reverts with `git revert -m 1`;
  a squash is one commit; a rebase-merge is a range — reverting only its last commit leaves the
  rest deployed. If the shape is unclear, stop and identify the full range. If branch protection
  rejects pushing the revert, do not bypass it: push the revert to a new branch, open a revert PR
  instead, report the rollback as pending, and merge only on separate approval. The rollback is
  done only when the revert is deployed and the monitoring window above passes.

## Observability and alerting

- **Alert on error-budget burn rate over multiple windows** (for example fast: 1h at ~14× burn;
  slow: 6h at ~6×; ticket: 3 days at ~1×), each paired with a short window (about 5 min, 30 min,
  6 h) so the alert clears once the burn stops — not on a single raw error-rate threshold.
- **Agree what happens when the error budget runs out,** in writing, before it does
  (budget = 1 − SLO over the window; 99.9% over 30 days is about 43 minutes):

  | budget left | policy |
  |---|---|
  | above ~50% | normal releases |
  | 25–50% | extra review and a named approver for risky deploys; watch every deploy |
  | under 25% | pause non-critical feature work; ship reliability fixes and critical bug fixes only |
  | exhausted | feature freeze: only security patches and fixes that restore reliability ship, every incident gets a review, until the budget recovers over the window |

  Exceptions (a security patch, a contractual deadline) need a named approver and are recorded.
  A budget nobody acts on is only a dashboard.
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
