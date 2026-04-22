---
name: mpt-ext-task-fix-repository-check-failures
description: Fix repository validation failures step by step after local checks or tests fail. Use this task to read the failing validation output, isolate one blocker at a time, apply the smallest required fix, rerun the relevant checks, and continue until the repository-required validation flow is clean or a clear blocker remains.
---

# Fix Repository Check Failures

## Purpose

Fix failing repository checks or tests in a controlled step-by-step loop until the required validation flow passes or a clear blocker remains.

## Use When

- The repository validation flow has failed.
- The user wants to work through local check or test failures one by one.
- The task requires isolating the next actionable validation blocker before changing code or documentation.

## Do Not Use When

- The task is only to run checks without fixing failures.
- The task is only to address `pre-commit` hook failures triggered during `git commit`.
- The task is to create a commit or open a pull request.
- The task is to guess fixes without reading the failing validation output first.

## Inputs

- Current failing validation output from the repository-required checks.
- Repository validation rules from repo docs.
- Current repository change scope.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The target repository is available locally and the documented validation commands can be executed.
- The failing validation output being handled matches the current repository state.
- Repository-required tooling is installed or otherwise available before rerunning checks.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific validation and testing docs first.
- Read shared package docs only when the repository explicitly points to them.

2. Read the failing validation result.
- Start from the current failing command output instead of rerunning everything blindly.
- Identify the first actionable failing check, test, or build step.
- Separate true repository failures from environment or setup problems.

3. Fix one blocker at a time.
- Apply the smallest change that addresses the current blocker.
- Keep the fix scoped to the reported failure instead of opportunistically refactoring unrelated areas.
- If the failing output is ambiguous, stop and inspect the implicated file or test before changing more code.

4. Rerun the relevant validation.
- Rerun the narrowest safe command that confirms the fix for the current blocker.
- When the repository workflow requires a broader rerun before the work is considered clean, run the broader check after the targeted rerun passes.

5. Repeat until clean or blocked.
- Continue through the next failing blocker only after the current one is resolved or explicitly understood.
- Stop when all required validation passes or when the remaining failure needs user input, unavailable environment access, or a broader design decision.

6. Report the result clearly.
- State which failures were fixed.
- State which commands were rerun.
- State what is still failing or blocked, if anything.

## Guardrails

- Never guess the cause of a failure without reading the reported output first.
- Never batch unrelated speculative fixes together when the validation output identifies a narrower blocker.
- Never treat environment/setup failures as product-code failures.
- Never mix commit creation, PR creation, or Jira transitions into this task.
- For repositories that follow this shared package validation guidance, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md` as the shared reference for the validation loop.

## Expected Outcome

Repository validation failures are addressed one by one with scoped fixes and targeted reruns until the required checks pass or a precise blocker remains.
