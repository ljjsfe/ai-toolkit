---
name: agent-instructions
description: Write or audit a repository's agent instruction files (CLAUDE.md, AGENTS.md, rules) so they stay short and earn their cost — put each rule in the cheapest place that enforces it, keep only what the agent cannot infer, verify every command and path, treat corrective lines as friction to fix, trim generated drafts, and harvest lessons after delivery through a user gate. Use when creating, reviewing or trimming CLAUDE.md, AGENTS.md or agent rules, or after a change where the user corrected the agent or a check failed before passing; for security vetting of a cloned repo's agent files use agent-security.
version: 1.4.0
sources:
  - upstream/villetakanen-asdlc-io/src/content/practices/agents-md-spec.md, src/content/recipes/write-agents-md.md (MIT) — enforcement ladder, corrective lines as friction, init output as candidates
  - upstream/claude-plugins-official/plugins/claude-md-management (Apache-2.0) — command and path currency check; generic and one-off cut tests
  - upstream/karanb192-claude-code-hooks/plugins/dead-rules-audit (MIT) — promote repeatedly violated rules to a hook
  - upstream/compound-engineering-plugin/docs/solutions/{developer-experience/always-on-agents-md.md, workflow/measuring-a-packs-effect-needs-non-inferable-rules.md, skill-design/authoring-auto-invoke-standing-instructions.md} (MIT) — load-when notes, sample output for helpers, standing-instruction phrasing
  - Claude Code memory docs, https://code.claude.com/docs/en/memory — AGENTS.md versus CLAUDE.md loading (checked 2026-10-15)
  - Codex AGENTS.md docs, https://learn.chatgpt.com/docs/agent-configuration/agents-md — discovery from project root to launch directory (checked 2026-10-15)
  - authored for this toolkit from a stated need (an internal spec-driven workflow reviewed 2026-10-30) — harvest after delivery, a human gate before any writeback, route each lesson to the place that owns it
  - 'Gloaguen et al., "Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?" (2026), https://arxiv.org/abs/2602.11988 — context files cost over 20% more without general gains; overviews unhelpful'
---

# Agent Instructions

Every line is paid for on every turn. Measured on real repositories, context files raised cost
by over a fifth without generally raising success, and overviews did not help (Gloaguen et al. 2026).

## 1. Place each rule before writing it

Walk down this ladder and stop at the first place that can carry the rule:

| the rule is… | it goes in |
|---|---|
| checkable by a formatter, linter or type checker | that tool's config |
| checkable on every change | CI |
| an action to block or require at a tool call | a hook |
| a procedure for one kind of task | a skill; at most its name and trigger in the file |
| needed only in one directory or file type | a path-scoped rule (Claude Code) or a skill; see layout for nested files |
| needed only for some tasks | a notes file, pointed to by a one-line "read X when Y" |
| one person's preference | the user-level file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`); `CLAUDE.local.md` only where a `CLAUDE.md` already exists |
| a project-wide invariant that needs judgement | the root instruction file |

Where a tool already enforces something, the file names the command and does not restate the rule.

## 2. Test each line that reaches the root file

Cut it if any answer is no:

- **Hidden?** Code, configs, directory names and existing docs do not already reveal it. A rule
  whose helper or pattern is already in the tree may be inferable, but not for every model:
  check whether a fresh agent finds and follows it before cutting.
- **Specific?** It is about this project, not advice any competent engineer would apply.
- **Recurring?** It applies to future tasks, not to one bug that is already fixed.
- **Stable?** It will still be true next month. Content that churns belongs in a spec, a task brief or a skill.
- **True now?** Every command in it runs, and every path in it exists. Check, do not assume.

What usually passes: non-default build, test and run commands; decisions that need a human first
(new dependency, schema change, public API change); domain constraints the code cannot express;
places that are not where the framework convention puts them; and, for a tool that does not
list skills itself, which skill to use when.

## 3. Phrase what survives

- Say what to do. A line that names the forbidden option keeps it in front of the agent.
- A rule that names a helper or format also gives one sample output (`u_1a1b2fjc3mq7`), so a
  recreated helper can be checked against it.
- A standing instruction to run a skill on its own names the skill, not a slash command another
  tool cannot call. If the skill's value lands when work is finished, it fires at a boundary the
  agent can see ("before commit or handoff", never "after each edit" or "at session end"); if
  some change kinds never yield anything for it, list them as exclusions, taken from that skill's
  scope (a docs reviewer must not skip docs). Cheap or always-relevant skills need neither.

## 4. Treat corrections as friction

- A line written to stop a repeated mistake ("import from X, not Y") shows the code makes the
  wrong path easy. Remove the cause — delete the old path, add a lint rule, rename — then the line.
- A rule the agent keeps breaking despite being loaded will not be fixed by bolder wording. Move
  it to a hook or CI check. If you can, count violations over a few sessions first, so the move
  is based on evidence rather than one memorable miss.

## 5. Harvest after delivery

Run this when a finished change surfaced something a future agent would trip on: the user
corrected the agent, verification failed before it passed, or the code behaved unexpectedly.
Not after every task.

1. Propose zero to three candidates. Each gives the claim in one sentence, its evidence (commit,
   diff, the correction in the conversation), the mistake it would prevent next time, and its
   home on the section 1 ladder: a linter, CI check (a test counts) or hook first, a line in
   the instruction file last.
2. Drop candidates that are task-local, already written somewhere, or owned by a spec or a
   decision record.
3. The user decides each one: apply now, reject or defer. Write nothing before that. "Nothing
   worth keeping" is a valid outcome and still needs the user's yes; in an unattended run,
   report the candidates and write nothing.
4. A candidate headed for an instruction file passes section 2 like any other line.

## Layout across tools

Under Claude Code's default Project instructions setting (it can be set to load both files):

- Default to a single `AGENTS.md`. Codex reads it, and Claude Code reads it natively
  (v2.1.277+) when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the
  directory or above it.
- **If a `CLAUDE.md` exists, Claude Code reads it instead of `AGENTS.md`.** Add one only for
  Claude-specific notes, and open it with `@AGENTS.md` so the shared content still loads. A
  `CLAUDE.md` without that import silently hides `AGENTS.md`; so does a personal
  `CLAUDE.local.md` unless Project instructions is set to load both. The import also covers
  sessions where native `AGENTS.md` loading is unavailable.
- A nested `AGENTS.md` is unreliable. Codex discovers files automatically only from the project
  root down to the directory it was launched in, not below it; Claude Code reads a subdirectory's `AGENTS.md` only
  when no `CLAUDE.md` exists, and `@AGENTS.md` imports just the root file. For per-path rules
  prefer a path-scoped rule (Claude Code only) or a skill.

## Procedures

**New file or generated draft** (init command, template, another agent's output): treat every
line as a candidate and run it through sections 1–2. Expect most to go.

**Audit an existing file:**
1. Resolve every path and validate every command: read-only ones may run; for anything that
   deploys, migrates or deletes, inspect it, use a dry run or an isolated environment, and keep
   to the session's approval rules. Record what fails.
2. Mark each line **keep**, **move** (where, per section 1), **fix** (friction to remove, then
   delete) or **cut** (fails section 2, with the reason).
3. Give a fresh agent that did not write the file a question only the file can answer; it should
   find the answer without reading through the repository.
4. Any claim that the new file improves results goes through `agent-evals`, with a no-file arm.

## Output

```
File:      the proposed file, as short as it can be (diff when auditing)
Moved:     each rule moved out, and to which linter, CI job, hook, skill or notes file
Fix list:  codebase friction behind each corrective line still kept
Cut:       each removed line and the failed test (hidden, specific, recurring, stable, true)
Broken:    commands that failed validation and paths that do not exist
Harvest:   (§5 only) each candidate · evidence · home · apply now | reject | defer
```
