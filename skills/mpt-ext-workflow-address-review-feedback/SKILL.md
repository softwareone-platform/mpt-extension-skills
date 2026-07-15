---
name: mpt-ext-workflow-address-review-feedback
description: Run the full re-review iteration on an open PR: process review comments, validate the changes, commit, and update the branch for re-review. Excludes initial PR creation and post-merge Jira steps.
---

# Address Review Feedback

## Purpose

Coordinate one review-feedback iteration from current PR comments through updated branch publication.

## Use When

- The user wants to process review comments on an existing pull request.
- The task requires triaging comments, applying selected fixes or replies, rerunning validation, and updating the branch for another review pass.
- The workflow should stop once the updated branch is back in review.

## Do Not Use When

- The task is to publish a branch for the first time.
- The task is to move Jira to `QA` after merge.
- The task is only to address one review comment without the surrounding validation and update flow.
- The task is to wait for review or merge inside the same workflow.

## Inputs

- Existing pull request context from the current branch or an explicit PR number.
- Jira issue key when Jira-linked reporting is needed.
- Repository validation, commit, and PR update rules from repo docs.
- Optional user direction about which comments to fix, which to reply to, and which to leave unresolved.
- GitHub authentication that can read review threads and push updates to the branch.
- Local Git identity and repository access needed to validate, amend or create commits, and push the branch.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- A pull request already exists for the branch being updated.
- Review feedback is currently active and the user wants another review iteration.
- The workflow should stop after the updated branch is pushed back for review.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Process review comments.
- Use `mpt-ext-task-handle-pr-comments` to read the unresolved and unanswered review threads, triage the actionable feedback, and apply the selected fixes or replies.
- Stop when comment intent is ambiguous, conflicts with repository rules, or requires explicit user direction.

3. Run repository validation for the applied fixes.
- Use `mpt-ext-task-run-repository-checks` to execute the repository-required local validation flow for the changed scope.
- If repository checks or tests fail, hand the failing output to `mpt-ext-task-fix-repository-check-failures` once; that task owns the bounded fix-and-rerun loop. Do not re-loop it from here.
- Act on its returned outcome: continue only on `fixed`; on any other outcome stop and report the blocker when the updated branch is not ready to send back for review.

4. Update the commit history for the branch.
- Use `mpt-ext-task-commit-changes` to stage the intended files and amend or create the repository-compliant commit for this review iteration.
- If the commit is blocked by automatic `pre-commit` hook failures or hook-generated file rewrites, hand control to `mpt-ext-task-fix-pre-commit-failures` once; that task owns the bounded fix-and-retry loop. Do not re-loop it from here.
- Act on its returned outcome: continue only on `committed`; on any other outcome stop and report the blocker.

5. Update the pull request branch.
- Push the updated branch so the existing PR reflects the latest review fixes.
- Use `mpt-ext-task-open-pull-request` only when the PR title, description, or reporting contract must be refreshed instead of reimplementing that logic locally.

6. Report the review iteration clearly.
- State which comments were fixed versus only answered.
- State which validation was run for the updated branch.
- State that the branch is ready for another round of review.
- Show blockers clearly when comment ambiguity, validation failure, commit failure, or push permissions stop the workflow.

## Guardrails

- Never start from already resolved or already answered review threads unless the user explicitly asks to revisit them.
- Never skip repository-required validation after code changes made for review feedback.
- Never wrap a fix task that already owns its bounded loop in a second retry loop; invoke it once, consume its classified outcome, and stop on anything other than success.
- Never create a duplicate pull request when updating the existing review branch.
- Never move Jira to `Code Review` or `QA` inside this workflow.
- Never assume every review comment must be fixed; use explanation or pushback when that is the correct outcome.

## Expected Outcome

Selected PR review feedback is addressed, the resulting changes are validated and committed, the existing review branch is updated for another review pass, and remaining blockers are reported clearly.
