# SDK Pipeline Steps Guidelines

## Owner
Sirius Team

## Scope

Applies to:
 - pipeline steps in MPT extensions built on the Extension SDK
 - reusable pipeline steps shipped in shared libraries

Does not apply to:
 - non-SDK business logic that does not run inside a pipeline

## Purpose

Define how to write `BaseStep` implementations so that pipeline flows stay
predictable, retry-safe, and consistent with the Extension SDK runtime contract.

## Definitions

- A `step` is a `mpt_extension_sdk.pipeline.BaseStep` subclass implementing the
  `pre()` / `process()` / `post()` lifecycle.
- A `snapshot` is an MPT business object on the context (`ctx.order`,
  `ctx.agreement`) that reflects the platform state at the start of execution.
- A `transition` is an order or agreement status change (for example `Failed`,
  `Querying`, `Completed`).

## General Rules

1. A step has a single responsibility. Keep validate, fetch, transform, persist,
   and enforce as separate steps instead of combining them. Split a step that
   does more than one unit of work.

2. Treat MPT snapshots as immutable. Never mutate or reassign `ctx.order`,
   `ctx.agreement`, their `parameters`, `lines`, or nested objects. Build new
   parameter values with the immutable `ParameterBag` helpers and persist them
   through `ctx.mpt_api_service`.

BAD
```python
ctx.order.parameters.set_fulfillment_value(param_id, value)  # mutates snapshot
```

GOOD
```python
updated = ctx.order.parameters.with_fulfillment_value(param_id, value)
await ctx.mpt_api_service.orders.update(ctx.order_id, {"parameters": updated.to_dict()})
```

3. Refresh only when needed. Use `@refresh_order` / `ctx.refresh_order()` (and
   the agreement equivalents) only for read-after-write, when a later step must
   read the updated snapshot. Do not refresh by default; it adds an extra fetch.

4. Declare transitions; do not execute them from a step. A step must not call
   `orders.fail`/`query`/`complete` directly. It records intent on
   `ctx.order_state.action` (an `OrderStatusAction`) and raises the matching
   step error; a pipeline `on_step_*` hook applies the transition. The default
   pipeline only logs and stops, so the consumer pipeline must implement the
   hook for the transition to take effect.

GOOD
```python
@override
async def process(self, ctx: OrderContext) -> None:
    if not self._is_valid(ctx.order):
        ctx.order_state.action = OrderStatusAction(
            target_status=OrderStatusActionType.FAIL,
            message="Validation failed",
            status_notes={"reason": "..."},
        )
        raise StopStepError("Validation failed")
```

5. Use the correct flow-control error: `SkipStepError` to skip the current step,
   `StopStepError` to stop the pipeline with cancel semantics, `DeferStepError`
   when third-party state is pending and the flow should retry later. Subclass
   `StopStepError` for a distinguishable business outcome so hooks and error
   handlers can react with `isinstance`.

6. Put "is there work to do?" guards in `pre()` and raise `SkipStepError`, rather
   than an early `return` in `process()`. The pipeline dispatches `on_step_skipped`
   (which logs the reason), and `process()` stays focused on the actual work.

GOOD
```python
@override
async def pre(self, ctx: OrderContext) -> None:
    if get_due_date(ctx.order.parameters, _param(ctx)) is None:
        raise SkipStepError("due date is not set")
```

7. Steps must be idempotent and retry-safe. Event-driven flows re-run steps, so
   a step must be safe to execute again. Apply set-once semantics for stable
   values and keep no hidden in-memory state across runs.

8. Read configuration from the context; take behavior from the constructor.
   Read environment-driven configuration from `ctx.ext_settings` (typed with a
   `Protocol`), not from hardcoded constants or `os.getenv`. Expose the step's
   required settings as a `Protocol`, and have the extension's `ExtensionSettings`
   inherit it so the contract is explicit and type-checked. Pass behavioral
   parameters (counts, templates, thresholds) as constructor arguments and
   validate them, failing fast on invalid input. Prefer expressing the
   constraint in the parameter type (for example a `pydantic` constrained type
   with `@validate_call`) over an imperative check, so the invariant lives in
   the type definition rather than in the step body.

GOOD
```python
from pydantic import NonNegativeInt, validate_call


class SetDueDate(BaseStep):
    @validate_call
    def __init__(self, *, days: NonNegativeInt) -> None:
        self._days = days
```

9. Keep shared and library steps free of product-specific business logic. A
   reusable step takes its product specifics (parameter ids, thresholds) from
   settings or an injected protocol; vendor and business rules stay in the
   extension.

10. Implement `process()`, and `pre()` / `post()` only when needed; decorate
    overrides with `@override`. Step lifecycle methods are `async`.

11. Test steps against a real `OrderContext` with an autospec'd
    `mpt_api_service`. Assert the declared `ctx.order_state.action` and the
    raised step error, not a direct client call. See
    [unittests.md](./unittests.md).

## Related Documents

- [extensions-best-practices.md](./extensions-best-practices.md)
- [python-coding.md](./python-coding.md)
- [unittests.md](./unittests.md)
