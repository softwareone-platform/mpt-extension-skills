# Commit Message Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - commits in repositories for extensions, tools, and libraries

## Purpose

Define a shared format for commit titles and commit descriptions.

## General Rules

1. Every commit message must use this title format:
   - `<tag>: <JIRA-ID> <short summary>`
2. The title must contain:
   - a tag
   - the Jira issue key
   - a short summary in imperative form
3. The commit description must contain a more detailed explanation of what changed.
4. The first line of the commit description must be exactly:
   - `AI Generated.`

## Allowed Tags

- `doc`: documentation changes
- `fix`: bug fixes
- `refactor`: refactoring without intended behavior change
- `feature`: new functionality

## Examples

GOOD

```text
doc: MPT-1234 add property

AI Generated.
Update the shared documentation for the new property naming rule and link the related standards.
```

GOOD

```text
fix: MPT-4567 handle empty payload

AI Generated.
Prevent the parser from failing when the upstream payload is empty and keep the existing response shape.
```

## Related Documents

- [pull-requests.md](./pull-requests.md)
