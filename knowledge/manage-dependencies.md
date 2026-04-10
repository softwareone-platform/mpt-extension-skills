# Manage Dependencies

## Purpose

Describe the shared workflow for adding and upgrading Python dependencies in repositories that use `uv`.

## When To Use This Document

Use this document when you need to:

- add a runtime dependency
- add a development dependency
- upgrade one dependency or all dependencies
- understand the expected dependency-management workflow in repositories that wrap `uv` with `make`

## Dependency Management

Follow the shared dependency standard in [packages-and-dependencies.md](../standards/packages-and-dependencies.md) for version policy and lockfile expectations.

This repository family uses `uv` for dependency management. When a repository exposes the `make` targets below, prefer them over ad hoc dependency commands so dependency changes stay consistent with the repository workflow.

```bash
make uv-add pkg=<package>
make uv-add-dev pkg=<package>
make uv-upgrade
make uv-upgrade pkg=<package>
```

Repositories may run `uv` through Docker-backed `make` targets. In those repositories, use the `make` targets above instead of calling `uv` directly unless the repository documentation explicitly requires a different command.

## What To Verify

After changing dependencies, verify that:

- the dependency declaration is updated in the expected repository file, typically `pyproject.toml`
- `uv.lock` is refreshed when dependency inputs changed
- any required build or validation steps from the target repository were run

## Related Documents

- [standards/packages-and-dependencies.md](../standards/packages-and-dependencies.md)
- [knowledge/make-targets.md](./make-targets.md)
- [knowledge/build-and-checks.md](./build-and-checks.md)
