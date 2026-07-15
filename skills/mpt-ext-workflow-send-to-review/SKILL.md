---
name: mpt-ext-workflow-send-to-review
description: Run the whole send-to-review flow that takes committed work to a review-ready PR and moves Jira to Code Review. Orchestrates the docs, checks, PR, and Jira tasks.
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
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Bring documentation up to date for the change.
- Use `mpt-ext-task-update-docs-from-changes` against the uncommitted change set to map the change to affected documents and edit them, then stage only the updated documentation files so docs are validated and committed together with the change.
- The task no-ops when the change has no documentation impact, so this step is safe to always run.
- Call the task directly here; do not enter a separate documentation workflow, to avoid nested workflow loading and repeated context rebuilds.

3. Run repository validation.
- Use `mpt-ext-task-run-repository-checks` to execute the repository-required local validation flow for the current change scope.
- If repository checks or tests fail, hand the failing output to `mpt-ext-task-fix-repository-check-failures` once; that task owns the bounded fix-and-rerun loop. Do not re-loop it from here.
- Act on its returned outcome: continue only on `fixed`; on any other outcome stop and report the blocker, redirecting back to implementation when the work is not yet ready to publish.

4. Create the commit.
- Use `mpt-ext-task-commit-changes` to stage the intended files and create a repository-compliant commit.
- If the commit is blocked by automatic `pre-commit` hook failures or hook-generated file rewrites, hand control to `mpt-ext-task-fix-pre-commit-failures` once; that task owns the bounded fix-and-retry loop. Do not re-loop it from here.
- Act on its returned outcome: continue only on `committed`; on any other outcome stop and report the blocker.

5. Publish the branch for review.
- Push the committed branch before creating or updating the PR so review state is based on the published branch instead of unpublished local history.
- Stop and report the blocker when branch push permissions, remote configuration, or branch protection prevent publication.

6. Open or update the pull request.
- Use `mpt-ext-task-open-pull-request` to create or update the PR for the current branch.
- Keep PR formatting, base-branch rules, and reporting format delegated to the task skill and repository docs.

7. Move Jira to `Code Review`.
- Use `mpt-ext-task-move-jira-to-code-review` after the PR is ready for review.
- Stop if the issue should not move to review yet.

8. Report the handoff clearly.
- State that the branch is now ready for review.
- Follow the reporting format defined by `mpt-ext-task-open-pull-request` so the user receives the PR URL, Jira item URL when available, and testing status in a compact final message.
- Surface blockers clearly when repository rules, Git push permissions, Jira workflow, GitHub permissions, or failing validation stop the flow.

## Guardrails

- Never duplicate the lower-level instructions already owned by the task skills used in this workflow.
- Never skip repository-required validation before commit and PR creation.
- Never publish a change that affects documented behaviour without updating documentation first; delegate the update to `mpt-ext-task-update-docs-from-changes`.
- Never retry failing validation or `pre-commit` loops blindly without routing through the relevant failure-handling task.
- Never wrap a fix task that already owns its bounded loop in a second retry loop; invoke it once, consume its classified outcome, and stop on anything other than success.
- Never rely on unpublished local commits when opening or updating the review PR; publish the branch first.
- Never move Jira to `Code Review` without a review-ready PR.
- Never continue into review-comment or post-merge handling inside this workflow.
- Prefer the narrower task skill when the user request is only for one step of the workflow.

## Expected Outcome

Completed implementation is validated, committed, published in a compliant PR, and handed off in Jira for review, with clear blocker reporting when any step cannot proceed.
