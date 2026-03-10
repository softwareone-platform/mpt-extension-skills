#!/usr/bin/env bash
set -euo pipefail

summary="${1:-}"

if [[ -z "$summary" ]]; then
  echo "Usage: $0 '<summary line>'" >&2
  exit 1
fi

cat <<BODY
🤖 **AI-generated PR** — Please review carefully.

## Summary
- ${summary}

BODY
