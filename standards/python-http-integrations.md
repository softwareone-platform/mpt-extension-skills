# Python HTTP Integrations Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - Python code that calls HTTP APIs or other external services

## Purpose
Define how Python code handles HTTP and external-service integrations: timeouts, error translation, retry policies, and idempotency. General exception raising, wrapping, and logging rules live in [python-error-handling.md](./python-error-handling.md), including the definitions of *domain exception* and *boundary* used below.

## Definitions

- **Retryable error**: a transient failure that may succeed on a later attempt (timeout, connection error, HTTP 429, HTTP 5xx).
- **Non-retryable error**: a failure that will not change on retry (most HTTP 4xx, validation errors, authentication or authorization failures).
- **Idempotent operation**: an operation that produces the same result when executed more than once.

## General Rules

1. Every HTTP or external-service call must set an explicit timeout. Never rely on library defaults or allow unbounded waits.

BAD
```python
response = httpx.get(url)
```

GOOD
```python
response = httpx.get(url, timeout=30.0)
```

2. Translate transport and client-library errors into domain exceptions at the client boundary. Callers must not depend on `httpx`, `requests`, or other library exception types.

BAD
```python
# in business logic, far from the client wrapper
except httpx.ConnectTimeout:
    ...
```

GOOD
```python
# inside the client wrapper
except httpx.TimeoutException as err:
    raise VendorUnavailableError(f"Vendor API timed out for order {order_id}") from err
```

3. Classify failures as retryable (timeouts, connection errors, HTTP 429, HTTP 5xx) or non-retryable (most HTTP 4xx, validation, authentication, authorization) and handle the two classes differently. Never retry a non-retryable failure.

4. Retry only retryable failures, with exponential backoff and a bounded number of attempts. Never retry unboundedly.

BAD
```python
while True:
    try:
        return client.get_order(order_id)
    except VendorUnavailableError:
        continue
```

GOOD
```python
for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        return client.get_order(order_id)
    except VendorUnavailableError:
        if attempt == MAX_ATTEMPTS:
            raise
        time.sleep(BACKOFF_BASE * 2 ** (attempt - 1))
```

5. Retry only idempotent operations automatically. Guard non-idempotent calls (creations, payments) with idempotency keys or a pre-check before any retry.

6. Raise on unexpected HTTP statuses. Never pass an error payload onward as if it were valid data.

BAD
```python
response = client.get_order(order_id)
return response.json()  # may be an error body
```

GOOD
```python
response = client.get_order(order_id)
response.raise_for_status()
return response.json()
```

## Related Documents

- [python-coding.md](./python-coding.md)
- [python-error-handling.md](./python-error-handling.md)
