import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-apply-dashboard-jira-decision/scripts/plan_dashboard_decision.py"
mod = load(SCRIPT_UNDER_TEST)


def plan(**kw):
    defaults = dict(
        action="new", target_key=None, component=None, failures_count=None,
        current_hitcount=None, accumulate=False, merge_target_action=None,
        skip_reason=None, release_fix_version="v6",
    )
    defaults.update(kw)
    return mod.plan_decision(**defaults)


def test_new_sets_hitcount_and_policy():
    out = plan(action="new", component="Commerce", failures_count=3)
    assert out["hitcount"] == 3
    assert out["blockers"] == []
    assert out["policy"]["fix_versions"] == ["v6", "hotfix"]


def test_new_missing_component():
    assert "component_missing" in plan(action="new", failures_count=3)["blockers"]


def test_update_increments_and_missing_current():
    assert plan(action="update", target_key="MPT-1", failures_count=2, current_hitcount=5)["hitcount"] == 7
    assert "current_hitcount_missing" in plan(action="update", target_key="MPT-1", failures_count=2)["blockers"]


def test_reopen_reset_and_accumulate():
    assert plan(action="reopen", target_key="MPT-1", failures_count=4, current_hitcount=9)["hitcount"] == 4
    assert plan(action="reopen", target_key="MPT-1", failures_count=4, current_hitcount=9, accumulate=True)["hitcount"] == 13
    assert "current_hitcount_missing" in plan(action="reopen", target_key="MPT-1", failures_count=4, accumulate=True)["blockers"]


@pytest.mark.parametrize("target_action,expected", [("new", 1), ("reopen", 1), ("update", 8)])
def test_merge_follows_target_action(target_action, expected):
    out = plan(action="merge", target_key="MPT-1", failures_count=1, current_hitcount=7, merge_target_action=target_action)
    assert out["hitcount"] == expected


def test_merge_missing_and_invalid_action():
    assert "merge_target_action_missing" in plan(action="merge", target_key="MPT-1", failures_count=1)["blockers"]
    assert "merge_target_action_invalid" in plan(action="merge", target_key="MPT-1", failures_count=1, merge_target_action="bogus")["blockers"]


def test_targeted_actions_require_key():
    assert "target_key_missing" in plan(action="update", failures_count=1, current_hitcount=0)["blockers"]


def test_negative_counts_block():
    assert "failures_count_negative" in plan(action="new", component="X", failures_count=-1)["blockers"]
    assert "current_hitcount_negative" in plan(action="update", target_key="MPT-1", failures_count=1, current_hitcount=-2)["blockers"]


def test_missing_failures_blocks():
    assert "failures_count_missing" in plan(action="new", component="X")["blockers"]


def test_skip_requires_reason_and_has_no_policy():
    ok = plan(action="skip", skip_reason="dupe")
    assert ok["policy"] is None and ok["skip_reason"] == "dupe" and ok["blockers"] == []
    assert "skip_reason_missing" in plan(action="skip")["blockers"]


def test_blank_release_blocks_and_drops_policy():
    out = plan(action="new", component="X", failures_count=2, release_fix_version="")
    assert "release_fix_version_missing" in out["blockers"] and out["policy"] is None


def test_normalize_helpers():
    assert mod.normalize_action(" NEW ") == "new"
    assert mod.normalize_jira_key(None) is None
    assert mod.normalize_jira_key("  ") is None
    assert mod.normalize_jira_key("mpt-9") == "MPT-9"
    with pytest.raises(ValueError):
        mod.normalize_action("bogus")
    with pytest.raises(ValueError):
        mod.normalize_jira_key("nope")


def test_main_cli_paths():
    code, out, _ = call_main(mod, ["--decision", "new", "--component", "X", "--failures-count", "3"])
    assert code == 0 and '"hitcount": 3' in out
    code, out, _ = call_main(mod, ["--decision", "merge", "--target-key", "MPT-1", "--failures-count", "1", "--current-hitcount", "2", "--merge-target-action", "UPDATE", "--pretty"])
    assert code == 0 and '"hitcount": 3' in out
    code, _, err = call_main(mod, ["--decision", "update", "--target-key", "foo", "--failures-count", "1"])
    assert code == 1 and "error" in err
