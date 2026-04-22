---
name: mpt-ext-task-fix-pre-commit-failures
description: Fix pre-commit hook failures step by step when a git commit is blocked by automatic hook execution. Use this task to read the hook output, keep or inspect hook-generated file changes, address one remaining hook failure at a time, rerun the relevant validation when needed, and retry the commit only after the hook set is expected to pass cleanly.
---

# Fix Pre-commit Failures

## Purpose

Resolve `pre-commit` hook failures that block a `git commit`, one hook failure at a time.

## Use When

- `git commit` triggered `pre-commit` and the hooks failed.
- `pre-commit` rewrote files and the user wants to continue safely.
- The task requires inspecting hook output and fixing the remaining blockers before retrying commit.

## Do Not Use When

- The task is only to run the repository validation flow before commit.
- The task is to fix normal checks or tests that failed outside the `git commit` hook run.
- The task is to create or update a pull request.
- The task is to ignore or bypass hook failures.

## Inputs

- The failed `pre-commit` hook output from the attempted `git commit`.
- Current repository diff, including any hook-generated file changes.
- Repository validation rules from repo docs.
- Installed shared package root:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Assumptions

- The target repository is available locally and Git commands can be executed.
- Repository-required hook tooling is installed or otherwise available in the current environment.
- The failed `pre-commit` output being handled matches the current repository state.

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific commit and validation docs first.
- Read shared package docs only when the repository explicitly points to them.

2. Confirm the pre-commit requirement.
- Use repository commit and validation docs as the source of truth for commit-time hooks.
- For repositories that follow this shared package guidance, use `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/knowledge/build-and-checks.md` as the shared reference instead of restating the policy in this skill.

3. Read the failed hook output.
- Identify which hook failed and whether any hooks rewrote files automatically.
- Inspect hook-generated file changes before making more edits.
- Keep hook-generated fixes unless there is a clear reason they are incorrect.

4. Fix one remaining hook blocker at a time.
- Apply the smallest change needed to satisfy the currently failing hook.
- If a hook failure reflects a broader repository check failure, run the relevant underlying validation command before retrying the commit.
- Avoid speculative edits unrelated to the failing hook.

5. Revalidate and retry the commit.
- Rerun the narrowest safe validation needed to confirm the hook-related fix.
- Retry the commit only after the current hook blockers are addressed.
- Confirm that the automatic `pre-commit` run triggered by the retried commit passes cleanly.

6. Report the result clearly.
- State which hooks failed and which were fixed.
- State whether hook-generated file changes were kept.
- State whether the commit is now unblocked or what blocker remains.

## Guardrails

- Never ignore a failed `pre-commit` run and pretend the commit succeeded.
- Never discard hook-generated file rewrites without inspecting them first.
- Never retry commits blindly without addressing the current hook failures.
- Never mix PR creation or Jira transitions into this task.
- Never bypass repository-required hooks unless the user explicitly directs that and repository policy allows it.

## Expected Outcome

The `pre-commit` failures triggered by `git commit` are resolved step by step, hook-generated fixes are handled safely, and the commit can be retried only when the automatic hook run is expected to pass cleanly.
