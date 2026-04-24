---
name: mpt-ext-task-move-jira-to-qa
description: Move a Jira issue into the correct post-merge Jira status after the reviewed pull request is merged. Use this task to read the current Jira issue state, confirm merge readiness has already been achieved, resolve the correct post-merge target status from issue context and repository rules, transition the issue accordingly, and stop with a clear blocker when the work has not actually reached post-merge state yet.
---

# Move Jira After Merge

## Purpose

Move a Jira issue into the correct post-merge Jira status after the reviewed pull request has been merged.

## Use When

- The user wants to complete the development flow after merge.
- The task requires transitioning a Jira issue from review-complete state to its post-merge Jira status.
- The pull request has already been merged or the user explicitly confirms the work is in post-merge state.

## Do Not Use When

- The task is to start work and move Jira issues to `In Progress`.
- The task is to hand work over for review and move the issue to `Code Review`.
- The task is to create or update a pull request.
- The task is to process PR review comments.

## Inputs

- Jira issue key.
- Confirmation that the relevant pull request was already merged.
- Optional repository-specific post-merge target status when local docs define one explicitly.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Jira authentication is available and the target issue can be read and transitioned through `mpt-ext-tool-jira-workitem-ops`.
- The repository workflow exposes a usable transition into the correct post-merge status for the issue type.
- The corresponding pull request has been merged, or the user explicitly confirms the work is in post-merge state.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs only when the repository defines Jira workflow or post-merge handoff exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Read the Jira issue first.
- Use `mpt-ext-tool-jira-workitem-ops` to fetch the current issue state.
- Confirm the issue exists and identify its current workflow status and issue type.

3. Verify post-merge readiness.
- Confirm the relevant pull request was already merged.
- If merge state is unclear from the current workflow context, ask the user before moving the issue.
- If the work is still under review or not yet merged, stop and explain that the issue should not move to a post-merge status yet.

4. Resolve the target post-merge status.
- Follow repository-specific Jira workflow or post-merge handoff docs when they define the target status explicitly.
- If the Jira issue is a subtask, default the target status to `Done`.
- Otherwise default the target status to `QA`.
- If the issue is already in the resolved post-merge target status, preserve the current state rather than rewriting it unnecessarily.

5. Transition the issue to the resolved post-merge status.
- Use `mpt-ext-tool-jira-workitem-ops` to move the Jira issue to the resolved target status when it is not already there.
- If the resolved target status is not allowed by the actual Jira workflow, stop and report the blocker instead of guessing another status silently.

6. Report the result clearly.
- State which post-merge target status was selected.
- State whether the issue moved to that status.
- State whether the issue was already in that status.
- Show blockers clearly when Jira workflow rules, permissions, or missing merge confirmation prevent completion.

## Guardrails

- Never move the issue to a post-merge status before the relevant PR is merged.
- Never assume merge completion when the workflow context is ambiguous.
- Never hard-code `QA` for subtasks when their workflow should end in `Done`.
- Never rewrite already-correct Jira state without need.
- Never mix merge execution, PR comment handling, or branch operations into this task.

## Expected Outcome

The Jira issue is in the correct post-merge status once the reviewed work is merged, or the task stops with a clear blocker that explains why the issue should not move yet.
