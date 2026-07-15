import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-tool-git-branch-ops/scripts/resolve_base_branch.py"
mod = load(SCRIPT_UNDER_TEST)


import subprocess


def test_numeric_release_detection_and_sort():
    assert mod.is_numeric_release_branch("release/6")
    assert not mod.is_numeric_release_branch("release/foo")
    branches = ["release/5", "release/10", "release/6"]
    assert max(branches, key=mod.release_sort_key) == "release/10"
    assert mod.release_sort_key("release/foo")[0] == -1


def test_list_remote_release_branches_parses(monkeypatch):
    out = "origin/release/5\norigin/release/6\norigin/main\n"
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, stdout=out, stderr=""))
    branches = mod.list_remote_release_branches("origin")
    assert "release/5" in branches and "release/6" in branches


def test_resolve_unsupported_type_raises():
    try:
        mod.resolve_base_branch("bogus", "origin")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_main_error_path(monkeypatch):
    def boom(branch_type, remote):
        raise ValueError("no release branch")
    monkeypatch.setattr(mod, "resolve_base_branch", boom)
    code, _, err = call_main(mod, ["--branch-type", "hotfix"])
    assert code == 1 and "error" in err


def test_feature_and_bugfix_resolve_to_main():
    assert mod.resolve_base_branch("feature", "origin") == "main"
    assert mod.resolve_base_branch("bugfix", "origin") == "main"


def test_hotfix_resolves_to_highest_release(monkeypatch):
    monkeypatch.setattr(mod, "list_remote_release_branches", lambda remote: ["release/5", "release/6"])
    assert mod.resolve_base_branch("hotfix", "origin") == "release/6"
    assert mod.resolve_base_branch("backport", "origin") == "release/6"


def test_hotfix_without_release_raises(monkeypatch):
    monkeypatch.setattr(mod, "list_remote_release_branches", lambda remote: [])
    try:
        mod.resolve_base_branch("hotfix", "origin")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_main_plain_and_json():
    code, out, _ = call_main(mod, ["--branch-type", "feature"])
    assert code == 0 and out.strip() == "main"
    code, out, _ = call_main(mod, ["--branch-type", "bugfix", "--json"])
    assert code == 0 and json.loads(out)["base_branch"] == "main"
