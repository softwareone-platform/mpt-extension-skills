import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-dependabot-pr-policy-fix/scripts/analyze_dependabot_pr.py"
mod = load(SCRIPT_UNDER_TEST)


def test_author_and_dependabot_detection():
    assert mod.get_author_login({"author": {"login": "dependabot[bot]"}}) == "dependabot[bot]"
    assert mod.get_author_login({"author": "someone"}) == "someone"
    assert mod.is_dependabot({"author": {"login": "dependabot[bot]"}})
    assert mod.is_dependabot({"headRefName": "dependabot/pip/x"})
    assert not mod.is_dependabot({"author": {"login": "human"}, "headRefName": "feature/x"})


def test_dependency_file_and_normalize():
    assert mod.is_dependency_file("uv.lock")
    assert mod.is_dependency_file("pkg/pyproject.toml")
    assert not mod.is_dependency_file("src/app.py")
    assert mod.normalize_changed_files(["a", "b"]) == ["a", "b"]
    assert mod.normalize_changed_files("not-a-list") == []
    assert mod.normalize_changed_files([{"path": "x.py"}, {"filename": "y.py"}]) == ["x.py", "y.py"]
    assert mod.normalize_changed_files({"files": ["z.py"]}) == ["z.py"]
    assert mod.get_author_login({}) == ""


def test_diff_and_package_extraction():
    added, removed = mod.added_removed_diff_lines("+opentelemetry-api==1.0\n-requests==2.0\n context\n")
    assert any("opentelemetry" in line for line in added)
    assert any("requests" in line for line in removed)
    assert "requests" in mod.extract_package_names_from_line('"requests>=2.0"')
    assert mod.detect_opentelemetry_packages(['"opentelemetry-api>=1.0"']) == ["opentelemetry-api"]
    violations = mod.detect_broad_pyproject_specifiers(['"requests>=2.0"'])
    assert any(v["package"] == "requests" for v in violations)


PYPROJECT_DIFF = "\n".join([
    "[project]",
    "dependencies = [",
    '    "requests>=2.0",',
    '    "urllib3==2.0.0",',
    "]",
    "[dependency-groups]",
    'dev = [',
    '    "pytest>=8",',
    "]",
    "# a comment",
    "",
])


def test_broad_specifier_detection():
    lines = PYPROJECT_DIFF.splitlines()
    violations = mod.detect_broad_pyproject_specifiers(lines)
    assert any(v["package"] == "requests" for v in violations)
    assert all(v["package"] != "urllib3" for v in violations)  # pinned is fine


def test_is_dependency_assignment():
    assert mod.is_dependency_assignment("requests", "") is True
    assert mod.is_dependency_assignment("requests", "project.optional-dependencies") in (True, False)
    for key in mod.NON_DEPENDENCY_ASSIGNMENT_KEYS:
        assert mod.is_dependency_assignment(key, "project") is False
        break


def test_dev_indicators_and_pre_commit():
    assert "pytest" in mod.detect_dev_dependency_indicators(PYPROJECT_DIFF.splitlines())
    assert mod.detect_pre_commit_indicators(["rev: v1.2.3"]) is True
    assert mod.detect_pre_commit_indicators(["nothing here"]) is False


def test_build_analysis_skip_reasons(tmp_path):
    # not dependabot
    a = mod.build_analysis({"author": {"login": "human"}, "headRefName": "feature/x"}, [], "")
    assert a["skip_reason"]
    # dependabot but no dependency files
    a = mod.build_analysis({"author": {"login": "dependabot[bot]"}}, ["src/app.py"], "+print()\n")
    assert a["skip_reason"]


def test_main_dependabot_and_human(tmp_path):
    meta = tmp_path / "m.json"
    diff = tmp_path / "d.txt"
    meta.write_text(json.dumps({"number": 1, "title": "Bump requests", "author": {"login": "dependabot[bot]"}, "headRefName": "dependabot/pip/requests", "baseRefName": "main"}))
    diff.write_text("--- a/uv.lock\n+++ b/uv.lock\n+requests==2.32.0\n")
    code, out, _ = call_main(mod, ["--metadata-json", str(meta), "--diff-file", str(diff), "--changed-file", "uv.lock", "--pretty"])
    assert code == 0
    data = json.loads(out)
    assert data["is_dependabot"] is True
    assert "changed_files" in data

    meta.write_text(json.dumps({"number": 2, "author": {"login": "human"}, "headRefName": "feature/x", "baseRefName": "main"}))
    code, out, _ = call_main(mod, ["--metadata-json", str(meta), "--diff-file", str(diff)])
    assert code == 0 and json.loads(out)["is_dependabot"] is False


def test_main_non_object_metadata_errors(tmp_path):
    meta = tmp_path / "m.json"
    diff = tmp_path / "d.txt"
    meta.write_text("[]")
    diff.write_text("")
    assert call_main(mod, ["--metadata-json", str(meta), "--diff-file", str(diff)])[0] == 1
