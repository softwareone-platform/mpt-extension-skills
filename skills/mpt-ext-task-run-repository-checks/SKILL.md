---
name: mpt-ext-task-run-repository-checks
description: Run the repository-required local validation flow when users need to verify that changes are ready for commit or review. Use this task to read repository validation docs, determine the correct local checks for the changed scope, run them in the required order, and report failures clearly so the next task can decide whether to fix issues or stop.
---

# Run Repository Checks

## Purpose

Run the repository-required local checks and tests for the current change scope before commit or review handoff.

## Use When

- The user wants to verify that current changes pass the required local validation flow.
- The task requires running repository checks before commit.
- The task requires rerunning validation after review-driven fixes.
- The repository defines local checks through repo docs, `Makefile` targets, or shared validation guidance.

## Do Not Use When

- The task is only to create a branch or update Jira status.
- The task is only to create a commit without running or deciding checks.
- The task is only to open or update a pull request.
- The task is to invent a validation flow without reading repository docs first.

## Inputs

- Current repository change scope.
- Repository validation rules from repo docs.
- Optional explicit scope from the user when only part of the repository should be validated.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The target repository is available locally and the documented validation commands can be executed in the current environment.
- Repository-required tooling and dependencies are installed or otherwise available before the check run starts.
- Any credentials, tokens, or repository access needed by the documented validation flow are already available.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific validation and testing docs first.
- Read shared package docs only when the repository explicitly points to them.

2. Resolve the required validation flow.
- Determine which local commands are required for the current change scope.
- Use repository docs as the source of truth for command names and ordering.
- For repositories that follow this shared package validation guidance, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md` and related repository docs as the shared reference.

3. Prepare the environment only as required by the repo workflow.
- Confirm prerequisite tooling required by the repository validation flow.
- If the repository requires environment refresh after dependency-lock changes, include that step before running checks.
- If the repository relies on shared validation guidance from this package, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md` as the source of truth for commit-oriented preparation such as `pre-commit`.
- Do not run unrelated setup steps that are not required for the current validation flow.

4. Run the required checks in order.
- Execute the repository-required validation commands in the documented sequence.
- Keep command output attributable to the specific check that produced it.
- If the user asked for a scoped validation run and the repository supports that safely, limit execution to that scope.

5. Interpret failures clearly.
- Separate environment or setup failures from real lint, test, or build failures.
- Identify which command failed and which files or checks are implicated.
- If checks modify files automatically, report that clearly so the next task can decide whether to keep and recommit the changes.

6. Report the validation result.
- State which commands were run.
- State whether the validation passed fully, failed, or was only partially run.
- Show the blocking failures clearly when validation does not pass.

## Guardrails

- Never guess the validation commands without reading repository context first.
- Never silently skip a required check in the repository-defined flow.
- Never present a partial validation run as if it were the full repository check set.
- Never hide auto-fixed file changes caused by validation tools.
- Never mix commit creation, PR creation, or Jira transitions into this task.

## Expected Outcome

The repository-required local validation flow for the current change scope is run in the documented order, with a clear pass/fail result and precise reporting of any blockers or auto-generated file changes.
