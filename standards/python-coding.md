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
4. `__init__.py` files must not include module-level docstrings. More generally, avoid redundant module-level docstrings: do not add one that only restates the module name or path — if a module seems to need a docstring to explain "what it contains", that usually signals a naming problem. This rule `#4` does not override rule `#2`: public functions, methods, and classes still require docstrings.
5. Function and variable names must be explicit and intention-revealing.
6. `pyproject.toml` is the source of truth for code quality rules. Generated code must not violate any configured rules.
7. `ruff` is the primary linter for general Python style and best practices.
8. `flake8` is used only for rules that are not covered by `ruff`, such as:
 - `wemake-python-styleguide` for stricter Python conventions
 - `flake8-aaa` for validating the AAA pattern in tests
9. Follow PEP 8 style and naming conventions unless repository tooling explicitly overrides them.
10. Prefer simple, explicit code over clever or overly compact implementations.
11. Organize modules into cohesive packages by responsibility. Group related modules into a package with a clear purpose instead of leaving flat modules at the top level or accumulating unrelated helpers in a generic `utils`/`helpers` dump.

BAD
```text
extension/
  utils.py     # unrelated helpers piled together
  helpers.py
  stuff.py
  client.py
  vendor.py
```

GOOD
```text
extension/
  flows/
    steps/
    fulfillment.py
    validation.py
  client/
    mpt.py
    vendor.py
```

12. Fix linter and type-checker findings by correcting the code, not by silencing the check.

BAD
```python
result = compute(data)  # noqa
```

GOOD
```python
result = compute(data)
```

13. Inline suppressions (`# noqa`, `# noqa: <rule>`, `# type: ignore`, ruff per-file ignores) are a last resort. When a suppression is genuinely unavoidable, use it only for a specific rule, on the narrowest possible scope, place it on the same line as the code it suppresses, and add a short comment explaining why it is justified. Do not silence whole files or broad rule sets just to make checks pass.

BAD
```python
# the suppression sits on its own line, so it does not apply to the code below
# noqa: E501
VENDOR_SIGNATURE_URL = "https://vendor.example.com/very/long/callback/path?with=many&query=params"
```

GOOD
```python
VENDOR_SIGNATURE_URL = "https://vendor.example.com/very/long/callback/path?with=many&query=params"  # noqa: E501 — vendor signature URL must stay on a single line
```
