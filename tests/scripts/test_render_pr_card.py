import io
import json
import sys

import pytest
from helpers import load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-notify-pr-ready-in-teams/scripts/render_pr_card.py"
mod = load(SCRIPT_UNDER_TEST)


def _heading(card):
    return card["body"][0]["items"][0]["text"]


def _fact_containers(card):
    # The header band is also a Container, but only the facts one has no style.
    return [b for b in card["body"] if b["type"] == "Container" and "style" not in b]


def _comment_boxes(card):
    return [b for b in card["body"] if b.get("style") == "warning"]


def _fact_rows(card):
    return _fact_containers(card)[0]["items"]


def _row_value(row):
    value = row["columns"][1]["items"][0]
    if value["type"] == "ColumnSet":
        return value["columns"][1]["items"][0]["text"]
    return value["text"]


def _facts(card):
    return [
        {"title": row["columns"][0]["items"][0]["text"], "value": _row_value(row)}
        for row in _fact_rows(card)
    ]


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
    assert _facts(card)[0] == {"title": "Author", "value": "a\\*b"}


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
    header = card["body"][0]
    assert (header["type"], header["style"], header["bleed"]) == ("Container", "good", True)
    assert _heading(card) == "✅ PR #42 ready for merge"
    assert header["items"][0]["weight"] == "bolder"
    assert header["items"][0]["size"] == "large"
    facts = _facts(card)
    titles = [f["title"] for f in facts]
    assert titles == ["Author", "Repository", "Branch", "Checks", "CodeRabbit"]
    assert facts[1]["value"] == "acme/widgets"
    assert facts[2]["value"] == "feature/x → main"
    assert facts[3]["value"] == "✅"
    assert facts[4]["value"] == "✅"
    assert len(card["actions"]) == 2


def test_build_card_uses_red_crosses_for_unexpected_states():
    card = mod.build_card(
        title="Add X",
        number="42",
        url="https://gh/pr/42",
        checks_state="failure",
        coderabbit_state="CHANGES_REQUESTED",
    )
    assert _facts(card) == [
        {"title": "Checks", "value": "❌"},
        {"title": "CodeRabbit", "value": "❌"},
    ]
    assert card["body"][0]["style"] == "attention"
    assert _heading(card) == "❌ PR #42 not ready for merge"


@pytest.mark.parametrize(
    ("checks_state", "coderabbit_state", "style", "heading"),
    [
        ("success", "APPROVED", "good", "✅ PR #42 ready for merge"),
        ("success", "CHANGES_REQUESTED", "attention", "❌ PR #42 not ready for merge"),
        ("failure", "APPROVED", "attention", "❌ PR #42 not ready for merge"),
        (None, None, "good", "✅ PR #42 ready for merge"),
    ],
)
def test_build_card_header_follows_states(checks_state, coderabbit_state, style, heading):
    card = mod.build_card(
        title="T",
        number="42",
        url="u",
        checks_state=checks_state,
        coderabbit_state=coderabbit_state,
    )

    assert card["body"][0]["style"] == style
    assert _heading(card) == heading


def test_build_card_minimal_no_number_no_facts():
    card = mod.build_card(title="T", number=None, url="https://u")
    assert _heading(card) == "✅ Pull request ready for merge"
    assert not _fact_containers(card)
    assert len(card["actions"]) == 1


@pytest.mark.parametrize(("kwargs", "expected"), [({"branch": "b"}, "b"), ({"base": "m"}, "m")])
def test_build_card_branch_only_and_base_only(kwargs, expected):
    card = mod.build_card(title="T", number=None, url="u", **kwargs)

    assert _facts(card) == [{"title": "Branch", "value": expected}]


def test_build_card_author_with_avatar():
    card = mod.build_card(
        title="T", number=None, url="u", author="me", avatar_url="https://avatar/me"
    )

    value = _fact_rows(card)[0]["columns"][1]["items"][0]
    assert value["type"] == "ColumnSet"
    assert value["columns"][0]["items"][0] == {
        "type": "Image",
        "url": "https://avatar/me",
        "width": "20px",
        "height": "20px",
        "style": "person",
    }
    assert value["columns"][1]["items"][0]["text"] == "me"


def test_build_card_avatar_ignored_without_author():
    card = mod.build_card(title="T", number=None, url="u", avatar_url="https://avatar/me")

    assert not _fact_containers(card)


def test_fact_rows_align_titles():
    rows = mod.fact_rows([{"title": "A", "value": "1"}, {"title": "B", "value": "2"}])["items"]

    assert [row["columns"][0]["width"] for row in rows] == ["100px", "100px"]
    assert [row["columns"][0]["items"][0]["weight"] for row in rows] == ["bolder", "bolder"]
    assert "spacing" not in rows[0]
    assert rows[1]["spacing"] == "none"


def test_build_card_changes_fact():
    card = mod.build_card(
        title="T",
        number=None,
        url="u",
        commits=1,
        additions=4,
        deletions=4,
        changed_files=1,
    )

    assert _facts(card) == [
        {"title": "Changes", "value": "1 commit · +4 -4 · 1 file changed"},
    ]


@pytest.mark.parametrize(
    ("commits", "additions", "deletions", "changed_files", "expected"),
    [
        (3, 4, 4, 2, "3 commits · +4 -4 · 2 files changed"),
        (None, 4, None, 1, "1 file changed"),
        (0, 0, 0, None, "+0 -0"),
        (None, None, None, None, None),
    ],
)
def test_changes(commits, additions, deletions, changed_files, expected):
    result = mod._changes(commits, additions, deletions, changed_files)

    assert result == expected


@pytest.mark.parametrize(
    ("login", "expected"),
    [
        ("octocat", "https://avatars.githubusercontent.com/octocat?size=64"),
        ("app/dependabot", None),
        ("evil?x=1", None),
        (None, None),
    ],
)
def test_avatar_url(login, expected):
    result = mod._avatar_url(login)

    assert result == expected


def test_build_card_comment_box_after_header():
    card = mod.build_card(title="Add X", number=1, url="https://u", comment="Review by *Friday*")

    assert card["body"][1] == {
        "type": "Container",
        "style": "warning",
        "spacing": "medium",
        "items": [{"type": "TextBlock", "text": "💬 Review by \\*Friday\\*", "wrap": True}],
    }
    assert card["body"][2]["text"] == "Add X"


@pytest.mark.parametrize("comment", [None, "", "  \n  "])
def test_build_card_without_comment_has_no_box(comment):
    card = mod.build_card(title="Add X", number=1, url="https://u", comment=comment)

    assert _comment_boxes(card) == []
    assert card["body"][1]["text"] == "Add X"


def test_comment_text_keeps_line_breaks():
    result = mod._comment_text("  first line\n\n  second line  \n")

    assert result == "first line\n\nsecond line"


def test_comment_text_caps_length():
    result = mod._comment_text("x" * (mod.COMMENT_MAX_LENGTH + 10))

    assert len(result) == mod.COMMENT_MAX_LENGTH
    assert result.endswith("…")


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
        "avatar_url": "https://avatars.githubusercontent.com/octocat?size=64",
        "commits": None,
        "additions": None,
        "deletions": None,
        "changed_files": None,
    }


def test_fields_from_snapshot_preview_fields():
    f = mod.fields_from_snapshot(
        {
            "author": {"name": "Jane"},
            "commits": [{"oid": "a"}, {"oid": "b"}],
            "additions": 4,
            "deletions": 2,
            "changedFiles": 1,
        }
    )

    assert f["avatar_url"] is None
    assert f["commits"] == 2
    assert (f["additions"], f["deletions"], f["changed_files"]) == (4, 2, 1)


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
    assert _heading(card) == "✅ PR #42 ready for merge"
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
    assert _heading(json.loads(out)) == "✅ PR #7 ready for merge"


def test_main_empty_title(set_cli, capsys):
    set_cli(["--title", "   ", "--url", "https://u"])

    code = mod.main()
    err = capsys.readouterr().err

    assert code == 1
    assert "error:" in err


def test_main_author_override_drops_snapshot_avatar(set_cli, capsys):
    snap = json.dumps({"title": "T", "url": "https://u", "author": {"login": "octocat"}})
    set_cli(["--pr-json", "-", "--author", "someone-else"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    author_value = _fact_rows(json.loads(out))[0]["columns"][1]["items"][0]
    assert author_value == {"type": "TextBlock", "text": "someone-else", "wrap": True}


def test_main_snapshot_author_keeps_avatar(set_cli, capsys):
    snap = json.dumps({"title": "T", "url": "https://u", "author": {"login": "octocat"}})
    set_cli(["--pr-json", "-"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    author_value = _fact_rows(json.loads(out))[0]["columns"][1]["items"][0]
    assert author_value["columns"][0]["items"][0]["url"] == mod.AVATAR_URL.format(login="octocat")


def test_main_commit_count_flag_overrides_snapshot(set_cli, capsys):
    snap = json.dumps({"title": "T", "url": "https://u", "commits": [{"oid": "a"}] * 100})
    set_cli(["--pr-json", "-", "--commit-count", "150"], stdin=snap)

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    assert _facts(json.loads(out)) == [{"title": "Changes", "value": "150 commits"}]


def test_main_comment_file(set_cli, capsys, tmp_path):
    p = tmp_path / "comment.txt"
    p.write_text("Needs a second look\n", encoding="utf-8")
    set_cli(["--title", "T", "--url", "https://u", "--comment-file", str(p)])

    code = mod.main()
    out = capsys.readouterr().out

    assert code == 0
    box = _comment_boxes(json.loads(out))[0]
    assert box["items"][0]["text"] == "💬 Needs a second look"


def test_main_comment_file_missing(set_cli, capsys, tmp_path):
    set_cli(["--title", "T", "--url", "https://u", "--comment-file", str(tmp_path / "none.txt")])

    code = mod.main()
    err = capsys.readouterr().err

    assert code == 1
    assert "error:" in err
