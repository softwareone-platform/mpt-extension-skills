#!/usr/bin/env python3
"""Poll a pull request until CodeRabbit submits a new review, within a budget.

Runs ``gh pr view <pr> --json reviews,latestReviews,...`` on an interval and
stops as soon as CodeRabbit submits a *verdict* after ``--since`` — a review
whose state carries a decision (APPROVED / CHANGES_REQUESTED / DISMISSED).
COMMENTED reviews are ignored by default because CodeRabbit records its chat
auto-replies as COMMENTED reviews, so counting them ends the wait on a reply to
the agent's own thread replies rather than on the re-review. Pass
``--accept-commented`` for repositories where CodeRabbit only ever comments.
One invocation
is a single bounded foreground command, so the calling skill never hand-rolls
sleep loops; run it again for another polling round.

Exit code 0 covers both classified outcomes (``new_review`` and ``timeout``);
exit code 1 means the poller itself failed (bad inputs, or every poll errored).
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime


MIN_PYTHON = (3, 12)

# Default GitHub login for the CodeRabbit bot (the "[bot]" suffix is dropped in
# the review author login, but accept both forms).
DEFAULT_CODERABBIT_LOGINS = ("coderabbitai", "coderabbitai[bot]")

# Review states that carry a verdict. A COMMENTED review does not: CodeRabbit
# posts one for every chat auto-reply, so it is not evidence of a re-review.
DECISION_STATES = ("APPROVED", "CHANGES_REQUESTED", "DISMISSED")

# Consecutive failed fetches that mean the environment is broken rather than
# CodeRabbit being quiet.
CONSECUTIVE_ERROR_LIMIT = 2

# Upper bound for one gh invocation; later polls are capped by the remaining
# budget so a fetch started near the deadline cannot extend the round.
FETCH_TIMEOUT_SECONDS = 60.0

# Indirections so tests can fake time without real delays.
_sleep = time.sleep
_monotonic = time.monotonic


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def parse_iso_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp (trailing Z accepted) as an aware UTC datetime."""
    normalized = value.strip()
    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def fetch_pr_snapshot(pr: str, timeout_seconds: float = FETCH_TIMEOUT_SECONDS) -> dict:
    """Fetch the PR reviews snapshot with the gh CLI."""
    command = ["gh", "pr", "view", pr, "--json", "reviews,latestReviews,headRefOid"]
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout_seconds, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"gh invocation failed: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"gh pr view failed: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"gh pr view returned invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError("gh pr view returned a non-object JSON payload")
    return payload


def review_login(review: dict) -> str:
    """Return a review's author login, tolerating malformed payload shapes."""
    author = review.get("author")
    if not isinstance(author, dict):
        return ""
    login = author.get("login")
    return login.lower() if isinstance(login, str) else ""


def review_commit_oid(review: dict) -> str | None:
    """Return the SHA a review was submitted against, when the payload has it."""
    commit = review.get("commit")
    if isinstance(commit, dict):
        oid = commit.get("oid")
        if isinstance(oid, str) and oid:
            return oid
    return None


# A short SHA must not silently match nothing: that failure is indistinguishable
# from "CodeRabbit is silent", which is the misdiagnosis this loop exists to avoid.
MIN_SHA_PREFIX = 7


def sha_matches(review_oid: str | None, head_sha: str | None) -> bool:
    """Compare commit SHAs, accepting an abbreviated form on either side."""
    if not review_oid or not head_sha:
        return False
    left = review_oid.strip().lower()
    right = head_sha.strip().lower()
    if len(left) < MIN_SHA_PREFIX or len(right) < MIN_SHA_PREFIX:
        return False
    return left.startswith(right) or right.startswith(left)


def latest_review_after(
    payload: dict,
    logins: tuple[str, ...],
    since: datetime,
    accept_commented: bool = False,
    head_sha: str | None = None,
) -> dict | None:
    """Return the newest qualifying CodeRabbit review submitted after ``since``.

    Only reviews carrying a verdict qualify unless ``accept_commented`` is set;
    when ``head_sha`` is given the review must also have been submitted against
    that commit, so a review of the previous head never ends the wait.
    """
    reviews = payload.get("reviews")
    source = reviews if isinstance(reviews, list) and reviews else payload.get("latestReviews")
    if not isinstance(source, list):
        return None
    wanted = {name.lower() for name in logins}
    newest = None
    newest_at = None
    for review in source:
        if not isinstance(review, dict):
            continue
        login = review_login(review)
        if login not in wanted:
            continue
        state = review.get("state")
        state = state.upper() if isinstance(state, str) else ""
        if not accept_commented and state not in DECISION_STATES:
            continue
        if head_sha is not None and not sha_matches(review_commit_oid(review), head_sha):
            continue
        submitted_raw = review.get("submittedAt")
        if not submitted_raw:
            continue
        try:
            submitted = parse_iso_timestamp(str(submitted_raw))
        except ValueError:
            continue
        if submitted <= since:
            continue
        if newest_at is None or submitted > newest_at:
            newest_at = submitted
            newest = {
                "state": state,
                "submitted_at": submitted.isoformat(),
                "commit_oid": review_commit_oid(review),
            }
    return newest


def poll(
    pr: str,
    since: datetime,
    budget_seconds: int,
    interval_seconds: int,
    logins: tuple[str, ...],
    accept_commented: bool = False,
    head_sha: str | None = None,
) -> dict:
    """Poll until a new CodeRabbit review appears or the budget is spent.

    Every fetch is bounded by the polling deadline: the first one by the whole
    budget, later ones by what is left, and no fetch starts once the budget is
    exhausted. ``budget_seconds=0`` is the documented "poll exactly once" case,
    where the single attempt gets the full fetch timeout because a zero-second
    subprocess timeout could never complete a ``gh`` call.
    """
    start = _monotonic()
    polls = 0
    errors = 0
    consecutive_errors = 0
    last_error = None
    while True:
        if polls == 0:
            fetch_timeout = (
                FETCH_TIMEOUT_SECONDS
                if budget_seconds <= 0
                else min(FETCH_TIMEOUT_SECONDS, float(budget_seconds))
            )
        else:
            remaining = budget_seconds - (_monotonic() - start)
            if remaining <= 0:
                break
            fetch_timeout = min(FETCH_TIMEOUT_SECONDS, remaining)
        polls += 1
        try:
            snapshot = fetch_pr_snapshot(pr, fetch_timeout)
        except RuntimeError as error:
            errors += 1
            consecutive_errors += 1
            last_error = str(error)
        else:
            consecutive_errors = 0
            found = latest_review_after(
                snapshot, logins, since, accept_commented, head_sha
            )
            if found is not None:
                return {"outcome": "new_review", **found, "polls": polls, "errors": errors}
        elapsed = _monotonic() - start
        if elapsed >= budget_seconds:
            break
        _sleep(min(interval_seconds, budget_seconds - elapsed))
    # A run of failing fetches means the environment is broken, not that
    # CodeRabbit is quiet; reporting that as a plain timeout would send the
    # caller's escalation ladder chasing an unresponsive bot instead.
    environment_broken = errors == polls or consecutive_errors >= CONSECUTIVE_ERROR_LIMIT
    outcome = "error" if errors and environment_broken else "timeout"
    return {
        "outcome": outcome,
        "state": None,
        "submitted_at": None,
        "polls": polls,
        "errors": errors,
        "consecutive_errors": consecutive_errors,
        "last_error": last_error,
    }


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Poll a PR until CodeRabbit submits a new review, within a budget."
    )
    parser.add_argument(
        "--pr", required=True, help="pull request number or branch, passed to gh pr view"
    )
    parser.add_argument(
        "--since",
        required=True,
        help="ISO-8601 timestamp; only reviews submitted strictly after it count",
    )
    parser.add_argument(
        "--budget-seconds",
        type=int,
        default=540,
        help="total polling budget in seconds (0 = poll exactly once)",
    )
    parser.add_argument(
        "--interval-seconds", type=int, default=90, help="delay between polls in seconds"
    )
    parser.add_argument(
        "--coderabbit-login",
        action="append",
        help="Override the CodeRabbit review author login (repeatable).",
    )
    parser.add_argument(
        "--accept-commented",
        action="store_true",
        help="Count COMMENTED reviews as a verdict (they include chat auto-replies).",
    )
    parser.add_argument(
        "--head-sha",
        help="Only count a review submitted against this commit SHA.",
    )
    args = parser.parse_args()

    try:
        since = parse_iso_timestamp(args.since)
    except ValueError as error:
        print(f"error: invalid --since timestamp: {error}", file=sys.stderr)
        return 1
    if args.budget_seconds < 0:
        print("error: --budget-seconds must be zero or positive", file=sys.stderr)
        return 1
    if args.interval_seconds <= 0:
        print("error: --interval-seconds must be positive", file=sys.stderr)
        return 1

    logins = tuple(args.coderabbit_login) if args.coderabbit_login else DEFAULT_CODERABBIT_LOGINS
    result = poll(
        args.pr,
        since,
        args.budget_seconds,
        args.interval_seconds,
        logins,
        args.accept_commented,
        args.head_sha,
    )
    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 1 if result["outcome"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
