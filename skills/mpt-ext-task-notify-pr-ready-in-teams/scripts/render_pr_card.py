#!/usr/bin/env python3
"""Render the Adaptive Card body for a "PR ready" Teams notification.

Deterministically templates the pull-request facts into an Adaptive Card
(``type: AdaptiveCard``) that the Teams send-message tool wraps and posts.
Only the card content is built here; resolving the destination, evaluating the
"green" gate, and posting are handled elsewhere in the skill.

PR-supplied text (title, author, repository, branch names) and the optional
user comment are placed into the card as data only; they never control the
card structure.
"""
import argparse
import json
import re
import sys


MIN_PYTHON = (3, 12)

ADAPTIVE_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ADAPTIVE_VERSION = "1.4"
GREEN_TICK = "✅"
RED_CROSS = "❌"
AVATAR_URL = "https://avatars.githubusercontent.com/{login}?size=64"
FACT_TITLE_WIDTH = "100px"
AVATAR_SIZE = "20px"
COMMENT_ICON = "💬"
COMMENT_MAX_LENGTH = 500


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


# Markdown control characters to neutralize. Adaptive Card TextBlock.text and
# FactSet title/value render a Markdown subset, so PR-authored text could inject
# spoofed links (`[x](y)`) or emphasis unless these are escaped.
_MD_SPECIAL = set("\\`*_[]()~|")


def md_escape(value) -> str:
    """Backslash-escape Markdown control characters in untrusted text."""
    return "".join("\\" + ch if ch in _MD_SPECIAL else ch for ch in str(value))


def _fact(title: str, value: str | None) -> dict | None:
    if value is None or str(value).strip() == "":
        return None
    return {"title": title, "value": md_escape(value)}


def _ready_state_value(value: str | None, expected: str) -> str | None:
    if value is None or not value.strip():
        return None
    return GREEN_TICK if value.casefold() == expected.casefold() else RED_CROSS


def _comment_text(comment: str | None) -> str | None:
    """Return the escaped comment text, capped in length, or None when empty."""
    text = str(comment or "").strip()
    if not text:
        return None
    if len(text) > COMMENT_MAX_LENGTH:
        text = text[: COMMENT_MAX_LENGTH - 1].rstrip() + "…"
    # Card Markdown joins single line breaks, so each line becomes a paragraph.
    lines = [md_escape(line.strip()) for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)


def _plural(count: int, noun: str) -> str:
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def _changes(commits, additions, deletions, changed_files) -> str | None:
    parts = []
    if commits:
        parts.append(_plural(commits, "commit"))
    if additions is not None and deletions is not None:
        parts.append(f"+{additions} -{deletions}")
    if changed_files is not None:
        parts.append(f"{_plural(changed_files, 'file')} changed")
    return " · ".join(parts) or None


def _fact_value(fact: dict) -> dict:
    text = {"type": "TextBlock", "text": fact["value"], "wrap": True}
    if not fact.get("avatar_url"):
        return text
    avatar = {
        "type": "Image",
        "url": fact["avatar_url"],
        "width": AVATAR_SIZE,
        "height": AVATAR_SIZE,
        "style": "person",
    }
    return {
        "type": "ColumnSet",
        "columns": [
            {"type": "Column", "width": "auto", "items": [avatar]},
            {
                "type": "Column",
                "width": "stretch",
                "spacing": "small",
                "verticalContentAlignment": "center",
                "items": [text],
            },
        ],
    }


def fact_rows(facts: list[dict]) -> dict:
    """Lay facts out as title/value rows.

    A FactSet value can only hold text, so the facts are rendered as rows with a
    fixed-width title column instead; this keeps every row aligned while letting
    the Author row show the avatar next to the name.
    """
    rows = []
    for index, fact in enumerate(facts):
        row = {
            "type": "ColumnSet",
            "columns": [
                {
                    "type": "Column",
                    "width": FACT_TITLE_WIDTH,
                    "items": [
                        {"type": "TextBlock", "text": fact["title"], "weight": "bolder", "wrap": True}
                    ],
                },
                {"type": "Column", "width": "stretch", "items": [_fact_value(fact)]},
            ],
        }
        if index:
            row["spacing"] = "none"
        rows.append(row)
    return {"type": "Container", "items": rows}


def build_card(
    *,
    title: str,
    number,
    url: str,
    author: str | None = None,
    repository: str | None = None,
    branch: str | None = None,
    base: str | None = None,
    jira_url: str | None = None,
    checks_state: str | None = None,
    coderabbit_state: str | None = None,
    avatar_url: str | None = None,
    commits: int | None = None,
    additions: int | None = None,
    deletions: int | None = None,
    changed_files: int | None = None,
    comment: str | None = None,
) -> dict:
    if not str(title).strip():
        raise ValueError("--title must not be empty")
    if not str(url).strip():
        raise ValueError("--url must not be empty")

    checks_value = _ready_state_value(checks_state, "success")
    coderabbit_value = _ready_state_value(coderabbit_state, "APPROVED")
    # The header must agree with the facts: a supplied failing state turns it red.
    ready = RED_CROSS not in (checks_value, coderabbit_value)
    readiness = "ready for merge" if ready else "not ready for merge"
    heading = f"PR #{number} {readiness}" if number else f"Pull request {readiness}"
    author_fact = _fact("Author", author)
    if author_fact and avatar_url:
        author_fact["avatar_url"] = avatar_url
    facts = [
        f
        for f in (
            author_fact,
            _fact("Repository", repository),
            _fact("Branch", f"{branch} → {base}" if branch and base else branch or base),
            _fact("Changes", _changes(commits, additions, deletions, changed_files)),
            _fact("Checks", checks_value),
            _fact("CodeRabbit", coderabbit_value),
        )
        if f is not None
    ]

    body: list[dict] = [
        # The heading sits in a band that bleeds to the card edges, so it stands
        # apart from the bold PR title and the facts below it.
        {
            "type": "Container",
            "style": "good" if ready else "attention",
            "bleed": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"{GREEN_TICK if ready else RED_CROSS} {heading}",
                    "weight": "bolder",
                    "size": "large",
                    "wrap": True,
                }
            ],
        },
    ]
    comment_text = _comment_text(comment)
    if comment_text:
        # An inset note in the warning (yellow) style, so it is noticed first.
        body.append(
            {
                "type": "Container",
                "style": "warning",
                "spacing": "medium",
                "items": [
                    {"type": "TextBlock", "text": f"{COMMENT_ICON} {comment_text}", "wrap": True}
                ],
            }
        )
    body.append(
        {
            "type": "TextBlock",
            "text": md_escape(title),
            "weight": "bolder",
            "spacing": "medium",
            "wrap": True,
        }
    )
    if facts:
        body.append(fact_rows(facts))

    actions: list[dict] = [{"type": "Action.OpenUrl", "title": "Open PR", "url": url}]
    if jira_url and jira_url.strip():
        actions.append({"type": "Action.OpenUrl", "title": "Open Jira", "url": jira_url})

    return {
        "type": "AdaptiveCard",
        "$schema": ADAPTIVE_SCHEMA,
        "version": ADAPTIVE_VERSION,
        "body": body,
        "actions": actions,
    }


_PR_URL = re.compile(r"^https://github\.com/([^/\s]+/[^/\s]+)/pull/\d+")


def _repository_from_url(url) -> str | None:
    """Return ``owner/repo`` from a GitHub PR URL, or None when it does not match."""
    match = _PR_URL.match(str(url or ""))
    return match.group(1) if match else None


_LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")


def _avatar_url(login) -> str | None:
    """Return the public GitHub avatar URL for a user login, or None for bots/teams."""
    return AVATAR_URL.format(login=login) if login and _LOGIN.match(str(login)) else None


def _count(value) -> int | None:
    return len(value) if isinstance(value, list) else None


def fields_from_snapshot(data: dict) -> dict:
    """Extract card fields from a ``gh pr view --json ...`` snapshot object.

    Reading the fields here (as JSON data) keeps untrusted PR-authored values
    such as the title, author, and branch names out of any shell command line.
    """
    author = data.get("author")
    author_name = None
    author_login = None
    if isinstance(author, dict):
        author_login = author.get("login")
        author_name = author_login or author.get("name")
    return {
        "title": data.get("title"),
        "number": data.get("number"),
        "url": data.get("url"),
        "author": author_name,
        "repository": _repository_from_url(data.get("url")),
        "branch": data.get("headRefName"),
        "base": data.get("baseRefName"),
        "avatar_url": _avatar_url(author_login),
        "commits": _count(data.get("commits")),
        "additions": data.get("additions"),
        "deletions": data.get("deletions"),
        "changed_files": data.get("changedFiles"),
    }


def load_snapshot(path: str) -> dict:
    """Load the PR JSON snapshot from a file path, or from stdin when path is '-'."""
    text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("--pr-json must contain a 'gh pr view' JSON object")
    return data


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Render the Adaptive Card for a PR-ready Teams notification."
    )
    parser.add_argument(
        "--pr-json",
        help="Path to a 'gh pr view --json ...' snapshot (or '-' for stdin); "
        "PR fields are read from it as data instead of the shell.",
    )
    parser.add_argument("--title", help="PR title (overrides --pr-json).")
    parser.add_argument("--url", help="PR URL (overrides --pr-json).")
    parser.add_argument("--number", help="PR number (overrides --pr-json).")
    parser.add_argument("--author", help="PR author (overrides --pr-json).")
    parser.add_argument(
        "--repository", help="Repository as owner/repo (overrides --pr-json, derived from its URL)."
    )
    parser.add_argument("--branch", help="Head branch name (overrides --pr-json).")
    parser.add_argument("--base", help="Base branch name (overrides --pr-json).")
    parser.add_argument(
        "--commit-count",
        type=int,
        help="Exact commit count, e.g. from the REST pulls endpoint (overrides --pr-json, "
        "whose commits list gh caps).",
    )
    parser.add_argument("--jira-url", help="Linked Jira issue URL, when known.")
    parser.add_argument("--checks-state", help="Summary of the checks state, e.g. 'success'.")
    parser.add_argument("--coderabbit-state", help="CodeRabbit review state, e.g. 'APPROVED'.")
    parser.add_argument(
        "--comment-file",
        help="Path to a file with an optional user comment, shown under the header; "
        "read as data instead of the shell.",
    )
    args = parser.parse_args()

    snapshot: dict = {}
    if args.pr_json:
        try:
            snapshot = fields_from_snapshot(load_snapshot(args.pr_json))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    comment = None
    if args.comment_file:
        try:
            with open(args.comment_file, encoding="utf-8") as handle:
                comment = handle.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    def pick(flag, key):
        return flag if flag is not None else snapshot.get(key)

    try:
        card = build_card(
            title=pick(args.title, "title") or "",
            number=pick(args.number, "number"),
            url=pick(args.url, "url") or "",
            author=pick(args.author, "author"),
            repository=pick(args.repository, "repository"),
            branch=pick(args.branch, "branch"),
            base=pick(args.base, "base"),
            jira_url=args.jira_url,
            checks_state=args.checks_state,
            coderabbit_state=args.coderabbit_state,
            # The snapshot avatar belongs to the snapshot author, not an --author override.
            avatar_url=snapshot.get("avatar_url") if args.author is None else None,
            commits=pick(args.commit_count, "commits"),
            additions=snapshot.get("additions"),
            deletions=snapshot.get("deletions"),
            changed_files=snapshot.get("changed_files"),
            comment=comment,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(card, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
