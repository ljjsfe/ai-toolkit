---
paths:
  - "**/*.sql"
  - "**/migrations/**"
  - "**/Dockerfile*"
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/compose*.yml"
  - "**/compose*.yaml"
---
# SQL, migrations and containers

- Paginate with a cursor (`WHERE id > $last ORDER BY id LIMIT n`), not `OFFSET`, on anything
  that grows.
- Schema changes follow `production-ops` (expand → migrate → contract; `CONCURRENTLY` for
  indexes; batched backfills).
- Supabase / Postgres RLS: wrap auth calls in a subquery — `(SELECT auth.uid()) = user_id` — so
  they are evaluated once per query, not per row.
- Containers: pin image tags (never `:latest`), run as a non-root user, keep secrets out of
  layers, and publish database ports only on `127.0.0.1`.
