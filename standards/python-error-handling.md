# Python Error Handling Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - all Python repositories, including extensions, tools, and libraries

## Purpose
Define how Python code raises, catches, wraps, logs, and recovers from errors. Timeout, retry, and error-classification rules for HTTP and external-service calls live in [python-http-integrations.md](./python-http-integrations.md).

## Definitions

- **Domain exception**: an exception type defined by the package to represent a failure in its own terms (e.g. `VendorOrderError`), independent of the library that caused it.
- **Boundary**: a place where the code crosses into another system or layer — an HTTP client wrapper, an SDK entry point, a CLI command, a top-level handler.

## General Rules

1. Define a custom exception hierarchy per package, rooted in a single base exception. Raise domain exceptions, not generic `Exception` or `RuntimeError`.

BAD
```python
if order is None:
    raise Exception("order not found")
```

GOOD
```python
class ExtensionError(Exception):
    """Base exception for this extension."""

class OrderNotFoundError(ExtensionError):
    """Raised when the referenced order does not exist."""

if order is None:
    raise OrderNotFoundError(f"Order {order_id} not found")
```

2. Catch the narrowest exception type you can actually handle. Catch `Exception` only at the process's final top-level boundary, following the logging contract of rule 6; never catch `BaseException`.

BAD
```python
try:
    price = parse_price(item)
except Exception:
    price = 0
```

GOOD
```python
try:
    price = parse_price(item)
except InvalidPriceError:
    price = 0
```

3. Never use a bare `except:` and never swallow an exception silently.

BAD
```python
try:
    notify_vendor(order)
except:
    pass
```

GOOD
```python
try:
    notify_vendor(order)
except VendorNotificationError:
    logger.exception("Failed to notify vendor for order %s", order.id)
```

4. Handle an exception only where you can act on it; otherwise let it propagate. Do not catch and re-raise without adding value (context, translation, cleanup).

BAD
```python
try:
    order = fetch_order(order_id)
except OrderNotFoundError:
    raise
```

GOOD
```python
order = fetch_order(order_id)
```

5. When wrapping a lower-level exception at a boundary, preserve the cause chain with `raise ... from err`. Use `from None` only when hiding the cause is a deliberate, justified decision.

BAD
```python
except httpx.HTTPStatusError:
    raise VendorOrderError("vendor rejected the order")
```

GOOD
```python
except httpx.HTTPStatusError as err:
    raise VendorOrderError(f"Vendor rejected order {order_id}") from err
```

6. Log a failure once, at the site that handles it, using `logger.exception(...)` so the traceback is preserved. Do not log the same error at multiple levels and do not log-and-re-raise; the handler that finally deals with the exception owns the log entry. The single exemption is the process's final top-level boundary (rule 2): it is the last handler, so it logs once and may re-raise solely to preserve the non-zero exit — an intermediate boundary must instead add context via wrapping (rule 5) or let the error propagate without logging.

BAD
```python
except VendorOrderError:
    logger.exception("vendor call failed")
    raise  # the caller will log it again
```

GOOD
```python
except VendorOrderError:
    logger.exception("Vendor call failed for order %s", order_id)
    return notify_failure(order_id)
```

7. Error and log messages must be written in English, be actionable, and include the relevant context values (identifiers, statuses). Never include secrets, tokens, or credentials.

8. Do not use exceptions for normal control flow. Expected outcomes are return values; exceptions are for failures.

BAD
```python
try:
    subscription = find_subscription(order)
except SubscriptionNotFoundError:
    subscription = create_subscription(order)
```

GOOD
```python
subscription = find_subscription(order)
if subscription is None:
    subscription = create_subscription(order)
```

9. Release resources on error paths. Prefer context managers; use `try/finally` when no context manager exists. Never leak connections, files, or locks because an exception skipped the cleanup.

BAD
```python
client = build_client()
orders = client.list_orders()
client.close()  # skipped when list_orders raises
```

GOOD
```python
with build_client() as client:
    orders = client.list_orders()
```

## Related Documents

- [python-coding.md](./python-coding.md)
- [python-http-integrations.md](./python-http-integrations.md)
- [unittests.md](./unittests.md)
