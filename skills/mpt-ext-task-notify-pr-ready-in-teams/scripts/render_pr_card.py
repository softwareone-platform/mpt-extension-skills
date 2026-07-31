#!/usr/bin/env python3
"""Render the Adaptive Card body for a "PR ready" Teams notification.

Deterministically templates the pull-request facts into an Adaptive Card
(``type: AdaptiveCard``) that the Teams send-message tool wraps and posts.
Only the card content is built here; resolving the destination, evaluating the
"green" gate, and posting are handled elsewhere in the skill.

PR-supplied text (title, author, branch names) is placed into the card as data
only; it never controls the card structure.
"""
import argparse
import json
import sys


MIN_PYTHON = (3, 12)

ADAPTIVE_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ADAPTIVE_VERSION = "1.4"
GREEN_TICK = "✅"
RED_CROSS = "❌"


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


def build_card(
    *,
    title: str,
    number,
    url: str,
    author: str | None = None,
    branch: str | None = None,
    base: str | None = None,
    jira_url: str | None = None,
    checks_state: str | None = None,
    coderabbit_state: str | None = None,
) -> dict:
    if not str(title).strip():
        raise ValueError("--title must not be empty")
    if not str(url).strip():
        raise ValueError("--url must not be empty")

    heading = f"PR #{number} ready for merge" if number else "Pull request ready for merge"
    facts = [
        f
        for f in (
            _fact("Author", author),
            _fact("Branch", f"{branch} → {base}" if branch and base else branch or base),
            _fact("Checks", _ready_state_value(checks_state, "success")),
            _fact("CodeRabbit", _ready_state_value(coderabbit_state, "APPROVED")),
        )
        if f is not None
    ]

    body: list[dict] = [
        {
            "type": "TextBlock",
            "text": heading,
            "weight": "bolder",
            "size": "medium",
            "wrap": True,
        },
        {"type": "TextBlock", "text": md_escape(title), "wrap": True},
    ]
    if facts:
        body.append({"type": "FactSet", "facts": facts})

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


def fields_from_snapshot(data: dict) -> dict:
    """Extract card fields from a ``gh pr view --json ...`` snapshot object.

    Reading the fields here (as JSON data) keeps untrusted PR-authored values
    such as the title, author, and branch names out of any shell command line.
    """
    author = data.get("author")
    author_name = None
    if isinstance(author, dict):
        author_name = author.get("login") or author.get("name")
    return {
        "title": data.get("title"),
        "number": data.get("number"),
        "url": data.get("url"),
        "author": author_name,
        "branch": data.get("headRefName"),
        "base": data.get("baseRefName"),
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
    parser.add_argument("--branch", help="Head branch name (overrides --pr-json).")
    parser.add_argument("--base", help="Base branch name (overrides --pr-json).")
    parser.add_argument("--jira-url", help="Linked Jira issue URL, when known.")
    parser.add_argument("--checks-state", help="Summary of the checks state, e.g. 'success'.")
    parser.add_argument("--coderabbit-state", help="CodeRabbit review state, e.g. 'APPROVED'.")
    args = parser.parse_args()

    snapshot: dict = {}
    if args.pr_json:
        try:
            snapshot = fields_from_snapshot(load_snapshot(args.pr_json))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
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
            branch=pick(args.branch, "branch"),
            base=pick(args.base, "base"),
            jira_url=args.jira_url,
            checks_state=args.checks_state,
            coderabbit_state=args.coderabbit_state,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(card, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
