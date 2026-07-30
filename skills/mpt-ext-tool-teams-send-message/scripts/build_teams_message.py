#!/usr/bin/env python3
"""Build the Microsoft Teams "workflow webhook" message envelope.

Teams "Send webhook alerts to chat" (Power Automate Workflows incoming webhook)
does not accept a bare MessageCard the way the legacy Office 365 connector did.
It expects a message envelope whose attachment carries an Adaptive Card:

    {"type": "message",
     "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive",
                      "contentUrl": null,
                      "content": { <adaptive card> }}]}

This script builds that envelope deterministically so callers can POST it as-is.
Give it either an existing Adaptive Card (``--card-file``) or a plain text body
(``--text``), from which it wraps a minimal single-TextBlock card.

The script only renders JSON; POSTing it to the resolved webhook URL is the
caller's step (see the skill).
"""
import argparse
import json
import sys


MIN_PYTHON = (3, 12)

ADAPTIVE_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"
ADAPTIVE_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ADAPTIVE_VERSION = "1.4"


def require_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print("error: Python 3.12 or later is required", file=sys.stderr)
        raise SystemExit(1)


def text_card(text: str) -> dict:
    """Wrap a plain-text body into a minimal Adaptive Card."""
    return {
        "type": "AdaptiveCard",
        "$schema": ADAPTIVE_SCHEMA,
        "version": ADAPTIVE_VERSION,
        "body": [{"type": "TextBlock", "text": text, "wrap": True}],
    }


def is_adaptive_card(card: object) -> bool:
    # A top-level Adaptive Card requires both "type" and a non-empty "version".
    return (
        isinstance(card, dict)
        and card.get("type") == "AdaptiveCard"
        and isinstance(card.get("version"), str)
        and card["version"].strip() != ""
    )


def build_envelope(card: dict) -> dict:
    """Wrap an Adaptive Card into the Teams workflow-webhook message envelope."""
    if not is_adaptive_card(card):
        raise ValueError("card must be an Adaptive Card object with type 'AdaptiveCard'")
    return {
        "type": "message",
        "attachments": [
            {
                "contentType": ADAPTIVE_CONTENT_TYPE,
                "contentUrl": None,
                "content": card,
            }
        ],
    }


def load_card(text: str | None, card_file: str | None) -> dict:
    if (text is None) == (card_file is None):
        raise ValueError("provide exactly one of --text or --card-file")
    if card_file is not None:
        with open(card_file, encoding="utf-8") as handle:
            card = json.load(handle)
        if not is_adaptive_card(card):
            raise ValueError("--card-file must contain an Adaptive Card (type 'AdaptiveCard')")
        return card
    # Check emptiness with strip(), but pass the original text through so the
    # caller's leading/trailing whitespace is delivered verbatim.
    if not text.strip():
        raise ValueError("--text must not be empty")
    return text_card(text)


def main() -> int:
    require_python_version()

    parser = argparse.ArgumentParser(
        description="Build the Teams workflow-webhook message envelope from a card or text."
    )
    parser.add_argument("--text", help="Plain-text body wrapped into a minimal Adaptive Card")
    parser.add_argument("--card-file", help="Path to a JSON file holding an Adaptive Card")
    args = parser.parse_args()

    try:
        card = load_card(args.text, args.card_file)
        envelope = build_envelope(card)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    json.dump(envelope, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
