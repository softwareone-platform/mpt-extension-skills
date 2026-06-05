#!/usr/bin/env python3
"""Report the token-budget footprint of skills in this repository.

Skills are consumed by two runtimes, each with an always-on surface (loaded
every session, whether or not the skill is used) and a per-invocation surface
(loaded only when the skill runs):

- Claude reads ``SKILL.md``: the frontmatter ``description`` is always-on, the
  body is per-invocation.
- Codex/OpenAI reads ``agents/openai.yaml``: ``short_description`` is always-on,
  ``default_prompt`` is per-invocation.

This script prints all four per skill, flags fields over the limits in
``standards/skills.md``, and exits non-zero in ``--check`` mode when any gated
field is over budget. It has no third-party dependencies.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)

# Word limits from standards/skills.md. The always-on surfaces (SKILL.md
# description, openai.yaml short_description) are kept tightest; the
# per-invocation default_prompt has more room. A small margin is allowed before
# --check fails.
DESCRIPTION_WORD_LIMIT = 35
SHORT_DESCRIPTION_WORD_LIMIT = 15
DEFAULT_PROMPT_WORD_LIMIT = 50


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def _reject_multiline(value: str, path: Path, field: str) -> str:
    """Fail loudly on multi-line YAML scalars instead of mis-measuring them.

    The line-based reader supports only single-line values. A folded (``>``),
    literal (``|``), or empty-then-indented value would otherwise be counted as
    1 or 0 words and pass the budget check incorrectly, so reject it.
    """
    if value in (">", "|", ""):
        print(
            f"error: {path}: multi-line or empty YAML value for '{field}' is not "
            f"supported; use a single-line string.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return value


def read_frontmatter_description(skill_md: Path) -> str:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index in range(1, len(lines)):
        stripped = lines[index].strip()
        if stripped == "---":
            break
        if stripped.startswith("description:"):
            value = stripped[len("description:"):].strip()
            return _reject_multiline(value, skill_md, "description")
    return ""


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def read_openai_field(openai_yaml: Path, key: str) -> str:
    """Read a single-line ``interface`` field from openai.yaml.

    The shared standard defines these as single-line scalars, so a line-based
    read avoids a YAML dependency. Multi-line scalars are rejected rather than
    silently mis-measured.
    """
    if not openai_yaml.is_file():
        return ""
    prefix = f"{key}:"
    for line in openai_yaml.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(prefix):
            raw = line.strip()[len(prefix):].strip()
            return _reject_multiline(_unquote(raw), openai_yaml, key)
    return ""


def iter_skill_dirs(skills_root: Path):
    for child in sorted(skills_root.iterdir()):
        if (child / "SKILL.md").is_file():
            yield child


def main() -> int:
    require_python_version()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skills-root",
        default=str(Path(__file__).resolve().parent.parent / "skills"),
        help="Path to the skills/ directory (default: repo skills/).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if any gated field exceeds its word limit.",
    )
    args = parser.parse_args()

    skills_root = Path(args.skills_root)
    if not skills_root.is_dir():
        print(f"error: skills root not found: {skills_root}", file=sys.stderr)
        return 1

    desc_total = body_total = short_total = prompt_total = 0
    over_limit: list[tuple[str, str, int, int]] = []  # (skill, field, words, limit)

    header = (
        f"{'desc':>5} {'body':>7} | {'short':>5} {'prompt':>6}  skill"
    )
    print("        SKILL.md (Claude) | openai.yaml (Codex)")
    print(header)
    print(f"{'-' * 5} {'-' * 7} | {'-' * 5} {'-' * 6}  {'-' * 5}")
    for skill_dir in iter_skill_dirs(skills_root):
        skill_md = skill_dir / "SKILL.md"
        openai_yaml = skill_dir / "agents" / "openai.yaml"

        desc_words = len(read_frontmatter_description(skill_md).split())
        body_chars = len(skill_md.read_text(encoding="utf-8"))
        short_words = len(read_openai_field(openai_yaml, "short_description").split())
        prompt_words = len(read_openai_field(openai_yaml, "default_prompt").split())

        desc_total += desc_words
        body_total += body_chars
        short_total += short_words
        prompt_total += prompt_words

        flags = []
        if desc_words > DESCRIPTION_WORD_LIMIT:
            over_limit.append((skill_dir.name, "description", desc_words, DESCRIPTION_WORD_LIMIT))
            flags.append("desc")
        if short_words > SHORT_DESCRIPTION_WORD_LIMIT:
            over_limit.append((skill_dir.name, "short_description", short_words, SHORT_DESCRIPTION_WORD_LIMIT))
            flags.append("short")
        if prompt_words > DEFAULT_PROMPT_WORD_LIMIT:
            over_limit.append((skill_dir.name, "default_prompt", prompt_words, DEFAULT_PROMPT_WORD_LIMIT))
            flags.append("prompt")
        flag = f"  <-- over: {', '.join(flags)}" if flags else ""

        print(
            f"{desc_words:>5} {body_chars:>7} | {short_words:>5} {prompt_words:>6}  "
            f"{skill_dir.name}{flag}"
        )

    print(f"{'-' * 5} {'-' * 7} | {'-' * 5} {'-' * 6}  {'-' * 5}")
    print(f"{desc_total:>5} {body_total:>7} | {short_total:>5} {prompt_total:>6}  TOTAL")
    print()
    print(
        "Limits (words, from standards/skills.md): "
        f"description={DESCRIPTION_WORD_LIMIT}, "
        f"short_description={SHORT_DESCRIPTION_WORD_LIMIT}, "
        f"default_prompt={DEFAULT_PROMPT_WORD_LIMIT}. "
        f"Over limit: {len(over_limit)}."
    )

    if args.check and over_limit:
        print("\nFields over the word limit:", file=sys.stderr)
        for name, field, words, limit in over_limit:
            print(f"  {words} words (limit {limit})  {name} [{field}]", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
