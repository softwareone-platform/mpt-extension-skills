# Documentation

## Purpose

Describe the repository-specific rules for validating documentation changes in this repository.

## Source Of Truth

Use the shared documentation standard as the primary source of truth:

- [../standards/documentation.md](../standards/documentation.md)

This repository-specific document exists only to define how documentation changes should be validated here.

## Documentation Validation Rules

When changing documentation in this repository, validate the following:

1. Shared rules are linked, not copied.
- Use local repository links to shared standards and shared knowledge.
- Do not replace shared standard references with GitHub URLs when a local repository path is available.

2. Repository-specific docs stay in the right place.
- Put repository-specific contribution and testing guidance in `docs/`.
- Put package installation guidance in `docs/`.
- Keep reusable cross-repository rules in `standards/` or `knowledge/`.

3. Navigation stays consistent.
- Update [README.md](../README.md) when a new discoverable document is added.
- Update [AGENTS.md](../AGENTS.md) when a new document changes how agents should navigate the repository.

4. Shared skill documentation stays locally referential.
- When a skill or repository document links to shared standards, shared knowledge, or package docs, use local paths.
- Do not rely on remote repository URLs for required documentation context.

5. Topic boundaries stay clear.
- Do not mix contribution workflow, testing guidance, and package distribution rules in one document when a dedicated document already exists.
- Prefer linking to:
  - [contributing.md](./contributing.md)
  - [installation.md](./installation.md)
  - [usage.md](./usage.md)
  - [testing.md](./testing.md)

## Validation Checklist

Before committing documentation changes, check:

- links resolve locally within the repository
- shared standards are referenced with local paths
- README and AGENTS indexes are updated when needed
- the document is stored in the correct directory
- the document does not duplicate an existing shared standard
- repository testing instructions match the commands in [testing.md](./testing.md)

## Related Documents

- [../standards/documentation.md](../standards/documentation.md)
- [contributing.md](./contributing.md)
- [installation.md](./installation.md)
- [usage.md](./usage.md)
- [testing.md](./testing.md)
- [../README.md](../README.md)
- [../AGENTS.md](../AGENTS.md)
