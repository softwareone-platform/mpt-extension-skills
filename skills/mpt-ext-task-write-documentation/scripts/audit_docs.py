#!/usr/bin/env python3
"""Audit a repository's documentation set against the documentation guideline.

Reports which required documents exist or are missing, which conditional
documents are recommended based on repository signals (e.g. a migrations
directory, a Dockerfile, an e2e suite), and which documents already exist.

The required and conditional sets and the recommendation signals mirror
standards/documentation.md. This is a deterministic presence/signal check; the
write-documentation skill decides what to author and writes the content.

Output is JSON on stdout.
"""

import argparse
import json
import sys
from pathlib import Path

MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


# Minimal required documentation set (standards/documentation.md, Rule 2).
REQUIRED_DOCS = [
    "README.md",
    "AGENTS.md",
    "docs/architecture.md",
    "docs/contributing.md",
    "docs/testing.md",
]

# Conditional documents and the repository signals that recommend them
# (standards/documentation.md, Rule 3 and Recommended Structure). Each signal is
# a list of glob patterns checked against the repository tree.
CONDITIONAL_DOCS = {
    "docs/local-development.md": ["compose*.y*ml", "Dockerfile", "*/Dockerfile"],
    "docs/deployment.md": [
        "helm/**",
        "k8s/**",
        "compose*prod*.yml",
        "compose*prod*.yaml",
    ],
    "docs/migrations.md": ["**/migrations/", "migrations/"],
    "docs/e2e.md": ["**/e2e/", "e2e/", "**/tests/e2e/"],
    "docs/external-integrations.md": [],  # judgement call; never auto-recommended
    "docs/documentation.md": [],  # optional repository documentation guideline
}


def repo_has(root: Path, pattern: str) -> bool:
    if pattern.endswith("/"):
        # Directory signal: match the full relative directory path, not just the
        # basename, so "**/tests/e2e/" does not match an unrelated "foo/e2e".
        target = pattern.rstrip("/")
        return any(p.is_dir() for p in root.glob(target))
    return any(root.glob(pattern))


def audit(root: Path) -> dict:
    present_required = [d for d in REQUIRED_DOCS if (root / d).is_file()]
    missing_required = [d for d in REQUIRED_DOCS if not (root / d).is_file()]

    recommended = []
    for doc, signals in CONDITIONAL_DOCS.items():
        if (root / doc).is_file():
            continue
        if signals and any(repo_has(root, sig) for sig in signals):
            recommended.append(doc)

    existing_docs = sorted(
        str(p.relative_to(root))
        for p in (root / "docs").glob("*.md")
        if (root / "docs").is_dir()
    )
    for top in ("README.md", "AGENTS.md"):
        if (root / top).is_file():
            existing_docs.append(top)

    return {
        "repo_root": str(root),
        "required": {"present": present_required, "missing": missing_required},
        "conditional_recommended": sorted(recommended),
        "existing_docs": sorted(set(existing_docs)),
    }


def main() -> None:
    require_python_version()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root to audit (default: current directory).",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    if not root.is_dir():
        print(f"error: repo root not found: {root}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps(audit(root), indent=2))


if __name__ == "__main__":
    main()
