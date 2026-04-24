---
name: mpt-ext-workflow-send-to-review
description: Send completed implementation to review when the user wants to validate the change, create or update the pull request, and move Jira into Code Review. Use this workflow to coordinate the existing validation, commit, PR, and Jira review-handoff task skills without including later review-feedback or post-merge steps.
---

# Send To Review

## Purpose

Coordinate the path from completed local implementation to a review-ready pull request and Jira handoff.

## Use When

- The user has finished implementation and wants to publish the current branch for review.
- The task requires repository checks, commit creation, PR publication, and Jira transition to `Code Review`.
- The work should stop once the branch is ready for human or bot review.

## Do Not Use When

- The task is only to run checks, create a commit, or open a pull request.
- The task is to process review comments on an existing PR.
- The task is to move Jira to `QA` after merge.
- The task is to wait for review or merge inside the same workflow.

## Inputs

- Current repository worktree and branch context.
- Jira issue key for the work being published.
- Repository contribution, validation, commit, and PR rules from repo docs.
- GitHub authentication that can push the branch and create or update pull requests.
- Jira authentication for the `Code Review` transition and Jira-linked reporting.
- Local Git identity and repository access needed to commit and push changes.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Implementation is complete enough to enter review.
- The repository state is clean enough to run validation and create the intended commit, or the user is available to resolve blockers surfaced by the underlying tasks.
- The workflow should stop after review handoff instead of waiting for comments or merge.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` before orchestrating the workflow if it has not already been read for the current task.
- Read repository-specific docs that define validation, commit, PR, or Jira workflow exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Run repository validation.
- Use `mpt-ext-task-run-repository-checks` to execute the repository-required local validation flow for the current change scope.
- If repository checks or tests fail, use `mpt-ext-task-fix-repository-check-failures` to work through the blockers step by step and rerun the required validation.
- Stop and redirect back to implementation when validation still fails or the work is not yet ready to publish.

3. Create the commit.
- Use `mpt-ext-task-commit-changes` to stage the intended files and create a repository-compliant commit.
- If the commit is blocked by automatic `pre-commit` hook failures or hook-generated file rewrites, use `mpt-ext-task-fix-pre-commit-failures` before retrying the commit.

4. Publish the branch for review.
- Push the committed branch before creating or updating the PR so review state is based on the published branch instead of unpublished local history.
- Stop and report the blocker when branch push permissions, remote configuration, or branch protection prevent publication.

5. Open or update the pull request.
- Use `mpt-ext-task-open-pull-request` to create or update the PR for the current branch.
- Keep PR formatting, base-branch rules, and reporting format delegated to the task skill and repository docs.

6. Move Jira to `Code Review`.
- Use `mpt-ext-task-move-jira-to-code-review` after the PR is ready for review.
- Stop if the issue should not move to review yet.

7. Report the handoff clearly.
- State that the branch is now ready for review.
- Follow the reporting format defined by `mpt-ext-task-open-pull-request` so the user receives the PR URL, Jira item URL when available, and testing status in a compact final message.
- Surface blockers clearly when repository rules, Git push permissions, Jira workflow, GitHub permissions, or failing validation stop the flow.

## Guardrails

- Never duplicate the lower-level instructions already owned by the task skills used in this workflow.
- Never skip repository-required validation before commit and PR creation.
- Never retry failing validation or `pre-commit` loops blindly without routing through the relevant failure-handling task.
- Never rely on unpublished local commits when opening or updating the review PR; publish the branch first.
- Never move Jira to `Code Review` without a review-ready PR.
- Never continue into review-comment or post-merge handling inside this workflow.
- Prefer the narrower task skill when the user request is only for one step of the workflow.

## Expected Outcome

Completed implementation is validated, committed, published in a compliant PR, and handed off in Jira for review, with clear blocker reporting when any step cannot proceed.
