#!/usr/bin/env python3
"""Classify a Jira issue's Sprint field for start-jira-work.

Reads an issue's ``fields`` object (or a full issue with a ``fields`` key) and
deterministically reports the Sprint-field state so the skill can decide sprint
placement: which sprints are active/closed/future, whether an active sprint
already exists, the candidate board ids, and whether the issue is a subtask.

Multi-active-sprint selection and board-id prompting are intentionally left to
the skill; this script only surfaces the facts.

The Sprint custom-field id is documented in ``standards/jira-fields.md`` and can
be overridden with ``--sprint-field-id`` instead of being assumed elsewhere.
"""
import argparse
import json
import re
import sys


MIN_PYTHON = (3, 12)

DEFAULT_SPRINT_FIELD_ID = "customfield_10020"

# Legacy greenhopper Sprint toString: ...Sprint@abc[id=1,rapidViewId=2,state=ACTIVE,name=S,...]
_LEGACY_KEY_RE = re.compile(r"(\w+)=(.*?)(?=,\w+=|\]?$)")


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def _classify_state(state: str) -> str:
    normalized = (state or "").strip().lower()
    if normalized in {"active", "closed", "future"}:
        return normalized
    return "unknown"


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_sprint_entry(entry) -> dict:
    """Normalize one Sprint field entry (object or legacy string)."""
    if isinstance(entry, dict):
        board_id = entry.get("boardId")
        if board_id is None:
            board_id = entry.get("rapidViewId")
        return {
            "id": _to_int(entry.get("id")),
            "name": entry.get("name"),
            "state": _classify_state(entry.get("state", "")),
            "board_id": _to_int(board_id),
        }
    if isinstance(entry, str):
        fields = {}
        bracket = entry[entry.find("[") + 1 : entry.rfind("]")] if "[" in entry else ""
        for key, raw in _LEGACY_KEY_RE.findall(bracket):
            fields[key] = raw
        board_id = fields.get("boardId", fields.get("rapidViewId"))
        return {
            "id": _to_int(fields.get("id")),
            "name": fields.get("name") or None,
            "state": _classify_state(fields.get("state", "")),
            "board_id": _to_int(board_id),
        }
    raise ValueError(f"unsupported sprint entry type: {type(entry).__name__}")


def analyze(fields: dict, sprint_field_id: str) -> dict:
    raw = fields.get(sprint_field_id)
    if raw is None:
        entries = []
    elif isinstance(raw, list):
        entries = raw
    else:
        raise ValueError(f"{sprint_field_id} is not a list or null")

    sprints = [parse_sprint_entry(entry) for entry in entries]
    active = [s for s in sprints if s["state"] == "active"]
    closed = [s for s in sprints if s["state"] == "closed"]
    future = [s for s in sprints if s["state"] == "future"]

    board_ids = []
    for sprint in sprints:
        board_id = sprint["board_id"]
        if board_id is not None and board_id not in board_ids:
            board_ids.append(board_id)

    issuetype = fields.get("issuetype") or {}
    is_subtask = bool(issuetype.get("subtask", False))

    return {
        "is_subtask": is_subtask,
        "sprints": sprints,
        "active_sprints": active,
        "closed_sprints": closed,
        "future_sprints": future,
        "has_active_sprint": bool(active),
        "multiple_active_sprints": len(active) > 1,
        "board_ids": board_ids,
    }


def _extract_fields(payload: dict) -> dict:
    if "fields" in payload:
        fields = payload["fields"]
        if not isinstance(fields, dict):
            raise ValueError("full issue envelope has a non-object 'fields'")
        return fields
    return payload


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Classify a Jira issue's Sprint field for start-jira-work."
    )
    parser.add_argument(
        "--issue-file",
        help="path to issue JSON (fields object or full issue); default stdin",
    )
    parser.add_argument(
        "--sprint-field-id",
        default=DEFAULT_SPRINT_FIELD_ID,
        help=f"Sprint custom-field id (default {DEFAULT_SPRINT_FIELD_ID}, per standards/jira-fields.md)",
    )
    args = parser.parse_args()

    try:
        if args.issue_file:
            with open(args.issue_file, encoding="utf-8") as handle:
                text = handle.read()
        else:
            text = sys.stdin.read()
    except OSError as error:
        print(f"error: cannot read {args.issue_file}: {error}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"error: invalid JSON: {error}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("error: expected a JSON object (issue or fields)", file=sys.stderr)
        return 1

    try:
        result = analyze(_extract_fields(payload), args.sprint_field_id)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
