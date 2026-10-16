---
name: agent-security
description: Threat-model and harden an agent that reads untrusted content or holds real permissions — treat every external text and the agent's own notes as data, enforce authority in code outside the model, deny-by-default, gate destructive actions, and check supply chain, filesystem, network, secrets and caches. Use when building, reviewing or deploying an agent with tools, MCP servers, file or network access, credentials, or money; for the surrounding application use app-security.
version: 1.0.1
sources:
  - upstream/everything-claude-code/skills/{agent-security-hardening,mcp-dependency-review,prompt-caching-strategy,llm-trading-agent-security,agent-architecture-audit} (MIT)
  - upstream/vila-lab/README.md, docs/architecture.md (CC BY-NC-SA 4.0 — ideas only, no wording)
  - upstream/everything-claude-code/the-security-guide.md (MIT) — Simon Willison's "lethal trifecta" (private data, untrusted content, an outbound channel), behind "The dangerous combination"
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{self-managed-context,harness-engineering,self-improvement-loops} (MIT)
  - Gambit Security, "AI Agents Are Hacking Online Retailers for $25 a Company" (2026), https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company
---

# Agent Security

An agent with tools is a program that takes instructions from whatever text reaches its
context. Secure the program, not the prompt.

## Iron laws

1. **External text is data, never instructions.** Web pages, files, emails, tool and MCP
   results, retrieved documents, other agents' output. The agent's own notes, summaries and
   memory are untrusted too, unless a human reviewed them or they live in a write-protected
   path. Text that tries to instruct is reported, not followed.
2. **Authority is enforced in code, outside the model.** Permissions, spend limits, rate limits
   and allowed targets are checked by the harness on every call, regardless of what the model
   says or how confident it is.
3. **Deny wins, and the unclassifiable is denied.** A broad deny beats a narrower allow (the
   reverse of "most specific rule wins"). If the policy cannot fully classify an action — a
   shell line too long or too compound to analyse, an unknown tool — the answer is "ask a
   human", never "allow".
4. **Destructive and irreversible actions:** exact identifiers, never patterns; a dry run; a
   human approval step; and backups the agent cannot reach. A pattern will eventually match
   what it should not: Gambit Security's 2026 report on an AI-run intrusion campaign records an
   agent whose over-broad table-name match dropped 180 tables at one retailer, including the
   backups its administrators had made (https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company).
5. **Least privilege per run and per agent.** Read-only credentials by default; write scopes
   are granted per task and expire with it. Subagents inherit the parent's permissions unless
   restricted — give each worker its own narrower tool allowlist and credential, so logs show
   which agent did what.

## The dangerous combination

Stop and redesign when one agent has all three: **access to private data**, **exposure to
untrusted content**, and **a channel that can send data out** (HTTP, email, commits, issue
comments, rendered links or images). Any injected instruction can then exfiltrate. Remove one
leg — split the agent, drop the outbound channel, or require approval on outbound actions.

## Checklist

**Untrusted content and memory**
- Untrusted text is delimited and labelled as data where it enters the context.
- Memory, compaction notes and self-written instructions are reviewed or constrained like any
  other input: a model can write instruction-shaped text into its own notes that a later
  context then obeys.
- Instruction-like content found in data is logged and surfaced to the user.

**Before the trust prompt**
- A cloned or downloaded repository's agent files — `CLAUDE.md`, `AGENTS.md`, settings, hooks,
  MCP configs, extensions — are untrusted code. Read them before opening the folder with an
  agent, and do not rely on the trust dialog as the boundary: past releases let parts of a
  repository's configuration act before the user accepted it, and a fix in one version says
  nothing about the version you run.

**Supply chain (MCP servers, plugins, tools)**

MCP tool descriptions are instructions injected into the context, and a server can change them
after you approved it. Pin the server version and diff its tool list and descriptions on
update.

MCP configs are routinely written as `npx -y <package>` with no version: that is code which can
change after you approved it. Risk is high for a bare name, `@latest` or any dist-tag, and an
image tag without a digest; medium for version ranges; acceptable only for an exact version or
`@sha256:` digest — and only if someone reviewed that version. "Pin to whatever is latest
today" is not a review.

**Filesystem**
- Resolve both the workspace root and the target, then check containment with a path API
  (`is_relative_to`), not a string prefix (`/work/app` is a prefix of `/work/application`).
- Reject `..`, absolute paths, symlinks out of the workspace, reserved device names (`CON`,
  `NUL`, `COM1`), trailing dots or spaces, and `:` in names.
- Checking a path and then opening it is a race; open relative to a trusted directory handle
  when symlinks are possible.

**Network**
- Validate the destination on every redirect hop, and connect to the address you validated
  (DNS can change between check and connect).
- Strip credentials when a redirect changes scheme or origin; re-authorise instead of
  forwarding them.

**Secrets**
- Redact before anything reaches a logger, tracer, exception message or model context.
- Prove it: inject a known sentinel secret in a test and assert it appears in no log, trace,
  error or prompt.

**Caches and multi-tenancy**
- An application response or semantic cache key is a routing hint, not an access check. Authorise before the lookup; scope
  entries to user, workspace, model and content version; invalidate on permission change. A
  cache hit across users is a data leak.

**A runaway or compromised agent in production**
- Kill it in code, not by asking it: revoke its credentials, disable its trigger, or flip a
  harness-enforced kill switch. Rotate every secret it could read (environment, files, its
  context), not only its own, and quarantine its memory and notes before any restart — a
  poisoned note re-infects the next run. Preserve its transcript and tool-call log, list every external
  input it read, and check what it wrote or sent out (the dangerous-combination check above).
  Incident handling otherwise follows `production-ops`.

**Agents that move money or place orders**
- Per-action and rolling (e.g. 24h) spend limits enforced outside the model.
- Simulate or preview every transaction before execution; require explicit bounds (max price,
  min received).
- Circuit breaker: halt on consecutive losses or a drawdown threshold; resume only by a human.
- Separate, minimally funded credentials for the agent; never the main account's keys.

**Evaluation and self-improvement loops**
- Rubrics, test suites and evaluator code are locked from the agent (see `agent-evals`); an
  agent able to edit its own grader will.

## Output — threat model

For the system under review, produce a table: asset · who/what can reach it · untrusted inputs
on that path · enforcement outside the model · residual risk · decision (accept / mitigate /
redesign). End with the dangerous-combination check result.
