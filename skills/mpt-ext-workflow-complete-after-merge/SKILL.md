---
name: mpt-ext-workflow-complete-after-merge
description: Run the final post-merge step after a PR is merged: verify the merge, then hand off Jira to its correct post-merge status. End-of-flow wrapper; excludes review publication and feedback.
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
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

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
