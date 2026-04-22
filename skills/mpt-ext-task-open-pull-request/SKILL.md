---
name: mpt-ext-task-open-pull-request
description: Open or update a repository-compliant pull request when users want to publish committed work for review. Use this task to inspect branch PR state, build the pull request title and description from repository rules, create a new PR when needed, or update the existing PR instead of creating a duplicate.
---

# Open Pull Request

## Purpose

Create or update a repository-compliant pull request for committed work.

## Use When

- The user wants to open a pull request for the current branch.
- The user wants to update the title or description of an existing pull request.
- The task requires applying repository PR rules before publishing work for review.
- The branch already contains the intended committed changes.

## Do Not Use When

- The task is to create or switch branches.
- The task is to create the commit itself.
- The task is to transition Jira issue state.
- The task is to handle review comments after the pull request already exists.

## Inputs

- Current branch or explicit head branch.
- Optional explicit base branch.
- Optional Jira issue key for the work being published.
- GitHub authentication that can read and create or edit pull requests for the target repository.
- Local Git checkout and network access needed for the repository-supported GitHub tooling.
- Jira authentication is required only when the task must emit a Jira item URL from `acli jira auth status`.
- Repository PR rules from repo docs and shared standards.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs that define PR workflow, PR title rules, PR description rules, or review expectations.
- Read shared package docs only when the repository explicitly points to them.

2. Resolve the target PR context.
- Determine the current repository and head branch.
- Determine the intended base branch from repo context or user direction.
- Use `mpt-ext-tool-gh-pr-ops` to check whether a PR already exists for the branch.

3. Read PR rules before mutation.
- Use repository PR rules from repo docs first.
- When the repository relies on this shared package standard for PR formatting, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/pull-requests.md` as the source of truth.
- Build the PR title and description from those rules.

4. Create or update the PR.
- If no PR exists for the branch, create a new PR through `mpt-ext-tool-gh-pr-ops`.
- If a PR already exists for the branch, update the existing PR instead of creating a duplicate.

5. Report the result clearly.
- Show whether the PR was created or updated.
- Show the PR title.
- Show the PR URL.
- When the Jira issue key is available, try to resolve the Jira site through `acli jira auth status` and build the Jira item URL as `https://<site>/browse/<issue-key>`.
- Include testing status in the user-facing result message.
- Use this compact result format for user-facing output after successful PR creation or update:

```text
PR: <pr-url>
Jira: <jira-url>
Testing: <testing-status>
```

- If the Jira item URL is not available safely, omit that line instead of inventing it.
- If `acli jira auth status` does not return a reliable site value, omit the `Jira:` line instead of inventing it.
- Show blockers clearly when auth, permissions, missing branch context, or GitHub API failures prevent the operation.

## Guardrails

- Never create a duplicate PR when one already exists for the branch.
- Never invent PR formatting rules; read repository context first.
- Never mix commit creation, branch creation, or Jira transitions into this task.
- Never silently choose the wrong base branch when repo context or user intent is ambiguous.

## Expected Outcome

The current branch has a repository-compliant pull request that was either created or updated successfully, or the task stops with a clear blocker that explains what must be fixed before the PR can be opened.
