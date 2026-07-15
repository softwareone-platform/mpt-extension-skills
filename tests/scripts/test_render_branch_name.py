import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-create-work-branch/scripts/render_branch_name.py"
mod = load(SCRIPT_UNDER_TEST)


def test_render_slug_drops_stopwords():
    assert mod.render_slug("Fix the broken thing") == "fix-broken-thing"
    assert mod.render_slug("!!!") == ""


def test_is_valid_jira_key():
    assert mod.is_valid_jira_key("MPT-1")
    assert not mod.is_valid_jira_key("nope")


def test_render_branch_name_keeps_key_uppercase():
    assert mod.render_branch_name("feature", "MPT-1", "fix-thing") == "feature/MPT-1/fix-thing"


def test_render_branch_name_all_types():
    assert mod.render_branch_name("bugfix", "MPT-1", "s") == "bugfix/MPT-1/s"
    assert mod.render_branch_name("hotfix", "MPT-1", "s").startswith("hotfix-hotfix/MPT-1/")
    assert mod.render_branch_name("backport", "MPT-1", "s").startswith("backport-backport/MPT-1/")
    try:
        mod.render_branch_name("bogus", "MPT-1", "s")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_main_json_output():
    import json
    code, out, _ = call_main(mod, ["--jira-key", "MPT-1", "--branch-type", "feature", "--title", "Fix thing", "--json"])
    assert code == 0
    data = json.loads(out)
    assert data["branch_name"].startswith("feature/MPT-1/") and data["source"] == "title"


def test_main_requires_title_or_description():
    code, _, err = call_main(mod, ["--jira-key", "MPT-1", "--branch-type", "feature"])
    assert code == 1 and "error" in err


def test_main_from_title():
    code, out, _ = call_main(mod, ["--jira-key", "mpt-1", "--branch-type", "feature", "--title", "Fix the thing"])
    assert code == 0
    assert out.strip().startswith("feature/MPT-1/")
    assert "fix" in out and "thing" in out


def test_main_falls_back_to_description():
    code, out, _ = call_main(mod, ["--jira-key", "MPT-2", "--branch-type", "bugfix", "--description", "Broken login flow"])
    assert code == 0
    assert out.strip().startswith("bugfix/MPT-2/")


def test_main_invalid_key_errors():
    code, _, err = call_main(mod, ["--jira-key", "bad", "--branch-type", "feature", "--title", "x y"])
    assert code == 1 and "error" in err


def test_main_no_slug_errors():
    code, _, err = call_main(mod, ["--jira-key", "MPT-3", "--branch-type", "feature", "--title", "!!!"])
    assert code == 1 and "error" in err
