# Extension UI Testing Best Practices

> **Audience:** Consumed by extension and product repositories when working in those repositories. The skills in this repository do not reference this standard.

## Owner
Sirius Team

## Scope

Applies to:
 - tests for the frontend (browser) UI of MPT extensions, using Jest + Testing Library + jsdom.

## Purpose

Define how extension UI is tested so tests are behaviour-focused, deterministic, and cheap to
maintain. For UI authoring rules see
[extensions-ui-best-practices.md](./extensions-ui-best-practices.md); for general Python
unit-testing rules see [unittests.md](./unittests.md).

## General Rules

1. Every component, hook, and helper must ship with a colocated `*.test.{ts,tsx}` (Jest + Testing
   Library + jsdom). Tests must assert observable behaviour — rendered text, the placeholder for
   missing data, the request URL called — and must not assert implementation details.
2. Tests should assert against stable selectors — a `data-testid` or stable text exposed by the
   component — and must not rely on brittle structural selectors.
3. Tests must mock the SDK at the module boundary (`jest.mock('@mpt-extension/sdk', …, { virtual: true })`)
   and should drive hooks with `renderHook` + `waitFor`. Each test must assert both the success and
   the failure path.

GOOD (`shared/hooks/useSettings.test.ts`, abridged)
```ts
jest.mock('@mpt-extension/sdk', () => ({ http: { get: jest.fn() } }), { virtual: true });
const mockGet = jest.mocked(http.get);

it('returns undefined when the request fails', async () => {
  mockGet.mockRejectedValue(new Error('Settings unavailable'));
  const { result } = renderHook(() => useSettings());
  await waitFor(() => expect(mockGet).toHaveBeenCalled());
  expect(result.current).toBeUndefined();
});
```

## Related Documents

- [extensions-ui-best-practices.md](./extensions-ui-best-practices.md)
- [unittests.md](./unittests.md)
