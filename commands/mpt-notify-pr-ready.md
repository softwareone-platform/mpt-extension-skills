---
description: Notify a Teams chat that a reviewed PR is ready — post its details when all checks pass and CodeRabbit has approved.
argument-hint: [<pr-number>] [--to <destination>] [--] [<comment>]
---

Use the `mpt-ext-workflow-notify-pr-ready` skill to notify a Microsoft Teams chat that a reviewed PR is ready.

Request: $ARGUMENTS

Read the request from the start, in this order:

- PR: the first word, only when it is a PR number (`144` or `#144`); otherwise use the current branch's PR.
- Destination override: `--to <destination>`, only when it comes next.
- Comment: all remaining text, verbatim, shown on the card. A standalone `--` ends the options, so everything after it is the comment, even text that starts with a number or `--to`. Omit the comment when no text remains.

Evaluate the green gate once and do not wait or poll. Follow the skill exactly.
