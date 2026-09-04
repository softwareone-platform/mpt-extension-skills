#!/usr/bin/env python3
"""Classify the CodeRabbit service status from an Instatus summary payload.

Reads the JSON served at ``https://status.coderabbit.ai/summary.json`` on
stdin (fetch it with ``curl -fsS --max-time 30 ...``) and reports
deterministically whether the service is operational: the page status is
``UP`` and there are no active incidents. The script only classifies facts;
the calling skill decides how a degraded or unknown status affects the loop.
"""
import json
import sys


MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def _named_entries(entries) -> list[dict]:
    """Normalize incident or maintenance entries to ``{name, status}`` dicts."""
    normalized = []
    for entry in entries or []:
        if not isinstance(entry, dict):
            continue
        normalized.append(
            {
                "name": str(entry.get("name") or "<unnamed>"),
                "status": str(entry.get("status") or "UNKNOWN"),
            }
        )
    return normalized


def classify_status(payload: dict) -> dict:
    """Classify one Instatus summary payload into an operational verdict."""
    page = payload.get("page")
    page_status = None
    if isinstance(page, dict):
        status = page.get("status")
        if status:
            page_status = str(status).upper()
    incidents = _named_entries(payload.get("activeIncidents"))
    maintenances = _named_entries(payload.get("activeMaintenances"))

    reasons = []
    if page_status is None:
        reasons.append("no page status found in the summary payload")
    elif page_status != "UP":
        reasons.append(f"status page reports {page_status}, not UP")
    for incident in incidents:
        reasons.append(f"active incident: {incident['name']} ({incident['status']})")

    return {
        "operational": page_status == "UP" and not incidents,
        "page_status": page_status,
        "active_incidents": incidents,
        "active_maintenances": maintenances,
        "reasons": reasons,
    }


def main() -> int:
    require_python_version()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON on stdin: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("error: expected the Instatus summary JSON object", file=sys.stderr)
        return 1

    json.dump(classify_status(payload), sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
