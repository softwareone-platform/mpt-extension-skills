"""Keep skill_token_budget.py word limits in sync with standards/skills.md.

The budget script hardcodes the per-field word limits and its output claims they
come from standards/skills.md. This test parses the limits declared in the
standard and asserts the script constants match, so the two never drift (the
description limit was 30 in the standard but 35 in the script before MPT-23287).
"""
import re

from helpers import REPO_ROOT, load

budget = load("scripts/skill_token_budget.py")


def _declared_limit(field: str) -> int:
    text = (REPO_ROOT / "standards" / "skills.md").read_text(encoding="utf-8")
    match = re.search(rf"`{re.escape(field)}`\s+(\d+)\s+words", text)
    assert match, f"standards/skills.md does not declare a word limit for `{field}`"
    return int(match.group(1))


def test_description_limit_matches_standard():
    assert budget.DESCRIPTION_WORD_LIMIT == _declared_limit("description")


def test_short_description_limit_matches_standard():
    assert budget.SHORT_DESCRIPTION_WORD_LIMIT == _declared_limit("short_description")


def test_default_prompt_limit_matches_standard():
    assert budget.DEFAULT_PROMPT_WORD_LIMIT == _declared_limit("default_prompt")
