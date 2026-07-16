import json

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-open-pull-request/scripts/render_pr_title.py"
mod = load(SCRIPT_UNDER_TEST)


def test_is_release_branch():
    assert mod.is_release_branch("release/5")
    assert mod.is_release_branch("release/5.1")
    assert not mod.is_release_branch("release/")
    assert not mod.is_release_branch("main")
    assert not mod.is_release_branch("feature/x")


def test_normalize_jira_key():
    assert mod.normalize_jira_key(" mpt-1234 ") == "MPT-1234"
    with pytest.raises(ValueError):
        mod.normalize_jira_key("1234")
    with pytest.raises(ValueError):
        mod.normalize_jira_key("MPT-abc")


def test_normalize_summary():
    assert mod.normalize_summary("  add   the  thing ") == "add the thing"
    with pytest.raises(ValueError):
        mod.normalize_summary("   ")
    with pytest.raises(ValueError):
        mod.normalize_summary("feat: add the thing")
    with pytest.raises(ValueError):
        mod.normalize_summary("Fix(scope)!: bang")


def test_resolve_marker():
    assert mod.resolve_marker("feature", "main") == ""
    assert mod.resolve_marker("bugfix", "main") == ""
    assert mod.resolve_marker("hotfix", "release/5") == "[HF]"
    assert mod.resolve_marker("backport", "release/5") == "[BACKPORT]"
    # hotfix/backport against main (opened there first) carry no marker
    assert mod.resolve_marker("hotfix", "main") == ""
    assert mod.resolve_marker("backport", "main") == ""


def test_resolve_marker_rejects_feature_against_release():
    with pytest.raises(ValueError):
        mod.resolve_marker("feature", "release/5")


def test_resolve_marker_unsupported_kind():
    with pytest.raises(ValueError):
        mod.resolve_marker("nonsense", "main")


def test_render_pr_title_variants():
    assert mod.render_pr_title("MPT-1", "add x", "feature", "main") == "MPT-1 add x"
    assert mod.render_pr_title("mpt-2", "fix y", "hotfix", "release/5") == "[HF] MPT-2 fix y"
    assert (
        mod.render_pr_title("MPT-3", "port z", "backport", "release/9")
        == "[BACKPORT] MPT-3 port z"
    )


def test_main_plain():
    code, out, _ = call_main(
        mod, ["--jira-key", "MPT-1", "--summary", "add feature"]
    )
    assert code == 0
    assert out.strip() == "MPT-1 add feature"


def test_main_json():
    code, out, _ = call_main(
        mod,
        [
            "--jira-key",
            "MPT-7",
            "--summary",
            "fix bug",
            "--kind",
            "hotfix",
            "--base-branch",
            "release/5",
            "--json",
        ],
    )
    assert code == 0
    data = json.loads(out)
    assert data["title"] == "[HF] MPT-7 fix bug"
    assert data["marker"] == "[HF]"
    assert data["is_release_base"] is True
    assert data["jira_key"] == "MPT-7"


def test_main_invalid_key_errors():
    code, _, err = call_main(mod, ["--jira-key", "bad", "--summary", "x"])
    assert code == 1
    assert "invalid Jira key" in err


def test_main_feature_against_release_errors():
    code, _, err = call_main(
        mod, ["--jira-key", "MPT-1", "--summary", "x", "--base-branch", "release/5"]
    )
    assert code == 1
    assert "release branch" in err
