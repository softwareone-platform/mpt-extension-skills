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
import re
import sys
import tomllib
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
    "docs/documentation.md": [],  # optional repository documentation guideline
}

# Recommended for MPT extensions specifically (they almost always integrate with
# external systems). Handled via the is_extension() signal below rather than a
# path glob, because there is no single file path that marks an integration.
EXTENSION_DOC = "docs/external-integrations.md"

# Directory names whose immediate children are treated as integration modules.
# `swo` is the platform convention for grouping per-service clients
# (e.g. swo/<service>/), alongside the generic clients/ and integrations/.
INTEGRATION_PARENT_DIRS = {"clients", "integrations", "swo"}

# Tokens that are infrastructure or cross-cutting code, not external
# integrations, and should not be reported as uncovered candidates.
INTEGRATION_TOKEN_IGNORE = {
    "base",
    "base_client",
    "async",
    "http",
    "common",
    "utils",
    "models",
    "errors",
    "exceptions",
    "constants",
    "conftest",
}

# Directory names that hold vendored or generated code, never first-party
# integration modules. Any path under one of these is skipped.
VENDORED_DIRS = {
    ".venv",
    "venv",
    ".tox",
    "site-packages",
    "node_modules",
    "build",
    "dist",
    ".eggs",
    ".git",
    "__pycache__",
}


def repo_has(root: Path, pattern: str) -> bool:
    if pattern.endswith("/"):
        # Directory signal: match the full relative directory path, not just the
        # basename, so "**/tests/e2e/" does not match an unrelated "foo/e2e".
        target = pattern.rstrip("/")
        return any(p.is_dir() for p in root.glob(target))
    return any(root.glob(pattern))


def is_extension(root: Path) -> bool:
    """True when the repository is an MPT extension built on the extension SDK.

    Detected by a dependency on `mpt-extension-sdk` in pyproject.toml (root or
    backend/), excluding the SDK package itself. Extensions integrate with
    external systems, so they should document those integrations.
    """
    for rel in ("pyproject.toml", "backend/pyproject.toml"):
        pyproject = root / rel
        if not pyproject.is_file():
            continue
        text = pyproject.read_text(encoding="utf-8", errors="ignore")
        try:
            name = tomllib.loads(text).get("project", {}).get("name")
        except tomllib.TOMLDecodeError:
            name = None
        if name == "mpt-extension-sdk":
            continue  # this is the SDK itself, not an extension built on it
        if re.search(r"mpt[-_]extension[-_]sdk", text):
            return True
    return False


def integration_candidates(root: Path) -> list[str]:
    """Heuristic list of likely external-integration modules in the repository.

    Two signals: files named ``*_client.py`` (the token before ``_client``), and
    modules/packages that sit directly under an integration parent directory
    (``clients/``, ``integrations/``, or the platform ``swo/`` grouping). Test
    code is excluded. These are candidates, not a definitive list; the skill
    confirms which represent real external systems.
    """
    names: set[str] = set()
    for path in root.rglob("*.py"):
        parts = path.relative_to(root).parts
        if (
            any(part in VENDORED_DIRS or part.startswith(".") for part in parts)
            or "tests" in parts
            or path.name.startswith("test_")
        ):
            continue
        if path.name.endswith("_client.py"):
            token = path.name[: -len("_client.py")]
            if token and token not in INTEGRATION_TOKEN_IGNORE:
                names.add(token)
        for i in range(len(parts) - 1):
            if parts[i] in INTEGRATION_PARENT_DIRS:
                child = parts[i + 1]
                token = child[:-3] if child.endswith(".py") else child
                if token and not token.startswith("__") and token not in INTEGRATION_TOKEN_IGNORE:
                    names.add(token)
    return sorted(names)


def external_integration_coverage(root: Path) -> dict | None:
    """Compare integration candidates against the external-integrations index.

    Returns None when the index does not exist yet (it is already recommended
    for authoring in that case). Otherwise reports candidate modules whose name
    is mentioned neither in the index nor as a ``docs/external/<name>.md`` page.
    """
    index = root / EXTENSION_DOC
    if not index.is_file():
        return None
    text = index.read_text(encoding="utf-8", errors="ignore").lower()
    external_dir = root / "docs" / "external"
    covered_pages = (
        {p.stem.lower() for p in external_dir.glob("*.md")}
        if external_dir.is_dir()
        else set()
    )
    candidates = integration_candidates(root)
    uncovered = [
        name
        for name in candidates
        if name.lower() not in text and name.lower() not in covered_pages
    ]
    return {"candidates": candidates, "uncovered": uncovered}


def audit(root: Path) -> dict:
    present_required = [d for d in REQUIRED_DOCS if (root / d).is_file()]
    missing_required = [d for d in REQUIRED_DOCS if not (root / d).is_file()]

    recommended = []
    for doc, signals in CONDITIONAL_DOCS.items():
        if (root / doc).is_file():
            continue
        if signals and any(repo_has(root, sig) for sig in signals):
            recommended.append(doc)

    # Extensions integrate with external systems; recommend documenting them.
    if is_extension(root) and not (root / EXTENSION_DOC).is_file():
        recommended.append(EXTENSION_DOC)

    existing_docs = sorted(
        str(p.relative_to(root))
        for p in (root / "docs").glob("*.md")
        if (root / "docs").is_dir()
    )
    for top in ("README.md", "AGENTS.md"):
        if (root / top).is_file():
            existing_docs.append(top)

    result = {
        "repo_root": str(root),
        "required": {"present": present_required, "missing": missing_required},
        "conditional_recommended": sorted(recommended),
        "existing_docs": sorted(set(existing_docs)),
    }

    # Extensions: flag integration modules with no entry in the existing index.
    if is_extension(root):
        coverage = external_integration_coverage(root)
        if coverage is not None:
            result["external_integrations"] = coverage

    return result


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
