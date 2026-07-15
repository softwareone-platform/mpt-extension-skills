import json

from helpers import call_main, load

SCRIPT_UNDER_TEST = "skills/mpt-ext-task-write-documentation/scripts/audit_docs.py"
mod = load(SCRIPT_UNDER_TEST)


def test_audit_plain_repo(tmp_path):
    (tmp_path / "README.md").write_text("# Title")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "usage.md").write_text("usage")
    result = mod.audit(tmp_path)
    assert result["repo_root"] == str(tmp_path)
    assert "required" in result and "present" in result["required"]
    assert "README.md" in result["existing_docs"]
    assert "docs/usage.md" in result["existing_docs"]


def test_conditional_docs_recommended(tmp_path):
    (tmp_path / "README.md").write_text("# T")
    (tmp_path / "compose.yml").write_text("services: {}")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "migrations").mkdir()
    result = mod.audit(tmp_path)
    assert "docs/local-development.md" in result["conditional_recommended"]
    assert "docs/migrations.md" in result["conditional_recommended"]


def test_extension_repo_recommends_integration_doc(tmp_path):
    (tmp_path / "README.md").write_text("# T")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-ext"\ndependencies = ["mpt-extension-sdk>=6"]\n')
    (tmp_path / "clients").mkdir()
    (tmp_path / "clients" / "stripe_client.py").write_text("x = 1")
    result = mod.audit(tmp_path)
    assert mod.is_extension(tmp_path) is True
    assert "docs/external-integrations.md" in result["conditional_recommended"]
    assert "stripe" in mod.integration_candidates(tmp_path)
    # index absent -> coverage is None -> not attached
    assert mod.external_integration_coverage(tmp_path) is None


def test_external_integration_coverage_with_index(tmp_path):
    (tmp_path / "README.md").write_text("# T")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "my-ext"\ndependencies = ["mpt-extension-sdk>=6"]\n')
    (tmp_path / "clients").mkdir()
    (tmp_path / "clients" / "stripe_client.py").write_text("x = 1")
    (tmp_path / "clients" / "adyen_client.py").write_text("x = 1")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "external-integrations.md").write_text("We integrate with stripe.")
    result = mod.audit(tmp_path)
    assert "external_integrations" in result
    cov = result["external_integrations"]
    assert "stripe" in cov["candidates"] and "adyen" in cov["candidates"]
    assert "adyen" in cov["uncovered"] and "stripe" not in cov["uncovered"]


def test_sdk_itself_is_not_extension(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "mpt-extension-sdk"\n')
    assert mod.is_extension(tmp_path) is False


def test_repo_has_directory_and_glob(tmp_path):
    (tmp_path / "helm").mkdir()
    assert mod.repo_has(tmp_path, "helm/") is True
    assert mod.repo_has(tmp_path, "*.nope") is False


def test_main_ok_and_missing_root(tmp_path):
    (tmp_path / "README.md").write_text("# T")
    code, out, _ = call_main(mod, ["--repo-root", str(tmp_path)])
    assert code == 0 and "required" in json.loads(out)
    assert call_main(mod, ["--repo-root", str(tmp_path / "nope")])[0] == 1
