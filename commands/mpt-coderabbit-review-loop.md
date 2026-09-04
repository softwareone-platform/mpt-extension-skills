---
description: Loop CodeRabbit review iterations on the open PR — address bot feedback and re-push until CodeRabbit approves or a safeguard stops the loop with a report.
argument-hint: [<pr-or-branch>]
arguments: [target]
---

Use the `mpt-ext-workflow-coderabbit-review-loop` skill to drive the pull request to CodeRabbit approval.

- PR or branch: $target (default to the current branch's PR when omitted)

Run at most 5 iterations, report every iteration, and stop with a classified outcome. Follow the skill exactly.
