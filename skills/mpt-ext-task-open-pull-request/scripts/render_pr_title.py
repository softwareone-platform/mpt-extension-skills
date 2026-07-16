#!/usr/bin/env python3
"""Deterministically render a pull request title per standards/pull-requests.md.

The title format is ``[MARKER ]<JIRA-ID> <short summary>`` where the optional
``[HF]``/``[BACKPORT]`` marker is required only for pull requests opened against a
release branch, matching what the shared Danger action enforces. The Jira key is
validated and a leading Conventional Commit prefix in the summary is rejected
(PR titles must not carry one).
"""
import argparse
import json
import re
import sys


MIN_PYTHON = (3, 12)

JIRA_KEY_RE = re.compile(r"[A-Z][A-Z0-9]+-\d+")
CONVENTIONAL_PREFIX_RE = re.compile(
    r"^(feat|fix|chore|docs|refactor|test|build|ci|perf|style|revert)"
    r"(\([^)]*\))?!?:\s",
    re.IGNORECASE,
)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def is_release_branch(base_branch: str) -> bool:
    """A release branch is ``release/*`` with a non-empty suffix."""
    suffix = base_branch.strip().removeprefix("release/")
    return base_branch.strip().startswith("release/") and bool(suffix)


def normalize_jira_key(jira_key: str) -> str:
    normalized = jira_key.strip().upper()
    if not JIRA_KEY_RE.fullmatch(normalized):
        raise ValueError(f"invalid Jira key: {jira_key!r} (expected e.g. MPT-1234)")
    return normalized


def normalize_summary(summary: str) -> str:
    collapsed = " ".join(summary.split())
    if not collapsed:
        raise ValueError("summary is empty")
    if CONVENTIONAL_PREFIX_RE.match(collapsed):
        raise ValueError(
            "summary must not start with a Conventional Commit prefix "
            "(feat:, fix:, …); PR titles carry only the Jira key and summary"
        )
    return collapsed


def resolve_marker(kind: str, base_branch: str) -> str:
    """Return ``[HF]``/``[BACKPORT]`` only for release-branch PRs, else ``""``."""
    if kind in {"feature", "bugfix"}:
        if is_release_branch(base_branch):
            raise ValueError(
                f"kind {kind!r} targets {base_branch!r}: feature/bugfix pull "
                "requests are opened against main, not a release branch"
            )
        return ""
    if kind == "hotfix":
        return "[HF]" if is_release_branch(base_branch) else ""
    if kind == "backport":
        return "[BACKPORT]" if is_release_branch(base_branch) else ""
    raise ValueError(f"unsupported kind: {kind!r}")


def render_pr_title(jira_key: str, summary: str, kind: str, base_branch: str) -> str:
    normalized_key = normalize_jira_key(jira_key)
    normalized_summary = normalize_summary(summary)
    marker = resolve_marker(kind, base_branch)
    prefix = f"{marker} " if marker else ""
    return f"{prefix}{normalized_key} {normalized_summary}"


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Render a pull request title per standards/pull-requests.md."
    )
    parser.add_argument("--jira-key", required=True, help="e.g. MPT-1234")
    parser.add_argument("--summary", required=True, help="short PR summary")
    parser.add_argument(
        "--kind",
        choices=["feature", "bugfix", "hotfix", "backport"],
        default="feature",
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="target base branch (e.g. main, release/5)",
    )
    parser.add_argument("--json", action="store_true", help="emit a JSON object")
    args = parser.parse_args()

    try:
        title = render_pr_title(args.jira_key, args.summary, args.kind, args.base_branch)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if args.json:
        marker = resolve_marker(args.kind, args.base_branch)
        print(
            json.dumps(
                {
                    "title": title,
                    "jira_key": normalize_jira_key(args.jira_key),
                    "summary": normalize_summary(args.summary),
                    "kind": args.kind,
                    "base_branch": args.base_branch.strip(),
                    "is_release_base": is_release_branch(args.base_branch),
                    "marker": marker,
                },
                indent=2,
            )
        )
    else:
        print(title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
