from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-open-pull-request/scripts/render_result.py"
mod = load(SCRIPT_UNDER_TEST)


def test_normalize_jira_site():
    assert mod.normalize_jira_site("Site: softwareone.atlassian.net") == "softwareone.atlassian.net"
    assert mod.normalize_jira_site("https://softwareone.atlassian.net/x") == "softwareone.atlassian.net"
    assert mod.normalize_jira_site("  ") == ""


def test_render_jira_url_variants():
    assert mod.render_jira_url("softwareone.atlassian.net", "mpt-1").endswith("/browse/MPT-1")
    assert mod.render_jira_url("", "MPT-1") == ""
    assert mod.render_jira_url("site", "bad-key") == ""


def test_main_full_output():
    code, out, _ = call_main(mod, ["--pr-url", "https://x/pull/1", "--testing", "make check", "--jira-site", "softwareone.atlassian.net", "--jira-key", "MPT-1"])
    assert code == 0
    assert "PR: https://x/pull/1" in out
    assert "Jira: https://softwareone.atlassian.net/browse/MPT-1" in out
    assert "Testing: make check" in out


def test_main_without_jira():
    code, out, _ = call_main(mod, ["--pr-url", "https://x/pull/2", "--testing", "ran"])
    assert code == 0 and "Jira:" not in out


def test_main_missing_values_error():
    assert call_main(mod, ["--pr-url", "  ", "--testing", "ran"])[0] == 1
    assert call_main(mod, ["--pr-url", "https://x", "--testing", "  "])[0] == 1
