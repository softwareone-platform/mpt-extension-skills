---
name: mpt-ext-task-fix-repository-check-failures
description: Fix failures from a standalone repository validation run (`make check`/`make test`), outside the `git commit` hook. Isolates one blocker at a time, applies the smallest fix, and reruns; max 5 iterations.
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

## Shared References

Use this shared document as the source of truth instead of restating its guidance. When shared guidance is needed, resolve it from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read the same path from the `main` branch of the shared GitHub repository.

- `knowledge/build-and-checks.md`

## Workflow

1. Build repository context first.
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Read the failing validation result.
- Start from the current failing command output instead of rerunning everything blindly.
- Identify the first actionable failing check, test, or build step.
- Separate true repository failures from environment or setup problems.

3. Check for a stale-toolchain/config-parse failure first.
- Before spending a fix iteration, check whether the failure matches the stale-toolchain/config-parse pattern in `knowledge/build-and-checks.md`: the validation tool fails on its own configuration or rejects an option/rule it does not recognize, rather than reporting a finding tied to a specific file, line, or test (for example a `ruff` "unknown rule selector" error right after switching to a branch that pins a different `ruff` version).
- If the failure matches this pattern, rebuild the local environment once using the repository's documented rebuild target (for example `make build`), then rerun the failing check. This single rebuild-and-rerun attempt is not counted as one of the 5 fix iterations.
- If the rebuild resolves the failure, treat that check as passing and continue with the remaining required validation instead of entering the fix loop for it.
- If the failure does not match this pattern, or persists after the rebuild, proceed to the bounded fix loop starting at the next step.

4. Fix one blocker at a time.
- Apply the smallest change that addresses the current blocker.
- Keep the fix scoped to the reported failure instead of opportunistically refactoring unrelated areas.
- If the failing output is ambiguous, stop and inspect the implicated file or test before changing more code.

5. Rerun the relevant validation.
- Rerun the narrowest safe command that confirms the fix for the current blocker.
- When the repository workflow requires a broader rerun before the work is considered clean, run the broader check after the targeted rerun passes.

6. Repeat until clean, blocked, or the iteration limit is reached.
- One iteration = one scoped fix + one targeted re-run of the affected check. A final full-suite confirmation run after the loop is not an iteration. The pre-loop rebuild-and-rerun attempt in Step 3 is not an iteration either.
- Before each attempt, state the iteration explicitly: `Iteration N/5 — failing check: <command>`.
- Continue through the next failing blocker only after the current one is resolved or explicitly understood.
- Stop early, without consuming the remaining iterations, when there is no progress: the same check fails with the same error signature after a fix attempt, or a fix re-introduces a previously-passing check. Report it as a non-converging blocker.
- Stop when all required validation passes, when the remaining failure needs user input, unavailable environment access, or a broader design decision, or after 5 fix iterations. Report the last failing command output as the blocker.

7. Report the result clearly.
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
- Never spend a fix iteration on a config-parse/unknown-rule failure before attempting the single pre-loop rebuild described in Step 3.
- Never rebuild more than once per failure before falling back to the bounded loop; a rebuild that does not resolve the failure is evidence of a real blocker, not a retry target.
- Never let the caller re-loop this task; this task owns the bounded fix-and-rerun loop and returns a single classified outcome.
- Never mix commit creation, PR creation, or Jira transitions into this task.

## Expected Outcome

A stale-toolchain/config-parse failure is caught and resolved with a single pre-loop rebuild-and-rerun before any fix iteration is spent on it. Remaining repository validation failures are addressed one by one with scoped fixes and targeted reruns until the required checks pass, the loop stops converging, a precise blocker remains, or the 5-iteration limit is reached, and the task returns a single classified outcome (`fixed`, `needs-user-input`, `environment-blocker`, `non-converging`, or `iteration-limit-reached`) for the caller to act on.
