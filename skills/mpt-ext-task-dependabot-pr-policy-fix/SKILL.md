---
name: mpt-ext-task-dependabot-pr-policy-fix
description: Fix open Dependabot pull requests in SoftwareOne extension repositories by applying shared dependency policy, syncing pre-commit dependency pins when needed, reverting opentelemetry-family dependency bumps, validating through the shared workflow, and pushing fixes back to the same Dependabot branches.
---

# Dependabot PR Policy Fix

## Purpose

Apply SoftwareOne dependency policy fixes directly to open Dependabot pull requests in extension repositories.

## Use When

- The user wants to process open Dependabot PRs for an extension repository.
- A Dependabot PR changes Python dependencies in `pyproject.toml`, `uv.lock`, or `.pre-commit-config.yaml`.
- The work requires enforcing shared dependency policy before the Dependabot PR can be reviewed or merged.
- The fix must be pushed back to the existing Dependabot branch.

## Do Not Use When

- The PR is not authored by Dependabot.
- The user wants to bump dependencies manually from a normal feature branch.
- The repository does not follow the shared Python dependency-management and validation workflow.
- The task requires changing dependency policy itself rather than applying the existing policy.

## Inputs

- Target repository under the `softwareone-platform` organization.
- Open Dependabot PR number or permission to process all open Dependabot PRs in the repository.
- GitHub authentication that can read PR metadata and push to Dependabot branches in the upstream repository.
- Local Git checkout of the target upstream repository.
- Repository dependency and validation workflow that follows the shared package guidance.

## Shared References

Use these shared documents as the source of truth instead of restating their policy. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/packages-and-dependencies.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/manage-dependencies.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/pull-requests.md`

## Dependabot-Specific Policy

This task applies shared dependency policy with these Dependabot-specific additions:

1. Dev dependency bumps must stay in sync with pre-commit:
- If a dev dependency changes in `pyproject.toml` or `uv.lock`, and the same tool is pinned or referenced in `.pre-commit-config.yaml`, update `.pre-commit-config.yaml` in the same PR.
- Examples commonly include linters, formatters, type checkers, and hook `additional_dependencies`.

2. Dependencies whose package name contains `opentelemetry` must not be bumped by Dependabot in this workflow:
- Match package names containing `opentelemetry`, including names like `azure-monitor-opentelemetry-exporter` and `*-opentelemetry-*`.
- Restore matching dependency versions to the base branch version in both dependency declarations and lockfile entries.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them, using the resolution rule from Shared References.

2. Find the target Dependabot PRs.
- If the user provided a PR number, inspect only that PR.
- Otherwise list open Dependabot PRs in the upstream repository:

```bash
gh pr list --repo softwareone-platform/<repo> --state open --author 'dependabot[bot]' --limit 200 --json number,title,url,headRefName,baseRefName
```

- Collect PR number, title, URL, head branch, and base branch.

3. Read each PR before changing anything.
- Read PR metadata, changed files, and diff.
- Verify the PR head branch is a Dependabot branch.
- Verify the changed files are dependency-related before applying this task.
- Skip PRs that have no relevant dependency policy issue and report them as no-op.

4. Detect policy violations.
- Inspect `pyproject.toml` changes for dependency specifiers that violate the shared patch-level version policy.
- Inspect `pyproject.toml` and `uv.lock` changes for dev dependency bumps that require `.pre-commit-config.yaml` updates.
- Inspect all dependency declaration and lockfile changes for package names containing `opentelemetry`.
- For each PR, record which shared or Dependabot-specific rules were violated.

5. Check out the exact Dependabot branch.
- Fetch the base and head branches from upstream.
- Check out the existing Dependabot branch directly.
- Rebase the Dependabot branch on the latest base branch before editing:

```bash
git fetch origin <base-branch> <head-branch>
git checkout <head-branch>
git pull --rebase origin <base-branch>
```

- Do not create a new work branch.

6. Apply fixes in place.
- Convert invalid `pyproject.toml` dependency specifiers according to the shared dependency policy.
- Revert all `*opentelemetry*` dependency version changes to the base branch version.
- Update `.pre-commit-config.yaml` when the corresponding dev dependency changed.
- Refresh `uv.lock` through the target repository dependency-management workflow.

7. Validate sequentially.
- Run the shared build and validation workflow required after dependency changes.
- If either command fails, stop before commit or push, preserve the full command output, and ask the user how to proceed.

8. Commit and push to the same Dependabot branch.
- Stage only files that actually changed, typically:

```bash
git add pyproject.toml uv.lock .pre-commit-config.yaml
```

- Amend the existing Dependabot commit:

```bash
git commit --amend --no-edit
git push -f origin <head-branch>
```

- Do not create a new PR and do not push to a personal fork.

9. Report results.
- For each PR, report PR number and URL.
- State which policy rules were violated and fixed.
- State which files changed.
- State the shared validation commands that were run and their results.
- State amended commit SHA and push result.
- For skipped PRs, state why no change was needed.

## Guardrails

- Never process non-Dependabot PRs with this task.
- Never create a new branch or PR for this workflow.
- Never push fixes anywhere except the original Dependabot branch in upstream.
- Never leave `pyproject.toml` dependency specifiers broader than the shared dependency policy allows.
- Never keep Dependabot `opentelemetry`-family version bumps in the PR.
- Never update `.pre-commit-config.yaml` opportunistically for unrelated tools.
- Never continue to commit or push after failed validation without explicit user direction.
- Never run repository-required validation steps in parallel when the shared validation workflow requires a sequence.

## Expected Outcome

Open Dependabot PRs that violate dependency policy are fixed in their existing upstream Dependabot branches, validated with the repository-required checks, amended in place, and pushed back for review, or the workflow stops with a clear blocker and full failure context.
