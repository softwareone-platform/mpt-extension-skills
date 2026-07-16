"""Structural lint for skills: SKILL.md frontmatter, sections, and adapter.

Every skill under ``skills/<name>/`` must have:
- a ``SKILL.md`` whose YAML frontmatter matches ``schemas/skill_frontmatter.schema.json``
  (parsed with python-frontmatter, validated with jsonschema),
- the body sections required by ``standards/skills.md``, and
- an ``agents/openai.yaml`` adapter with the three interface fields.

This closes the gap where a skill with malformed frontmatter, a missing section,
or a missing/empty adapter would still pass the token-budget check.
"""
import json
import re

import frontmatter
import jsonschema
import pytest
import yaml

from helpers import REPO_ROOT

REQUIRED_SECTIONS = [
    "## Purpose",
    "## Use When",
    "## Do Not Use When",
    "## Workflow",
    "## Guardrails",
    "## Expected Outcome",
]
ADAPTER_FIELDS = ["display_name", "short_description", "default_prompt"]

_SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "skill_frontmatter.schema.json").read_text(encoding="utf-8")
)


def _skill_dirs():
    # Every directory under skills/ is a skill; do not filter by SKILL.md presence,
    # otherwise a skill directory missing SKILL.md would be silently skipped instead
    # of failing the lint.
    return sorted(
        p
        for p in (REPO_ROOT / "skills").iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def _headings(text):
    """Return the set of actual Markdown heading lines, excluding fenced code blocks.

    A required section must be a real ``#``-prefixed heading line, not a substring
    of prose (``## Purposeful``) or a heading embedded in an example code fence.
    """
    without_fences = re.sub(r"^```.*?^```", "", text, flags=re.DOTALL | re.MULTILINE)
    return {
        line.strip()
        for line in without_fences.splitlines()
        if line.lstrip().startswith("#")
    }


@pytest.mark.parametrize("skill", _skill_dirs(), ids=lambda p: p.name)
def test_skill_frontmatter_matches_schema(skill):
    skill_md = skill / "SKILL.md"
    assert skill_md.is_file(), f"{skill.name}: missing SKILL.md"
    meta = frontmatter.load(str(skill_md)).metadata
    jsonschema.validate(instance=meta, schema=_SCHEMA)
    assert meta["name"] == skill.name, (
        f"{skill.name}: frontmatter name {meta['name']!r} must match the directory name"
    )


@pytest.mark.parametrize("skill", _skill_dirs(), ids=lambda p: p.name)
def test_skill_md_has_required_sections(skill):
    headings = _headings((skill / "SKILL.md").read_text(encoding="utf-8"))
    for heading in REQUIRED_SECTIONS:
        assert heading in headings, f"{skill.name}: SKILL.md missing section {heading!r}"
    # Inputs or Prerequisites (either heading is allowed by the standard).
    assert ("## Inputs" in headings) or ("## Prerequisites" in headings), (
        f"{skill.name}: SKILL.md missing an Inputs/Prerequisites section"
    )


@pytest.mark.parametrize("skill", _skill_dirs(), ids=lambda p: p.name)
def test_skill_has_valid_openai_adapter(skill):
    adapter = skill / "agents" / "openai.yaml"
    assert adapter.is_file(), f"{skill.name}: missing agents/openai.yaml adapter"
    data = yaml.safe_load(adapter.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{skill.name}: openai.yaml is not a mapping"
    interface = data.get("interface")
    assert isinstance(interface, dict), f"{skill.name}: openai.yaml missing interface mapping"
    for field in ADAPTER_FIELDS:
        value = interface.get(field)
        assert isinstance(value, str) and value.strip(), (
            f"{skill.name}: openai.yaml interface.{field} must be a non-empty string"
        )
