---
name: mpt-ext-task-move-jira-to-code-review
description: Move a Jira issue to Code Review when development is done and a PR is ready. Verifies PR context, transitions the issue, and reports blockers when the state is not ready.
---

# Move Jira To Code Review

## Purpose

Move a Jira issue into `Code Review` after development work is committed and the pull request is ready for review.

## Use When

- The user has finished implementation and wants to hand work over for review.
- The task requires transitioning a Jira issue from active development to `Code Review`.
- A pull request already exists or is being treated as ready for review in the current workflow.

## Do Not Use When

- The task is to start work and move Jira issues to `In Progress`.
- The task is to create or update a pull request.
- The task is to respond to PR review comments.
- The task is to move the issue to `QA` after merge.

## Inputs

- Jira issue key.
- Confirmation that the relevant branch work is already committed.
- Confirmation that the pull request already exists or is otherwise ready for review.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- Jira authentication is available and the target issue can be read and transitioned through `mpt-ext-tool-jira-workitem-ops`.
- The repository workflow exposes a usable transition into `Code Review`.
- The corresponding commit or pull request already exists, or the user explicitly wants to move the issue despite incomplete review context.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Read the Jira issue first.
- Use `mpt-ext-tool-jira-workitem-ops` to fetch the current issue state.
- Confirm the issue exists and identify its current workflow status.

3. Verify readiness for review.
- Confirm the development work is already committed.
- Confirm a pull request already exists or the user explicitly wants the issue moved to review now.
- If the workflow state is clearly not ready for review, stop and tell the user what is still missing instead of transitioning Jira prematurely.

4. Transition the issue to `Code Review`.
- Use `mpt-ext-tool-jira-workitem-ops` to move the Jira issue to `Code Review` when it is not already there.
- Preserve already-correct state rather than rewriting it unnecessarily.

5. Report the result clearly.
- State whether the issue moved to `Code Review`.
- State whether the issue was already in `Code Review`.
- Show blockers clearly when Jira workflow rules, permissions, or missing PR readiness prevent completion.

## Guardrails

- Never move the issue to `Code Review` when the user has not finished the branch work.
- Never assume PR readiness when the current workflow context contradicts it.
- Never rewrite already-correct Jira state without need.
- Never mix PR creation, commit creation, review comment handling, or merge actions into this task.

## Expected Outcome

The Jira issue is in `Code Review` when the work is ready for review, or the task stops with a clear blocker that explains why the issue should not be transitioned yet.
