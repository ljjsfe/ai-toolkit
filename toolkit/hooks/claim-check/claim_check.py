#!/usr/bin/env python3
"""Stop hook: block a completion claim made after editing files without running anything.

Fires when, in the current turn, the assistant edited or wrote workspace files, ran no
command (or browser verification tool) after the last edit, and its final message claims
success. Blocks once per stop and tells the agent to verify. Fails open on any error.

Supports Claude Code, Antigravity (agy), and Codex Stop hook payloads and transcripts.
A tripwire, not proof: any command call after the last edit satisfies it, whatever it ran.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EDIT_TOOLS = frozenset({
    "Edit", "MultiEdit", "Write", "NotebookEdit",
    "edit_file", "write_file",
    "apply_patch",
})
RUN_TOOLS = frozenset({
    "Bash",
    "run_command",
    "exec_command", "shell", "shell_command", "unified_exec",
})
RUN_TOOL_PREFIXES = ("mcp__playwright__", "mcp__chrome", "browser_")

FIXED_ADJECTIVE_NOUNS = (
    r"width|height|size|header|footer|nav|navbar|sidebar|position|positioning|"
    r"layout|point|rate|income|interval|length|offset|buffer|seed|cost|price|"
    r"window|column|row|top|bottom|left|right"
)
CLAIM = re.compile(
    rf"\bfixed\b(?!-[a-z]|\s+({FIXED_ADJECTIVE_NOUNS})\b)"
    r"|\b(works now|is working|all (tests )?pass(ed|ing|es)?|tests (now )?pass(ed|ing|es)?|"
    r"(successfully )?deployed (to|successfully)|verified|ready to (merge|ship)|"
    r"all done|it'?s done|is done)\b"
    r"|\b(done|deployed)\s*([.!]|$)"
    r"|(完成了|已完成|全部完成|修好了|已修复|修复完成|改好了|写好了|搞定|测试通过|测试已通过|都通过|部署好了|已部署)",
    re.IGNORECASE,
)
# A claim preceded closely in the same clause by a negation or conditional ("not verified",
# "haven't fixed", "if tests pass", "还没完成") is not an unverified completion claim.
NEGATION_EN = re.compile(
    r"\b(not|never|no|cannot|without|if|once|when|until|whether)\b|n't\b",
    re.IGNORECASE,
)
NEGATION_ZH = re.compile(r"[没未不尚若如]")
CLAUSE_SPLIT = re.compile(r"[.!?;:,\n—–。！？；：，、]")
INJECTED_PREFIXES = (
    "<task-notification",
    "<system-reminder",
    "<local-command",
    "<command-",
    "<SYSTEM_MESSAGE>",
    "<environment_context",
    "<permissions",
    "<collaboration_mode",
    "Caveat:",
    "[Request interrupted",
)
REASON = (
    "You edited files this turn and ran no command after the last edit, but your message "
    "claims success. Run the command that proves the claim (tests, build, a reproduction, "
    "a live check), then report what ran, where, and the result. If it cannot be run, say "
    "explicitly that it is unverified."
)


def _negated(text: str, start: int) -> bool:
    """True when one of the three words (or three CJK characters) in the same clause negates it."""
    before = CLAUSE_SPLIT.split(text[:start])[-1]
    return bool(
        NEGATION_EN.search(" ".join(before.split()[-3:]))
        or NEGATION_ZH.search(before[-3:])
    )


def claims_success(text: str) -> bool:
    return bool(text) and any(not _negated(text, m.start()) for m in CLAIM.finditer(text))


def _is_edit_tool(name: str, args: dict | None = None) -> bool:
    if name not in EDIT_TOOLS:
        return False
    # Antigravity writes conversation artifacts (plans/walkthroughs) via write_file/edit_file
    # with ArtifactMetadata set; those are UI artifacts, not workspace code edits.
    if isinstance(args, dict) and args.get("ArtifactMetadata"):
        return False
    return True


def _is_run_tool(name: str) -> bool:
    return name in RUN_TOOLS or name.startswith(RUN_TOOL_PREFIXES)


def _entries(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except json.JSONDecodeError:
                continue
    return rows


def _is_user_prompt(entry: dict) -> bool:
    """A prompt typed by the user across Claude Code, Antigravity, or Codex transcripts."""
    etype = entry.get("type")

    # Antigravity transcript.jsonl
    if etype == "USER_INPUT":
        if entry.get("source") != "USER_EXPLICIT":
            return False
        content = entry.get("content", "")
        return isinstance(content, str) and not content.lstrip().startswith(INJECTED_PREFIXES)

    # Codex rollout JSONL
    if etype == "event_msg":
        payload = entry.get("payload", {})
        if isinstance(payload, dict) and payload.get("type") == "user_message":
            msg = payload.get("message", "")
            return isinstance(msg, str) and not msg.lstrip().startswith(INJECTED_PREFIXES)
        return False
    if etype == "response_item":
        payload = entry.get("payload", {})
        if not isinstance(payload, dict) or payload.get("type") != "message" or payload.get("role") != "user":
            return False
        parts = payload.get("content", [])
        text = "".join(
            c.get("text", "") for c in parts
            if isinstance(c, dict) and c.get("type") in ("input_text", "text")
        ) if isinstance(parts, list) else ""
        return bool(text) and not text.lstrip().startswith(INJECTED_PREFIXES)

    # Claude Code transcript JSONL
    if etype != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
        return False
    content = entry.get("message", {}).get("content")
    if isinstance(content, list):
        if any(isinstance(c, dict) and c.get("type") == "tool_result" for c in content):
            return False
        texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
        content = "".join(texts)
    return isinstance(content, str) and not content.lstrip().startswith(INJECTED_PREFIXES)


def should_block(entries: list[dict], final_text: str | None = None) -> bool:
    """final_text: the last assistant message as given to the hook; falls back to the transcript."""
    start = max((i for i, e in enumerate(entries) if _is_user_prompt(e)), default=-1)
    turn = entries[start + 1 :]
    step, last_edit, last_run, transcript_text = 0, -1, -1, ""

    for e in turn:
        etype = e.get("type")

        # Claude Code assistant entry
        if etype == "assistant":
            for c in e.get("message", {}).get("content", []) or []:
                if not isinstance(c, dict):
                    continue
                step += 1
                if c.get("type") == "tool_use":
                    name = c.get("name", "")
                    args = c.get("input") if isinstance(c.get("input"), dict) else None
                    if _is_edit_tool(name, args):
                        last_edit = step
                    elif _is_run_tool(name):
                        last_run = step
                elif c.get("type") == "text":
                    transcript_text = c.get("text", "")

        # Antigravity PLANNER_RESPONSE entry
        elif etype == "PLANNER_RESPONSE":
            content = e.get("content")
            if isinstance(content, str) and content:
                transcript_text = content
            for tc in e.get("tool_calls") or []:
                if not isinstance(tc, dict):
                    continue
                step += 1
                name = tc.get("name", "")
                args = tc.get("args") if isinstance(tc.get("args"), dict) else None
                if _is_edit_tool(name, args):
                    last_edit = step
                elif _is_run_tool(name):
                    last_run = step

        # Codex rollout response_item entry
        elif etype == "response_item":
            p = e.get("payload", {})
            if not isinstance(p, dict):
                continue
            ptype = p.get("type")
            if ptype in ("function_call", "custom_tool_call"):
                step += 1
                name = p.get("name", "")
                if _is_edit_tool(name):
                    last_edit = step
                elif _is_run_tool(name):
                    last_run = step
            elif ptype == "message" and p.get("role") == "assistant":
                parts = p.get("content", [])
                if isinstance(parts, list):
                    texts = [
                        c.get("text", "") for c in parts
                        if isinstance(c, dict) and c.get("type") in ("output_text", "text")
                    ]
                    if texts:
                        transcript_text = "".join(texts)

    text = final_text if final_text is not None else transcript_text
    return last_edit >= 0 and last_run < last_edit and claims_success(text)


def _is_antigravity(payload: dict) -> bool:
    return any(k in payload for k in ("hookEventName", "transcriptPath", "terminationReason", "executionNum"))


def main() -> int:
    is_agy = False
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        is_agy = _is_antigravity(payload)

        if is_agy:
            reason = payload.get("terminationReason")
            exec_num = payload.get("executionNum", 1)
            if (reason and reason != "NO_TOOL_CALL") or (isinstance(exec_num, int) and exec_num > 1):
                print(json.dumps({"decision": "allow"}))
                return 0
            path = Path(payload.get("transcriptPath", ""))
            if path.is_file() and should_block(_entries(path)):
                print(json.dumps({"decision": "continue", "reason": REASON}))
            else:
                print(json.dumps({"decision": "allow"}))
            return 0

        if payload.get("stop_hook_active"):
            return 0
        path = Path(payload.get("transcript_path", ""))
        if not path.is_file():
            return 0
        if should_block(_entries(path), payload.get("last_assistant_message")):
            print(json.dumps({"decision": "block", "reason": REASON}))
    except (OSError, ValueError, TypeError):
        if is_agy:
            print(json.dumps({"decision": "allow"}))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
