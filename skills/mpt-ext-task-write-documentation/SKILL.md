---
name: mpt-ext-task-write-documentation
description: Author or refresh a repository's required documentation set (README, AGENTS, docs/*) following the shared documentation guideline. Use when docs are missing, incomplete, or need a structural pass.
---

# Write Documentation

## Purpose

Author or refresh the required repository documentation set so it matches the shared documentation guideline, filling gaps from the repository's code and structure.

## Use When

- A repository is missing some or all of its required documentation set.
- Existing documentation is incomplete, inconsistent, or does not follow the documentation guideline.
- A repository needs a full documentation pass (structure, required files, navigation).

## Do Not Use When

- Documentation only needs to reflect a specific code change set (use `mpt-ext-task-update-docs-from-changes`).
- The task is to commit, open a pull request, or transition Jira state.
- The task is to verify documentation without writing it.

## Inputs

- A target repository to document.
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

2. Read the documentation guideline.
- Read `standards/documentation.md` for the required set, conditional documents, document responsibilities, and authoring rules. Treat it as the source of truth.

3. Audit the current documentation set with the bundled script.

```bash
python3 "${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-write-documentation/scripts/audit_docs.py" \
  --repo-root .
```

- Use `required.missing` for the documents that must be authored.
- Use `conditional_recommended` for documents the repository signals it should have.
- Use `existing_docs` and `required.present` for documents to review and refresh.
- When present (extensions with an existing `docs/external-integrations.md`), use `external_integrations.uncovered` as candidate integration modules that the index does not yet mention; confirm which are real external systems and cover them.

4. Author the missing required documents.
- Create each missing required document following the responsibilities and structure in `standards/documentation.md`.
- Derive content from the repository's actual code, structure, commands, and configuration. Do not invent behaviour.

5. Author the recommended conditional documents.
- Create each recommended conditional document when it is genuinely relevant to the repository.
- Skip a recommendation when it does not apply, and say why.

6. Refresh existing documents.
- Bring existing documents in line with the guideline: single topic per file, explicit language, examples that are short and valid.
- Keep `README.md` concise and navigational; keep `AGENTS.md` operational and ordered for agent navigation.
- Link shared standards instead of copying them; document only repository-specific behaviour, exceptions, or context.

7. Report the result.
- List documents created, documents refreshed, and recommendations intentionally skipped with a short reason.

## Guardrails

- Never duplicate shared engineering rules that already live in `standards/`; link to them instead.
- Never document behaviour, commands, or configuration that does not exist in the repository.
- Never turn `README.md` into a full reference manual or `AGENTS.md` into an explanatory document; keep both navigational.
- Never reproduce the deterministic documentation audit in prose; always use the bundled script.
- Never commit, push, open a pull request, or change Jira state in this task.
- Do not perform change-driven incremental edits here; that is `mpt-ext-task-update-docs-from-changes`.

## Shared References

- `standards/documentation.md`: required documentation set, conditional documents, responsibilities, and authoring rules.

## Bundled Resources

- `scripts/audit_docs.py`
  - Inputs: optional `--repo-root`
  - Output: JSON with `required` (`present`/`missing`), `conditional_recommended`, and `existing_docs`
  - Runtime path: `${MPT_EXTENSION_SKILLS_HOME:-$HOME/.mpt-extension-skills}/current/skills/mpt-ext-task-write-documentation/scripts/audit_docs.py`

## Expected Outcome

The repository has its required documentation set authored and any relevant conditional documents created, all consistent with `standards/documentation.md`, with `README.md` and `AGENTS.md` kept navigational, and a clear report of what was created, refreshed, or intentionally skipped.
