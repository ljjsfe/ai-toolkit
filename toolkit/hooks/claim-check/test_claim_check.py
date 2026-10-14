import json
import subprocess
import sys
from pathlib import Path

from claim_check import should_block

HOOK = Path(__file__).with_name("claim_check.py")


def user(text):
    return {"type": "user", "message": {"content": text}}


def tool_result():
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def asst(*parts):
    return {"type": "assistant", "message": {"content": list(parts)}}


def tool(name):
    return {"type": "tool_use", "name": name, "input": {}}


def text(t):
    return {"type": "text", "text": t}


def test_blocks_claim_after_edit_without_run():
    t = [user("fix it"), asst(tool("Edit")), tool_result(), asst(text("Fixed, all tests pass."))]
    assert should_block(t)


def test_allows_claim_when_command_ran_after_edit():
    t = [user("fix it"), asst(tool("Edit")), tool_result(), asst(tool("Bash")), tool_result(),
         asst(text("Fixed: pytest shows 12 passed."))]
    assert not should_block(t)


def test_blocks_when_command_ran_only_before_edit():
    t = [user("fix it"), asst(tool("Bash")), tool_result(), asst(tool("Edit")), tool_result(),
         asst(text("Done."))]
    assert should_block(t)


def test_allows_when_no_edit_this_turn():
    t = [user("status?"), asst(text("Done reading; here is the summary."))]
    assert not should_block(t)


def test_allows_unverified_wording_without_claim():
    t = [user("fix it"), asst(tool("Edit")), tool_result(),
         asst(text("I changed the handler; I have not run the tests yet."))]
    assert not should_block(t)


def test_chinese_claim_is_detected():
    t = [user("修一下"), asst(tool("Write")), tool_result(), asst(text("已修复，测试通过。"))]
    assert should_block(t)


def test_previous_turn_edits_do_not_count():
    t = [user("a"), asst(tool("Edit")), tool_result(), asst(text("ok")),
         user("b"), asst(text("Done, see above."))]
    assert not should_block(t)


def test_injected_messages_do_not_reset_the_turn():
    t = [user("fix it"), asst(tool("Edit")), tool_result(),
         user("<task-notification>agent finished</task-notification>"),
         {"type": "user", "isMeta": True, "message": {"content": "skill body"}},
         asst(text("Fixed."))]
    assert should_block(t)


def test_last_assistant_message_overrides_transcript_text():
    t = [user("fix it"), asst(tool("Edit")), tool_result(), asst(text("Editing more files now"))]
    assert should_block(t, final_text="All done.")
    assert not should_block(t, final_text="I have not run anything yet.")


def test_done_inside_a_sentence_is_not_a_claim():
    t = [user("fix it"), asst(tool("Edit")), tool_result(),
         asst(text("Here is what I've done so far; tests not run."))]
    assert not should_block(t)


def test_edit_and_run_in_same_message_are_ordered():
    t = [user("fix it"), asst(tool("Bash"), tool("Edit")), tool_result(), asst(text("Fixed."))]
    assert should_block(t)


def _run(tmp_path, entries, active=False):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in entries))
    payload = json.dumps({"transcript_path": str(p), "stop_hook_active": active})
    return subprocess.run([sys.executable, str(HOOK)], input=payload, capture_output=True,
                          text=True, check=True).stdout


def test_cli_emits_block_json(tmp_path):
    out = _run(tmp_path, [user("x"), asst(tool("Edit")), tool_result(), asst(text("Fixed."))])
    assert json.loads(out)["decision"] == "block"


def test_cli_respects_stop_hook_active(tmp_path):
    out = _run(tmp_path, [user("x"), asst(tool("Edit")), tool_result(), asst(text("Fixed."))],
               active=True)
    assert out == ""


def test_cli_fails_open_on_bad_input():
    r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True,
                       text=True)
    assert r.returncode == 0 and r.stdout == ""
