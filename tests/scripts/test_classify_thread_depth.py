import json

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-handle-pr-comments/scripts/classify_thread_depth.py"
mod = load(SCRIPT_UNDER_TEST)

BOT = "app-bot"


def _c(login):
    return {"user": {"login": login}}


def test_comment_author_shapes():
    assert mod.comment_author({"user": {"login": "a"}}) == "a"
    assert mod.comment_author({"author": {"login": "b"}}) == "b"
    assert mod.comment_author({"author": "c"}) == "c"
    assert mod.comment_author({"login": "d"}) == "d"
    assert mod.comment_author({}) == ""
    assert mod.comment_author({"user": {}}) == ""


def test_only_original_comment_not_back_and_forth():
    result = mod.classify_thread_depth([_c("reviewer")], BOT)
    assert result["has_agent_reply"] is False
    assert result["next_reply_is_back_and_forth"] is False


def test_first_agent_reply_not_back_and_forth():
    # original -> agent reply (agent's next would be a *first* reply, no counter yet)
    result = mod.classify_thread_depth([_c("reviewer"), _c(BOT)], BOT)
    assert result["has_agent_reply"] is True
    assert result["has_reviewer_counter_reply"] is False
    assert result["next_reply_is_back_and_forth"] is False


def test_reviewer_counter_reply_is_back_and_forth():
    # original -> agent reply -> reviewer counter-reply; next agent reply = back-and-forth
    thread = [_c("reviewer"), _c(BOT), _c("reviewer")]
    result = mod.classify_thread_depth(thread, BOT)
    assert result["has_reviewer_counter_reply"] is True
    assert result["next_reply_is_back_and_forth"] is True
    assert result["agent_reply_count"] == 1


def test_case_insensitive_login_match():
    thread = [_c("Reviewer"), _c("APP-BOT"), _c("reviewer")]
    result = mod.classify_thread_depth(thread, "app-bot")
    assert result["next_reply_is_back_and_forth"] is True


def test_reviewer_before_agent_only_not_counted():
    # non-agent comments only before the first agent reply do not count as counter-replies
    thread = [_c("reviewer"), _c("other"), _c(BOT)]
    result = mod.classify_thread_depth(thread, BOT)
    assert result["has_reviewer_counter_reply"] is False
    assert result["next_reply_is_back_and_forth"] is False


def test_empty_agent_login_raises():
    with pytest.raises(ValueError):
        mod.classify_thread_depth([_c("x")], "   ")


def test_non_dict_comment_element_raises():
    with pytest.raises(ValueError):
        mod.classify_thread_depth([_c("reviewer"), None], BOT)
    with pytest.raises(ValueError):
        mod.classify_thread_depth(["scalar"], BOT)


def test_main_non_dict_element_errors():
    code, _, err = call_main(mod, ["--agent-login", BOT], stdin=json.dumps([_c("r"), None]))
    assert code == 1
    assert "not an object" in err


def test_main_stdin_array():
    payload = json.dumps([_c("reviewer"), _c(BOT), _c("reviewer")])
    code, out, _ = call_main(mod, ["--agent-login", BOT], stdin=payload)
    assert code == 0
    assert json.loads(out)["next_reply_is_back_and_forth"] is True


def test_main_comments_object_wrapper():
    payload = json.dumps({"comments": [_c("reviewer"), _c(BOT)]})
    code, out, _ = call_main(mod, ["--agent-login", BOT], stdin=payload)
    assert code == 0
    assert json.loads(out)["next_reply_is_back_and_forth"] is False


def test_main_reads_file(tmp_path):
    path = tmp_path / "thread.json"
    path.write_text(json.dumps([_c("reviewer"), _c(BOT), _c("reviewer")]))
    code, out, _ = call_main(mod, ["--agent-login", BOT, "--comments-file", str(path)])
    assert code == 0
    assert json.loads(out)["next_reply_is_back_and_forth"] is True


def test_main_unreadable_file():
    code, _, err = call_main(mod, ["--agent-login", BOT, "--comments-file", "/no/such.json"])
    assert code == 1
    assert "cannot read" in err


def test_main_invalid_json():
    code, _, err = call_main(mod, ["--agent-login", BOT], stdin="{bad")
    assert code == 1
    assert "invalid JSON" in err


def test_main_bad_shape():
    code, _, err = call_main(mod, ["--agent-login", BOT], stdin='{"x": 1}')
    assert code == 1
    assert "expected a JSON array" in err
