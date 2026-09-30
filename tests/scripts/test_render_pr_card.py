import io
import json
import sys

import pytest
from helpers import load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-notify-pr-ready-in-teams/scripts/render_pr_card.py"
mod = load(SCRIPT_UNDER_TEST)


def test_fact_skips_empty():
    assert mod._fact("A", "v") == {"title": "A", "value": "v"}
    assert mod._fact("A", "") is None
    assert mod._fact("A", None) is None


def test_ready_state_value():
    assert mod._ready_state_value("success", "success") == "✅"
    assert mod._ready_state_value("approved", "APPROVED") == "✅"
    assert mod._ready_state_value("failure", "success") == "❌"
    assert mod._ready_state_value(None, "success") is None
    assert mod._ready_state_value("  ", "success") is None


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
        repository="acme/widgets",
        branch="feature/x",
        base="main",
        jira_url="https://jira/MPT-1",
        checks_state="success",
        coderabbit_state="APPROVED",
    )
    assert card["type"] == "AdaptiveCard"
    assert card["body"][0]["text"] == "PR #42 ready for merge"
    assert card["body"][0]["weight"] == "bolder"
    assert card["body"][0]["size"] == "medium"
    factset = [b for b in card["body"] if b["type"] == "FactSet"][0]
    titles = [f["title"] for f in factset["facts"]]
    assert titles == ["Author", "Repository", "Branch", "Checks", "CodeRabbit"]
    assert factset["facts"][1]["value"] == "acme/widgets"
    assert factset["facts"][2]["value"] == "feature/x → main"
    assert factset["facts"][3]["value"] == "✅"
    assert factset["facts"][4]["value"] == "✅"
    assert len(card["actions"]) == 2


def test_build_card_uses_red_crosses_for_unexpected_states():
    card = mod.build_card(
        title="Add X",
        number="42",
        url="https://gh/pr/42",
        checks_state="failure",
        coderabbit_state="CHANGES_REQUESTED",
    )
    factset = [body for body in card["body"] if body["type"] == "FactSet"][0]
    assert factset["facts"] == [
        {"title": "Checks", "value": "❌"},
        {"title": "CodeRabbit", "value": "❌"},
    ]


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
            "url": "https://github.com/acme/widgets/pull/7",
            "author": {"login": "octocat"},
            "headRefName": "feature/x",
            "baseRefName": "main",
        }
    )
    assert f == {
        "title": "T",
        "number": 7,
        "url": "https://github.com/acme/widgets/pull/7",
        "author": "octocat",
        "repository": "acme/widgets",
        "branch": "feature/x",
        "base": "main",
    }


def test_fields_from_snapshot_author_fallbacks():
    assert mod.fields_from_snapshot({"author": {"name": "Jane"}})["author"] == "Jane"
    assert mod.fields_from_snapshot({"author": None})["author"] is None
    assert mod.fields_from_snapshot({})["author"] is None


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://github.com/acme/widgets/pull/7", "acme/widgets"),
        ("https://u", None),
        ("https://gitlab.com/acme/widgets/pull/7", None),
        (None, None),
    ],
)
def test_fields_from_snapshot_repository(url, expected):
    result = mod.fields_from_snapshot({"url": url})["repository"]

    assert result == expected


@pytest.fixture
def set_cli(monkeypatch):
    def _set(args, stdin=""):
        monkeypatch.setattr(sys, "argv", ["prog", *args])
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))

    return _set


def _facts(card):
    return [b for b in card["body"] if b["type"] == "FactSet"][0]["facts"]


def test_main_repository_derived_from_snapshot_url(set_cli, capsys):
    snap = json.dumps(
        {
            "title": "T",
            "url": "https://github.com/acme/widgets/pull/7",
            "author": {"login": "me"},
            "headRefName": "feature/x",
        }
    )
    set_cli(["--pr-json", "-"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    assert [f["title"] for f in _facts(json.loads(out))] == ["Author", "Repository", "Branch"]
    assert _facts(json.loads(out))[1]["value"] == "acme/widgets"


def test_main_repository_omitted_when_url_does_not_match(set_cli, capsys):
    snap = json.dumps({"title": "T", "url": "https://u", "author": {"login": "me"}})
    set_cli(["--pr-json", "-"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    assert [f["title"] for f in _facts(json.loads(out))] == ["Author"]


def test_main_repository_flag_overrides_snapshot(set_cli, capsys):
    snap = json.dumps({"title": "T", "url": "https://github.com/acme/widgets/pull/7"})
    set_cli(["--pr-json", "-", "--repository", "other/repo"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    assert _facts(json.loads(out))[0] == {"title": "Repository", "value": "other/repo"}


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


def test_main_pr_json_file(set_cli, capsys, tmp_path):
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
    set_cli(["--pr-json", str(p), "--coderabbit-state", "APPROVED"])

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    card = json.loads(out)
    assert card["body"][0]["text"] == "PR #42 ready for merge"
    assert card["actions"][0]["url"] == "https://gh/pr/42"


def test_main_pr_json_stdin_with_flag_override(set_cli, capsys):
    snap = json.dumps({"title": "From snapshot", "url": "https://u", "number": 1})
    set_cli(["--pr-json", "-", "--title", "Overridden"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    # Explicit --title overrides the snapshot value.
    assert json.loads(out)["body"][1]["text"] == "Overridden"


def test_main_pr_json_invalid(set_cli, capsys, tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    set_cli(["--pr-json", str(p)])

    code = mod.main()
    err = capsys.readouterr().err

    assert code == 1
    assert "error:" in err


def test_main_no_source_errors(set_cli, capsys):
    # Neither --pr-json nor --title/--url provided -> build_card rejects empty title.
    set_cli([])

    code = mod.main()
    err = capsys.readouterr().err

    assert code == 1
    assert "error:" in err


def test_main_success(set_cli, capsys):
    set_cli(["--title", "Add X", "--url", "https://u", "--number", "7"])

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    assert json.loads(out)["body"][0]["text"] == "PR #7 ready for merge"


def test_main_empty_title(set_cli, capsys):
    set_cli(["--title", "   ", "--url", "https://u"])

    code = mod.main()
    err = capsys.readouterr().err

    assert code == 1
    assert "error:" in err
