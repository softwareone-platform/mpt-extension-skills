#!/usr/bin/env python3
import argparse
import json
import re
import sys


STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "it",
    "of",
    "or",
    "that",
    "the",
    "this",
    "to",
    "try",
    "using",
    "with",
}


def render_slug(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    useful_words = [word for word in words if word not in STOP_WORDS]
    return "-".join(useful_words)


def is_valid_jira_key(jira_key: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", jira_key))


def render_branch_name(branch_type: str, jira_key: str, slug: str) -> str:
    if branch_type in {"feature", "bugfix"}:
        return f"{branch_type}/{jira_key}/{slug}"
    if branch_type == "hotfix":
        return f"hotfix-{branch_type}/{jira_key}/{slug}"
    if branch_type == "backport":
        return f"backport-{branch_type}/{jira_key}/{slug}"
    raise ValueError(f"unsupported branch type: {branch_type}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a Jira-based work branch name from issue text."
    )
    parser.add_argument("--jira-key", required=True, help="Jira issue key")
    parser.add_argument(
        "--branch-type",
        choices=("feature", "bugfix", "hotfix", "backport"),
        required=True,
        help="Work branch type",
    )
    parser.add_argument("--title", help="Jira issue title or summary")
    parser.add_argument("--description", help="Fallback Jira issue description")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of only the branch name",
    )
    args = parser.parse_args()

    source_name = "title"
    source_text = (args.title or "").strip()
    if not source_text:
        source_name = "description"
        source_text = (args.description or "").strip()

    if not source_text:
        print("error: provide --title or --description", file=sys.stderr)
        return 1

    jira_key = args.jira_key.strip().upper()
    if not is_valid_jira_key(jira_key):
        print(
            "error: --jira-key must match PROJECT-123 format",
            file=sys.stderr,
        )
        return 1

    slug = render_slug(source_text)
    if not slug:
        print("error: issue text did not produce a branch slug", file=sys.stderr)
        return 1

    branch_name = render_branch_name(args.branch_type, jira_key, slug)
    if args.json:
        json.dump(
            {
                "jira_key": jira_key,
                "branch_type": args.branch_type,
                "source": source_name,
                "short_description": slug,
                "branch_name": branch_name,
            },
            sys.stdout,
        )
        sys.stdout.write("\n")
    else:
        print(branch_name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
