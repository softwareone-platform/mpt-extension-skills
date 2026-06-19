---
name: mpt-ext-task-fix-repository-check-failures
description: Fix repository validation failures after local checks or tests fail. Isolates one blocker at a time, applies the smallest fix, and reruns checks (max 5 iterations) until clean or blocked.
---

# Fix Repository Check Failures

## Purpose

Fix failing repository checks or tests in a controlled step-by-step loop until the required validation flow passes, the loop stops converging, a clear blocker remains, or 5 fix iterations have been attempted.

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
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

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

5. Repeat until clean, blocked, or the iteration limit is reached.
- One iteration = one scoped fix + one targeted re-run of the affected check. A final full-suite confirmation run after the loop is not an iteration.
- Before each attempt, state the iteration explicitly: `Iteration N/5 — failing check: <command>`.
- Continue through the next failing blocker only after the current one is resolved or explicitly understood.
- Stop early, without consuming the remaining iterations, when there is no progress: the same check fails with the same error signature after a fix attempt, or a fix re-introduces a previously-passing check. Report it as a non-converging blocker.
- Stop when all required validation passes, when the remaining failure needs user input, unavailable environment access, or a broader design decision, or after 5 fix iterations. Report the last failing command output as the blocker.

6. Report the result clearly.
- State which failures were fixed.
- State which commands were rerun.
- State what is still failing or blocked, if anything.
- End with exactly one classified outcome the caller can act on, chosen by this precedence (success first):
  - `fixed` — the full required validation passes, even when reached on the final allowed iteration.
  - `needs-user-input` — a remaining failure needs user direction or a broader design decision.
  - `environment-blocker` — the remaining failure is environment or setup related, not product code.
  - `non-converging` — the same failure signature recurred after a fix, or a fix reintroduced a previously-passing check.
  - `iteration-limit-reached` — 5 fix iterations were spent without reaching any of the above.

## Guardrails

- Never guess the cause of a failure without reading the reported output first.
- Never batch unrelated speculative fixes together when the validation output identifies a narrower blocker.
- Never treat environment/setup failures as product-code failures.
- Never run more than 5 validation-fix iterations before stopping with a blocker, and stop sooner when the loop stops converging.
- Never let the caller re-loop this task; this task owns the bounded fix-and-rerun loop and returns a single classified outcome.
- Never mix commit creation, PR creation, or Jira transitions into this task.
- For repositories that follow this shared package validation guidance, read `knowledge/build-and-checks.md` using the shared-doc resolution rule from the repository context step as the shared reference for the validation loop.

## Expected Outcome

Repository validation failures are addressed one by one with scoped fixes and targeted reruns until the required checks pass, the loop stops converging, a precise blocker remains, or the 5-iteration limit is reached, and the task returns a single classified outcome (`fixed`, `needs-user-input`, `environment-blocker`, `non-converging`, or `iteration-limit-reached`) for the caller to act on.
