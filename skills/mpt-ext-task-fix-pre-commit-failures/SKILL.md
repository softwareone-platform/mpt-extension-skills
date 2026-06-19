---
name: mpt-ext-task-fix-pre-commit-failures
description: Fix pre-commit hook failures when a git commit is blocked. Reads hook output, fixes one failure at a time, reruns validation, and retries the commit (max 5 iterations).
---

# Fix Pre-commit Failures

## Purpose

Resolve `pre-commit` hook failures that block a `git commit`, one hook failure at a time, stopping when the commit is clean, when the loop stops converging, or after at most 5 fix-and-retry iterations.

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
- Read the target repository `AGENTS.md` once per session. If you already loaded it earlier in this session and still have its full contents, reuse them instead of re-reading; if the context was summarized or you are unsure it is complete, read it again. Do not pre-load shared docs in this step; read them lazily only when the repository points to them.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Confirm the pre-commit requirement.
- Use repository commit and validation docs as the source of truth for commit-time hooks.
- For repositories that follow this shared package guidance, read `knowledge/build-and-checks.md` using the shared-doc resolution rule from the repository context step instead of restating the policy in this skill.

3. Read the failed hook output.
- Identify which hook failed and whether any hooks rewrote files automatically.
- Inspect hook-generated file changes before making more edits.
- Keep hook-generated fixes unless there is a clear reason they are incorrect.

4. Fix one remaining hook blocker at a time.
- Apply the smallest change needed to satisfy the currently failing hook.
- If a hook failure reflects a broader repository check failure, run the relevant underlying validation command before retrying the commit.
- Avoid speculative edits unrelated to the failing hook.

5. Revalidate and retry the commit.
- One iteration = one scoped hook fix + one commit retry. Confirming a clean automatic `pre-commit` run after the loop is not a separate iteration.
- Before each attempt, state the iteration explicitly: `Iteration N/5 — failing hook: <hook>`.
- Rerun the narrowest safe validation needed to confirm the hook-related fix.
- Retry the commit only after the current hook blockers are addressed.
- Confirm that the automatic `pre-commit` run triggered by the retried commit passes cleanly.
- Stop early, without consuming the remaining iterations, when there is no progress: the same hook fails the same way after a fix attempt, or a fix re-introduces a previously-passing hook. Report it as a non-converging blocker.
- Stop when the commit is still blocked after 5 fix-and-retry iterations, and report the remaining hook output as the blocker.

6. Report the result clearly.
- State which hooks failed and which were fixed.
- State whether hook-generated file changes were kept.
- State whether the commit is now unblocked or what blocker remains.
- End with exactly one classified outcome the caller can act on, chosen by this precedence (success first):
  - `committed` — the commit completed with a clean automatic `pre-commit` run, even when reached on the final allowed iteration.
  - `needs-user-input` — a remaining hook failure needs user direction or a broader design decision.
  - `environment-blocker` — the remaining failure is environment or hook-setup related, not product code.
  - `non-converging` — the same hook failed the same way after a fix, or a fix reintroduced a previously-passing hook.
  - `iteration-limit-reached` — 5 fix-and-retry iterations were spent without reaching any of the above.

## Guardrails

- Never ignore a failed `pre-commit` run and pretend the commit succeeded.
- Never discard hook-generated file rewrites without inspecting them first.
- Never retry commits blindly without addressing the current hook failures.
- Never run more than 5 pre-commit fix-and-retry iterations before stopping with a blocker, and stop sooner when the loop stops converging.
- Never let the caller re-loop this task; this task owns the bounded fix-and-retry loop and returns a single classified outcome.
- Never mix PR creation or Jira transitions into this task.
- Never bypass repository-required hooks unless the user explicitly directs that and repository policy allows it.

## Expected Outcome

The `pre-commit` failures triggered by `git commit` are resolved step by step, hook-generated fixes are handled safely, and the commit is retried only when the automatic hook run is expected to pass cleanly, up to the 5-iteration limit or until the loop stops converging, and the task returns a single classified outcome (`committed`, `needs-user-input`, `environment-blocker`, `non-converging`, or `iteration-limit-reached`) for the caller to act on.
