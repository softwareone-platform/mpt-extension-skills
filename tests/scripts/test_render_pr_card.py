import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-notify-pr-ready-in-teams/scripts/render_pr_card.py"
mod = load(SCRIPT_UNDER_TEST)


def test_fact_skips_empty():
    assert mod._fact("A", "v") == {"title": "A", "value": "v"}
    assert mod._fact("A", "") is None
    assert mod._fact("A", None) is None


def test_md_escape():
    assert mod.md_escape("plain text") == "plain text"
    assert mod.md_escape("[x](y)") == "\\[x\\]\\(y\\)"
    assert mod.md_escape("a*b_c`d~e|f\\g") == "a\\*b\\_c\\`d\\~e\\|f\\\\g"


def test_build_card_escapes_untrusted_markdown():
    card = mod.build_card(
        title="[click](http://evil)", number=1, url="https://u", author="a*b"
    )
    assert card["body"][1]["text"] == "\\[click\\]\\(http://evil\\)"
    author_fact = [b for b in card["body"] if b["type"] == "FactSet"][0]["facts"][0]
    assert author_fact["value"] == "a\\*b"


def test_build_card_full():
    card = mod.build_card(
        title="Add X",
        number="42",
        url="https://gh/pr/42",
        author="me",
        branch="feature/x",
        base="main",
        jira_url="https://jira/MPT-1",
        checks_state="success",
        coderabbit_state="APPROVED",
    )
    assert card["type"] == "AdaptiveCard"
    assert card["body"][0]["text"] == "PR #42 ready for merge"
    factset = [b for b in card["body"] if b["type"] == "FactSet"][0]
    titles = [f["title"] for f in factset["facts"]]
    assert titles == ["Author", "Branch", "Checks", "CodeRabbit"]
    assert factset["facts"][1]["value"] == "feature/x → main"
    assert len(card["actions"]) == 2


def test_build_card_minimal_no_number_no_facts():
    card = mod.build_card(title="T", number=None, url="https://u")
    assert card["body"][0]["text"] == "Pull request ready for merge"
    assert all(b["type"] != "FactSet" for b in card["body"])
    assert len(card["actions"]) == 1


def test_build_card_branch_only_and_base_only():
    assert (
        [f for f in mod.build_card(title="T", number=None, url="u", branch="b")["body"]
         if f["type"] == "FactSet"][0]["facts"][0]["value"]
        == "b"
    )
    assert (
        [f for f in mod.build_card(title="T", number=None, url="u", base="m")["body"]
         if f["type"] == "FactSet"][0]["facts"][0]["value"]
        == "m"
    )


def test_build_card_requires_title_and_url():
    for kwargs in ({"title": "", "url": "u"}, {"title": "T", "url": ""}):
        try:
            mod.build_card(number=None, **kwargs)
            raised = False
        except ValueError:
            raised = True
        assert raised


def test_fields_from_snapshot():
    f = mod.fields_from_snapshot(
        {
            "title": "T",
            "number": 7,
            "url": "https://u",
            "author": {"login": "octocat"},
            "headRefName": "feature/x",
            "baseRefName": "main",
        }
    )
    assert f == {
        "title": "T",
        "number": 7,
        "url": "https://u",
        "author": "octocat",
        "branch": "feature/x",
        "base": "main",
    }


def test_fields_from_snapshot_author_fallbacks():
    assert mod.fields_from_snapshot({"author": {"name": "Jane"}})["author"] == "Jane"
    assert mod.fields_from_snapshot({"author": None})["author"] is None
    assert mod.fields_from_snapshot({})["author"] is None


def test_load_snapshot_file_and_non_dict(tmp_path):
    p = tmp_path / "pr.json"
    p.write_text('{"title":"T"}', encoding="utf-8")
    assert mod.load_snapshot(str(p))["title"] == "T"
    p.write_text("[]", encoding="utf-8")
    try:
        mod.load_snapshot(str(p))
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_main_pr_json_file(tmp_path):
    snap = {
        "title": "Add X",
        "number": 42,
        "url": "https://gh/pr/42",
        "author": {"login": "me"},
        "headRefName": "feature/x",
        "baseRefName": "main",
    }
    p = tmp_path / "pr.json"
    p.write_text(json.dumps(snap), encoding="utf-8")
    code, out, _ = call_main(mod, ["--pr-json", str(p), "--coderabbit-state", "APPROVED"])
    assert code == 0
    card = json.loads(out)
    assert card["body"][0]["text"] == "PR #42 ready for merge"
    assert card["actions"][0]["url"] == "https://gh/pr/42"


def test_main_pr_json_stdin_with_flag_override():
    snap = json.dumps({"title": "From snapshot", "url": "https://u", "number": 1})
    code, out, _ = call_main(mod, ["--pr-json", "-", "--title", "Overridden"], stdin=snap)
    assert code == 0
    # Explicit --title overrides the snapshot value.
    assert json.loads(out)["body"][1]["text"] == "Overridden"


def test_main_pr_json_invalid(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    code, _, err = call_main(mod, ["--pr-json", str(p)])
    assert code == 1
    assert "error:" in err


def test_main_no_source_errors():
    # Neither --pr-json nor --title/--url provided -> build_card rejects empty title.
    code, _, err = call_main(mod, [])
    assert code == 1
    assert "error:" in err


def test_main_success():
    code, out, _ = call_main(
        mod, ["--title", "Add X", "--url", "https://u", "--number", "7"]
    )
    assert code == 0
    assert json.loads(out)["body"][0]["text"] == "PR #7 ready for merge"


def test_main_empty_title():
    code, _, err = call_main(mod, ["--title", "   ", "--url", "https://u"])
    assert code == 1
    assert "error:" in err
