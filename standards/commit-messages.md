# Commit Message Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - commits in repositories for extensions, tools, and libraries

## Purpose

Define a shared format for commit titles and commit descriptions.

## General Rules

Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for title format, allowed types, and breaking-change markers. The rule below extends it for this repository:

1. The commit body is required and must explain what changed and why.

## Examples

GOOD

```text
docs: add property

Update the shared documentation for the new property naming rule and
link the related standards.
```

GOOD (breaking change)

```text
feat(api)!: drop deprecated v1 endpoints

Remove the v1 routes that were marked deprecated in the previous
release. Clients must migrate to v2.

BREAKING CHANGE: v1 endpoints are no longer served.
```

## Related Documents

- [pull-requests.md](./pull-requests.md)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
