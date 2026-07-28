#!/usr/bin/env python3
"""Decide whether a pull request is "green" and ready to notify.

Reads the JSON produced by
``gh pr view <pr> --json statusCheckRollup,latestReviews,reviews`` on stdin and
reports, deterministically, whether the PR meets the notification gate:

- every status check has passed (none failing, none still pending), and
- CodeRabbit has submitted a review whose latest state is ``APPROVED``.

The script only classifies facts and returns the combined ``is_green`` verdict
with human-readable reasons; the skill decides what to do with the result.
"""
import argparse
import json
import sys


MIN_PYTHON = (3, 12)

# Default GitHub login for the CodeRabbit bot (the "[bot]" suffix is dropped in
# the review author login, but accept both forms).
DEFAULT_CODERABBIT_LOGINS = ("coderabbitai", "coderabbitai[bot]")

# CheckRun.conclusion values that count as passing.
_PASSING_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
# CheckRun.status / StatusContext.state values that mean "not finished yet".
_PENDING_STATES = {"PENDING", "EXPECTED", "IN_PROGRESS", "QUEUED", "WAITING", "REQUESTED"}


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def _check_name(entry: dict) -> str:
    return entry.get("name") or entry.get("context") or "<unnamed>"


def classify_check(entry: dict) -> str:
    """Return 'passing', 'pending', or 'failing' for one statusCheckRollup entry."""
    # CheckRun: has a status; when COMPLETED look at conclusion.
    status = (entry.get("status") or "").upper()
    if status:
        if status != "COMPLETED":
            return "pending" if status in _PENDING_STATES else "failing"
        conclusion = (entry.get("conclusion") or "").upper()
        return "passing" if conclusion in _PASSING_CONCLUSIONS else "failing"
    # StatusContext: has a state.
    state = (entry.get("state") or "").upper()
    if state == "SUCCESS":
        return "passing"
    if state in _PENDING_STATES:
        return "pending"
    return "failing"


def evaluate_checks(rollup: list) -> dict:
    passing, pending, failing = [], [], []
    for entry in rollup or []:
        if not isinstance(entry, dict):
            continue
        bucket = classify_check(entry)
        {"passing": passing, "pending": pending, "failing": failing}[bucket].append(
            _check_name(entry)
        )
    if failing or pending:
        state = "failing" if failing else "pending"
    elif passing:
        state = "success"
    else:
        state = "none"
    return {
        "state": state,
        "ok": state == "success",
        "passing": passing,
        "pending": pending,
        "failing": failing,
    }


def _latest_reviews(payload: dict) -> list:
    """Return a per-author latest-state review list, preferring gh's latestReviews."""
    latest = payload.get("latestReviews")
    if isinstance(latest, list) and latest:
        return latest
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        return []
    by_author: dict[str, dict] = {}
    for review in reviews:
        if not isinstance(review, dict):
            continue
        login = ((review.get("author") or {}).get("login") or "").lower()
        # reviews are returned in chronological order; keep the last per author.
        by_author[login] = review
    return list(by_author.values())


# Only these review states carry an approval decision. A COMMENTED (or PENDING)
# review does not, and must not mask an earlier APPROVED: CodeRabbit often posts a
# COMMENTED summary moments after its APPROVED review, and GitHub itself ignores
# COMMENTED reviews when computing the review decision.
_DECISION_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}


def evaluate_coderabbit(payload: dict, logins: tuple[str, ...]) -> dict:
    wanted = {name.lower() for name in logins}
    # Prefer the full chronological reviews list so a trailing COMMENTED summary
    # does not hide the real decision; fall back to latestReviews when absent.
    reviews = payload.get("reviews")
    source = reviews if isinstance(reviews, list) and reviews else _latest_reviews(payload)
    last_any = None
    last_decision = None
    for review in source:
        if not isinstance(review, dict):
            continue
        login = ((review.get("author") or {}).get("login") or "").lower()
        if login not in wanted:
            continue
        state = (review.get("state") or "").upper()
        last_any = state
        if state in _DECISION_STATES:
            last_decision = state
    effective = last_decision if last_decision is not None else last_any
    return {
        "found": effective is not None,
        "state": effective,
        "approved": effective == "APPROVED",
    }


def evaluate(payload: dict, logins: tuple[str, ...]) -> dict:
    checks = evaluate_checks(payload.get("statusCheckRollup"))
    coderabbit = evaluate_coderabbit(payload, logins)
    reasons = []
    if not checks["ok"]:
        if checks["failing"]:
            reasons.append("failing checks: " + ", ".join(checks["failing"]))
        if checks["pending"]:
            reasons.append("pending checks: " + ", ".join(checks["pending"]))
        if checks["state"] == "none":
            reasons.append("no status checks found on the PR")
    if not coderabbit["approved"]:
        if not coderabbit["found"]:
            reasons.append("no CodeRabbit review found")
        else:
            reasons.append(f"CodeRabbit review state is {coderabbit['state']}, not APPROVED")
    return {
        "is_green": checks["ok"] and coderabbit["approved"],
        "checks": checks,
        "coderabbit": coderabbit,
        "reasons": reasons,
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Decide whether a PR is green (all checks pass and CodeRabbit approved)."
    )
    parser.add_argument(
        "--coderabbit-login",
        action="append",
        help="Override the CodeRabbit review author login (repeatable).",
    )
    args = parser.parse_args()

    logins = tuple(args.coderabbit_login) if args.coderabbit_login else DEFAULT_CODERABBIT_LOGINS

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON on stdin: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("error: expected a JSON object from 'gh pr view --json ...'", file=sys.stderr)
        return 1

    result = evaluate(payload, logins)
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
