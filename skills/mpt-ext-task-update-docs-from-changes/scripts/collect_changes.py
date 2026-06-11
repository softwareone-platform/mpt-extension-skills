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
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


# --- Change->document mapping ------------------------------------------------
#
# Path-only rules: the changed path alone maps it to a document. Ordered,
# most-specific-first; the first matching rule wins for a given path.
# Keep aligned with the shared CodeRabbit gate ("Documentation Up To Date" in
# coderabbit-shared.yaml), which restates this mapping in prose for review.
PATH_RULES = [
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
        "build/dev-tooling change",
        ["Makefile", "make/*", "*.mk", ".pre-commit-config.yaml"],
    ),
    # A new dependency can introduce a new integration; a lockfile refresh
    # (uv.lock) is churn, so it is deliberately excluded to avoid false positives.
    (
        "docs/external-integrations.md",
        "dependency/integration change",
        ["pyproject.toml", "*/pyproject.toml"],
    ),
]

# Architecture is mapped separately. A modified line inside an existing module
# is rarely an architecture change, but adding or removing a module, or touching
# a structural entry point, is. Mapping every modified *.py to architecture.md
# floods missing_doc_updates and trains reviewers to ignore it, so architecture
# requires a structural signal: a structural path, or an added/deleted code
# module. Plain modifications fall through to unmapped_code for a manual call.
ARCH_DOC = "docs/architecture.md"
ARCH_STRUCTURAL_PATTERNS = [
    "app.py",
    "*/app.py",
    "router.py",
    "*/router.py",
    "routing/*",
    "*/routing/*",
    "routers/*",
    "*/routers/*",
    "__init__.py",
    "*/__init__.py",
]
ARCH_CODE_PATTERNS = ["*.py", "*.ts", "*.tsx", "*.js", "*.jsx"]

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
    """Parse `git diff --name-status` lines into {status, path, old_path} records.

    Renames/copies (R###/C###) carry the old and new path; the new path is used
    as `path` and the source path is kept as `old_path` so removed-path
    references can be detected.
    """
    changes = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0][:1]
        if status in {"R", "C"} and len(parts) >= 3:
            old_path, path = parts[1], parts[2]
        else:
            old_path, path = None, parts[-1]
        changes.append({"status": status, "path": path, "old_path": old_path})
    return changes


def classify(change: dict) -> tuple[str, str] | None:
    path = change["path"]
    for doc, reason, patterns in PATH_RULES:
        if any(fnmatch(path, pattern) for pattern in patterns):
            return doc, reason
    if any(fnmatch(path, pattern) for pattern in ARCH_STRUCTURAL_PATTERNS):
        return ARCH_DOC, "structural source change"
    if change["status"] in {"A", "D"} and any(
        fnmatch(path, pattern) for pattern in ARCH_CODE_PATTERNS
    ):
        verb = "module added" if change["status"] == "A" else "module removed"
        return ARCH_DOC, f"source {verb}"
    return None


def existing_docs_on_disk() -> list[str]:
    """Repository documents present on disk (docs/**/*.md plus README/AGENTS)."""
    out: list[str] = []
    docs_dir = Path("docs")
    if docs_dir.is_dir():
        out += [str(p) for p in docs_dir.glob("**/*.md")]
    for top in ("README.md", "AGENTS.md"):
        if Path(top).is_file():
            out.append(top)
    return sorted(set(out))


def find_stale_doc_references(removed_paths: list[str]) -> list[dict]:
    """Existing docs that still reference a path removed in this change set.

    A removed module or asset whose name still appears in the docs is a likely
    stale reference. Matches the full relative path or the bare filename as a
    whole token; the skill confirms each before editing.
    """
    if not removed_paths:
        return []
    results: list[dict] = []
    for doc in existing_docs_on_disk():
        try:
            text = Path(doc).read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for removed in removed_paths:
            base = removed.rsplit("/", 1)[-1]
            hit = removed in text or (
                bool(base)
                and re.search(rf"(?<![\w./]){re.escape(base)}(?![\w])", text) is not None
            )
            if hit:
                results.append({"doc": doc, "removed_path": removed})
    return results


def build_report(source: str, base: str) -> dict:
    changes = parse_changes(git_diff_name_status(source, base))

    doc_changes = [c for c in changes if is_doc_path(c["path"])]
    code_changes = [c for c in changes if not is_doc_path(c["path"])]

    affected: dict[str, list[dict]] = {}
    unmapped: list[str] = []
    for change in code_changes:
        match = classify(change)
        if match is None:
            unmapped.append(change["path"])
            continue
        doc, reason = match
        affected.setdefault(doc, []).append({"path": change["path"], "reason": reason})

    changed_doc_paths = {c["path"] for c in doc_changes}

    removed_paths = sorted(
        {c["path"] for c in code_changes if c["status"] == "D"}
        | {c["old_path"] for c in code_changes if c["status"] == "R" and c["old_path"]}
    )

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
        "removed_paths": removed_paths,
        "stale_doc_references": find_stale_doc_references(removed_paths),
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
