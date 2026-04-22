---
name: mpt-ext-workflow-start-work
description: Start work on a Jira issue when users begin a feature, bugfix, hotfix, or backport. Use this workflow to create the correctly named work branch from Jira context and move the Jira issue into active development by reusing the shared branch-creation and Jira-start tasks.
---

# Start Work

## Purpose

Prepare a Jira issue and the local repository so development can begin safely and consistently.

## Use When

- The user wants to start work on a Jira issue.
- The task requires both branch creation and Jira start-state setup.
- The work item is a feature, bugfix, hotfix, or backport.
- The user wants one reusable start-of-work flow instead of running branch and Jira setup separately.

## Do Not Use When

- The task is only to create a branch.
- The task is only to update Jira status, sprint, or assignee.
- The task is to commit changes, open a pull request, or handle PR comments.
- The task is to finish development after merge.

## Inputs

- Jira issue key.
- Branch type:
  - `feature`
  - `bugfix`
  - `hotfix`
  - `backport`
- Optional sprint or board context when the active sprint cannot be determined automatically.
- Optional user confirmations for dirty worktrees, branch conflicts, or Jira reassignment decisions.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Local Git and repository access are available for branch creation through the underlying branch task.
- Jira authentication is active for `mpt-ext-task-start-jira-work` and `mpt-ext-task-create-work-branch` issue reads and updates.
- The user has the Jira permissions needed to move issue state, adjust sprint placement, and update assignee when confirmation is given.
- The repository state is clean enough for branch operations, or the user is available to confirm how to proceed when the worktree is dirty or a branch conflict exists.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs only when the repository defines branch, contribution, or Jira workflow exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Create the work branch.
- Use `mpt-ext-task-create-work-branch`.
- Let that task read Jira issue content, derive the short branch description, choose the correct branch naming pattern, and create the branch through the shared Git branch tool skill.

3. Start Jira work.
- Use `mpt-ext-task-start-jira-work`.
- Let that task move the issue and its full parent chain to `In Progress`, verify sprint placement, add the active sprint when needed, and ask before reassignment.

4. Report the combined result clearly.
- Show the final branch name.
- Show whether the Jira issue moved to `In Progress`.
- Show whether parent issues moved to `In Progress`.
- Show whether sprint placement changed.
- Show whether reassignment was requested, skipped, or completed.

## Guardrails

- Never reimplement branch creation logic that already belongs to `mpt-ext-task-create-work-branch`.
- Never reimplement Jira state update logic that already belongs to `mpt-ext-task-start-jira-work`.
- Never hide blockers from the underlying tasks.
- Never mix commit, PR, or review-comment handling into this workflow.

## Expected Outcome

The work branch is created from Jira context, the Jira issue and its parent chain are prepared for active development, and the user receives a clear summary of what changed and what still needs attention.
