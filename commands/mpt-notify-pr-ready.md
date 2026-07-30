---
description: Notify a Teams chat that a reviewed PR is ready — post its details when all checks pass and CodeRabbit has approved.
argument-hint: [<pr-or-branch>] [--to <destination>]
arguments: [target, destination]
---

Use the `mpt-ext-workflow-notify-pr-ready` skill to notify a Microsoft Teams chat that a reviewed PR is ready.

- PR or branch: $target (default to the current branch's PR when omitted)
- Destination override: $destination (optional `--to` value)

Evaluate the green gate once and do not wait or poll. Follow the skill exactly.
