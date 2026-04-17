# Build and Checks

## Purpose

Describe the shared approach for building a repository locally and running its checks and tests.

## When To Use This Document

Use this document when you need to:

- build a repository locally
- run all required local checks and tests
- understand the mandatory validation sequence used across repositories

## General Approach

This document describes the mandatory local validation workflow that should exist across repositories.

Before creating a commit, make sure `pre-commit` is installed or updated in the local environment.
Treat this as a required preparation step, not an optional cleanup task.
If the change includes dependency updates, follow the workflow in [manage-dependencies.md](./manage-dependencies.md) first. Repositories in this family commonly use `uv` through the repository-provided targets described in [make-targets.md](./make-targets.md) instead of ad hoc dependency commands.

## Typical Validation Flow

To run the full local validation flow:

1. Run `make build` if `uv.lock` was changed.
2. Then run `make check-all`.

These commands must be executed sequentially in that order.

```bash
make build
make check-all
```

Typical expectations:

- `build` refreshes the local build environment when dependency lock files change
- `check-all` runs the full validation set expected before merge

## Pre-commit

Before committing changes, make sure `pre-commit` is installed or updated locally.

`pre-commit` hooks run automatically during `git commit`.
Do not assume the commit step succeeded just because the commit command was started.
You must review the hook output and confirm that all hooks passed.

If hooks fail or rewrite files:

1. inspect the reported failures or file changes
2. apply or keep the hook-generated fixes
3. rerun the relevant checks if needed
4. retry the commit and confirm the hooks pass cleanly

The commit workflow is not complete until the automatic `pre-commit` run succeeds.

## What To Verify

Before considering a change ready, verify that:

- `make build` was executed if `uv.lock` changed
- `make check-all` passes successfully
- `pre-commit` is installed or updated before commit
- the automatic `pre-commit` run triggered by `git commit` was reviewed
- the automatic `pre-commit` run completed without remaining failures

## Related Documents

- [standards/documentation.md](../standards/documentation.md)
- [standards/makefiles.md](../standards/makefiles.md)
- [knowledge/manage-dependencies.md](./manage-dependencies.md)
- [knowledge/make-targets.md](./make-targets.md)
