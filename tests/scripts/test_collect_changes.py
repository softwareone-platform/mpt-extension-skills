import json
import subprocess

import pytest

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-update-docs-from-changes/scripts/collect_changes.py"
mod = load(SCRIPT_UNDER_TEST)


def test_is_doc_path():
    assert mod.is_doc_path("docs/usage.md")
    assert mod.is_doc_path("README.md")
    assert not mod.is_doc_path("src/app.py")


def test_parse_changes_plain_and_rename():
    assert mod.parse_changes(["M\tdocs/a.md"]) == [{"status": "M", "path": "docs/a.md", "old_path": None}]
    renamed = mod.parse_changes(["R100\tdocs/old.md\tdocs/new.md"])[0]
    assert renamed["status"] == "R" and renamed["path"] == "docs/new.md" and renamed["old_path"] == "docs/old.md"


def test_classify_branches():
    assert mod.classify({"status": "M", "path": "app/migrations/0001.py", "old_path": None})[0] == "docs/migrations.md"
    assert mod.classify({"status": "M", "path": "pyproject.toml", "old_path": None}) is not None
    assert mod.classify({"status": "M", "path": "assets/logo.png", "old_path": None}) is None
    added = mod.classify({"status": "A", "path": "src/newmod.py", "old_path": None})
    assert added == (mod.ARCH_DOC, "structural source change") or added[0] == mod.ARCH_DOC
    deleted = mod.classify({"status": "D", "path": "lib/gone.py", "old_path": None})
    assert deleted[0] == mod.ARCH_DOC


def test_git_diff_name_status_sources(monkeypatch):
    seen = {}

    def fake_run(args, capture_output, text):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="M\tdocs/x.md\n", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    assert mod.git_diff_name_status("unstaged", "origin/main") == ["M\tdocs/x.md"]
    assert seen["args"] == ["git", "diff", "--name-status"]
    mod.git_diff_name_status("uncommitted", "origin/main")
    assert seen["args"] == ["git", "diff", "--name-status", "HEAD"]
    mod.git_diff_name_status("last-commit", "origin/main")
    assert seen["args"] == ["git", "diff", "--name-status", "HEAD~1", "HEAD"]
    mod.git_diff_name_status("branch-diff", "origin/main")
    assert seen["args"] == ["git", "diff", "--name-status", "origin/main...HEAD"]


def test_git_diff_name_status_error(monkeypatch):
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 1, stdout="", stderr="boom"))
    with pytest.raises(SystemExit) as excinfo:
        mod.git_diff_name_status("unstaged", "origin/main")
    assert excinfo.value.code == 1


def test_git_untracked_files(monkeypatch):
    seen = {}

    def fake_run(args, capture_output, text):
        seen["args"] = args
        return subprocess.CompletedProcess(args, 0, stdout="skills/new/scripts/run.py\n\n", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    result = mod.git_untracked_files()

    assert result == ["skills/new/scripts/run.py"]
    assert seen["args"] == ["git", "ls-files", "--others", "--exclude-standard", "--full-name", "--", ":/"]


def test_untracked_changes_skips_paths_already_in_the_diff(monkeypatch):
    monkeypatch.setattr(mod, "git_untracked_files", lambda: ["src/new.py", "src/known.py"])

    result = mod.untracked_changes({"src/known.py"})

    assert result == [{"status": "A", "path": "src/new.py", "old_path": None}]


def test_find_stale_doc_references(tmp_path, monkeypatch):
    assert mod.find_stale_doc_references([]) == []
    doc = tmp_path / "d.md"
    doc.write_text("see gone.py for details")
    missing = tmp_path / "missing.md"
    monkeypatch.setattr(mod, "existing_docs_on_disk", lambda: [str(doc), str(missing)])
    hits = mod.find_stale_doc_references(["lib/gone.py"])
    assert any(h["removed_path"] == "lib/gone.py" for h in hits)


def test_existing_docs_on_disk_runs():
    assert isinstance(mod.existing_docs_on_disk(), list)


def test_build_report_and_main(monkeypatch):
    monkeypatch.setattr(mod, "git_diff_name_status", lambda s, b: ["M\tdocs/usage.md", "A\tsrc/app.py", "D\tlib/gone.py"])
    monkeypatch.setattr(mod, "git_untracked_files", lambda: [])
    monkeypatch.setattr(mod, "existing_docs_on_disk", lambda: [])
    report = mod.build_report("branch-diff", "origin/main")
    assert report["source"] == "branch-diff"
    assert report["base"] == "origin/main"
    assert "lib/gone.py" in report["removed_paths"]

    code, out, _ = call_main(mod, ["--source", "unstaged"])
    assert code == 0 and json.loads(out)["source"] == "unstaged"


@pytest.mark.parametrize("source", ["unstaged", "uncommitted"])
def test_build_report_collects_untracked_files_as_added(monkeypatch, source):
    monkeypatch.setattr(mod, "git_diff_name_status", lambda s, b: [])
    monkeypatch.setattr(mod, "git_untracked_files", lambda: ["src/newmod.py"])
    monkeypatch.setattr(mod, "existing_docs_on_disk", lambda: [])
    added = [{"status": "A", "path": "src/newmod.py", "old_path": None}]

    report = mod.build_report(source, "origin/main")

    assert (report["changed_files"], report["code_changes"]) == (added, added)


@pytest.mark.parametrize("source", ["unstaged", "uncommitted"])
def test_build_report_maps_untracked_files_to_docs(monkeypatch, source):
    monkeypatch.setattr(mod, "git_diff_name_status", lambda s, b: [])
    monkeypatch.setattr(mod, "git_untracked_files", lambda: ["src/newmod.py"])
    monkeypatch.setattr(mod, "existing_docs_on_disk", lambda: [])

    report = mod.build_report(source, "origin/main")

    assert report["affected_docs"] == {
        mod.ARCH_DOC: [{"path": "src/newmod.py", "reason": "source module added"}],
    }


def test_build_report_ignores_untracked_files_for_history_sources(monkeypatch):
    monkeypatch.setattr(mod, "git_diff_name_status", lambda s, b: [])
    monkeypatch.setattr(mod, "git_untracked_files", lambda: ["src/newmod.py"])
    monkeypatch.setattr(mod, "existing_docs_on_disk", lambda: [])

    report = mod.build_report("last-commit", "origin/main")

    assert report["changed_files"] == []
