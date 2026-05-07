#!/usr/bin/env python3
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MIN_PYTHON = (3, 12)

STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "it",
    "of",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
}


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def read_json(path: str) -> Any:
    with Path(path).open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def nested_get(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def normalize_jira_key(value: str) -> str:
    jira_key = value.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", jira_key):
        raise ValueError("--jira-key must match PROJECT-123 format")
    return jira_key


def extract_jira_key(issue: dict[str, Any], explicit_key: str | None) -> str:
    raw_key = explicit_key or str(issue.get("key") or "")
    if not raw_key:
        raise ValueError("Jira issue key is missing")
    return normalize_jira_key(raw_key)


def extract_issue_type(issue: dict[str, Any]) -> str:
    issue_type = nested_get(issue, "fields", "issuetype", "name")
    if issue_type is None:
        issue_type = nested_get(issue, "issuetype", "name")
    return str(issue_type or "").strip()


def classify_mode(issue_type: str) -> str:
    return "hotfix" if issue_type.casefold() == "bug" else "backport"


def marker_for_mode(mode: str) -> str:
    if mode == "hotfix":
        return "[HF]"
    if mode == "backport":
        return "[BACKPORT]"
    raise ValueError(f"unsupported mode: {mode}")


def prefix_for_mode(mode: str) -> str:
    if mode == "hotfix":
        return "hotfix-"
    if mode == "backport":
        return "backport-"
    raise ValueError(f"unsupported mode: {mode}")


def extract_summary(issue: dict[str, Any], explicit_summary: str | None) -> str:
    summary = explicit_summary or nested_get(issue, "fields", "summary") or issue.get("summary")
    return str(summary or "").strip()


def extract_fix_version_names(issue: dict[str, Any]) -> list[str]:
    raw_versions = nested_get(issue, "fields", "fixVersions")
    if raw_versions is None:
        raw_versions = issue.get("fixVersions")
    if not isinstance(raw_versions, list):
        return []
    names = []
    for version in raw_versions:
        if isinstance(version, str):
            name = version.strip()
        elif isinstance(version, dict):
            name = str(version.get("name") or "").strip()
        else:
            name = ""
        if name:
            names.append(name)
    return names


def matching_fix_versions(mode: str, version_names: list[str]) -> list[str]:
    marker = mode.casefold()
    return [name for name in version_names if marker in name.casefold()]


def render_slug(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    useful_words = [word for word in words if word not in STOP_WORDS]
    return "-".join(useful_words)


def render_branch_name(mode: str, jira_key: str, summary: str) -> str:
    slug = render_slug(summary)
    if not slug:
        raise ValueError("Jira summary did not produce a branch slug")
    return f"{prefix_for_mode(mode)}{jira_key.lower()}-{slug}"


def is_pr_open_or_merged(pr: dict[str, Any]) -> bool:
    state = str(pr.get("state") or "").upper()
    merged = pr.get("merged")
    merged_at = pr.get("mergedAt") or pr.get("merged_at")
    return state in {"OPEN", "MERGED"} or merged is True or bool(merged_at)


def extract_commit_sha(commit: Any) -> str:
    if isinstance(commit, str):
        return commit.strip()
    if not isinstance(commit, dict):
        return ""
    for key in ("oid", "sha", "commit", "commitSha"):
        value = commit.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    nested_commit = commit.get("commit")
    if isinstance(nested_commit, dict):
        return extract_commit_sha(nested_commit)
    return ""


def extract_source_commits(pr: dict[str, Any]) -> list[str]:
    raw_commits = pr.get("commits") or pr.get("commitNodes") or pr.get("source_commits")
    if isinstance(raw_commits, dict):
        raw_commits = raw_commits.get("nodes") or raw_commits.get("items")
    if not isinstance(raw_commits, list):
        return []
    commits = []
    for raw_commit in raw_commits:
        commit_sha = extract_commit_sha(raw_commit)
        if commit_sha:
            commits.append(commit_sha)
    return commits


def get_pr_number(pr: dict[str, Any]) -> Any:
    return pr.get("number") or pr.get("pr_number")


def render_context(
    issue: dict[str, Any],
    pr: dict[str, Any],
    jira_key: str | None,
    summary: str | None,
    target_release_branch: str | None,
) -> dict[str, Any]:
    blockers: list[str] = []

    normalized_jira_key = extract_jira_key(issue, jira_key)
    issue_type = extract_issue_type(issue)
    if not issue_type:
        blockers.append("jira_issue_type_missing")

    mode = classify_mode(issue_type)
    fix_versions = extract_fix_version_names(issue)
    matching_versions = matching_fix_versions(mode, fix_versions)
    needs_fix_version_confirmation = not matching_versions
    normalized_summary = extract_summary(issue, summary)
    branch_name = ""
    try:
        branch_name = render_branch_name(mode, normalized_jira_key, normalized_summary)
    except ValueError as error:
        blockers.append(str(error))

    source_commits = extract_source_commits(pr)
    if not is_pr_open_or_merged(pr):
        blockers.append("source_pr_not_open_or_merged")
    if not source_commits:
        blockers.append("source_pr_commits_missing")

    base_ref = str(pr.get("baseRefName") or pr.get("base_ref") or "").strip()
    if base_ref and base_ref != "main":
        blockers.append(f"source_pr_base_is_{base_ref}")

    return {
        "jira_key": normalized_jira_key,
        "issue_type": issue_type,
        "mode": mode,
        "pr_marker": marker_for_mode(mode),
        "branch_prefix": prefix_for_mode(mode),
        "fix_versions": fix_versions,
        "matching_fix_versions": matching_versions,
        "fix_version_ok": bool(matching_versions),
        "needs_fix_version_confirmation": needs_fix_version_confirmation,
        "release_branch_name": branch_name,
        "source_pr_number": get_pr_number(pr),
        "source_pr_url": pr.get("url") or pr.get("pr_url"),
        "source_pr_base": base_ref,
        "source_commits": source_commits,
        "target_release_branch": target_release_branch or "",
        "blockers": blockers,
        "ready": not blockers,
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Render deterministic hotfix or backport release workflow context."
    )
    parser.add_argument("--jira-json", required=True, help="Jira issue JSON file")
    parser.add_argument("--pr-json", required=True, help="GitHub main PR JSON file")
    parser.add_argument("--jira-key", help="Jira issue key override")
    parser.add_argument("--summary", help="Jira summary override")
    parser.add_argument("--target-release-branch", help="Resolved release branch")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    args = parser.parse_args()

    try:
        context = render_context(
            issue=read_json(args.jira_json),
            pr=read_json(args.pr_json),
            jira_key=args.jira_key,
            summary=args.summary,
            target_release_branch=args.target_release_branch,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    json.dump(context, sys.stdout, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
