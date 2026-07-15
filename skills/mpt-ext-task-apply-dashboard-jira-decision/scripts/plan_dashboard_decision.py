#!/usr/bin/env python3
import argparse
import json
import re
import sys
from typing import Any

MIN_PYTHON = (3, 12)

ACTIONS = {"new", "update", "reopen", "merge", "skip"}
WRITE_ACTIONS = {"new", "update", "reopen", "merge"}
TARGETED_ACTIONS = {"update", "reopen", "merge"}


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def normalize_action(value: str) -> str:
    action = value.strip().lower()
    if action not in ACTIONS:
        raise ValueError(f"--decision must be one of {sorted(ACTIONS)}")
    return action


def normalize_jira_key(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip().upper()
    if not key:
        return None
    if not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", key):
        raise ValueError("--target-key must match PROJECT-123 format")
    return key


def compute_hitcount(
    action: str,
    failures_count: int | None,
    current_hitcount: int | None,
    accumulate: bool,
    merge_target_action: str | None,
    blockers: list[str],
) -> int | None:
    if action == "skip":
        return None
    if failures_count is None:
        blockers.append("failures_count_missing")
        return None
    if failures_count < 0:
        blockers.append("failures_count_negative")
        return None

    def require_current() -> int | None:
        if current_hitcount is None:
            blockers.append("current_hitcount_missing")
            return None
        if current_hitcount < 0:
            blockers.append("current_hitcount_negative")
            return None
        return current_hitcount

    if action == "new":
        return failures_count
    if action == "update":
        current = require_current()
        return None if current is None else current + failures_count
    if action == "reopen":
        if accumulate:
            current = require_current()
            return None if current is None else current + failures_count
        return failures_count
    if action == "merge":
        if merge_target_action is None:
            blockers.append("merge_target_action_missing")
            return None
        # Apply the target issue's own action semantics.
        return compute_hitcount(
            merge_target_action,
            failures_count,
            current_hitcount,
            accumulate,
            None,
            blockers,
        )
    return None


def plan_decision(
    action: str,
    target_key: str | None,
    component: str | None,
    failures_count: int | None,
    current_hitcount: int | None,
    accumulate: bool,
    merge_target_action: str | None,
    skip_reason: str | None,
    release_fix_version: str,
) -> dict[str, Any]:
    blockers: list[str] = []

    if action == "new" and not component:
        blockers.append("component_missing")
    if action in TARGETED_ACTIONS and not target_key:
        blockers.append("target_key_missing")
    if action == "merge" and merge_target_action is not None:
        if merge_target_action not in {"new", "update", "reopen"}:
            blockers.append("merge_target_action_invalid")
            merge_target_action = None
    if action == "skip" and not skip_reason:
        blockers.append("skip_reason_missing")

    hitcount = compute_hitcount(
        action,
        failures_count,
        current_hitcount,
        accumulate,
        merge_target_action,
        blockers,
    )

    policy = None
    if action in WRITE_ACTIONS:
        if not release_fix_version:
            blockers.append("release_fix_version_missing")
        else:
            policy = {
                "fix_versions": [release_fix_version, "hotfix"],
                "environment": "prod",
                "keywords": ["dashboard"],
            }

    return {
        "action": action,
        "target_key": target_key,
        "component": component if action == "new" else None,
        "skip_reason": skip_reason if action == "skip" else None,
        "hitcount": hitcount,
        "policy": policy,
        "blockers": blockers,
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Plan a single approved dashboard-failure Jira decision: "
        "validate inputs, compute HitCount, and assemble policy fields."
    )
    parser.add_argument("--decision", required=True, help="new|update|reopen|merge|skip")
    parser.add_argument("--target-key", help="Target Jira key for update/reopen/merge")
    parser.add_argument("--component", help="Component for a new issue")
    parser.add_argument("--failures-count", type=int, help="Finding failures_count")
    parser.add_argument(
        "--current-hitcount", type=int, help="Current HitCount on the target issue"
    )
    parser.add_argument(
        "--accumulate",
        action="store_true",
        help="Reopen: accumulate HitCount instead of resetting (approved)",
    )
    parser.add_argument(
        "--merge-target-action",
        help="Merge: the target issue's approved action (new|update|reopen)",
    )
    parser.add_argument("--reason", help="Skip reason")
    parser.add_argument(
        "--release-fix-version",
        default="v6",
        help="Active release fixVersion (default: v6)",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        action = normalize_action(args.decision)
        target_key = normalize_jira_key(args.target_key)
        merge_target_action = (
            args.merge_target_action.strip().lower()
            if args.merge_target_action
            else None
        )
        result = plan_decision(
            action=action,
            target_key=target_key,
            component=(args.component.strip() if args.component else None),
            failures_count=args.failures_count,
            current_hitcount=args.current_hitcount,
            accumulate=args.accumulate,
            merge_target_action=merge_target_action,
            skip_reason=(args.reason.strip() if args.reason else None),
            release_fix_version=args.release_fix_version.strip(),
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
