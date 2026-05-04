#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any


def read_json(path: str) -> Any:
    with Path(path).open(encoding="utf-8") as file_obj:
        return json.load(file_obj)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def render_bullet_list(values: list[Any], empty: str = "none") -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def render_validation(validation: list[dict[str, Any]]) -> list[str]:
    if not validation:
        return ["- not run"]
    lines = []
    for item in validation:
        command = item.get("command", "unknown command")
        status = item.get("status", "unknown")
        lines.append(f"- `{command}`: {status}")
    return lines


def render_pr_result(item: dict[str, Any]) -> list[str]:
    number = item.get("number") or item.get("pr_number") or "unknown"
    url = item.get("url") or item.get("pr_url") or ""
    status = item.get("status") or ("skipped" if item.get("skip_reason") else "processed")
    title = f"### PR #{number}"
    if url:
        title += f" - {url}"

    lines = [title, "", f"- Status: {status}"]
    skip_reason = item.get("skip_reason")
    if skip_reason:
        lines.append(f"- Skip reason: {skip_reason}")

    rules = as_list(item.get("fixed_rules") or item.get("violated_rules"))
    lines.append("- Rules:")
    lines.extend(render_bullet_list(rules))

    changed_files = as_list(item.get("changed_files"))
    lines.append("- Changed files:")
    lines.extend(render_bullet_list(changed_files))

    validation = as_list(item.get("validation"))
    lines.append("- Validation:")
    lines.extend(render_validation(validation))

    amended_sha = item.get("amended_sha") or item.get("commit_sha")
    push_result = item.get("push_result")
    if amended_sha:
        lines.append(f"- Amended commit: `{amended_sha}`")
    if push_result:
        lines.append(f"- Push: {push_result}")
    return lines


def normalize_results(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, dict):
        if isinstance(raw.get("results"), list):
            return [item for item in raw["results"] if isinstance(item, dict)]
        return [raw]
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a stable markdown report for Dependabot PR policy fixes."
    )
    parser.add_argument("--results-json", required=True, help="Result JSON file")
    args = parser.parse_args()

    results = normalize_results(read_json(args.results_json))
    if not results:
        print("error: --results-json did not contain any result objects", file=sys.stderr)
        return 1

    output = ["## Dependabot PR Policy Fix Results", ""]
    for index, result in enumerate(results):
        if index:
            output.append("")
        output.extend(render_pr_result(result))

    print("\n".join(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
