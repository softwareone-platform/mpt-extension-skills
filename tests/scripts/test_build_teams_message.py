import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-tool-teams-send-message/scripts/build_teams_message.py"
mod = load(SCRIPT_UNDER_TEST)


def test_text_card_shape():
    card = mod.text_card("hello")
    assert card["type"] == "AdaptiveCard"
    assert card["body"][0]["text"] == "hello"


def test_is_adaptive_card():
    assert mod.is_adaptive_card({"type": "AdaptiveCard", "version": "1.4"})
    assert not mod.is_adaptive_card({"type": "AdaptiveCard"})  # missing version
    assert not mod.is_adaptive_card({"type": "AdaptiveCard", "version": "  "})  # blank version
    assert not mod.is_adaptive_card({"type": "Other"})
    assert not mod.is_adaptive_card("nope")


def test_build_envelope_valid():
    env = mod.build_envelope({"type": "AdaptiveCard", "version": "1.4", "body": []})
    assert env["type"] == "message"
    att = env["attachments"][0]
    assert att["contentType"] == mod.ADAPTIVE_CONTENT_TYPE
    assert att["content"]["type"] == "AdaptiveCard"


def test_build_envelope_rejects_non_card():
    try:
        mod.build_envelope({"type": "Other"})
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_load_card_requires_exactly_one_source():
    for args in [(None, None), ("text", "file")]:
        try:
            mod.load_card(*args)
            raised = False
        except ValueError:
            raised = True
        assert raised


def test_load_card_text_empty():
    try:
        mod.load_card("   ", None)
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_load_card_preserves_whitespace():
    # Emptiness is checked with strip(), but the original text must be delivered verbatim.
    card = mod.load_card("  hello world  ", None)
    assert card["body"][0]["text"] == "  hello world  "


def test_load_card_from_file(tmp_path):
    card = {"type": "AdaptiveCard", "version": "1.4", "body": []}
    p = tmp_path / "card.json"
    p.write_text(json.dumps(card), encoding="utf-8")
    assert mod.load_card(None, str(p)) == card


def test_load_card_file_not_a_card(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"type": "Other"}), encoding="utf-8")
    try:
        mod.load_card(None, str(p))
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_main_text_mode():
    code, out, _ = call_main(mod, ["--text", "Build passed"])
    assert code == 0
    env = json.loads(out)
    assert env["attachments"][0]["content"]["body"][0]["text"] == "Build passed"


def test_main_card_file_mode(tmp_path):
    p = tmp_path / "card.json"
    p.write_text(json.dumps({"type": "AdaptiveCard", "version": "1.4", "body": []}), encoding="utf-8")
    code, out, _ = call_main(mod, ["--card-file", str(p)])
    assert code == 0
    assert json.loads(out)["type"] == "message"


def test_main_conflicting_sources():
    code, _, err = call_main(mod, ["--text", "x", "--card-file", "y.json"])
    assert code == 1
    assert "exactly one" in err


def test_main_missing_file():
    code, _, err = call_main(mod, ["--card-file", "/no/such/file.json"])
    assert code == 1
    assert "error:" in err


def test_main_file_bad_json(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    code, _, err = call_main(mod, ["--card-file", str(p)])
    assert code == 1
    assert "error:" in err
