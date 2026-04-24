---
name: mpt-ext-tool-git-branch-ops
description: Create and switch Git branches when users need to start work on a feature, bugfix, hotfix, or backport. Use this tool skill to select the correct base branch from context, update the base branch locally, detect dirty worktrees or naming conflicts, and create the target branch safely.
---

# Git Branch Ops

## Purpose

Perform Git branch operations safely and consistently when starting work.

## Use When

- The user wants to create a new work branch.
- The user wants to start a feature, bugfix, hotfix, or backport branch.
- The task requires selecting the correct base branch from the branch type.
- The task requires checking for dirty worktrees or branch naming conflicts before branch creation.

## Do Not Use When

- The task is to read or update Jira issues.
- The task is to generate a branch name from Jira title or description.
- The task is to open or update a pull request.
- The task is to perform destructive Git history operations such as reset, rewrite, or force-delete.

## Inputs

- `branch_type`
  - `feature`
  - `bugfix`
  - `hotfix`
  - `backport`
- `target_branch_name`
- Optional `remote_name`
  - default: `origin`
- Installed shared package root when shared package guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The command is running inside the target Git repository and local Git tooling is available.
- Remote access and Git credentials are configured well enough to read and update the selected base branch.
- The current repository state is suitable for branch creation, or the user is available to decide how to proceed when the worktree is dirty or a branch conflict is detected.

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` before branch operations.
- Read repository-specific documentation only when the repository defines branch or contribution exceptions.
- Read shared package documents only when the repository explicitly points to them.

2. Resolve the base branch from the branch type.
- Use `main` for `feature` and `bugfix`.
- Use the latest `release/*` branch for `hotfix` and `backport`.
- Treat the latest release branch as the `release/*` branch with the highest numeric suffix.
- If no `release/*` branch exists for `hotfix` or `backport`, stop and report the blocker.

3. Inspect the current Git state.
- Check the current branch and worktree status.
- If the worktree is dirty, stop and ask the user whether to continue.
- Check whether the target branch already exists locally or remotely.
- If the target branch already exists, stop and ask the user what to do.

4. Update the base branch locally.
- Switch to the resolved base branch.
- Update it with:

```bash
git pull <remote_name> <base-branch>
```

5. Create and switch to the target branch.
- Create the new branch from the updated local base branch:

```bash
git checkout -b <target_branch_name>
```

6. Report the result clearly.
- State which base branch was selected.
- State whether the branch was created successfully.
- If blocked, report the exact blocker: dirty worktree, branch naming conflict, or missing release branch.

## Command Patterns

```bash
# Inspect repository state
git status --short --branch
git branch --list
git branch --remotes

# Determine latest release branch
git for-each-ref --format='%(refname:short)' "refs/remotes/<remote_name>/release/*" \
  | sed "s#^<remote_name>/##" \
  | sort -V \
  | tail -n 1

# Switch to base branch and update it
git checkout main
git pull <remote_name> main

# Create target branch
git checkout -b feature/MPT-1234/example-short-description
```

## Guardrails

- Never continue past a dirty worktree without explicit user confirmation.
- Never silently reuse an existing local or remote branch with the same name.
- Never invent a release branch when none exists.
- Never rewrite history or delete branches as part of this skill.
- Never generate business-specific branch names from Jira content inside this tool skill; accept the target branch name as input.

## Expected Outcome

The correct base branch is selected and updated, the target branch is created and checked out safely, or the operation stops with a clear blocker that requires user direction.
