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
- Schema changes follow `production-ops` (expand → migrate → contract; `SET lock_timeout` before
  lock-taking `ALTER TABLE`; `CONCURRENTLY` for indexes; batched backfills).
- Supabase / Postgres RLS: wrap auth calls in a subquery — `(SELECT auth.uid()) = user_id` — so
  they are evaluated once per query, not per row; index every column referenced in RLS predicates;
  avoid mutual cross-table RLS policies (`A → B → A`) that recurse.
- Postgres `SECURITY DEFINER` functions must pin `SET search_path = ''`, schema-qualify all
  referenced objects, and live outside API-exposed schemas (`public` in PostgREST).
- Connection poolers in transaction mode (e.g. PgBouncer port 6543): never rely on session-level
  `SET` variables or persistent prepared statements, and run DDL migrations over a direct
  connection instead.
- Containers: pin image tags (never `:latest`), run as a non-root user, keep secrets out of
  layers, and publish database ports only on `127.0.0.1`.
