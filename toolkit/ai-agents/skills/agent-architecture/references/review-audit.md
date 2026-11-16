# Agent review audit — full procedure

Read this when an existing agent misbehaves and the failing layer is not obvious, or before an
agent system ships. `SKILL.md` has the layer table; this file has the procedure, the search
queries, the finding format, the severity model and the report schema.

## 1. Scope (write it down before searching)

- target system and its entrypoints (UI, API, CLI, scheduler)
- model stack: every model and provider, including ones used by helper passes
- the reported symptom, in the user's words, and when it started (a date or a deploy)
- which of the twelve layers apply — a system without long-term memory skips layers 3–5

## 2. Collect evidence

Read, in this order: the agent loop, the tool router, prompt assembly, memory admission and
retrieval, every post-processing step between generation and delivery, the persistence layer.
Then pull a few real session traces — both a failing one and a passing one for the same input
shape if you can find them.

Ready anti-pattern queries (run from the repo root; adjust `--type` to the codebase):

```bash
# 1. tool requirements stated only in prose, never checked in code
rg -i "must (call|use).*tool|always call|required to call|you must use" -g '*.md' -g '*.txt' -g '*prompt*'

# 2. tool calls consumed without validating that they ran or what they returned
rg -n "tool_calls?|toolCall|tool_use|function_call" --type py --type ts

# 3. LLM calls outside the main loop (hidden passes)
rg -n "messages\.create|chat\.completions\.create|\.invoke\(|generate_content|completion\(" --type py --type ts

# 4. memory written without a correction-wins rule
rg -n -i "memory.*(add|admit|save|upsert)|persist.*memory|long.?term" --type py --type ts

# 5. fallback / retry / repair loops that call a model again
rg -n -i "fallback|retry.*(llm|model)|repair|re-?prompt|self.?correct|fix_output" --type py --type ts

# 6. output rewritten between generation and delivery
rg -n -i "rewrite|sanitize|post.?process|transform.*(output|response)|shape_answer|format_answer" --type py --type ts

# 7–8 are toolkit additions, not among the upstream audit's six queries
# 7. summaries / distilled notes fed back into prompts
rg -n -i "summar(y|ise|ize)|distill|compress|digest" --type py --type ts

# 8. caches or stored artifacts read back as current evidence
rg -n -i "cache\.(get|load)|load_state|from_cache|last_result|ttl" --type py --type ts
```

A hit is a lead, not a finding. Open the file and confirm the mechanism before writing it up.

## 3. Walk the twelve layers

| # | layer | what goes wrong | how to confirm |
|---|---|---|---|
| 1 | system prompt | contradictions, bloat, rules that conflict with tool descriptions | read the assembled prompt as sent, not the template |
| 2 | session history | earlier turns injected after they stopped being relevant | diff the context of turn N against what turn N needs |
| 3 | long-term memory | cross-session pollution; old topics in new conversations; corrections lost | trace one correction: is it stored, and does it outrank the old fact? |
| 4 | distillation | a compressed summary re-enters as if it were a source fact | find where summaries are written and where they are read back |
| 5 | active recall | the same material re-summarised by several layers, eating context | count how many times one fact appears in one assembled context |
| 6 | tool selection | a required tool can be skipped; two tools own the same job | run the case with the tool unavailable — does it still answer? |
| 7 | tool execution | the model claims a call that never ran | match every claimed call to a harness log row with arguments |
| 8 | tool interpretation | output truncated, misparsed or ignored | compare the raw tool output with what the model said it showed |
| 9 | answer shaping | format corrupted on the way to the final answer | compare raw model output with the shaped answer |
| 10 | platform rendering | UI, API or CLI mutates a correct answer (markdown, JSON, streaming chunks) | compare the logged answer with what the user received |
| 11 | hidden repair loops | a fallback or "auto-fix" agent runs a second model pass nobody budgeted or logged | query 3 and 5 above; check each hit for a model call |
| 12 | stale persistence | expired state or a cached artifact served as live evidence | check timestamps and invalidation on every read of stored results |

Do not blame the model until each wrapper layer that applies has been falsified. A clean
current state does not erase a dirty incident: the finding stands if the trace shows it.

## 4. Write each finding

Every finding has all of these fields; a finding missing evidence is a lead, not a finding.

- **symptom** — what the user sees
- **mechanism** — how the layer produces the symptom, step by step
- **source layer** — one of the twelve
- **root cause** — the deepest cause you can show, not the first one you found
- **evidence** — `file:line` or `trace-id:turn` references you opened
- **confidence** — 0.0–1.0; below 0.5 say what would confirm it
- **recommended fix** — in code where possible

## 5. Severity model

| severity | meaning | when to fix |
|---|---|---|
| critical | the agent can confidently take wrong operational action (wrong tool effect, wrong data written, wrong answer delivered as certain) | before the next release |
| high | correctness or stability degrades often | this sprint |
| medium | correctness usually survives, but the path is fragile or wastes tokens | next cycle |
| low | cosmetic or maintainability only | backlog |

## 6. Fix order — code first, prompt last

1. Gate required tools in code (refuse an answer that lacks the required call).
2. Remove hidden repair agents, or make each one explicit: a contract, a budget, a log row.
3. Cut context duplication (the same fact via prompt, history, memory and summary).
4. Tighten memory admission: user corrections outrank agent assertions; the agent's own
   monologue never becomes memory without review.
5. Tighten distillation triggers; mark summaries as derived so they are never cited as sources.
6. Make rendering pass-through; any transform is tested against the raw answer.
7. Move internal hand-offs to typed JSON envelopes instead of free prose.

Only after these, edit prompt wording.

## 7. Report schema

Lead with the findings, most severe first. No preamble. The schema name `agent-review.report.v1` is
this toolkit's: the layout is adapted from the upstream audit skill's report
(`ecc.agent-architecture-audit.report.v1`) — renamed fields, plus scope, entrypoints and
skipped layers — so do not label these reports with the upstream name.

```json
{
  "schema": "agent-review.report.v1",
  "verdict": {
    "health": "ok | at_risk | high_risk | broken",
    "primary_failure_mode": "string",
    "most_urgent_fix": "string"
  },
  "scope": {
    "target": "string",
    "entrypoints": ["string"],
    "model_stack": ["string"],
    "layers_audited": [1, 2, 6, 7, 11],
    "layers_skipped": [{"layer": 3, "reason": "no long-term memory"}]
  },
  "findings": [
    {
      "id": "F1",
      "severity": "critical | high | medium | low",
      "title": "string",
      "symptom": "string",
      "mechanism": "string",
      "source_layer": 11,
      "root_cause": "string",
      "evidence": ["src/agent/repair.py:42", "trace 8f3a turn 4"],
      "confidence": 0.8,
      "recommended_fix": "string"
    }
  ],
  "fix_plan": [
    {"order": 1, "finding_ids": ["F1"], "change": "string", "expected_effect": "string", "check": "string"}
  ]
}
```
