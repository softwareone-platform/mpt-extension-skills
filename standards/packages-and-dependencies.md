# Python Dependency Management Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - Python extensions
 - Python libraries
 - Python tools

Does not apply to:
 - other programming languages

## Purpose
Define how Python repositories should declare dependencies in `pyproject.toml` and maintain dependency lock files.

## General Rules
1. Use `uv` for dependency management.
2. Keep `uv.lock` up to date after every dependency change in `pyproject.toml`.
3. Prefer patch-level version ranges in `pyproject.toml` when the repository is expected to receive safe patch updates automatically.

BAD
```toml
[project]
dependencies = [
  "django>=4.2,<6.0",
]
```

GOOD
```toml
[project]
dependencies = [
  "django==4.2.*",
]
```

4. Pin an exact version only when the repository has a documented reason to do so, such as compatibility or reproducibility requirements.

GOOD
```toml
[project]
dependencies = [
  "django==4.2.2",
]
```

5. Reusable libraries (distributions other projects depend on) are an exception to rules 3 and 4: declare a bounded compatible range up to the next major instead of pinning a single minor, so consumers are not forced onto one minor. Applications and extensions keep the patch-level pin from rule 3.

GOOD (library)
```toml
[project]
dependencies = [
  "mpt-extension-sdk>=6.3,<7",
]
```

6. When a repository exposes the `uv` wrapper targets below, prefer them over direct `uv` commands so dependency changes go through the repository workflow. Some repositories run `uv` inside Docker through these targets, so calling `uv` directly can bypass the required environment. Deviate only when the repository documentation requires a different command.

```bash
make uv-add pkg=<package>      # add a runtime dependency
make uv-add-dev pkg=<package>  # add a development dependency
make uv-upgrade                # upgrade all dependencies and refresh uv.lock
make uv-upgrade pkg=<package>  # upgrade one dependency and refresh uv.lock
```
