---
name: mpt-ext-workflow-finish-work
description: Finish development work when implementation is complete and the user wants to move the change through commit, pull request, review handoff, review feedback handling, and Jira completion states. Use this workflow to coordinate the existing shared task skills for commit, PR opening, Jira Code Review transition, PR comment handling, and Jira QA transition without redefining their lower-level logic.
---

# Finish Work

## Purpose

Coordinate the end-to-end workflow for finishing development work from completed changes through post-merge Jira handoff.

## Use When

- The user has finished implementation and wants to move the work into review.
- The task requires coordinating commit, PR, Jira review handoff, review comment handling, and post-merge Jira completion.
- The repository already has or should use the shared task skills for the individual end-of-flow steps.

## Do Not Use When

- The task is only to perform one atomic step such as committing changes or opening a pull request.
- The task is to start work from Jira and branch creation.
- The task is to merge the pull request itself.
- The task is to define repository-specific release or deployment workflow beyond development completion.

## Inputs

- Current repository worktree and branch context.
- Jira issue key for the work being finished.
- Repository contribution, validation, commit, and PR rules from repo docs.
- Optional user direction about whether review comments should be handled now or later.
- GitHub authentication that can push the branch and create or update pull requests.
- Jira authentication for the issue transitions and Jira-linked reporting steps used by this workflow.
- Local Git identity and repository access needed to commit and push changes.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` before orchestrating the workflow if it has not already been read for the current task.
- Read repository-specific docs that define validation, commit, PR, or Jira workflow exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Run repository validation.
- Use `mpt-ext-task-run-repository-checks` to execute the repository-required local validation flow for the current change scope.
- If repository checks or tests fail, use `mpt-ext-task-fix-repository-check-failures` to work through the blockers step by step and then rerun the required validation.
- Stop and redirect back to implementation when validation still fails or the work is not yet ready to publish.

3. Create the commit.
- Use `mpt-ext-task-commit-changes` to stage the intended files and create a repository-compliant commit.
- If the commit is blocked by automatic `pre-commit` hook failures or hook-generated file rewrites, use `mpt-ext-task-fix-pre-commit-failures` before retrying the commit.
- Do not reimplement commit message or staging rules in this workflow.

4. Open or update the pull request.
- Use `mpt-ext-task-open-pull-request` to create or update the PR for the current branch.
- Keep PR formatting and base-branch rules delegated to the task skill and repository docs.

5. Move Jira to `Code Review`.
- Use `mpt-ext-task-move-jira-to-code-review` after the PR is ready for review.
- Stop if the issue should not move to review yet.

6. Handle PR review comments as needed.
- When the user wants to process review feedback, use `mpt-ext-task-handle-pr-comments`.
- Repeat this step as needed while review is active.
- Keep comment-specific fixes, replies, and validation scoped inside the comment-handling task.

7. Move Jira to `QA` after merge.
- Once the PR is merged, use `mpt-ext-task-move-jira-to-qa`.
- Do not move the issue to `QA` before merge completion is confirmed.

8. Report the workflow state clearly.
- State which finish-work steps were completed.
- State which step is currently blocked or still waiting on external review or merge.
- When the workflow reaches PR creation or update, follow the reporting format defined by `mpt-ext-task-open-pull-request` so the user receives the PR URL, Jira item URL when available, and testing status in a compact final message.
- Surface blockers clearly when repository rules, Jira workflow, GitHub permissions, or failing validation stop the flow.

## Guardrails

- Never duplicate the lower-level instructions already owned by the task skills used in this workflow.
- Never skip repository-required validation before commit and PR creation.
- Never retry failing validation or `pre-commit` loops blindly without routing through the relevant failure-handling task.
- Never move Jira to `Code Review` without a review-ready PR.
- Never move Jira to `QA` before merge completion.
- Never assume review comments must always be fixed immediately; comment handling is iterative and user-directed.
- Prefer the narrower task skill when the user request is only for one step of the workflow.

## Expected Outcome

Completed implementation is moved through a consistent finish-work flow: committed cleanly, published in a compliant PR, handed off in Jira for review, updated as review feedback is addressed, and transitioned to `QA` after merge, with clear blocker reporting when any step cannot proceed.
