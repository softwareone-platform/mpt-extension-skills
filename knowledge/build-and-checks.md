# Build and Checks

## General Approach

Before creating a commit, make sure `pre-commit` is installed or updated in the local environment.
Treat this as a required preparation step, not an optional cleanup task.

If the change includes dependency updates, apply them first through the shared dependency standard in [standards/packages-and-dependencies.md](../standards/packages-and-dependencies.md), preferring the repository-provided `make uv-*` targets over ad hoc dependency commands.

## Typical Validation Flow

To run the full local validation flow:

1. Run `make build` if `uv.lock` was changed.
2. Then run `make check-all`.

These commands must be executed sequentially in that order.

```bash
make build
make check-all
```

## Pre-commit

`pre-commit` hooks run automatically during `git commit`.
Do not assume the commit step succeeded just because the commit command was started.
You must review the hook output and confirm that all hooks passed.

If hooks fail or rewrite files:

1. inspect the reported failures or file changes
2. apply or keep the hook-generated fixes
3. rerun the relevant checks if needed
4. retry the commit and confirm the hooks pass cleanly

The commit workflow is not complete until the automatic `pre-commit` run succeeds.
