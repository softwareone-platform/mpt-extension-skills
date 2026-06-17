# Python Unit Testing Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - Python extension unit tests
 - Python library unit tests
 - Python tool unit tests

Does not apply to:
 - integration tests
 - end-to-end tests

## Purpose
Define general rules for unit test code in Python repositories.

## General Rules
1. Use `pytest` for unit tests.
2. Write tests as functions, not classes. Do not group tests inside a `class`, even to share setup. Share setup with fixtures and modules instead.

BAD
```python
class TestValidatePayload:
    def test_returns_error_for_invalid_payload(self):
        payload = {"name": ""}

        result = validate_payload(payload)

        assert result.is_valid is False
```

GOOD
```python
def test_returns_error_for_invalid_payload():
    payload = {"name": ""}

    result = validate_payload(payload)

    assert result.is_valid is False
```

3. Do *NOT* use type annotations (PEP 484). This includes test function parameters and `@pytest.mark.parametrize` arguments. Annotating arguments adds no value in tests, and a boolean parameter annotation also triggers `ruff` `FBT` findings.

BAD
```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, True), (2, False)],
)
def test_is_valid(value: int, expected: bool) -> None:  # FBT001 on `expected`
    assert is_valid(value) is expected
```

GOOD
```python
@pytest.mark.parametrize(
    ("value", "expected"),
    [(1, True), (2, False)],
)
def test_is_valid(value, expected):
    assert is_valid(value) is expected
```
4. Name test files and test functions with the `test_` prefix.
5. Do *NOT* write docstrings.
6. Follow AAA (Arrange, Act, Assert). See the [flake8-aaa documentation](https://flake8-aaa.readthedocs.io/en/stable/index.html).

BAD
```python
def test_returns_error_for_invalid_payload():
    payload = {"name": ""}

    validate = validate_payload(payload)

    assert validate.is_valid is False
```

GOOD
```python
def test_returns_error_for_invalid_payload():
    payload = {"name": ""}

    result = validate_payload(payload)

    assert result.is_valid is False
```

BAD
```python
def test_reverse_shopping() -> None:
    shopping = ["apples", "bananas", "cabbages"]

    shopping.reverse()

    assert shopping == ["cabbages", "bananas", "apples"]

```

GOOD
```python
def test_reverse_shopping() -> None:
    shopping = ["apples", "bananas", "cabbages"]

    shopping.reverse()  # act

    assert shopping == ["cabbages", "bananas", "apples"]
```

7. Do not use `if` statements or branching logic inside tests.

BAD
```python
@pytest.mark.parametrize("payload", [1, 2])
def test_validation_payload(payload):
    result = validate_payload(payload)

    if payload == 1:
        assert result.is_valid
    elif payload == 2:
        assert not result.is_valid
```

GOOD
```python
@pytest.mark.parametrize(
    "a, is_valid_expected",
    [
        (1, True),
        (2, False),
    ],
)
def test_validation_payload(payload, is_valid_expected):
    result = validate_payload(payload)

    assert result.is_valid == is_valid_expected
```

8. Use `@pytest.mark.parametrize` when testing multiple permutations of the same behavior.
9. Keep the test directory structure aligned with the source code structure, and group related test modules into packages that mirror the source packages. Do not collect unrelated test modules in one flat directory.

BAD
```text
mpt-extension-<name>/
|-- <name>/ # main code of the extension
    |-- flows/  # definition of flows
        |-- steps/  # contains a set of steps used in flows
        |-- fulfillment.py # example of separated logic; split further if needed
        |-- validation.py
tests/
  |-- test_flows_steps.py # random names, hard to understand what module is under test
  |-- test_validation_flows.py
  |-- test_flows.py
```

GOOD
```text
mpt-extension-<name>/
|-- <name>/ # main code of the extension
     |-- flows/  # definition of flows
          |-- steps/  # contains a set of steps used in flows
          |-- fulfillment.py # example of separated logic; split further if needed
          |-- validation.py
tests/
  |-- flows/ # packages mirror the source packages
      |-- steps/
          |-- test_create_order.py
      |-- test_fulfillment.py  # same module name with test_ prefix
      |-- test_validation.py
```

10. Prefer a single logical assertion per test. If multiple assertions validate one result object, keep them tightly related and easy to read.

BAD
```python
def test_example():
    param = 1
    result = function_under_test(param)
    assert result[0] == "expected_value_1"
    assert result[1] == "expected_value_2"
    # or
    assert result.property_1 == "property_1"
    assert result.property_2 == "property_2"
    # or
    assert result["property_1"] == "property_1"
    assert result["property_2"] == "property_2"
```

GOOD
```python
def test_example():
    param = 1

    result = function_under_test(param)

    assert result == ["expected_value_1", "expected_value_2"]
    # or whole object
    assert result == expected_result
    # or
    assert result == {"property_1": "property_1", "property_2": "property_2"}
```

11. Test branches as close as possible to the function where the branch exists.
```python

def inner_function_to_test(a):
    return a == 2


def outer_function_to_test(b):
    return inner_function_to_test(b + 1)

# BAD tests example
@pytest.mark.parametrize(
    "input_value, is_valid",
    [
        (1, True),
        (2, False),
    ],
)
def test_outer_function(input_value, is_valid):
    assert outer_function_to_test(input_value) is is_valid
# no tests for inner function


# GOOD tests example
@pytest.mark.parametrize(
    "input_value, is_valid",
    [
        (1, True),
        (2, False),
    ],
)
def test_inner_function(input_value, is_valid):
    # Verify the branch where it actually exists.
    result = inner_function_to_test(input_value)

    assert result is is_valid

# Also add a focused test for the outer function behavior.
def test_outer_function():
    result = outer_function_to_test(1)

    assert result is True
```

12. Do not test private or protected functions or methods directly. Cover them through public behavior instead.

BAD
```python
from some_module import _private_function

def test_private_function():
    assert _private_function() is True
```

13. Unit tests must be deterministic. They must not depend on current time, randomness, or external state.

BAD
```python
assert get_timestamp() > 0
```

GOOD
```python
result = get_timestamp(fixed_time)

assert result == expected_value
```

14. Target unit test coverage above 95% unless a repository documents an explicit exception.
15. Every bugfix MUST have a test to reproduce it, or changes in existing tests.

## Fixtures And conftest

1. Prefer fixtures over repeated arrange code. When the same setup or value object appears in more than one test, extract it into a fixture instead of copy-pasting it.
2. Put shared fixtures in `conftest.py` at the narrowest scope that covers the tests that use them (per-package `conftest.py` is preferred over a single root `conftest.py` for fixtures used by one package only).
3. Do not let `conftest.py` grow into a single large grab-bag. When it accumulates many unrelated fixtures, split the fixtures into a dedicated package of focused modules and register them from `conftest.py` with `pytest_plugins`.

GOOD
```text
tests/
  conftest.py            # registers the fixtures package, no large fixture body
  fixtures/              # the "conftest package": fixtures grouped by topic
      __init__.py
      orders.py
      http.py
      vendor.py
```

```python
# tests/conftest.py
pytest_plugins = [
    "tests.fixtures.orders",
    "tests.fixtures.http",
    "tests.fixtures.vendor",
]
```

```python
# tests/fixtures/orders.py
import pytest


@pytest.fixture
def order():
    return {"id": "ORD-0001", "status": "processing"}
```

4. Keep fixture dependency chains shallow. A fixture must depend on **at most 3 levels** of other fixtures. If a chain grows deeper, flatten it by building the value directly or by combining intermediate fixtures.

BAD
```python
# 4 levels deep: settings -> client -> session -> authed_session -> order_api
@pytest.fixture
def client(settings): ...

@pytest.fixture
def session(client): ...

@pytest.fixture
def authed_session(session): ...

@pytest.fixture
def order_api(authed_session): ...
```

GOOD
```python
# at most 3 levels: settings -> client -> order_api
@pytest.fixture
def client(settings): ...

@pytest.fixture
def order_api(client):
    # build the authenticated session inline instead of chaining extra fixtures
    ...
```

## Test Data And Factories

1. Build test objects with factory fixtures, not with ad-hoc private helper methods scattered across test modules. A factory fixture returns a function that builds the object, so each test creates exactly the variant it needs while construction stays in one place.

BAD
```python
# private helper duplicated across test modules
def _make_order(id, name):
    return {"id": id, "name": name}


def test_order_name():
    order = _make_order("ORD-0001", "First order")

    ...
```

GOOD
```python
@pytest.fixture
def order_factory():
    def _build(id, name):
        return {"id": id, "name": name}

    return _build


def test_order_name(order_factory):
    order = order_factory("ORD-0001", "First order")

    ...
```

2. Place shared factory fixtures in the `conftest`/fixtures package so they can be reused across modules, following the fixtures rules above.
3. A factory fixture intentionally returns a nested builder function. The repository test lint configuration must permit nested functions in test code so the pattern does not fight the linter (for example, ignore `WPS430` for `tests/` paths). This is a sanctioned exception to the general "fix the code, do not silence the linter" rule because the nested builder is required by rule 1.

## Mocking Rules
1. Do not use `unittest.mock` directly.
2. Use the `mocker` fixture only when mocking is unavoidable.
3. Prefer fixtures and real value objects over mocks whenever possible. Build the real domain or context object (for example the SDK `OrderContext`) instead of an ad-hoc `SimpleNamespace` or bare `Mock`; mock only the parts that genuinely cannot be real (such as an outbound API client).
4. Always use `autospec=True` when patching, and build injected mock objects with `create_autospec(...)` so their attributes and call signatures match the real type. A spec-less `Mock`/`AsyncMock` accepts any attribute and any call, hiding wrong method names or signatures.

GOOD
```python
@pytest.fixture
def mock_mpt_update_asset(mocker):
    return mocker.patch("mpt_extension_sdk.mpt_http.mpt.update_asset", autospec=True)


@pytest.fixture
def order_service(mocker):
    # injected mock: spec it against the real type
    return mocker.create_autospec(OrderService, instance=True)
```
5. Unit tests must not call real APIs, databases, or any other external systems.
6. To control time, use `freezegun` (`freeze_time`) instead of patching `datetime`, `datetime.now`, or `time.time`. Freeze the clock to a fixed instant so the test stays deterministic (see General Rule 13). Freeze only when the code under test reads the clock itself; when the test can pass the instant explicitly (for example a `today=` or `now=` argument), pass it instead of freezing.

BAD
```python
def test_marks_order_expired(mocker):
    mocker.patch("extension.orders.datetime", autospec=True)

    ...
```

GOOD
```python
from freezegun import freeze_time


@freeze_time("2026-01-01T00:00:00Z")
def test_marks_order_expired():
    result = is_expired(order)

    assert result is True
```
