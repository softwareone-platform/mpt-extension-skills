---
name: mpt-ext-task-start-jira-work
description: Start Jira work on an issue when users begin implementing a feature, bugfix, hotfix, or backport. Use this task to move the issue and its full parent chain to In Progress, verify that the issue belongs to the active sprint, add the active sprint when missing, and check whether reassignment to the current Jira-authenticated user is needed.
---

# Start Jira Work

## Purpose

Prepare a Jira issue for active development by setting the correct working state.

## Use When

- The user starts work on a Jira issue.
- The issue should move to `In Progress`.
- Parent issues should also move to `In Progress`.
- The issue must be checked against the active sprint.
- The assignee must be checked against the current Jira-authenticated user.

## Do Not Use When

- The task is only to create or switch Git branches.
- The task is only to open or update a pull request.
- The task is only to read Jira issue data without changing working state.
- The task is to finish development and move the issue to `Code Review` or `QA`.

## Inputs

- Jira issue key.
- Optional sprint or board context when the active sprint cannot be determined automatically.
- Optional user confirmation when reassignment or sprint changes are needed.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Jira authentication is active and the current user can read, transition, and update the target issue and its parent chain.
- The current user has the Jira permissions needed for state transitions, sprint updates, and assignee changes when confirmed by the user.
- The repository or board context is sufficient to determine the active sprint, or the user is available to provide the missing board or sprint context before changes are made.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs only when the repository defines Jira workflow or contribution exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Read the Jira issue and Jira auth context.
- Use `mpt-ext-tool-jira-workitem-ops` to fetch the current issue state.
- Determine the currently authenticated Jira user from Jira auth context.

3. Resolve the full parent chain.
- Read the direct parent of the issue if it exists.
- Continue reading parent issues until the full parent chain is known.
- Stop only when the chain has no further parent.

4. Move the issue and parent chain to `In Progress`.
- Transition the current issue to `In Progress` when it is not already there.
- Transition each parent issue in the chain to `In Progress` when it is not already there.
- Preserve already-correct status values rather than rewriting them unnecessarily.

5. Verify sprint placement.
- Check whether the Jira issue belongs to the active sprint.
- If the issue is missing from the active sprint, add it.
- If the active sprint cannot be determined reliably from the available Jira context, ask the user for the correct board or sprint context before changing sprint placement.

6. Verify assignee.
- Compare the issue assignee with the current Jira-authenticated user.
- If they differ, ask the user whether the issue should be reassigned to the current Jira user.
- Reassign only when the user confirms.

7. Report the result clearly.
- State whether the issue moved to `In Progress`.
- State whether any parent issues moved to `In Progress`.
- State whether sprint placement changed.
- State whether reassignment was requested, skipped, or completed.

## Guardrails

- Never assume the active sprint if Jira context is ambiguous.
- Never reassign the issue automatically when the assignee differs from the current Jira-authenticated user.
- Never stop at the direct parent when a longer parent chain exists.
- Never rewrite already-correct Jira state without need.
- Never mix branch creation or PR operations into this task.

## Expected Outcome

The Jira issue and its full parent chain are in `In Progress`, the issue is placed in the active sprint when required, assignee mismatches are surfaced for confirmation, and any blockers are reported clearly.
