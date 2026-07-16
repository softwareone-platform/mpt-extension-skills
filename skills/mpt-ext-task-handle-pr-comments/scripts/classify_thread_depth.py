#!/usr/bin/env python3
"""Classify PR review-thread depth for the reviewer-call feature.

Given a review thread's comments (in chronological order) and the agent's login,
deterministically decide whether the agent's *next* reply would sit on top of an
existing back-and-forth: an earlier agent reply followed by a reviewer
counter-reply (original comment -> agent reply -> reviewer reply -> next reply).

When ``next_reply_is_back_and_forth`` is true, ``mpt-ext-task-handle-pr-comments``
pauses and asks the user whether a quick call with the reviewer would resolve the
disagreement faster than another written reply. This script only computes the
fact; it never posts anything.
"""
import argparse
import json
import sys


MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def comment_author(comment: dict) -> str:
    """Extract a login from common comment shapes (GitHub API or simplified)."""
    for key in ("user", "author"):
        value = comment.get(key)
        if isinstance(value, dict):
            login = value.get("login")
            if login:
                return str(login)
        elif isinstance(value, str) and value:
            return value
    login = comment.get("login")
    if login:
        return str(login)
    return ""


def classify_thread_depth(comments: list, agent_login: str) -> dict:
    normalized_agent = agent_login.strip().lower()
    if not normalized_agent:
        raise ValueError("agent_login is empty")

    for index, comment in enumerate(comments):
        if not isinstance(comment, dict):
            raise ValueError(f"comment at index {index} is not an object")

    authors = [comment_author(c) for c in comments]
    is_agent = [a.strip().lower() == normalized_agent for a in authors]

    has_agent_reply = any(is_agent)

    # A reviewer counter-reply is a non-agent comment that appears after the
    # first agent comment in the thread.
    has_reviewer_counter_reply = False
    first_agent_index = next((i for i, flag in enumerate(is_agent) if flag), None)
    if first_agent_index is not None:
        has_reviewer_counter_reply = any(
            not flag for flag in is_agent[first_agent_index + 1:]
        )

    return {
        "agent_login": agent_login.strip(),
        "comment_count": len(comments),
        "authors": authors,
        "agent_reply_count": sum(is_agent),
        "has_agent_reply": has_agent_reply,
        "has_reviewer_counter_reply": has_reviewer_counter_reply,
        "next_reply_is_back_and_forth": has_agent_reply and has_reviewer_counter_reply,
    }


def _extract_comments(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("comments"), list):
        return payload["comments"]
    raise ValueError("expected a JSON array of comments or an object with 'comments'")


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Classify PR review-thread depth for the reviewer-call feature."
    )
    parser.add_argument("--agent-login", required=True, help="the agent's GitHub login")
    parser.add_argument(
        "--comments-file",
        help="path to thread comments JSON (array or {comments:[...]}); default stdin",
    )
    args = parser.parse_args()

    try:
        if args.comments_file:
            with open(args.comments_file, encoding="utf-8") as handle:
                text = handle.read()
        else:
            text = sys.stdin.read()
    except OSError as error:
        print(f"error: cannot read {args.comments_file}: {error}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"error: invalid JSON: {error}", file=sys.stderr)
        return 1

    try:
        result = classify_thread_depth(_extract_comments(payload), args.agent_login)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
