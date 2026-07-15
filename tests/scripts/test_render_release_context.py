import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-workflow-hotfix-backport/scripts/render_release_context.py"
mod = load(SCRIPT_UNDER_TEST)


def test_slug_and_key_helpers():
    assert mod.render_slug("Fix the crash") == "fix-crash"
    assert mod.normalize_jira_key("mpt-1") == "MPT-1"


def test_classify_mode_and_markers():
    assert mod.classify_mode("Bug") == "hotfix"
    assert mod.classify_mode("Story") == "backport"
    assert mod.marker_for_mode("hotfix") == "[HF]"
    assert mod.marker_for_mode("backport") == "[BACKPORT]"
    assert mod.prefix_for_mode("hotfix") == "hotfix-"
    assert mod.prefix_for_mode("backport") == "backport-"
    for bad_fn in (mod.marker_for_mode, mod.prefix_for_mode):
        try:
            bad_fn("bogus")
            raised = False
        except ValueError:
            raised = True
        assert raised


def test_extract_summary_and_fixversions_top_level():
    assert mod.extract_summary({"summary": "top"}, None) == "top"
    assert mod.extract_fix_version_names({"fixVersions": ["v6"]}) == ["v6"]


def test_pr_open_or_merged():
    assert mod.is_pr_open_or_merged({"state": "MERGED"})
    assert mod.is_pr_open_or_merged({"merged": True})
    assert mod.is_pr_open_or_merged({"mergedAt": "2026-01-01"})
    assert not mod.is_pr_open_or_merged({"state": "CLOSED"})


def test_extract_commit_sha_variants():
    assert mod.extract_commit_sha("abc") == "abc"
    assert mod.extract_commit_sha({"oid": "def"}) == "def"
    assert mod.extract_commit_sha({"commit": {"sha": "ghi"}}) == "ghi"
    assert mod.extract_commit_sha(123) == ""


def test_extract_helpers():
    assert mod.extract_jira_key({"key": "MPT-1"}, None) == "MPT-1"
    assert mod.extract_jira_key({}, "mpt-9") == "MPT-9"
    assert mod.extract_issue_type({"fields": {"issuetype": {"name": "Bug"}}}) == "Bug"
    assert mod.extract_issue_type({}) == ""
    assert mod.extract_summary({"fields": {"summary": "S"}}, None) == "S"
    assert mod.extract_summary({}, "override") == "override"
    assert mod.nested_get({"a": {"b": 1}}, "a", "b") == 1
    assert mod.nested_get({"a": 1}, "a", "b") is None
    assert mod.get_pr_number({"number": 5}) == 5
    assert mod.get_pr_number({"pr_number": 6}) == 6


def test_fix_version_extraction_shapes():
    assert mod.extract_fix_version_names({"fields": {"fixVersions": ["v6", {"name": "hotfix"}, 3]}}) == ["v6", "hotfix"]
    assert mod.extract_fix_version_names({"fields": {"fixVersions": "nope"}}) == []
    assert mod.matching_fix_versions("hotfix", ["v6", "hotfix"]) == ["hotfix"]


def test_source_commits_shapes():
    assert mod.extract_source_commits({"commits": {"nodes": [{"oid": "a"}]}}) == ["a"]
    assert mod.extract_source_commits({"source_commits": ["b"]}) == ["b"]
    assert mod.extract_source_commits({"commits": "bad"}) == []


def _files(tmp_path, issue, pr):
    ip, pp = tmp_path / "i.json", tmp_path / "p.json"
    ip.write_text(json.dumps(issue))
    pp.write_text(json.dumps(pr))
    return str(ip), str(pp)


def test_main_happy(tmp_path):
    issue = {"key": "MPT-1", "fields": {"issuetype": {"name": "Bug"}, "summary": "Fix crash", "fixVersions": [{"name": "hotfix"}]}}
    pr = {"state": "MERGED", "baseRefName": "main", "commits": {"nodes": [{"oid": "abc123"}]}}
    ip, pp = _files(tmp_path, issue, pr)
    code, out, _ = call_main(mod, ["--jira-json", ip, "--pr-json", pp, "--pretty"])
    assert code == 0
    ctx = json.loads(out)
    assert ctx["jira_key"] == "MPT-1"
    assert "mode" in ctx and "pr_marker" in ctx and ctx["blockers"] == []


def test_main_blocks_on_bad_pr(tmp_path):
    issue = {"key": "MPT-2", "fields": {"issuetype": {"name": ""}, "summary": "x", "fixVersions": []}}
    pr = {"state": "CLOSED", "baseRefName": "develop", "commits": {"nodes": []}}
    ip, pp = _files(tmp_path, issue, pr)
    code, out, _ = call_main(mod, ["--jira-json", ip, "--pr-json", pp])
    assert code == 0
    ctx = json.loads(out)
    assert ctx["blockers"]  # base develop, not open/merged, no commits, missing type


def test_main_bad_json(tmp_path):
    bad = tmp_path / "b.json"
    bad.write_text("{not json")
    other = tmp_path / "o.json"
    other.write_text("{}")
    assert call_main(mod, ["--jira-json", str(bad), "--pr-json", str(other)])[0] == 1
