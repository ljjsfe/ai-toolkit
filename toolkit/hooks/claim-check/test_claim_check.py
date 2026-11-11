#!/usr/bin/env python3
"""Tests for claim_check.py (runnable with stdlib unittest or pytest)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from claim_check import claims_success, should_block  # noqa: E402

HOOK = Path(__file__).with_name("claim_check.py")


# ---- Claude Code helpers ----------------------------------------------------------------
def user(text: str) -> dict:
    return {"type": "user", "message": {"content": text}}


def tool_result() -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def asst(*parts: dict) -> dict:
    return {"type": "assistant", "message": {"content": list(parts)}}


def tool(name: str, inp: dict | None = None) -> dict:
    return {"type": "tool_use", "name": name, "input": inp or {}}


def text(t: str) -> dict:
    return {"type": "text", "text": t}


# ---- Antigravity helpers ----------------------------------------------------------------
def agy_user(content: str, source: str = "USER_EXPLICIT") -> dict:
    return {"type": "USER_INPUT", "source": source, "content": content}


def agy_model(content: str = "", tool_calls: list[dict] | None = None) -> dict:
    return {
        "type": "PLANNER_RESPONSE",
        "source": "MODEL",
        "content": content,
        "tool_calls": tool_calls or [],
    }


def agy_tc(name: str, args: dict | None = None) -> dict:
    return {"name": name, "args": args or {}}


# ---- Codex rollout helpers --------------------------------------------------------------
def codex_user(msg: str) -> dict:
    return {"type": "event_msg", "payload": {"type": "user_message", "message": msg}}


def codex_call(name: str, call_type: str = "function_call") -> dict:
    return {"type": "response_item", "payload": {"type": call_type, "name": name}}


def codex_asst(msg: str) -> dict:
    return {
        "type": "response_item",
        "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": msg}]},
    }


class ClaimCheckTests(unittest.TestCase):
    def test_blocks_claim_after_edit_without_run(self):
        t = [user("fix it"), asst(tool("Edit")), tool_result(), asst(text("Fixed, all tests pass."))]
        self.assertTrue(should_block(t))

    def test_allows_claim_when_command_ran_after_edit(self):
        t = [
            user("fix it"), asst(tool("Edit")), tool_result(),
            asst(tool("Bash")), tool_result(),
            asst(text("Fixed: pytest shows 12 passed.")),
        ]
        self.assertFalse(should_block(t))

    def test_allows_claim_when_playwright_or_browser_ran_after_edit(self):
        t = [
            user("fix UI"), asst(tool("Edit")), tool_result(),
            asst(tool("mcp__playwright__browser_snapshot")), tool_result(),
            asst(text("Fixed and verified in browser.")),
        ]
        self.assertFalse(should_block(t))

    def test_blocks_when_command_ran_only_before_edit(self):
        t = [
            user("fix it"), asst(tool("Bash")), tool_result(),
            asst(tool("Edit")), tool_result(),
            asst(text("Done.")),
        ]
        self.assertTrue(should_block(t))

    def test_allows_when_no_edit_this_turn(self):
        t = [user("status?"), asst(text("Done reading; here is the summary."))]
        self.assertFalse(should_block(t))

    def test_allows_unverified_wording_without_claim(self):
        t = [
            user("fix it"), asst(tool("Edit")), tool_result(),
            asst(text("I changed the handler; I have not run the tests yet.")),
        ]
        self.assertFalse(should_block(t))

    def test_chinese_claim_is_detected(self):
        for claim in ("已修复，测试通过。", "改好了。", "代码写好了，全部完成。"):
            with self.subTest(claim=claim):
                t = [user("修一下"), asst(tool("Write")), tool_result(), asst(text(claim))]
                self.assertTrue(should_block(t))

    def test_previous_turn_edits_do_not_count(self):
        t = [
            user("a"), asst(tool("Edit")), tool_result(), asst(text("ok")),
            user("b"), asst(text("Done, see above.")),
        ]
        self.assertFalse(should_block(t))

    def test_injected_messages_do_not_reset_the_turn_but_ide_user_prompts_do(self):
        t_injected = [
            user("fix it"), asst(tool("Edit")), tool_result(),
            user("<task-notification>agent finished</task-notification>"),
            {"type": "user", "isMeta": True, "message": {"content": "skill body"}},
            asst(text("Fixed.")),
        ]
        self.assertTrue(should_block(t_injected))

        t_ide_prompt = [
            user("fix it"), asst(tool("Edit")), tool_result(), asst(text("edited")),
            user("<ide_opened_file>foo.ts</ide_opened_file>\nIs this done?"),
            asst(text("Done.")),
        ]
        self.assertFalse(should_block(t_ide_prompt))

    def test_last_assistant_message_overrides_transcript_text(self):
        t = [user("fix it"), asst(tool("Edit")), tool_result(), asst(text("Editing more files now"))]
        self.assertTrue(should_block(t, final_text="All done."))
        self.assertFalse(should_block(t, final_text="I have not run anything yet."))

    def test_done_inside_a_sentence_is_not_a_claim(self):
        t = [
            user("fix it"), asst(tool("Edit")), tool_result(),
            asst(text("Here is what I've done so far; tests not run.")),
        ]
        self.assertFalse(should_block(t))

    def test_adjectival_fixed_is_not_a_claim(self):
        for msg in (
            "I updated the fixed header and fixed-width sidebar; tests not run.",
            "Adjusted the fixed position offset in CSS; please run the app.",
        ):
            with self.subTest(msg=msg):
                self.assertFalse(claims_success(msg))

    def test_edit_and_run_in_same_message_are_ordered(self):
        t = [user("fix it"), asst(tool("Bash"), tool("Edit")), tool_result(), asst(text("Fixed."))]
        self.assertTrue(should_block(t))

    def test_negated_or_conditional_claims_are_not_claims(self):
        for msg in (
            "I have not verified this yet.",
            "Not fixed — the test still fails.",
            "I haven't fixed the flaky test.",
            "The migration is not done.",
            "Let me know if tests pass on your machine.",
            "Once fixed, re-run the suite.",
            "还没完成了一半。",
            "这个 bug 还未修复，测试没有都通过。",
        ):
            with self.subTest(msg=msg):
                self.assertFalse(claims_success(msg))

    def test_unnegated_claims_still_count(self):
        for msg in (
            "The refactor is done.",
            "Done",
            "Deployed.",
            "All tests passed.",
            "Tests now passed.",
            "No regressions, tests pass.",
            "Not the prettiest code, but it's fixed.",
            "I couldn't reproduce it at first; it's fixed now.",
            "问题不大，已修复。",
            "已修复，测试通过。",
        ):
            with self.subTest(msg=msg):
                self.assertTrue(claims_success(msg))

    # ---- Antigravity transcript & CLI tests ---------------------------------------------
    def test_antigravity_transcript_blocks_and_allows(self):
        blocked = [
            agy_user("fix bug"),
            agy_model("Editing file", [agy_tc("edit_file")]),
            agy_user("<SYSTEM_MESSAGE>subagent done</SYSTEM_MESSAGE>", source="SYSTEM"),
            agy_model("All tests passed."),
        ]
        self.assertTrue(should_block(blocked))

        allowed = [
            agy_user("fix bug"),
            agy_model("Editing file", [agy_tc("edit_file")]),
            agy_model("Running tests", [agy_tc("run_command")]),
            agy_model("All tests passed."),
        ]
        self.assertFalse(should_block(allowed))

        artifact_only = [
            agy_user("write plan"),
            agy_model("Writing artifact", [agy_tc("write_file", {"ArtifactMetadata": {"UserFacing": True}})]),
            agy_model("Done."),
        ]
        self.assertFalse(should_block(artifact_only))

    def test_codex_rollout_transcript_blocks_and_allows(self):
        blocked = [
            codex_user("patch it"),
            codex_call("apply_patch", "custom_tool_call"),
            codex_asst("Fixed, ready to merge."),
        ]
        self.assertTrue(should_block(blocked))

        allowed = [
            codex_user("patch it"),
            codex_call("apply_patch", "custom_tool_call"),
            codex_call("exec_command", "function_call"),
            codex_asst("Fixed, ready to merge."),
        ]
        self.assertFalse(should_block(allowed))

    def _run_cli(self, entries: list[dict], payload: dict) -> str:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.jsonl"
            p.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")
            body = dict(payload)
            if "hookEventName" in body or "terminationReason" in body or "executionNum" in body:
                body["transcriptPath"] = str(p)
            else:
                body["transcript_path"] = str(p)
            return subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(body),
                capture_output=True,
                text=True,
                check=True,
            ).stdout

    def test_cli_claude_emits_block_and_respects_stop_hook_active(self):
        entries = [user("x"), asst(tool("Edit")), tool_result(), asst(text("Fixed."))]
        out = self._run_cli(entries, {"stop_hook_active": False})
        self.assertEqual(json.loads(out)["decision"], "block")
        out_active = self._run_cli(entries, {"stop_hook_active": True})
        self.assertEqual(out_active, "")

    def test_cli_antigravity_emits_continue_or_allow_and_respects_execution_num(self):
        entries = [agy_user("x"), agy_model("", [agy_tc("edit_file")]), agy_model("Fixed.")]
        out_block = self._run_cli(entries, {"hookEventName": "Stop", "terminationReason": "NO_TOOL_CALL", "executionNum": 1})
        self.assertEqual(json.loads(out_block)["decision"], "continue")

        out_second = self._run_cli(entries, {"hookEventName": "Stop", "terminationReason": "NO_TOOL_CALL", "executionNum": 2})
        self.assertEqual(json.loads(out_second)["decision"], "allow")

        out_canceled = self._run_cli(entries, {"hookEventName": "Stop", "terminationReason": "USER_CANCELED", "executionNum": 1})
        self.assertEqual(json.loads(out_canceled)["decision"], "allow")

    def test_cli_fails_open_on_bad_input(self):
        r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
