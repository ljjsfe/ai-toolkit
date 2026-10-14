---
name: agent-instructions
description: Write or audit a repository's agent instruction files (CLAUDE.md, AGENTS.md, rules) so they stay short and earn their cost — put anything a linter, CI, hook or skill can enforce there instead, keep only what the agent cannot infer, treat every corrective line as a sign of codebase friction to fix, and trim generated drafts (such as init-command output) before keeping them. Use when creating, generating, reviewing or trimming CLAUDE.md, AGENTS.md or agent rules for a project; for security vetting of a cloned repo's agent files use agent-security.
version: 1.0.0
sources:
  - upstream/villetakanen-asdlc-io (MIT) — toolchain-first decision rule, instruction files as a friction diagnostic, generated files as a list of what to leave out, map only hidden knowledge, skills listed by name
  - Gloaguen et al., "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" (2026), https://arxiv.org/abs/2602.11988 — context files did not generally improve task success and raised inference cost by over 20%; agents follow the instructions; repository overviews were not helpful
---

# Agent Instructions

An instruction file is loaded into every session and its instructions are followed. Each line
therefore costs tokens and steers behaviour on every task — which is only worth it when the line
carries something the agent could not work out itself.

## Iron laws

1. **Only what the agent cannot infer.** If it is visible from the code, the configs, the directory layout or existing docs, leave it
   out. Repository overviews, though widely recommended, did not help in the study above.
2. **Toolchain first.** Before adding a rule, ask in order, and put it in the first place that
   can enforce it:

   | can it be enforced by… | put it in |
   |---|---|
   | a formatter, linter or type checker | that tool's config |
   | CI | the pipeline |
   | a hook | the hook |
   | a task-specific procedure | a skill, named in the file |
   | none of these — it needs judgement | the instruction file |

   Never restate what a tool already enforces; point to the command instead.
3. **A corrective line is a symptom.** A line added to stop a specific repeated mistake —
   "always import from X, not Y" — means the codebase makes the
   wrong choice easy. Fix the cause — delete the legacy path, add a lint rule, rename — then
   delete the line. Prefer stating what to use over naming what to avoid; a named alternative
   stays salient.
4. **Generated files are drafts to cut.** Output from an init command is a list of candidates,
   most of which fail law 1. Keep only the lines that pass.
5. **Stable content only.** If the file changes often, its content belongs in a spec, a task
   brief or a skill.

## What belongs

| section | content |
|---|---|
| purpose | 2–4 sentences: what the project is for and the domain constraints the code does not show |
| commands | how to build, test, run and lint — one line each, especially anything non-standard |
| judgement rules | what to ask before doing (new dependencies, schema changes, public API changes), architectural preferences a tool cannot check |
| skills | only for tools that do not discover skills themselves: names and when to use them, never their procedures (Claude Code and Codex already list installed skills) |
| hidden map | only locations that would surprise someone who knows the framework: where business rules live, which doc answers which question |

## Layout across tools

- Write the shared content once in `AGENTS.md`; make `CLAUDE.md` a one-line `@AGENTS.md`
  import, adding Claude-only notes below it if needed.
- Put a short file in a subdirectory only when that directory has its own conventions.
- Language-specific rules go in path-scoped rule files that load only for matching files
  (Claude Code); in Codex use a nested `AGENTS.md` in that directory or a skill.

## Audit an existing file

For each line, mark: **keep** (judgement, not inferable) · **move** (to which tool or skill) ·
**fix** (friction to remove in the code, then delete) · **cut** (inferable or stale). Then test with a fresh-context agent that did not write the
file: ask a question only the file can answer, and check it finds the answer without reading
the whole repository. A claim that the new file improves results needs `agent-evals`.

## Output

```
File:         the proposed AGENTS.md / CLAUDE.md, as short as it can be
Moved:        each rule moved to a linter, CI, hook or skill, and where
Fix list:     codebase friction behind any corrective line kept for now
Cut:          what was removed and why
```
