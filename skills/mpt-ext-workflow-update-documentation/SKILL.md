---
name: mpt-ext-workflow-update-documentation
description: Bring documentation up to date for a change set end to end: update affected docs, self-check against the guideline, and stage them. Use before committing or sending a change to review.
---

# Update Documentation Workflow

## Purpose

Coordinate updating repository documentation for a change set from start to staged: update the affected documents, verify the result against the documentation guideline, and stage the documentation for commit.

## Use When

- A change is ready and its documentation impact should be reflected as one coordinated flow.
- Documentation must be current and staged before committing or sending the change to review.

## Do Not Use When

- The repository has no documentation set yet and it must be authored from scratch (use `mpt-ext-task-write-documentation`).
- Only a single documentation edit is needed without the surrounding flow (use `mpt-ext-task-update-docs-from-changes` directly).
- The task is to commit, push, open a pull request, or transition Jira state.

## Inputs

- A target repository that is a Git working tree with history.
- The change source to document: `unstaged`, `uncommitted`, `last-commit`, or `branch-diff` (with an optional base ref).
- Installed shared package root when shared guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs required by this skill (see Shared References) regardless of repository pointers; read additional shared docs only when the repository explicitly points to them.
- Resolve shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Update the affected documentation.
- Use `mpt-ext-task-update-docs-from-changes` with the requested change source to map the change set to affected documents and edit them.

3. Self-check the result.
- Re-run the change collection from `mpt-ext-task-update-docs-from-changes` and compare its `affected_docs` and `missing_doc_updates` against what was actually edited.
- If a genuinely affected document is still not updated, return to step 2 for that document.
- Run at most 3 update-and-recheck iterations before stopping and reporting the remaining gaps.

4. Stage the documentation for commit.
- Stage only the documentation files that were updated (`docs/*`, `README.md`, `AGENTS.md`).
- Do not stage unrelated files.

5. Report the result.
- List the documents updated and staged.
- List affected documents intentionally left unchanged, with a short reason.
- Report any remaining gaps after the iteration limit, and anything that needs human judgement.

## Guardrails

- Never author a missing full documentation set here; delegate that to `mpt-ext-task-write-documentation`.
- Never commit, push, open a pull request, or change Jira state in this workflow.
- Never stage files that are not documentation updated by this flow.
- Never exceed 3 update-and-recheck iterations; stop and report instead of looping.
- Never invent documentation for behaviour that is not in the change set.

## Shared References

- `standards/documentation.md`: required documentation set, structure, and authoring rules.

## Expected Outcome

The documentation affected by the change set is updated, verified against `standards/documentation.md`, and staged for commit, or the workflow stops with a clear report of remaining gaps that need attention.
