---
name: mpt-ext-task-create-work-branch
description: Create a work branch from Jira issue context when users start a feature, bugfix, hotfix, or backport. Use this task to read the Jira issue, derive a short branch description from the issue title or description, choose the correct branch naming pattern from the branch type, and then create the branch through the shared Git branch tool skill.
---

# Create Work Branch

## Purpose

Create a correctly named work branch from Jira issue context.

## Use When

- The user wants to start work on a Jira issue.
- The user wants a branch name derived from Jira title or description.
- The task requires choosing the correct branch naming pattern for `feature`, `bugfix`, `hotfix`, or `backport`.
- The task requires creating the branch after reading Jira metadata.

## Do Not Use When

- The task is only to perform low-level Git branch operations on an already known branch name.
- The task is only to update Jira status, sprint, or assignee without creating a branch.
- The task is to open or update a pull request.

## Inputs

- Jira issue key.
- Branch type:
  - `feature`
  - `bugfix`
  - `hotfix`
  - `backport`
- Optional user direction when the Jira title or description is not sufficient to derive a safe short branch description.
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs only when the repository defines branch naming or contribution exceptions.
- Read shared package docs only when the repository explicitly points to them.

2. Read the Jira issue.
- Use the shared Jira tool skill to fetch the issue title and description.
- Use the issue title as the primary source for the branch short description.
- Use the description only as fallback when the title is not sufficient.

3. Derive the short branch description.
- Normalize the issue text into a concise, action-oriented, repository-safe slug.
- Prefer lowercase letters, digits, and hyphens.
- Remove punctuation and redundant filler words.
- If the result is unclear or ambiguous, ask the user before continuing.

4. Build the target branch name.
- Use this standard pattern for `feature` and `bugfix`:

```text
<type>/<jira>/<short-description>
```

- Use this pattern for `hotfix`:

```text
hotfix-<type>/<jira>/<short-description>
```

- Use this pattern for `backport`:

```text
backport-<type>/<jira>/<short-description>
```

- Keep the Jira key uppercase in the branch name.

5. Create the branch through the Git branch tool skill.
- Pass the resolved `branch_type` and the final `target_branch_name` to `mpt-ext-tool-git-branch-ops`.
- Let the Git branch tool skill handle base branch selection, dirty worktree checks, branch conflicts, and branch creation.

6. Report the result clearly.
- Show the Jira issue key used.
- Show the generated short description.
- Show the final branch name.
- If blocked, report whether the blocker comes from Jira data, branch-name ambiguity, or the underlying Git branch tool skill.

## Guardrails

- Never invent Jira issue content; read the actual issue first.
- Never hide the generated branch name from the user.
- Never bypass the Git branch tool skill for branch creation.
- Never embed Jira status transitions, sprint updates, or PR creation inside this task.
- Never continue with an unclear or low-quality branch slug when a short clarification from the user is needed.

## Expected Outcome

A repository-safe work branch name is derived from Jira issue context and the branch is created through the shared Git branch tool skill, or the task stops with a clear blocker that requires user direction.
