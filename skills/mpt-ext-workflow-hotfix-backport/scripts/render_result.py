#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any


MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def read_json(path: str) -> Any:
    with Path(path).open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def value(context: dict[str, Any], key: str, fallback: str = "unknown") -> str:
    raw_value = context.get(key)
    if raw_value is None or raw_value == "":
        return fallback
    return str(raw_value)


def render_validation(command: str, status: str) -> str:
    command = command.strip()
    status = status.strip()
    if command and status:
        return f"`{command}`: {status}"
    if status:
        return status
    return "not reported"


def render_blockers(context: dict[str, Any]) -> list[str]:
    blockers = context.get("blockers")
    if not isinstance(blockers, list) or not blockers:
        return []
    return ["", "Blockers:"] + [f"- {blocker}" for blocker in blockers]


def render_source_commits(context: dict[str, Any]) -> str:
    commits = context.get("source_commits")
    if not isinstance(commits, list) or not commits:
        return "unknown"
    return ", ".join(str(commit) for commit in commits)


def render_fix_version_state(context: dict[str, Any]) -> str:
    matching = context.get("matching_fix_versions")
    if isinstance(matching, list) and matching:
        return ", ".join(str(version) for version in matching)
    if context.get("needs_fix_version_confirmation") is True:
        return "missing confirmation required"
    return "not reported"


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Render a stable hotfix or backport workflow result."
    )
    parser.add_argument("--context-json", required=True, help="Release context JSON file")
    parser.add_argument("--release-pr-url", help="Release branch pull request URL")
    parser.add_argument("--validation-command", help="Validation command that was run")
    parser.add_argument("--validation-status", help="Validation result")
    parser.add_argument("--jira-status", help="Jira transition result")
    args = parser.parse_args()

    try:
        context = read_json(args.context_json)
    except (OSError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if not isinstance(context, dict):
        print("error: --context-json must contain an object", file=sys.stderr)
        return 1

    lines = [
        f"Mode: {value(context, 'mode')} {value(context, 'pr_marker', '')}".rstrip(),
        f"Jira: {value(context, 'jira_key')}",
        f"Source PR: {value(context, 'source_pr_url')}",
        f"Source commits: {render_source_commits(context)}",
        f"Fix version: {render_fix_version_state(context)}",
        f"Target release branch: {value(context, 'target_release_branch')}",
        f"Release branch: {value(context, 'release_branch_name')}",
        f"Release PR: {args.release_pr_url.strip() if args.release_pr_url else 'not created'}",
        "Validation: "
        + render_validation(args.validation_command or "", args.validation_status or ""),
        f"Jira transition: {args.jira_status.strip() if args.jira_status else 'not reported'}",
    ]
    lines.extend(render_blockers(context))
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
