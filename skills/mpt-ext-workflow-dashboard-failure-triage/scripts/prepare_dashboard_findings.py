#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


MIN_PYTHON = (3, 12)


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def clean_key(key: str) -> str:
    return key.strip().lstrip("\ufeff").strip('"')


def first_value(row: dict[str, Any], *names: str) -> str:
    normalized = {clean_key(str(key)): value for key, value in row.items()}
    for name in names:
        value = normalized.get(name)
        if value is not None:
            return str(value)
    return ""


def first_sample(row: dict[str, Any], *names: str) -> str:
    value = first_value(row, *names)
    if not value:
        return ""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    if isinstance(parsed, list) and parsed:
        return str(parsed[0])
    return value


def sample_values(row: dict[str, Any], *names: str, limit: int = 3) -> str:
    value = first_value(row, *names)
    if not value:
        return ""
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return value
    if not isinstance(parsed, list):
        return str(parsed)
    return ", ".join(str(item) for item in parsed[:limit])


def load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [{clean_key(key): value for key, value in row.items()} for row in reader]


def load_appinsights_json(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        return [dict(item) for item in data]

    tables = data.get("tables") or data.get("Tables") or []
    if not tables:
        value = data.get("value")
        if isinstance(value, list):
            return [dict(item) for item in value]
        raise ValueError("unsupported App Insights JSON shape: missing tables or value")

    table = tables[0]
    columns = [column["name"] if isinstance(column, dict) else str(column) for column in table["columns"]]
    rows = []
    for index, row in enumerate(table["rows"], start=1):
        try:
            rows.append(dict(zip(columns, row, strict=True)))
        except ValueError as error:
            raise ValueError(
                "App Insights JSON row length does not match columns "
                f"at row {index}: columns={len(columns)}, row={len(row)}"
            ) from error
    return rows


def compact_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def tail_lines(value: str, limit: int = 8) -> str:
    lines = [line.rstrip() for line in value.splitlines() if line.strip()]
    return "\n".join(lines[-limit:])


def failure_title(row: dict[str, Any]) -> str:
    error_type = first_value(row, "type", "outerType")
    message = first_value(row, "any_message", "message", "outerMessage")
    stack = first_value(row, "any_stack_trace", "stack_trace", "stackTrace")
    masked_url = first_value(row, "any_masked_url", "masked_url")

    source = compact_text(message) or compact_text(stack)
    if source:
        errors = re.findall(r"([A-Za-z0-9_.]+(?:Error|Exception)):\s*([^\n]+)", message or stack)
        if errors:
            error_name, error_message = errors[-1]
            title = f"{error_name.split('.')[-1]}: {compact_text(error_message)}"
        elif error_type:
            title = f"{error_type}: {source}"
        else:
            title = source
    elif error_type and masked_url:
        title = f"{error_type} on {masked_url}"
    else:
        title = error_type or masked_url or "Unknown dashboard failure"

    return title[:180]


def normalize_row(index: int, row: dict[str, Any]) -> dict[str, Any]:
    message = first_value(row, "any_message", "message", "outerMessage")
    stack = first_value(row, "any_stack_trace", "stack_trace", "stackTrace")
    preview_source = message or stack
    failures = first_value(row, "failures_count", "count_", "count")
    try:
        failures_count = int(float(failures))
    except ValueError:
        failures_count = 0

    return {
        "index": index,
        "cloud_RoleName": first_value(row, "cloud_RoleName"),
        "title": failure_title(row),
        "failures_count": failures_count,
        "operation_id": first_sample(
            row,
            "any_operation_Id",
            "operation_Id",
            "operation_id",
            "sample_operation_ids",
        ),
        "type": first_value(row, "type", "outerType"),
        "masked_url": first_value(row, "any_masked_url", "masked_url"),
        "resultCode": first_value(row, "resultCode"),
        "order_ids": sample_values(row, "sample_order_ids", "order_id", "orderId"),
        "agreement_ids": sample_values(
            row,
            "sample_agreement_ids",
            "agreement_id",
            "agreementId",
        ),
        "dependency_context": sample_values(
            row,
            "sample_dependency_names",
            "sample_request_names",
        ),
        "preview": tail_lines(preview_source),
    }


def markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = [
        "#",
        "cloud_RoleName",
        "Failure title",
        "Failures",
        "Type",
        "Result",
        "Masked URL",
        "Operation ID",
        "Orders",
        "Agreements",
        "Context",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "|---:|---|---|---:|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        values = [
            str(row["index"]),
            row["cloud_RoleName"],
            row["title"],
            str(row["failures_count"]),
            row["type"],
            row["resultCode"],
            row["masked_url"],
            row["operation_id"],
            row["order_ids"],
            row["agreement_ids"],
            row["dependency_context"],
        ]
        escaped = [str(value).replace("|", "\\|").replace("\n", "<br>") for value in values]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Normalize dashboard CSV or App Insights JSON into reviewable findings."
    )
    parser.add_argument("input", type=Path, help="Dashboard CSV or App Insights JSON file")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format",
    )
    args = parser.parse_args()

    if args.input.suffix.lower() == ".json":
        raw_rows = load_appinsights_json(args.input)
    else:
        raw_rows = load_csv(args.input)

    rows = [normalize_row(index, row) for index, row in enumerate(raw_rows, start=1)]
    rows.sort(key=lambda row: (row["cloud_RoleName"], -row["failures_count"], row["title"]))

    if args.format == "json":
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        print(markdown_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
