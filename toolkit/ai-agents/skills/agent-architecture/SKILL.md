---
name: agent-architecture
description: Design or review an LLM agent system that will run unattended or in production — decide whether it needs an agent at all, pick the topology, state model, tool surface, context pipeline and cost budget, and write stop conditions and human gates before the loop. Use when designing, building or debugging an agent product, multi-agent system or LLM pipeline (not for running subagents in this session — that is agent-orchestration); pair with agent-security once tools or credentials are involved.
version: 1.0.0
sources:
  - upstream/humanlayer-12-factor-agents/content/factor-02, factor-05, factor-07, factor-09 (prose CC BY-SA 4.0 — ideas only, no wording)
  - upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{multi-agent-patterns,tool-design,context-optimization,context-compression,self-managed-context,filesystem-context,long-horizon-prompting,harness-engineering,evaluation} (MIT)
  - upstream/everything-claude-code/skills/{agent-architecture-audit,prompt-caching-strategy,regex-vs-llm-structured-text,cost-aware-llm-pipeline} (MIT)
  - upstream/vila-lab/docs/architecture.md (CC BY-NC-SA 4.0 — ideas only, no wording)
---

# Agent Architecture

Design the system on paper before writing the loop. Most agent failures are architecture
failures that look like model failures.

## Iron laws

1. **Write the stop conditions before the loop.** Every loop has a turn cap, a spend cap, a
   consecutive-error ceiling for runtime tool errors (the same failure three times in a row → stop and escalate to a human), and a success check that is not the agent's own claim of success.
2. **A requirement that lives only in the prompt is a wish.** If the agent *must* call a tool
   or validate an output, enforce it in code and confirm from the trace that it happened.
   Models can report tool calls they never made. (Permissions and limits: `agent-security`.)
3. **One append-only event log is the state.** Derive the current step, retry count and
   "waiting for human" from that log instead of keeping a parallel state machine. Logging an
   intent before a side effect does not make a crash safe — afterwards you cannot tell whether
   the action happened. Pass an idempotency key derived from the event ID to every
   side-effecting call, so a resumed run can repeat it harmlessly (see `production-ops`).
4. **Pair persistence with verification.** Never add "keep going / don't give up" pressure
   without an equally strong check on the result, and list the near-misses that do not count
   (narrowed scope, a survey instead of the artifact, "reduced to" an unproven step). Pressure
   without a gate produces confident fake completion.
5. **Irreversible actions pass a human gate that is a tool call** (`request_approval(action,
   diff)`), not a sentence in the prompt asking the model to be careful. The rest of the rules
   for destructive actions are in `agent-security`.

## Step 1 — One agent or several?

Valid reasons for more than one agent: **context isolation** (a subtask would flood the main
context with material the main task does not need), **parallelism** over independent inputs,
or a **separate evaluator** that must not share the generator's context. "It mirrors a team"
is not a reason: a planner persona and a coder persona can share one context.

For large volumes of templated text, parse with code first, score each parse's confidence,
and send only the low-confidence items to the cheapest model that handles them.

## Step 2 — Topology and handoffs

- **Subagents isolate context; they do not reproduce an org chart.**
- **Cap fan-out at about 3–5 workers per supervisor that reads their output into its own
  context.** Past that its context fills with worker output; add a tier, or have workers write
  results to files and pass back only paths and summaries.
- **Do not let the supervisor paraphrase the answer.** When a worker's output *is* the result,
  pass it through verbatim; every restatement loses detail.
- **Handoffs are typed contracts, not personas.** Write the return schema before the worker
  prompt: named fields and named checks (`sources: list[url]`, `tests_passed: bool`,
  `open_questions: list[str]`). Downstream steps wait on fields, not on prose.

## Step 3 — Tool surface

- With a strong model, a few general primitives (shell, SQL, HTTP) often beat many narrow
  tools. Use narrow tools where you need a safety boundary, not for convenience.
- Repeated identical tool errors count toward the error ceiling.
- **Mark every destructive tool** and design it to `agent-security`'s rules (exact
  identifiers, dry run, human gate).

## Step 4 — Context pipeline

- **Order the prompt from stable to volatile.** Nothing that changes per request (timestamps,
  request IDs, user names) goes into the system prompt or early in the prefix: one changed byte
  invalidates the cache for everything after it. Tool definitions sit before the system prompt
  in the cached prefix on some providers (Anthropic: tools → system → messages), so adding,
  removing or reordering tools mid-session — dynamic tool loading, MCP reconnects — invalidates
  the whole cache.
- **An edit is priced by its tail.** Changing early context re-bills every token after it.
  Batch edits; do not compact a small early region that sits under a long, still-useful tail.
- **Reduce in stages, each with its own trigger:** cap tool outputs → drop stale tool results →
  summarise old turns → full compaction. One blunt summarise-at-the-limit step loses the wrong
  things.
- **Large outputs go to files;** the context gets a path and a short summary.
- **Model-written notes are untrusted input** to the next context — see `agent-security`.
- **Measure tokens per completed task,** including re-fetches. Frequent re-fetching of
  compressed material means compression is too aggressive.

## Step 5 — Cost and model choice

- **Pin the model per role in the system's code or config,** so a default never decides cost.
  (For dispatching subagents yourself, see `agent-orchestration`.)
- **Caching:** on providers that charge for cache writes, a prefix used once costs more cached
  than uncached. Claim savings only
  from the provider's usage counters (cache-read / cache-write tokens), never from arithmetic.

## Step 6 — Harness surfaces (autonomous or long-running agents)

Before granting autonomy, assign every file and resource to one of four surfaces:

| surface | examples | agent may |
|---|---|---|
| locked | eval suite, rubric (see `agent-evals`), secrets, CI config | read only, or not at all |
| editable | the code or document being worked on | read and write |
| append-only | run logs, results — failed attempts included | add, never edit or delete |
| human-controlled | budget, deploys, merges, credentials | request via the human gate |

## Output — the design note

Produce a design note before code, with one line or a short table for each:
goal and success check · one agent or several, and why · topology and fan-out · handoff schemas ·
tool list with destructive tools marked · state/event log shape · context budget and reduction
stages · model per role and the expected cost per task · stop conditions · human gates ·
harness surfaces · how it will be evaluated (see `agent-evals`).

## Review mode — an existing agent misbehaves

Do not blame the model first. Walk the layers in order and ask the question for each:

| layer | question |
|---|---|
| system prompt | does it contradict itself or the tool descriptions? |
| history / memory | is stale or contaminated memory being injected? |
| retrieval | did the right material reach the context at all? |
| tool selection | can the model skip a required tool and still answer? |
| tool execution | did the call actually run, with the arguments in the log? |
| result interpretation | is the tool output truncated or misparsed? |
| answer shaping | is a second LLM pass or "repair" step rewriting the answer? |
| rendering / persistence | does the UI or storage layer alter what was produced? |

Fix the first layer that fails, then re-check from that layer down.
