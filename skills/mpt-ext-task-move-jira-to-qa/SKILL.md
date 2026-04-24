---
name: mpt-ext-task-move-jira-to-qa
description: Move a Jira issue into QA after the reviewed pull request is merged. Use this task to read the current Jira issue state, confirm merge readiness has already been achieved, transition the issue to QA, and stop with a clear blocker when the work has not actually reached post-merge state yet.
---

# Move Jira To QA

## Purpose

Move a Jira issue into `QA` after the reviewed pull request has been merged.

## Use When

- The user wants to complete the development flow after merge.
- The task requires transitioning a Jira issue from review-complete state to `QA`.
- The pull request has already been merged or the user explicitly confirms the work is in post-merge state.

## Do Not Use When

- The task is to start work and move Jira issues to `In Progress`.
- The task is to hand work over for review and move the issue to `Code Review`.
- The task is to create or update a pull request.
- The task is to process PR review comments.

## Inputs

- Jira issue key.
- Confirmation that the relevant pull request was already merged.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Jira authentication is available and the target issue can be read and transitioned through `mpt-ext-tool-jira-workitem-ops`.
- The repository workflow exposes a usable transition into `QA`.
- The corresponding pull request has been merged, or the user explicitly confirms the work is in post-merge state.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs only when the repository defines Jira workflow or post-merge handoff exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Read the Jira issue first.
- Use `mpt-ext-tool-jira-workitem-ops` to fetch the current issue state.
- Confirm the issue exists and identify its current workflow status.

3. Verify post-merge readiness.
- Confirm the relevant pull request was already merged.
- If merge state is unclear from the current workflow context, ask the user before moving the issue.
- If the work is still under review or not yet merged, stop and explain that the issue should not move to `QA` yet.

4. Transition the issue to `QA`.
- Use `mpt-ext-tool-jira-workitem-ops` to move the Jira issue to `QA` when it is not already there.
- Preserve already-correct state rather than rewriting it unnecessarily.

5. Report the result clearly.
- State whether the issue moved to `QA`.
- State whether the issue was already in `QA`.
- Show blockers clearly when Jira workflow rules, permissions, or missing merge confirmation prevent completion.

## Guardrails

- Never move the issue to `QA` before the relevant PR is merged.
- Never assume merge completion when the workflow context is ambiguous.
- Never rewrite already-correct Jira state without need.
- Never mix merge execution, PR comment handling, or branch operations into this task.

## Expected Outcome

The Jira issue is in `QA` once the reviewed work is merged, or the task stops with a clear blocker that explains why the issue should not move to `QA` yet.
