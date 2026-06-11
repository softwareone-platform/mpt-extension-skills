---
name: mpt-ext-task-update-docs-from-changes
description: Update repository documentation from a code change set. Use when docs/*, README.md, or AGENTS.md must be brought up to date with unstaged, uncommitted, last-commit, or branch-diff changes.
---

# Update Docs From Changes

## Purpose

Bring repository documentation (`docs/*`, `README.md`, `AGENTS.md`) up to date with a specific set of code changes, following the shared documentation guideline.

## Use When

- Code or behaviour changed and the matching documentation must be updated.
- The user wants documentation regenerated from unstaged, uncommitted, last-commit, or branch-diff changes.
- A change is ready for review and its documentation impact must be reflected first.

## Do Not Use When

- The repository has no documentation yet and the full required set must be authored from scratch (use `mpt-ext-task-write-documentation`).
- The task is to commit, open a pull request, or transition Jira state.
- The task is to verify documentation without editing it.

## Inputs

- A target repository that is a Git working tree with history.
- The change source to document:
  - `unstaged`: working tree vs index
  - `uncommitted`: working tree vs `HEAD` (staged + unstaged)
  - `last-commit`: `HEAD~1..HEAD`
  - `branch-diff`: `<base>...HEAD` (base defaults to `origin/main`)
- Optional base ref when the source is `branch-diff`.
- Installed shared package root when shared guidance is needed:

```text
${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current
```

## Workflow

1. Build repository context first.
- If not already done for the current task, read the target repository `AGENTS.md`.
- Read repository-specific docs when they exist, because they may extend or override shared guidance.
- Read shared docs only when the repository explicitly points to them. Resolve those shared docs from `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current` when available; otherwise read them from the `main` branch of the shared GitHub repository.

2. Determine the change source.
- Use the source the user requested.
- If the source is ambiguous, ask the user before running. For `branch-diff`, confirm the base ref.

3. Collect the change set with the bundled script.

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-update-docs-from-changes/scripts/collect_changes.py" \
  --source branch-diff --base origin/main
```

- Use `affected_docs` to know which documents each changed path most likely affects.
- Use `missing_doc_updates` to see which affected docs were not yet touched in this change set.
- Treat `always_review` (`README.md`, `AGENTS.md`) as documents that need a judgement call, because behaviour and structure changes affecting them are not detectable from paths.
- Treat `unmapped_code` as changes with no default mapping; decide their documentation impact manually.

4. Update the affected documents.
- For each affected document, read the current document and the actual change content, then edit only what the change affects.
- Follow `standards/documentation.md` for structure, topic boundaries, and required-set expectations.
- Do not duplicate shared standards; link to them and document only repository-specific behaviour, exceptions, or context.
- Update `README.md` navigation and `AGENTS.md` reading order only when structure, entry points, or public behaviour actually changed.

5. Report the result.
- List the documents updated and the change paths that drove each update.
- List affected documents you intentionally left unchanged, with a short reason.
- Surface anything that needs human judgement (for example a behaviour change whose user-facing impact is unclear).

## Guardrails

- Never document behaviour that is not present in the change set; do not invent features or future plans.
- Never duplicate shared engineering rules that already live in `standards/`; link to them instead.
- Never edit documentation unrelated to the change set.
- Never reproduce the deterministic change collection in prose; always use the bundled script.
- Never commit, push, open a pull request, or change Jira state in this task.
- Keep edits minimal and scoped to the change; do not rewrite untouched sections.

## Shared References

- `standards/documentation.md`: required documentation set, structure, and authoring rules.

## Bundled Resources

- `scripts/collect_changes.py`
  - Inputs: `--source {unstaged,uncommitted,last-commit,branch-diff}`, optional `--base`
  - Output: JSON with `changed_files`, `affected_docs`, `missing_doc_updates`, `always_review`, and `unmapped_code`
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-update-docs-from-changes/scripts/collect_changes.py`

## Expected Outcome

The documentation affected by the given change set is updated in line with `standards/documentation.md`, README/AGENTS are adjusted only when structure or behaviour changed, and the result clearly states what was updated and what was intentionally left unchanged.
