---
name: mpt-ext-task-dependabot-pr-policy-fix
description: Apply dependency-policy fixes to an already selected Dependabot PR or checked-out Dependabot branch by syncing dev dependency pins, reverting opentelemetry-family bumps, and refreshing dependency lock state.
---

# Dependabot PR Policy Fix

## Purpose

Apply SoftwareOne dependency policy fixes to one already selected Dependabot PR or currently checked-out Dependabot branch in an extension repository.

## Use When

- A specific Dependabot PR or Dependabot branch has already been selected.
- The selected PR changes Python dependencies in `pyproject.toml`, `uv.lock`, or `.pre-commit-config.yaml`.
- The work requires enforcing shared dependency policy on the dependency files only.
- A broader workflow will handle PR discovery, branch checkout, validation, commit amendment, and push.

## Do Not Use When

- The PR is not authored by Dependabot.
- The user wants to bump dependencies manually from a normal feature branch.
- The repository does not follow the shared Python dependency-management and validation workflow.
- The task requires changing dependency policy itself rather than applying the existing policy.
- The user wants an end-to-end Dependabot PR processing workflow including discovery, checkout, validation, auto-fixing checks, commit amendment, and push.

## Inputs

- Target repository under the `softwareone-platform` organization.
- One selected Dependabot PR, or the current local checkout already positioned on the matching Dependabot branch.
- Analyzer inputs for the selected PR: `pr.json`, `files.json`, and `pr.diff`.
- Local Git checkout of the target upstream repository.
- Repository dependency and validation workflow that follows the shared package guidance.
- Python 3.12 or later is available as `python3` for the deterministic PR analysis script.

## Shared References

Use these shared documents as the source of truth instead of restating their policy. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/packages-and-dependencies.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/manage-dependencies.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md`
- `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/standards/pull-requests.md`

## Dependabot-Specific Policy

This task applies shared dependency policy with these Dependabot-specific additions:

1. Dependency bumps must stay in sync with pre-commit:
- If any dependency changes in `pyproject.toml` or `uv.lock`, and the same package is pinned or referenced in `.pre-commit-config.yaml`, update `.pre-commit-config.yaml` in the same PR.
- This rule applies regardless of whether the bumped package is a dev dependency, a runtime dependency, or an optional dependency, because pre-commit hooks may pin runtime packages as well, for example through `additional_dependencies` used to feed types or imports into type checkers.
- Pre-commit references covered by this rule include hook `rev` values that name the tool's upstream release and hook `additional_dependencies` entries that pin specific package versions.
- Examples commonly include linters, formatters, type checkers, and any runtime package version pinned inside a hook's `additional_dependencies` block.

2. Dependencies whose package name contains `opentelemetry` must not be bumped by Dependabot in this workflow:
- Match package names containing `opentelemetry`, including names like `azure-monitor-opentelemetry-exporter` and `*-opentelemetry-*`.
- Restore matching dependency versions to the base branch version in both dependency declarations and lockfile entries.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them, using the resolution rule from Shared References.

2. Confirm the selected Dependabot context.
- Verify the selected PR is authored by Dependabot, or verify the current branch is the selected Dependabot head branch.
- Verify the selected change is dependency-related before applying this task.
- If the PR has no relevant dependency policy issue, report it as no-op and do not edit files.
- Use the bundled analyzer to make deterministic PR classification and policy-signal detection repeatable:

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-dependabot-pr-policy-fix/scripts/analyze_dependabot_pr.py" \
  --metadata-json pr.json \
  --changed-files-json files.json \
  --diff-file pr.diff \
  --pre-commit-config .pre-commit-config.yaml \
  --pretty
```

- Pass `--pre-commit-config` from the checked-out branch when the repository has a `.pre-commit-config.yaml`; the analyzer reads it to detect runtime or dev dependencies pinned through hook `rev` or `additional_dependencies` and populates `pre_commit_pins_to_sync` accordingly.

- For branch-only mode, generate equivalent `pr.json`, `files.json`, and `pr.diff` from the checked-out branch before running the analyzer. If those inputs cannot be generated, run a preflight check and stop with a clear `missing required analyzer inputs` blocker instead of continuing from partial context.
- Use the analyzer output fields `is_dependabot`, `is_dependency_related`, `skip_reason`, `changed_dependency_files`, `opentelemetry_packages`, `dev_dependency_indicators`, `pre_commit_sync_needed`, `pre_commit_pins_to_sync`, and `pyproject_policy_violations`.
- `pre_commit_pins_to_sync` lists the specific package names that are pinned in `.pre-commit-config.yaml` (through hook `rev` or `additional_dependencies`) and were also changed by the Dependabot PR; treat this list as the authoritative scope for pre-commit synchronization.

3. Detect policy violations.
- Use the analyzer output as the initial violation plan.
- Inspect the implicated files directly before editing to confirm the deterministic findings in repository context.
- Record which shared or Dependabot-specific rules were violated.

4. Apply fixes in place.
- Convert invalid `pyproject.toml` dependency specifiers according to the shared dependency policy.
- Revert all `*opentelemetry*` dependency version changes to the base branch version.
- Update `.pre-commit-config.yaml` when a Dependabot-changed package is pinned there, regardless of whether it is a dev, runtime, or optional dependency; use `pre_commit_pins_to_sync` from the analyzer as the list of packages whose hook `rev` or `additional_dependencies` entries must be updated to match the new `pyproject.toml`/`uv.lock` versions.
- Refresh `uv.lock` through the target repository dependency-management workflow.

5. Report the policy-fix result.
- State whether dependency-policy changes were applied or the selected PR was a no-op.
- List the changed files.
- List the violated or fixed rules.
- Leave validation, commit amendment, push, and multi-PR reporting to the workflow that invoked this task.

## Guardrails

- Never process non-Dependabot PRs with this task.
- Never discover PRs, create branches, amend commits, push branches, or create pull requests from this task.
- Never leave `pyproject.toml` dependency specifiers broader than the shared dependency policy allows.
- Never keep Dependabot `opentelemetry`-family version bumps in the PR.
- Never update `.pre-commit-config.yaml` opportunistically for unrelated tools.
- Never fix validation failures that are unrelated to the dependency-policy files handled by this task.

## Expected Outcome

The selected Dependabot PR or checked-out Dependabot branch has dependency-policy violations fixed in place, with changed files and applied rules reported clearly for the invoking workflow to validate and publish.
