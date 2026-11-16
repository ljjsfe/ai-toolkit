# Scope creep and history

Procedures behind Pass 2 (scope creep) and Pass 3 (history) in `SKILL.md`.

## Scope creep

**Scope creep is the other half of the spec axis.** Map each hunk to the requirement it serves;
list hunks that serve none. Also list every behaviour the diff changes — a default, an exit
code, a stored value, a route, a side effect — that the PR description or commit messages do
not mention. Report these as `UNASKED: <change> — <file:line>`; each is a question for the
author (split it out, or add it to the spec), not automatically a defect. Two kinds count even
when small: public surface the stated intent rules out or plainly narrows away (an export,
endpoint, flag, config key or parameter) — a terse description that just does not mention it is
not evidence — and a new dependency doing what the standard library, the platform or an existing
repo helper already does (name the replacement). Acceptance text edited in the same diff is a
weakened gate: see "Spec edited to match" in `references/gate-patterns.md`.

## History of the changed lines

Toolkit policy (no current upstream runs this as a separate sweep); keep it to the changed lines.

- **Blame and log of the changed lines:** was this code written this way to fix something? A
  change that undoes an earlier fix, or reintroduces a reverted pattern, is a finding.
- **Earlier pull requests touching these files** — find them with
  `git log --format='%h %s' -- <path>`; when hosted on GitHub and `gh` is authenticated, also
  read `gh pr view <n> --comments` and the inline review comments
  (`gh api repos/<owner>/<repo>/pulls/<n>/comments`, else rely on local `git log`): objections
  raised there often apply again.
- **Comments in the modified files** that state an invariant ("must be called before…", "not
  thread-safe"): check the change still honours them.
