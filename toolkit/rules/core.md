# Core working rules

Always loaded. Keep this file short; detail lives in skills.

- **Evidence before claims.** Never say done, fixed, passing or deployed without running the
  command that shows it in this session, and say where it ran. (Detail: `verification` skill.)
- **Ask before irreversible or outward-facing actions:** force-push, history rewrite, deleting
  data or branches, `docker compose down -v`, dropping tables, publishing, sending messages.
- **Commit only the files you changed for this task,** listed explicitly. Never `git add -A` or
  a bare `git commit -a` in a tree that may hold the user's unrelated work.
- **Commit messages:** `<type>: <description>` with type one of feat, fix, refactor, docs, test,
  chore, perf, ci.
- **Check the installed version before using a library API** you have not used in this session
  (lockfile, `npm view`, `pip show`, docs). Training data lags releases.
- **No secrets in code, logs, commits or prompts.** Read them from the environment.
- **Never describe code you have not opened.** A call site does not tell you what the callee
  does; read it or say it is unknown.
- **Validate at system boundaries** (HTTP bodies, files, queue messages, env vars, external
  APIs); trust internal calls.
- **Scale process to the change.** A one-line fix does not need a plan, a subagent or a new
  test suite; a change to data, auth, money or a public API does.
- **Prefer immutable updates** (return new objects rather than mutating inputs) unless the
  surrounding code clearly does otherwise.
