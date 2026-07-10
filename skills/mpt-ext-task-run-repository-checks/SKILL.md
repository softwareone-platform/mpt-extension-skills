---
name: mpt-ext-task-run-repository-checks
description: Run the repository-required local validation flow to verify changes are ready for commit or review. Determines the right checks for the changed scope, runs them in order, and reports failures.
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

## Shared References

Use this shared document as the source of truth instead of restating its guidance. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `knowledge/build-and-checks.md`

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Resolve the required validation flow.
- Determine which local commands are required for the current change scope.
- Use repository docs as the source of truth for command names and ordering.
- For repositories that follow this shared package validation guidance, read `knowledge/build-and-checks.md` using the shared-doc resolution rule from the repository context step, and use it with related repository docs as the shared reference.

3. Prepare the environment only as required by the repo workflow.
- Confirm prerequisite tooling required by the repository validation flow.
- If the repository requires environment refresh after dependency-lock changes, include that step before running checks.
- If the repository relies on shared validation guidance from this package, read `knowledge/build-and-checks.md` using the shared-doc resolution rule from the repository context step, and use it as the source of truth for commit-oriented preparation such as `pre-commit`.
- Do not run unrelated setup steps that are not required for the current validation flow.

4. Run the required checks in order.
- Execute the repository-required validation commands in the documented sequence.
- Keep command output attributable to the specific check that produced it.
- If the user asked for a scoped validation run and the repository supports that safely, limit execution to that scope.

5. Interpret failures clearly.
- Separate environment or setup failures from real lint, test, or build failures.
- Treat a validation tool failing on its own configuration (for example an "unknown rule" or "unrecognized selector" error instead of a finding tied to a specific file or line) as an environment/setup failure, not a real finding; see the stale-toolchain pattern in `knowledge/build-and-checks.md`.
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
