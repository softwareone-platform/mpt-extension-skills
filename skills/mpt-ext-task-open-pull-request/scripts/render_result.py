#!/usr/bin/env python3
import argparse
import re
import sys
from urllib.parse import urlparse


def normalize_jira_site(site: str) -> str:
    normalized_site = site.strip().removeprefix("Site:").strip()
    if not normalized_site:
        return ""
    if normalized_site.startswith(("http://", "https://")):
        parsed = urlparse(normalized_site)
        return parsed.netloc or parsed.path
    return normalized_site


def render_jira_url(site: str, issue_key: str) -> str:
    normalized_site = normalize_jira_site(site)
    normalized_key = issue_key.strip().upper()
    if not normalized_site or not normalized_key:
        return ""
    if not re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", normalized_key):
        return ""
    return f"https://{normalized_site}/browse/{normalized_key}"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render compact pull request result output."
    )
    parser.add_argument("--pr-url", required=True)
    parser.add_argument("--testing", required=True)
    parser.add_argument("--jira-site")
    parser.add_argument("--jira-key")
    args = parser.parse_args()

    pr_url = args.pr_url.strip()
    testing = args.testing.strip()
    if not pr_url:
        print("error: provide --pr-url", file=sys.stderr)
        return 1
    if not testing:
        print("error: provide --testing", file=sys.stderr)
        return 1

    print(f"PR: {pr_url}")
    jira_url = render_jira_url(args.jira_site or "", args.jira_key or "")
    if jira_url:
        print(f"Jira: {jira_url}")
    print(f"Testing: {testing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
