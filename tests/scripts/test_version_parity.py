"""Guard that every plugin manifest and the Cursor rule share one version.

The release tooling stamps the version into several manifests and the Cursor
adapter; nothing else guaranteed they stayed in sync. This test collects every
version holder — including the marketplace ``source.ref`` pins — and asserts
they are all identical, so a hand-edit or bad merge to one file fails the build.
"""
import json
import re

from helpers import REPO_ROOT


def _json(path: str):
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def collect_versions() -> dict[str, str]:
    versions: dict[str, str] = {}

    claude = _json(".claude-plugin/plugin.json")
    versions[".claude-plugin/plugin.json:version"] = claude["version"]

    cmkt = _json(".claude-plugin/marketplace.json")
    versions[".claude-plugin/marketplace.json:metadata.version"] = cmkt["metadata"]["version"]
    versions[".claude-plugin/marketplace.json:plugins[0].version"] = cmkt["plugins"][0]["version"]
    versions[".claude-plugin/marketplace.json:plugins[0].source.ref"] = cmkt["plugins"][0]["source"]["ref"]

    codex = _json(".codex-plugin/plugin.json")
    versions[".codex-plugin/plugin.json:version"] = codex["version"]

    amkt = _json(".agents/plugins/marketplace.json")
    versions[".agents/plugins/marketplace.json:metadata.version"] = amkt["metadata"]["version"]
    versions[".agents/plugins/marketplace.json:plugins[0].version"] = amkt["plugins"][0]["version"]
    versions[".agents/plugins/marketplace.json:plugins[0].source.ref"] = amkt["plugins"][0]["source"]["ref"]

    cursor_text = (REPO_ROOT / ".cursor/rules/mpt-extension-skills.mdc").read_text(encoding="utf-8")
    match = re.search(r"mpt-extension-skills version:\s*(\S+)", cursor_text)
    assert match, ".cursor/rules/mpt-extension-skills.mdc: version marker not found"
    versions[".cursor/rules/mpt-extension-skills.mdc"] = match.group(1)

    return versions


def test_all_manifests_share_one_version():
    versions = collect_versions()
    distinct = sorted(set(versions.values()))
    assert len(distinct) == 1, (
        "plugin version holders disagree:\n"
        + "\n".join(f"  {loc} = {ver}" for loc, ver in sorted(versions.items()))
    )
