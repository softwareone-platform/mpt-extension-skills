---
name: mpt-ext-workflow-complete-after-merge
description: Complete the final Jira handoff after a pull request has merged when the user wants to verify merge state and move the related Jira issue into its correct post-merge status. Use this workflow to coordinate the post-merge verification and Jira completion step without including review publication or review-feedback handling.
---

# Complete After Merge

## Purpose

Coordinate the post-merge Jira completion step for reviewed work.

## Use When

- The user wants to finish the workflow after the pull request has merged.
- The task requires confirming merge completion and moving Jira to its correct post-merge status.
- The workflow should only perform the final post-merge handoff.

## Do Not Use When

- The pull request is still awaiting review or merge.
- The task is to create or update the pull request.
- The task is to process review comments.
- The task is to move Jira into `Code Review`.

## Inputs

- Existing pull request context from the current branch or an explicit PR number.
- Jira issue key for the merged work.
- Repository merge and Jira workflow rules from repo docs.
- GitHub authentication that can read the pull request merge state.
- Jira authentication for the post-merge transition used by this workflow.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The implementation and review work are already complete.
- The only remaining workflow action is the post-merge Jira handoff.
- The repository or Jira workflow defines the correct post-merge state, with `Done` as the default for subtasks and `QA` as the default otherwise.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` before orchestrating the workflow if it has not already been read for the current task.
- Read repository-specific docs that define merge verification or Jira workflow exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Confirm merge completion.
- Use `mpt-ext-tool-gh-pr-ops` to read the current PR state or merge status.
- Stop and report the blocker when merge completion is not confirmed.

3. Move Jira to its post-merge status.
- Use `mpt-ext-task-move-jira-to-qa` once merge completion is confirmed.
- Do not move the issue to a post-merge status before merge completion is confirmed.

4. Report the completion state clearly.
- State that merge completion was confirmed.
- State which post-merge Jira status was selected.
- State whether the Jira issue moved to that status or was already there.
- Surface blockers clearly when merge state, Jira workflow, or permissions stop the flow.

## Guardrails

- Never assume a PR was merged without reading the current PR state first.
- Never move Jira to a post-merge status before merge completion.
- Never mix review publication or comment handling into this workflow.
- Prefer the narrower task skill when the user only asked to move Jira after merge and merge confirmation is already known.

## Expected Outcome

Merge completion is confirmed and the related Jira issue is transitioned to the correct post-merge status, or the workflow stops with a clear blocker that explains why the final handoff cannot proceed yet.
