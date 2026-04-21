---
name: mpt-ext-task-commit-changes
description: Create a repository-compliant Git commit when users want to save completed work. Use this task to inspect the current diff, stage only the intended files, build the commit message from repository rules, and create the commit after repository-required validation is complete.
---

# Commit Changes

## Purpose

Create a clean, repository-compliant Git commit for completed work.

## Use When

- The user wants to commit finished changes.
- The task requires staging only the intended files.
- The task requires a commit message that follows repository standards.
- Repository-required validation has already been completed or the repository explicitly allows commit without additional validation.

## Do Not Use When

- The task is to create or switch branches.
- The task is to open or update a pull request.
- The task is to transition Jira issue state.
- The task is to decide or run the repository validation flow from scratch.

## Inputs

- The current repository diff.
- The current branch history, including whether the branch already contains work-in-progress commits.
- Optional explicit file scope when the user wants to commit only part of the current worktree.
- Repository commit rules from repo docs and shared standards.
- User intent for amending the existing branch commit versus creating intentionally separated commit history.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs that define commit or validation requirements.
- Read shared package docs only when the repository explicitly points to them.

2. Inspect the current change scope.
- Review the current branch and diff.
- Identify which files are intended for this commit.
- If unrelated files are present, keep them out of the commit.
- If the intended scope is unclear, ask the user before staging.

3. Confirm validation state.
- Check whether the repository-required validation has already been completed.
- If repository docs require checks before commit and they have not been run yet, stop and direct the flow back to the validation task instead of silently committing.
- If the repository relies on shared validation guidance from this package, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md` as the source of truth for commit-time validation and `pre-commit` expectations.
- If repository-required commit-time validation prerequisites are missing, stop and direct the flow back to the validation or pre-commit-fix task instead of attempting a blind commit.

4. Stage only the intended files.
- Add only the files that belong to the requested commit.
- Avoid staging unrelated edits, generated junk, or accidental local files.

5. Choose amend versus a new commit.
- Inspect whether the current branch already contains user-facing commits for the same work.
- If the branch already has a commit and the user did not explicitly ask for a separate follow-up commit, prefer updating the existing branch commit with `git commit --amend`.
- Create a new commit only when the user explicitly wants intentionally separated history or repository context requires it.
- If the branch is already pushed and amending would require rewriting published history, call that out clearly before proceeding.

6. Build the commit message.
- Follow repository commit rules from repo docs first.
- Use shared standards only when the repository points to them or does not define a stricter local rule.
- For repositories that follow this package standard, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/commit-messages.md` as the source of truth.

7. Create the commit.
- Amend the existing branch commit when the branch already has one and the user did not request separate history.
- Otherwise create a single clean commit unless the user explicitly requested intentionally separated commits.
- Review the repository-required automatic commit-time hooks and confirm the commit completed cleanly.
- If hooks fail or rewrite files, stop and direct the flow to the pre-commit-failure task instead of retrying blindly.

8. Report the result clearly.
- Show which files were staged and committed.
- Show whether the result was an amended commit or a new commit.
- Show the final commit title.
- Show blockers clearly when validation, hooks, or Git errors prevent the commit.

## Guardrails

- Never stage unrelated files silently.
- Never skip repository-required validation without telling the user.
- Never bypass repository-required commit-time hooks or their prerequisite setup when the repo workflow requires them.
- Never invent commit-message rules; read repository context first.
- Never create an unnecessary extra commit when the user expectation is a single squashed branch commit.
- Never amend a pushed branch silently when that will require force-pushing rewritten history.
- Never force a multi-commit history unless the user explicitly wants intentionally separated commits.
- Never mix PR creation or Jira transitions into this task.

## Expected Outcome

The intended repository changes are staged cleanly and committed with a repository-compliant message, or the task stops with a clear blocker that explains what must be resolved before commit.
