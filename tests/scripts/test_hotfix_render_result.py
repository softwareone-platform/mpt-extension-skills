import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-workflow-hotfix-backport/scripts/render_result.py"
mod = load(SCRIPT_UNDER_TEST)


def test_value_helper():
    assert mod.value({"k": "v"}, "k") == "v"
    assert mod.value({}, "k", "fallback") == "fallback"


def test_render_validation_states():
    assert mod.render_validation("make check", "pass") == "`make check`: pass"
    assert mod.render_validation("", "pass") == "pass"
    assert mod.render_validation("", "") == "not reported"


def test_render_source_commits_and_fix_version():
    assert mod.render_source_commits({"source_commits": ["a", "b"]}) == "a, b"
    assert mod.render_source_commits({}) == "unknown"
    assert mod.render_fix_version_state({"matching_fix_versions": ["hotfix"]}) == "hotfix"
    assert mod.render_fix_version_state({"needs_fix_version_confirmation": True}) == "missing confirmation required"
    assert mod.render_fix_version_state({}) == "not reported"


def test_render_blockers():
    assert mod.render_blockers({"blockers": ["x"]}) == ["", "Blockers:", "- x"]
    assert mod.render_blockers({"blockers": []}) == []
    assert mod.render_blockers({}) == []


def test_main_happy(tmp_path):
    ctx = tmp_path / "c.json"
    ctx.write_text(json.dumps({
        "mode": "hotfix", "pr_marker": "[HF]", "jira_key": "MPT-1",
        "source_pr_url": "https://x/pull/1", "source_commits": ["abc"],
        "target_release_branch": "release/6", "release_branch_name": "hotfix/MPT-1/x",
        "blockers": ["source_pr_base_is_develop"],
    }))
    code, out, _ = call_main(mod, ["--context-json", str(ctx), "--release-pr-url", "https://x/pull/9", "--validation-command", "make check", "--validation-status", "pass", "--jira-status", "moved"])
    assert code == 0
    assert "Mode: hotfix" in out and "Jira: MPT-1" in out
    assert "Release PR: https://x/pull/9" in out


def test_main_non_object_errors(tmp_path):
    ctx = tmp_path / "c.json"
    ctx.write_text("[]")
    assert call_main(mod, ["--context-json", str(ctx)])[0] == 1
