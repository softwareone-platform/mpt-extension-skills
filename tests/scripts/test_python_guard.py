"""Enforce a single, identical Python runtime guard across all skill scripts.

Skill scripts are self-contained and installed independently, so the guard
cannot be imported from a shared module. Instead of hand-maintaining ~13
copies, this test pins the canonical guard: every script must declare
MIN_PYTHON = (3, 12), define require_python_version() with the exact message,
and call it. Drift (a different minimum version, a changed message, or a
missing guard) fails the suite.
"""
import pytest

from helpers import REPO_ROOT

GUARD_LINES = [
    "MIN_PYTHON = (3, 12)",
    "def require_python_version() -> None:",
    "if sys.version_info < MIN_PYTHON:",
    'print("error: Python 3.12 or later is required", file=sys.stderr)',
    "raise SystemExit(1)",
]


def _skill_scripts():
    scripts = (REPO_ROOT / "skills").glob("*/scripts/*.py")
    return sorted(p for p in scripts if "__pycache__" not in p.parts)


@pytest.mark.parametrize(
    "script", _skill_scripts(), ids=lambda p: str(p.relative_to(REPO_ROOT))
)
def test_script_has_canonical_python_guard(script):
    text = script.read_text(encoding="utf-8")
    for line in GUARD_LINES:
        assert line in text, f"{script.relative_to(REPO_ROOT)} missing guard line: {line!r}"
    # The guard must be invoked, not only defined (definition + at least one call).
    assert text.count("require_python_version()") >= 2, (
        f"{script.relative_to(REPO_ROOT)} does not call require_python_version()"
    )
