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

## Assumptions

- Jira authentication is active so the issue title and description can be read before branch creation.
- Local repository access and Git tooling are available for the underlying branch-creation step.
- Python 3.9 or later is available as `python3` for the deterministic branch-name rendering script.
- The shared skills package is installed or updated locally, and `scripts/render_branch_name.py` is readable through `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current`.
- The repository state is clean enough for branch creation, or the user is available to decide how to proceed when the underlying Git branch tool reports a dirty worktree or branch conflict.

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
- Use the bundled deterministic script to render the short description and target branch name from the Jira key, branch type, and issue text:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-create-work-branch/scripts/render_branch_name.py" \
  --jira-key MPT-1234 \
  --branch-type feature \
  --title "Add property validation" \
  --json
```

- Use the script output fields `short_description` and `branch_name`.
- If the script cannot produce a slug, or if the generated slug is unclear or ambiguous for the requested work, ask the user before continuing.

4. Review the target branch name.
- Keep the Jira key uppercase in the branch name.
- Confirm the generated branch name follows the branch type pattern returned by the script.

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
- Never hand-build the branch slug or branch name when the bundled script can render it.
- Never hide the generated branch name from the user.
- Never bypass the Git branch tool skill for branch creation.
- Never embed Jira status transitions, sprint updates, or PR creation inside this task.
- Never continue with an unclear or low-quality branch slug when a short clarification from the user is needed.

## Bundled Resources

- `scripts/render_branch_name.py`
  - Inputs: Jira key, branch type, and Jira title or fallback description
  - Output: repository-safe branch name, or JSON with `short_description` and `branch_name`
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-create-work-branch/scripts/render_branch_name.py`

## Expected Outcome

A repository-safe work branch name is derived from Jira issue context and the branch is created through the shared Git branch tool skill, or the task stops with a clear blocker that requires user direction.
