# Python Coding Conventions

## Owner
Sirius Team

## Scope

Applies to:
 - all Python repositories, including extensions, tools, and libraries

## Purpose
Describe the general conventions for Python code.

## General Rules

1. Use type annotations (PEP 484), except in the `tests/` folder unless a repository explicitly requires them there.
2. All public functions, methods, and classes must include [Google-style docstrings](https://google.github.io/styleguide/pyguide.html).
3. Do not add explanatory comments for obvious code. Use comments only when they provide context that is hard to express in code or docstrings.
4. `__init__.py` files must not include module-level docstrings; this rule `#4` does not override rule `#2` for public functions, methods, and classes defined there.
5. Function and variable names must be explicit and intention-revealing.
6. `pyproject.toml` is the source of truth for code quality rules. Generated code must not violate any configured rules.
7. `ruff` is the primary linter for general Python style and best practices.
8. `flake8` is used only for rules that are not covered by `ruff`, such as:
 - `wemake-python-styleguide` for stricter Python conventions
 - `flake8-aaa` for validating the AAA pattern in tests
9. Follow PEP 8 style and naming conventions unless repository tooling explicitly overrides them.
10. Prefer simple, explicit code over clever or overly compact implementations.
