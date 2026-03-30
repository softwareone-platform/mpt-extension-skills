#!/usr/bin/env bash
set -euo pipefail

branch="${1:-$(git rev-parse --abbrev-ref HEAD)}"

# Expect branch prefix like ABC-123-description or abc-123-description
if [[ "$branch" =~ ^([A-Za-z][A-Za-z0-9]+-[0-9]+)- ]]; then
  echo "${BASH_REMATCH[1]}" | tr '[:lower:]' '[:upper:]'
  exit 0
fi

echo "Could not parse PR key from branch '$branch'. Expected <PR_KEY>-<description>." >&2
exit 1
