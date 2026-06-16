---
description: Start work on a Jira issue — create the correctly named work branch and move the issue into active development.
argument-hint: <JIRA-KEY> <feature|bugfix|hotfix|backport>
arguments: [issue, type]
---

Use the `mpt-ext-workflow-start-work` skill to start work.

- Jira issue: $issue
- Branch type: $type

If either argument is missing, ask for it before proceeding. Follow the skill exactly.
