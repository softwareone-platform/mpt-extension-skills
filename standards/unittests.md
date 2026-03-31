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
2. Write tests as functions, not classes.
3. Name test files and test functions with the `test_` prefix.
4. Follow AAA (Arrange, Act, Assert). See the [flake8-aaa documentation](https://flake8-aaa.readthedocs.io/en/stable/index.html).

GOOD
```python
def test_returns_error_for_invalid_payload():
    # Arrange
    payload = {"name": ""}
    
    # Act
    result = validate_payload(payload)
    
    # Assert
    assert result.is_valid is False
```
5. Do not use `if` statements or branching logic inside tests.

BAD
```python
@pytest.mark.parametrize("a", [1, 2])
def test_validation_payload(a):
    result = validate_payload(a)
    
    if a == 1:
        assert result.is_valid
    elif a == 2:
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
def test_validation_payload(a, is_valid_expected):
    result = validate_payload(a)

    assert result.is_valid == is_valid_expected
```
6. Use `@pytest.mark.parametrize` when testing multiple permutations of the same behavior.
7. Keep the test directory structure aligned with the source code structure.

BAD
```
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
```
mpt-extension-<name>/
|-- <name>/ # main code of the extension
     |-- flows/  # definition of flows
          |-- steps/  # contains a set of steps used in flows
          |-- fulfillment.py # example of separated logic; split further if needed
          |-- validation.py
tests/
  |-- flows/ # folders have the same name as in the source code
      |-- test_fulfillment.py  # same module name with test_ prefix
      |-- test_validation.py
```
8. Prefer a single logical assertion per test. If multiple assertions validate one result object, keep them tightly related and easy to read.

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
9. Test branches as close as possible to the function where the branch exists.
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

10. Do not test private or protected functions or methods directly. Cover them through public behavior instead.

BAD
```python
from some_module import _private_function

def test_private_function():
    assert _private_function() is True
```

11. Unit tests must be deterministic. They must not depend on current time, randomness, or external state.

BAD
```python
assert get_timestamp() > 0
```

GOOD
```python
result = get_timestamp(fixed_time)

assert result == expected_value
```

12. Target unit test coverage above 95% unless a repository documents an explicit exception.
13. Every bugfix MUST have test to reproduce it or changes in existing tests

## Mocking Rules
1. Do not use `unittest.mock` directly.
2. Use the `mocker` fixture only when mocking is unavoidable.
3. Prefer fixtures and real value objects over mocks whenever possible.
4. Always use `autospec=True` when patching.

GOOD
```python
@pytest.fixture
def mock_mpt_update_asset(mocker):
    return mocker.patch("mpt_extension_sdk.mpt_http.mpt.update_asset", autospec=True)
```
5. Unit tests must not call real APIs, databases, or any other external systems.
