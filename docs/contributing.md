# Contributing

## Purpose

Describe the repository-specific contribution workflow and point contributors to the shared standards that govern commits, pull requests, documentation, and skill authoring.

## Contribution Workflow

Use this repository workflow when adding or updating shared skills, standards, knowledge, installer scripts, or repository documentation:

1. Create or switch to the work branch for the target Jira item.
2. Keep the scope narrow and avoid mixing unrelated changes.
3. Update shared standards when the change affects cross-repository rules.
4. Update repository-specific docs in `docs/` when the change affects how this repository is used.
5. Run the repository validation commands from [testing.md](./testing.md) before committing.
 - Prefer `make check-all` as the default local validation command.
6. Commit and open a pull request using the shared commit and PR standards linked below.

## Shared Standards

Use these shared standards as the source of truth:

- [../standards/commit-messages.md](../standards/commit-messages.md)
- [../standards/pull-requests.md](../standards/pull-requests.md)
- [../standards/documentation.md](../standards/documentation.md)
- [../standards/skills.md](../standards/skills.md)

## Repository-Specific Notes

- This repository contains shared reusable materials rather than product runtime code.
- Keep local links inside repository documentation and skill references relative to installed package paths or repository-local paths, depending on the document type.
- When a change affects skill installation or runtime wiring, also review [installation.md](./installation.md).

## Related Documents

- [testing.md](./testing.md)
- [../README.md](../README.md)
- [../AGENTS.md](../AGENTS.md)
