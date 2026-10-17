#!/usr/bin/env python3
"""Stop hook: block a completion claim made after editing files without running anything.

Fires when, in the current turn, the assistant edited or wrote files, ran no command after
the last edit, and its final message claims success. Blocks once per stop (respects
stop_hook_active) and tells the agent to verify. Fails open on any error.

A tripwire, not proof: any Bash call after the last edit satisfies it, whatever it ran.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EDIT_TOOLS = frozenset({"Edit", "MultiEdit", "Write", "NotebookEdit"})
RUN_TOOLS = frozenset({"Bash"})
CLAIM = re.compile(
    r"\b(fixed|works now|is working|all (tests )?pass(ing|es)?|tests (now )?pass(ing)?|"
    r"(successfully )?deployed (to|successfully)|verified|ready to (merge|ship)|"
    r"all done|it'?s done|is done)\b|\bdone[.!]"
    r"|(完成了|已完成|修好了|已修复|搞定|测试通过|都通过|部署好了|已部署)",
    re.IGNORECASE,
)
# A claim preceded closely by a negation ("not verified", "haven't fixed", "还没完成") is a
# report of what is unfinished, not a success claim.
NEGATION_EN = re.compile(r"\b(not|never|no|yet|cannot)\b|n't\b", re.IGNORECASE)
NEGATION_ZH = re.compile(r"[没未不尚]")
INJECTED_PREFIXES = ("<", "Caveat:", "[Request interrupted")
REASON = (
    "You edited files this turn and ran no command after the last edit, but your message "
    "claims success. Run the command that proves the claim (tests, build, a reproduction, "
    "a live check), then report what ran, where, and the result. If it cannot be run, say "
    "explicitly that it is unverified."
)


def _negated(text: str, start: int) -> bool:
    """True when one of the three words (or three CJK characters) before start negates it."""
    before = re.split(r"[.!?;:\n。！？；：]", text[:start])[-1]
    return bool(NEGATION_EN.search(" ".join(before.split()[-3:])) or NEGATION_ZH.search(before[-3:]))


def claims_success(text: str) -> bool:
    return any(not _negated(text, m.start()) for m in CLAIM.finditer(text))


def _entries(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _is_user_prompt(entry: dict) -> bool:
    """A prompt typed by the user, not a tool result or a harness-injected message."""
    if entry.get("type") != "user" or entry.get("isMeta") or entry.get("isCompactSummary"):
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
        if e.get("type") != "assistant":
            continue
        for c in e.get("message", {}).get("content", []) or []:
            if not isinstance(c, dict):
                continue
            step += 1
            if c.get("type") == "tool_use":
                name = c.get("name", "")
                if name in EDIT_TOOLS:
                    last_edit = step
                elif name in RUN_TOOLS:
                    last_run = step
            elif c.get("type") == "text":
                transcript_text = c.get("text", "")
    text = final_text if final_text is not None else transcript_text
    return last_edit >= 0 and last_run < last_edit and claims_success(text)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("stop_hook_active"):
            return 0
        path = Path(payload.get("transcript_path", ""))
        if not path.is_file():
            return 0
        if should_block(_entries(path), payload.get("last_assistant_message")):
            print(json.dumps({"decision": "block", "reason": REASON}))
    except (OSError, ValueError, TypeError):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
