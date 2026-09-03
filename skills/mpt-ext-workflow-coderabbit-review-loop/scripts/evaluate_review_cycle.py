#!/usr/bin/env python3
"""Evaluate one CodeRabbit review-loop cycle from captured PR state.

Reads two captured files — a ``gh pr view --json
reviews,latestReviews,statusCheckRollup`` snapshot and the PR's review threads
(GraphQL ``reviewThreads`` in any of its common envelopes) — and reports
deterministically:

- whether CodeRabbit's effective review decision is ``APPROVED`` (a trailing
  COMMENTED summary never masks an earlier decision),
- whether CodeRabbit submitted any review strictly after ``--since``,
- the unresolved CodeRabbit threads awaiting an agent response ("actionable")
  and their content fingerprint,
- ``no_progress`` when that fingerprint equals ``--previous-fingerprint``,
- a status-check summary, and the combined ``exit_gate`` the loop terminates on
  (approved, confirmed against the current head, and checks green).

The script only classifies facts; the review-loop skill decides what to do.
"""
import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime


MIN_PYTHON = (3, 12)

# Default GitHub login for the CodeRabbit bot (the "[bot]" suffix is dropped in
# the review author login, but accept both forms).
DEFAULT_CODERABBIT_LOGINS = ("coderabbitai", "coderabbitai[bot]")

# Only these review states carry an approval decision; COMMENTED/PENDING do not.
_DECISION_STATES = {"APPROVED", "CHANGES_REQUESTED", "DISMISSED"}

# CheckRun.conclusion values that count as passing.
_PASSING_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}
# CheckRun.status / StatusContext.state values that mean "not finished yet".
_PENDING_STATES = {"PENDING", "EXPECTED", "IN_PROGRESS", "QUEUED", "WAITING", "REQUESTED"}


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


def comment_author(comment: dict) -> str:
    """Extract a login from common comment shapes (GraphQL, REST, or simplified)."""
    for key in ("user", "author"):
        value = comment.get(key)
        if isinstance(value, dict):
            login = value.get("login")
            if isinstance(login, str) and login:
                return login
        elif isinstance(value, str) and value:
            return value
    login = comment.get("login")
    if isinstance(login, str) and login:
        return login
    return ""


def review_login(review: dict) -> str:
    """Return a review's author login, tolerating malformed payload shapes."""
    author = review.get("author")
    if not isinstance(author, dict):
        return ""
    login = author.get("login")
    return login.lower() if isinstance(login, str) else ""


def _review_source(payload: dict) -> list:
    reviews = payload.get("reviews")
    if isinstance(reviews, list) and reviews:
        return reviews
    latest = payload.get("latestReviews")
    if isinstance(latest, list):
        return latest
    return []


def review_commit_oid(review: dict) -> str | None:
    """Return the SHA a review was submitted against, when the payload carries it."""
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


def evaluate_reviews(
    payload: dict,
    logins: tuple[str, ...],
    since: datetime | None,
    head_sha: str | None = None,
) -> dict:
    """Classify CodeRabbit's effective review decision and its currency.

    ``submittedAt`` orders the reviews (newest wins) only when every candidate
    carries a parseable timestamp; if any is missing one, array order decides
    instead, so an untimestamped newer verdict is never discarded in favour of
    an older timestamped one.

    Currency prefers the head SHA: a review is current when it was submitted
    against ``head_sha``. That is the real invariant ("this review reviewed
    this code") and needs no clock. ``since`` is the fallback when the payload
    carries no commit SHA, and an unknown answer stays ``None`` rather than
    collapsing to ``False``.
    """
    wanted = {name.lower() for name in logins}
    candidates = []  # (index, state, submitted, oid)
    latest_submitted = None
    new_review_since = False if since is not None else None
    for index, review in enumerate(_review_source(payload)):
        if not isinstance(review, dict):
            continue
        login = review_login(review)
        if login not in wanted:
            continue
        state = review.get("state")
        state = state.upper() if isinstance(state, str) else ""
        submitted = None
        submitted_raw = review.get("submittedAt")
        if submitted_raw:
            try:
                submitted = parse_iso_timestamp(str(submitted_raw))
            except ValueError:
                submitted = None
        candidates.append((index, state, submitted, review_commit_oid(review)))
        if submitted is None:
            continue
        if latest_submitted is None or submitted > latest_submitted:
            latest_submitted = submitted
        if since is not None and submitted > since:
            new_review_since = True

    # Timestamps order the reviews only when all of them have one; otherwise a
    # missing timestamp would silently outrank a newer verdict, so fall back to
    # the array order the API returned.
    fully_timestamped = bool(candidates) and all(c[2] is not None for c in candidates)
    if fully_timestamped:
        ordered = sorted(candidates, key=lambda c: (c[2], c[0]))
    else:
        ordered = sorted(candidates, key=lambda c: c[0])

    newest = ordered[-1] if ordered else None
    decisions = [c for c in ordered if c[1] in _DECISION_STATES]
    best = decisions[-1] if decisions else newest

    effective = best[1] if best is not None else None
    decision_submitted = best[2] if best is not None else None
    decision_oid = best[3] if best is not None else None
    approved = effective == "APPROVED"

    approval_is_current = None
    if approved:
        if head_sha and decision_oid:
            approval_is_current = sha_matches(decision_oid, head_sha)
        elif since is not None and decision_submitted is not None:
            approval_is_current = decision_submitted > since
    return {
        "found": bool(effective),
        "state": effective,
        "approved": approved,
        "approval_is_current": approval_is_current,
        "decision_submitted_at": decision_submitted.isoformat() if decision_submitted else None,
        "decision_commit_oid": decision_oid,
        "latest_submitted_at": latest_submitted.isoformat() if latest_submitted else None,
        "new_review_since": new_review_since,
    }


def extract_threads(payload) -> list:
    """Unwrap review threads from the common GraphQL envelopes or a bare list."""
    node = payload
    if isinstance(node, dict) and isinstance(node.get("data"), dict):
        node = node["data"]
        for key in ("repository", "pullRequest"):
            inner = node.get(key)
            if isinstance(inner, dict):
                node = inner
    if isinstance(node, dict) and isinstance(node.get("reviewThreads"), dict):
        node = node["reviewThreads"]
    if isinstance(node, dict) and isinstance(node.get("nodes"), list):
        # A truncated page would silently under-report actionable threads, so
        # refuse it instead of classifying an incomplete set.
        page_info = node.get("pageInfo")
        if isinstance(page_info, dict) and page_info.get("hasNextPage"):
            raise ValueError(
                "review threads are paginated (pageInfo.hasNextPage is true): "
                "refetch with 'after: endCursor' and merge every page before evaluating"
            )
        return node["nodes"]
    if isinstance(node, list):
        return node
    raise ValueError(
        "expected review threads as a list, {nodes: [...]}, or a GraphQL envelope"
    )


def _thread_comments(thread: dict) -> list:
    comments = thread.get("comments")
    if isinstance(comments, dict) and isinstance(comments.get("nodes"), list):
        return comments["nodes"]
    if isinstance(comments, list):
        return comments
    return []


def _thread_last_comment(thread: dict, comments: list) -> dict:
    """Return the thread's true last comment.

    Prefer the ``lastComment: comments(last: 1)`` alias from the capture
    query, because the plain ``comments(first: N)`` page can truncate a long
    thread and make ``comments[-1]`` the wrong "last" comment.
    """
    for key in ("lastComment", "last_comment"):
        value = thread.get(key)
        if isinstance(value, dict) and isinstance(value.get("nodes"), list):
            value = value["nodes"]
        if isinstance(value, list):
            nodes = [c for c in value if isinstance(c, dict)]
            if nodes:
                return nodes[-1]
    return comments[-1]


def classify_threads(threads: list, logins: tuple[str, ...]) -> tuple[list[dict], int]:
    """Split unresolved CodeRabbit threads into (actionable ones, total count).

    A thread is CodeRabbit's when its first comment was written by a CodeRabbit
    login; it is actionable when its last comment is also CodeRabbit's, meaning
    it still awaits an agent response (a fresh finding or a counter-reply).
    """
    wanted = {name.lower() for name in logins}
    actionable = []
    unresolved_bot_count = 0
    for thread in threads:
        if not isinstance(thread, dict) or thread.get("isResolved"):
            continue
        comments = [c for c in _thread_comments(thread) if isinstance(c, dict)]
        if not comments:
            continue
        if comment_author(comments[0]).strip().lower() not in wanted:
            continue
        unresolved_bot_count += 1
        last = _thread_last_comment(thread, comments)
        if comment_author(last).strip().lower() not in wanted:
            continue
        actionable.append(
            {
                "id": thread.get("id"),
                "path": thread.get("path"),
                "line": thread.get("line"),
                "last_comment_body": str(last.get("body") or ""),
            }
        )
    return actionable, unresolved_bot_count


def _normalized_body_digest(body: str) -> str:
    """Hash the whole normalized comment body.

    An excerpt is not discriminating enough: CodeRabbit bodies open with a
    fixed category/severity banner, so different findings on the same file
    share their opening characters and would collide.
    """
    normalized = " ".join(body.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_fingerprint(actionable: list[dict]) -> str:
    """Build a stable content fingerprint of the actionable CodeRabbit threads.

    The key deliberately excludes the line number: this loop amends and
    force-pushes every iteration, which shifts lines and nulls them out on
    outdated threads, so keying on the line would make an unchanged stalemate
    look like progress.
    """
    keys = sorted(
        "{path}|{digest}".format(
            path=thread.get("path"),
            digest=_normalized_body_digest(thread.get("last_comment_body") or ""),
        )
        for thread in actionable
    )
    digest = hashlib.sha256("\n".join(keys).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _check_name(entry: dict) -> str:
    return entry.get("name") or entry.get("context") or "<unnamed>"


def classify_check(entry: dict) -> str:
    """Return 'passing', 'pending', or 'failing' for one statusCheckRollup entry."""
    status = (entry.get("status") or "").upper()
    if status:
        if status != "COMPLETED":
            return "pending" if status in _PENDING_STATES else "failing"
        conclusion = (entry.get("conclusion") or "").upper()
        return "passing" if conclusion in _PASSING_CONCLUSIONS else "failing"
    state = (entry.get("state") or "").upper()
    if state == "SUCCESS":
        return "passing"
    if state in _PENDING_STATES:
        return "pending"
    return "failing"


def evaluate_checks(rollup) -> dict:
    # gh returns a flat list; a GraphQL capture nests the entries under "nodes".
    if isinstance(rollup, dict) and isinstance(rollup.get("nodes"), list):
        rollup = rollup["nodes"]
    if not isinstance(rollup, list):
        rollup = []
    passing, pending, failing = [], [], []
    for entry in rollup:
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
        # "none" means the PR has no checks configured; gating on absent checks
        # would deadlock the loop, so it does not block the exit gate.
        "ok": state in ("success", "none"),
        "passing": passing,
        "pending": pending,
        "failing": failing,
    }


def evaluate_cycle(
    pr_payload: dict,
    threads_payload,
    logins: tuple[str, ...],
    since: datetime | None,
    previous_fingerprint: str | None,
    head_sha: str | None = None,
) -> dict:
    """Combine review, thread, and check facts into one cycle verdict."""
    reviews = evaluate_reviews(pr_payload, logins, since, head_sha)
    actionable, unresolved_bot_count = classify_threads(
        extract_threads(threads_payload), logins
    )
    fingerprint = compute_fingerprint(actionable)
    no_progress = bool(
        previous_fingerprint and previous_fingerprint == fingerprint and actionable
    )
    checks = evaluate_checks(pr_payload.get("statusCheckRollup"))
    gate_reasons = []
    if not reviews["approved"]:
        gate_reasons.append("CodeRabbit has not approved")
    elif reviews["approval_is_current"] is not True:
        gate_reasons.append("the approval is not confirmed against the current head")
    if checks["failing"]:
        gate_reasons.append("failing checks: " + ", ".join(checks["failing"]))
    if checks["pending"]:
        gate_reasons.append("pending checks: " + ", ".join(checks["pending"]))
    exit_gate = {"ok": not gate_reasons, "reasons": gate_reasons}

    reasons = []
    if reviews["approved"]:
        reasons.append("CodeRabbit's effective review decision is APPROVED")
        if reviews["approval_is_current"] is False:
            if head_sha and reviews["decision_commit_oid"]:
                reasons.append(
                    "the approval reviewed "
                    f"{reviews['decision_commit_oid'][:7]}, not the current head "
                    f"{head_sha[:7]} (stale)"
                )
            else:
                reasons.append("the approval predates the --since cutoff (stale, pre-push)")
        elif reviews["approval_is_current"] is None:
            reasons.append(
                "approval currency is unknown (no --head-sha match and no usable "
                "--since cutoff); treat it as unverified"
            )
    elif not reviews["found"]:
        reasons.append("no CodeRabbit review found")
    else:
        reasons.append(f"CodeRabbit review state is {reviews['state']}, not APPROVED")
    if actionable:
        reasons.append(
            f"{len(actionable)} CodeRabbit thread(s) awaiting an agent response"
        )
    if no_progress:
        reasons.append(
            "no progress: the actionable CodeRabbit threads match the previous iteration"
        )
    if exit_gate["ok"]:
        reasons.append("exit gate is satisfied: approved on the current head and checks green")
    elif reviews["approved"]:
        reasons.append("exit gate blocked: " + "; ".join(exit_gate["reasons"]))
    return {
        "coderabbit": {
            key: reviews[key]
            for key in ("found", "state", "approved", "approval_is_current")
        },
        "decision_submitted_at": reviews["decision_submitted_at"],
        "decision_commit_oid": reviews["decision_commit_oid"],
        "new_review_since": reviews["new_review_since"],
        "latest_review_submitted_at": reviews["latest_submitted_at"],
        "actionable_threads": {
            "count": len(actionable),
            "items": [
                {"id": t["id"], "path": t["path"], "line": t["line"]}
                for t in actionable
            ],
        },
        "unresolved_bot_threads": unresolved_bot_count,
        "fingerprint": fingerprint,
        "no_progress": no_progress,
        "checks": checks,
        "exit_gate": exit_gate,
        "reasons": reasons,
    }


def _load_json_file(path: str, label: str):
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as error:
        raise ValueError(f"cannot read {label} file {path}: {error}") from error
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON in {label} file {path}: {error}") from error


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Evaluate one CodeRabbit review-loop cycle from captured PR state."
    )
    parser.add_argument(
        "--pr-json",
        required=True,
        help="file with 'gh pr view --json reviews,latestReviews,statusCheckRollup'",
    )
    parser.add_argument(
        "--threads-json",
        required=True,
        help="file with the PR review threads (GraphQL reviewThreads payload)",
    )
    parser.add_argument(
        "--since",
        help="ISO-8601 timestamp; report whether CodeRabbit reviewed after it",
    )
    parser.add_argument(
        "--previous-fingerprint",
        help="fingerprint from the previous iteration, to detect no progress",
    )
    parser.add_argument(
        "--head-sha",
        help="current head SHA; an approval is current when it reviewed this commit",
    )
    parser.add_argument(
        "--coderabbit-login",
        action="append",
        help="Override the CodeRabbit review author login (repeatable).",
    )
    args = parser.parse_args()

    since = None
    if args.since:
        try:
            since = parse_iso_timestamp(args.since)
        except ValueError as error:
            print(f"error: invalid --since timestamp: {error}", file=sys.stderr)
            return 1

    logins = tuple(args.coderabbit_login) if args.coderabbit_login else DEFAULT_CODERABBIT_LOGINS

    try:
        pr_payload = _load_json_file(args.pr_json, "--pr-json")
        threads_payload = _load_json_file(args.threads_json, "--threads-json")
        if not isinstance(pr_payload, dict):
            raise ValueError("expected a JSON object in the --pr-json file")
        result = evaluate_cycle(
            pr_payload,
            threads_payload,
            logins,
            since,
            args.previous_fingerprint,
            args.head_sha,
        )
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
