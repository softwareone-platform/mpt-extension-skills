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
django = "^4.2.2"
django = ">=4.2,<6.0"
```

GOOD
```toml
django = "==4.2.*"
```

4. Pin an exact version only when the repository has a documented reason to do so, such as compatibility or reproducibility requirements.

GOOD
```toml
django = "==4.2.2"
```
