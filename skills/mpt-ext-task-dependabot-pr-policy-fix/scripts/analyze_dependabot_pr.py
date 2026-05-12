#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional


MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


DEPENDENCY_FILES = {
    ".pre-commit-config.yaml",
    ".pre-commit-config.yml",
    "pyproject.toml",
    "uv.lock",
}

DEV_SECTION_NAMES = {
    "dependency-groups",
    "dev",
    "lint",
    "test",
    "typing",
    "tool.uv",
    "tool.uv.sources",
}

PYPROJECT_DEPENDENCY_SECTIONS = {
    "dependency-groups",
    "project",
    "project.dependencies",
    "project.optional-dependencies",
    "tool.poetry.dependencies",
    "tool.poetry.group",
}

NON_DEPENDENCY_ASSIGNMENT_KEYS = {
    "authors",
    "classifiers",
    "description",
    "dynamic",
    "keywords",
    "license",
    "name",
    "readme",
    "requires-python",
    "version",
}

PACKAGE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
QUOTED_DEP_RE = re.compile(r"""["']([A-Za-z0-9][A-Za-z0-9_.-]*)\s*([<>=!~^].*?)["']""")
ASSIGNMENT_DEP_RE = re.compile(
    r"""^["']?([A-Za-z0-9][A-Za-z0-9_.-]*)["']?\s*=\s*["']([^"']+)["']"""
)
LOCK_NAME_RE = re.compile(r"""name\s*=\s*["']([^"']+)["']""")
PRE_COMMIT_RE = re.compile(r"""(?:repo:|id:|rev:|additional_dependencies:)""")
PRE_COMMIT_HOOK_ID_RE = re.compile(r"""^\s*-\s*id:\s*["']?([A-Za-z0-9][A-Za-z0-9_.-]*)["']?\s*$""")
PRE_COMMIT_ADDL_ENTRY_RE = re.compile(
    r"""(?:^\s*-\s*|^\s*\[\s*|,\s*)["']?([A-Za-z0-9][A-Za-z0-9_.-]*)["']?\s*(?:\[[^\]]*\])?\s*(?:[<>=!~^][^,\]"']*)?""",
)


def read_json(path: Optional[str], default: Any) -> Any:
    if not path:
        return default
    with Path(path).open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def read_text(path: Optional[str]) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def normalize_changed_files(raw_files: Any) -> list[str]:
    if not raw_files:
        return []
    if isinstance(raw_files, list):
        normalized = []
        for item in raw_files:
            if isinstance(item, str):
                normalized.append(item)
            elif isinstance(item, dict):
                value = item.get("path") or item.get("filename") or item.get("name")
                if value:
                    normalized.append(str(value))
        return sorted(set(normalized))
    if isinstance(raw_files, dict):
        return normalize_changed_files(raw_files.get("files") or raw_files.get("changedFiles"))
    return []


def get_author_login(metadata: dict[str, Any]) -> str:
    author = metadata.get("author")
    if isinstance(author, dict):
        return str(author.get("login") or author.get("name") or "")
    return str(author or "")


def is_dependabot(metadata: dict[str, Any]) -> bool:
    author_login = get_author_login(metadata).lower()
    head_ref = str(metadata.get("headRefName") or "").lower()
    return author_login == "dependabot[bot]" or head_ref.startswith("dependabot/")


def is_dependency_file(path: str) -> bool:
    basename = Path(path).name
    return basename in DEPENDENCY_FILES or path.endswith("/pyproject.toml")


def added_removed_diff_lines(diff_text: str) -> tuple[list[str], list[str]]:
    added = []
    removed = []
    for line in diff_text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.append(line[1:])
        elif line.startswith("-"):
            removed.append(line[1:])
    return added, removed


def extract_package_names_from_line(line: str) -> set[str]:
    names: set[str] = set()
    stripped = line.strip()
    for match in QUOTED_DEP_RE.finditer(stripped):
        names.add(match.group(1).lower())

    assignment_match = ASSIGNMENT_DEP_RE.search(stripped)
    if assignment_match:
        names.add(assignment_match.group(1).lower())

    for match in LOCK_NAME_RE.finditer(stripped):
        names.add(match.group(1).lower())
    return names


def extract_package_names(lines: list[str]) -> list[str]:
    names: set[str] = set()
    for line in lines:
        names.update(extract_package_names_from_line(line))
    return sorted(names)


def detect_opentelemetry_packages(lines: list[str]) -> list[str]:
    return sorted(name for name in extract_package_names(lines) if "opentelemetry" in name)


def detect_broad_pyproject_specifiers(lines: list[str]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    active_section = ""
    for line in lines:
        stripped = line.strip().rstrip(",")
        if not stripped or stripped.startswith("#"):
            continue

        section_match = re.fullmatch(r"\[([^\]]+)\]", stripped)
        if section_match:
            active_section = section_match.group(1).lower()
            continue

        match = QUOTED_DEP_RE.search(stripped)
        if not match:
            assignment_match = ASSIGNMENT_DEP_RE.search(stripped)
            if assignment_match and is_dependency_assignment(
                assignment_match.group(1).lower(),
                active_section,
            ):
                match = assignment_match
        if not match:
            continue

        package_name = match.group(1).lower()
        specifier = match.group(2).strip()
        if re.fullmatch(r"==\d+(?:\.\d+){1,2}(?:\.\*)?", specifier):
            continue

        if any(token in specifier for token in ("^", "~=", ">=", ">", "<", "!=", "*")):
            violations.append(
                {
                    "package": package_name,
                    "specifier": specifier,
                    "line": stripped,
                }
            )
    return violations


def is_dependency_assignment(package_name: str, active_section: str) -> bool:
    if package_name in NON_DEPENDENCY_ASSIGNMENT_KEYS:
        return False
    if not active_section:
        return True
    return any(
        active_section == section or active_section.startswith(f"{section}.")
        for section in PYPROJECT_DEPENDENCY_SECTIONS
    )


def detect_dev_dependency_indicators(lines: list[str]) -> list[str]:
    indicators: set[str] = set()
    active_section = ""
    for line in lines:
        stripped = line.strip()
        section_match = re.fullmatch(r"\[([^\]]+)\]", stripped)
        if section_match:
            active_section = section_match.group(1).lower()
            continue

        package_names = extract_package_names_from_line(stripped)
        if not package_names:
            continue

        if any(name in active_section for name in DEV_SECTION_NAMES):
            indicators.update(package_names)
        elif stripped.startswith(('"', "'")) and "dependency-groups" in active_section:
            indicators.update(package_names)
    return sorted(indicators)


def detect_pre_commit_indicators(lines: list[str]) -> bool:
    return any(PRE_COMMIT_RE.search(line) for line in lines)


def extract_pre_commit_pinned_packages(text: str) -> set[str]:
    """Extract package names pinned in a .pre-commit-config.yaml file.

    Covers two sources of pinning:
    - hook `id:` entries, which usually match the tool's package name
      (for example `id: mypy`, `id: flake8`).
    - `additional_dependencies:` list entries, which pin specific package
      versions for hooks like mirrors-mypy.
    """
    pinned: set[str] = set()
    in_addl_block = False
    addl_indent: Optional[int] = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())

        hook_id_match = PRE_COMMIT_HOOK_ID_RE.match(line)
        if hook_id_match:
            pinned.add(hook_id_match.group(1).lower())

        stripped = line.strip()
        if stripped.startswith("additional_dependencies:"):
            in_addl_block = True
            addl_indent = indent
            inline = stripped[len("additional_dependencies:"):].strip()
            if inline:
                for match in PRE_COMMIT_ADDL_ENTRY_RE.finditer(inline):
                    pinned.add(match.group(1).lower())
                if inline.endswith("]"):
                    in_addl_block = False
                    addl_indent = None
            continue

        if in_addl_block:
            if addl_indent is not None and indent <= addl_indent and not stripped.startswith("-"):
                in_addl_block = False
                addl_indent = None
            else:
                for match in PRE_COMMIT_ADDL_ENTRY_RE.finditer(stripped):
                    pinned.add(match.group(1).lower())
                if stripped.endswith("]"):
                    in_addl_block = False
                    addl_indent = None
                continue
    return {name for name in pinned if name}


def detect_pre_commit_pins_to_sync(
    changed_packages: set[str],
    pre_commit_text: str,
) -> list[str]:
    if not pre_commit_text or not changed_packages:
        return []
    pinned = extract_pre_commit_pinned_packages(pre_commit_text)
    return sorted(pkg for pkg in changed_packages if pkg in pinned)


def build_analysis(
    metadata: dict[str, Any],
    changed_files: list[str],
    diff_text: str,
    pre_commit_text: str = "",
) -> dict[str, Any]:
    added_lines, removed_lines = added_removed_diff_lines(diff_text)
    changed_dependency_files = [path for path in changed_files if is_dependency_file(path)]
    all_changed_lines = added_lines + removed_lines
    added_pyproject_lines = [
        line
        for line in added_lines
        if any(token in line for token in ("=", "dependencies", "dependency-groups"))
    ]
    added_pre_commit_lines = [
        line
        for line in added_lines
        if "pre-commit" in line or PRE_COMMIT_RE.search(line)
    ]

    dependabot = is_dependabot(metadata)
    dependency_related = bool(changed_dependency_files)
    dev_dependency_indicators = detect_dev_dependency_indicators(added_pyproject_lines)
    opentelemetry_packages = detect_opentelemetry_packages(all_changed_lines)
    pyproject_policy_violations = detect_broad_pyproject_specifiers(added_pyproject_lines)
    pre_commit_changed = any(
        Path(path).name in {".pre-commit-config.yaml", ".pre-commit-config.yml"}
        for path in changed_files
    ) or detect_pre_commit_indicators(added_pre_commit_lines)

    changed_packages = set(extract_package_names(all_changed_lines))
    pre_commit_pins_to_sync = detect_pre_commit_pins_to_sync(
        changed_packages,
        pre_commit_text,
    )

    pre_commit_sync_needed = (
        bool(dev_dependency_indicators) or bool(pre_commit_pins_to_sync)
    ) and not pre_commit_changed

    skip_reason = ""
    if not dependabot:
        skip_reason = "PR is not authored by Dependabot and does not use a Dependabot head branch."
    elif not dependency_related:
        skip_reason = "PR does not change dependency-related files."
    elif not (
        opentelemetry_packages
        or pyproject_policy_violations
        or dev_dependency_indicators
        or pre_commit_pins_to_sync
    ):
        skip_reason = "No deterministic dependency policy issue was detected."

    return {
        "number": metadata.get("number"),
        "title": metadata.get("title"),
        "url": metadata.get("url"),
        "author": get_author_login(metadata),
        "head_ref": metadata.get("headRefName"),
        "base_ref": metadata.get("baseRefName"),
        "is_dependabot": dependabot,
        "is_dependency_related": dependency_related,
        "changed_files": changed_files,
        "changed_dependency_files": changed_dependency_files,
        "opentelemetry_packages": opentelemetry_packages,
        "dev_dependency_indicators": dev_dependency_indicators,
        "pre_commit_changed": pre_commit_changed,
        "pre_commit_pins_to_sync": pre_commit_pins_to_sync,
        "pre_commit_sync_needed": pre_commit_sync_needed,
        "pyproject_policy_violations": pyproject_policy_violations,
        "skip_reason": skip_reason,
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Analyze a Dependabot PR for deterministic dependency policy signals."
    )
    parser.add_argument("--metadata-json", required=True, help="PR metadata JSON file")
    parser.add_argument(
        "--changed-files-json",
        help="JSON file containing changed file paths or gh files output",
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed file path; may be provided multiple times",
    )
    parser.add_argument("--diff-file", required=True, help="PR diff file")
    parser.add_argument(
        "--pre-commit-config",
        help=(
            "Path to the current .pre-commit-config.yaml on the checked-out branch. "
            "Used to detect runtime/dev deps pinned in hook rev/additional_dependencies "
            "that must be synced when Dependabot bumps the underlying package."
        ),
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    metadata = read_json(args.metadata_json, {})
    if not isinstance(metadata, dict):
        print("error: --metadata-json must contain a JSON object", file=sys.stderr)
        return 1

    changed_files_json = read_json(args.changed_files_json, [])
    changed_files = normalize_changed_files(changed_files_json)
    changed_files.extend(args.changed_file)
    changed_files = sorted(set(changed_files))

    diff_text = read_text(args.diff_file)
    pre_commit_text = read_text(args.pre_commit_config) if args.pre_commit_config else ""
    analysis = build_analysis(metadata, changed_files, diff_text, pre_commit_text)
    json.dump(analysis, sys.stdout, indent=2 if args.pretty else None, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
