#!/usr/bin/env python3
"""Collect a change set for the documentation-update skill.

Given a change source (unstaged, uncommitted, last commit, or a diff between
branches), list the changed files and map each changed code path to the
repository documents that the change most likely affects, following the
documentation guideline in standards/documentation.md.

The path-to-document mapping is a deterministic heuristic. It tells the skill
which documents to inspect; the skill makes the final decision about which docs
to edit and writes the prose. README.md and AGENTS.md are always surfaced for
review because behaviour/structure changes that affect them cannot be detected
from file paths alone.

Output is JSON on stdout.
"""

import argparse
import json
import subprocess
import sys
from fnmatch import fnmatch

MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


# Ordered, most-specific-first. Each rule maps glob patterns (matched against the
# changed path) to a target document and a short reason. The first matching rule
# wins for a given path. Mirrors the intent of the shared CodeRabbit gate.
MAPPING_RULES = [
    ("docs/migrations.md", "migration change", ["*/migrations/*", "migrations/*"]),
    (
        "docs/testing.md",
        "test change",
        ["*/tests/*", "tests/*", "test_*.py", "*_test.py", "conftest.py"],
    ),
    (
        "docs/deployment.md",
        "deployment/config change",
        [
            "Dockerfile",
            "*/Dockerfile",
            "compose*.yml",
            "compose*.yaml",
            ".env*",
            "*/settings.py",
            "*/settings/*.py",
            "helm/*",
            "k8s/*",
        ],
    ),
    (
        "docs/contributing.md",
        "build/CI/workflow change",
        ["Makefile", "make/*", "*.mk", ".github/workflows/*", ".pre-commit-config.yaml"],
    ),
    (
        "docs/external-integrations.md",
        "dependency/integration change",
        ["pyproject.toml", "*/pyproject.toml", "uv.lock", "*/uv.lock"],
    ),
    (
        "docs/architecture.md",
        "source code change",
        ["*.py", "frontend/*", "src/*", "backend/*"],
    ),
]

# Documents that always warrant a review decision, because the changes that
# affect them (public behaviour, repository structure, agent navigation) are not
# reliably detectable from file paths.
ALWAYS_REVIEW = ["README.md", "AGENTS.md"]

DOC_PREFIXES = ("docs/",)
DOC_FILES = {"README.md", "AGENTS.md"}


def is_doc_path(path: str) -> bool:
    return path.startswith(DOC_PREFIXES) or path in DOC_FILES


def git_diff_name_status(source: str, base: str) -> list[str]:
    if source == "unstaged":
        args = ["diff", "--name-status"]
    elif source == "uncommitted":
        args = ["diff", "--name-status", "HEAD"]
    elif source == "last-commit":
        args = ["diff", "--name-status", "HEAD~1", "HEAD"]
    elif source == "branch-diff":
        args = ["diff", "--name-status", f"{base}...HEAD"]
    else:  # pragma: no cover - argparse restricts choices
        raise ValueError(f"unknown source: {source}")

    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"error: git {' '.join(args)} failed: {result.stderr.strip()}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return [line for line in result.stdout.splitlines() if line.strip()]


def parse_changes(lines: list[str]) -> list[dict]:
    """Parse `git diff --name-status` lines into {status, path} records.

    Renames/copies (R###/C###) carry the old and new path; the new path is used.
    """
    changes = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        path = parts[-1]  # new path for renames/copies, the path otherwise
        changes.append({"status": status[:1], "path": path})
    return changes


def classify(path: str) -> tuple[str, str] | None:
    for doc, reason, patterns in MAPPING_RULES:
        if any(fnmatch(path, pattern) for pattern in patterns):
            return doc, reason
    return None


def build_report(source: str, base: str) -> dict:
    changes = parse_changes(git_diff_name_status(source, base))

    doc_changes = [c for c in changes if is_doc_path(c["path"])]
    code_changes = [c for c in changes if not is_doc_path(c["path"])]

    affected: dict[str, list[dict]] = {}
    unmapped: list[str] = []
    for change in code_changes:
        match = classify(change["path"])
        if match is None:
            unmapped.append(change["path"])
            continue
        doc, reason = match
        affected.setdefault(doc, []).append({"path": change["path"], "reason": reason})

    changed_doc_paths = {c["path"] for c in doc_changes}

    return {
        "source": source,
        "base": base if source == "branch-diff" else None,
        "changed_files": changes,
        "code_changes": code_changes,
        "doc_changes": doc_changes,
        "affected_docs": affected,
        "missing_doc_updates": sorted(set(affected) - changed_doc_paths),
        "always_review": ALWAYS_REVIEW,
        "unmapped_code": sorted(unmapped),
    }


def main() -> None:
    require_python_version()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        required=True,
        choices=["unstaged", "uncommitted", "last-commit", "branch-diff"],
        help="Which change set to collect.",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base ref for --source branch-diff (default: origin/main).",
    )
    args = parser.parse_args()
    print(json.dumps(build_report(args.source, args.base), indent=2))


if __name__ == "__main__":
    main()
