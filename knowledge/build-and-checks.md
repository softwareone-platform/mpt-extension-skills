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

## What To Verify

Before considering a change ready, verify that:

- `make build` was executed if `uv.lock` changed
- `make check-all` passes successfully
- `pre-commit` is installed or updated before commit

## Related Documents

- [standards/documentation.md](../standards/documentation.md)
- [standards/makefiles.md](../standards/makefiles.md)
- [knowledge/make-targets.md](./make-targets.md)
