# Extension UI Best Practices

## Owner
Sirius Team

## Scope

Applies to:
 - frontend (browser) UI shipped inside MPT extensions

## Purpose
Define how extension UI is structured, built, and tested so that screens rendered inside the
MPT Marketplace platform shell are consistent, on-brand, type-safe, and maintainable.

## Definitions

- A `module` is a self-contained UI surface under `src/modules/<name>/` with its own `index.tsx`
  entry point. Each module is bundled into a separate output and mounted independently by the platform.
- A `plug` is a module rendered inline within a platform page (for example the agreement view).
- An `action` is a module opened as a modal from a plug (for example `request-commitment-action`).
- The `SDK` refers to `@mpt-extension/sdk` (framework-agnostic: `setup`, `http`) and
  `@mpt-extension/sdk-react` (React bindings: `useMPTContext`, `useMPTModal`).
- The `design system` refers to `@softwareone-platform/sdk-react-ui-v0` — the shared component
  library and design tokens.

## General Rules

### Project structure

1. Place every UI surface under `src/modules/<name>/` with an `index.tsx` entry point. The build
   auto-discovers one entry point per module directory, so the directory name defines the bundle.
2. Put code shared across modules under `src/modules/shared/` (domain model, hooks, domain
   constants) and generic, domain-agnostic helpers under `src/modules/utils/` (coercion, storage,
   pure predicates).
3. Colocate a component's `.tsx`, its `.scss`, and its `.test.tsx` in the same folder. Follow the
   file and folder naming conventions below.
4. Keep entry points thin: mount React and import global styles only. All logic lives in `App.tsx`
   and below.

GOOD (`src/modules/agreement/index.tsx`)
```tsx
import { setup } from '@mpt-extension/sdk';
import { createRoot } from 'react-dom/client';

import App from './App';
import '../../style.scss';

setup((element: Element) => {
  const root = createRoot(element);
  root.render(<App />);
});
```

### Naming conventions

5. Name files and folders by their role, using the conventions in the table below. Match the case
   exactly — the build, imports, and test discovery all depend on it. The rule in one line:
   **folders and all non-component `.ts` files are `kebab-case`, except hook files under
   `shared/hooks/`, which are `camelCase` named after the hook (e.g. `useAdobeCustomer.ts`);
   component files are `PascalCase`.**

| Kind | Convention | Examples |
| --- | --- | --- |
| Module directory | `kebab-case`; an action-modal module ends with `-action`, a plug uses a plain name | `agreement/`, `request-commitment-action/` |
| Module entry point | always `index.tsx` (mounts React only) | `agreement/index.tsx` |
| Module root component | `App.tsx` with styles in `App.scss` | `request-commitment-action/App.tsx` |
| Reusable component | folder in `kebab-case`, files in `PascalCase` (`.tsx` + matching `.scss` + `.test.tsx`) | `components/details/details-section/DetailsSection.tsx` |
| React hook | `camelCase` with a `use` prefix; file named exactly after the hook, under `shared/hooks/` | `shared/hooks/useAdobeCustomer.ts` |
| Domain model | always `model.ts`; shared model in `shared/model.ts`, module-specific model in its own module folder | `shared/model.ts`, `request-midterm-upgrade-action/model.ts` |
| Shared utility | `kebab-case` under `utils/` (a single word like `coerce.ts` is just hyphen-free kebab-case) | `utils/safe-storage.ts`, `utils/coerce.ts` |
| Test | `<source>.test.{ts,tsx}`, colocated next to its source | `DetailsSection.test.tsx`, `useAdobeCustomer.test.ts` |
| Component / view styles | `.scss` named after the component it styles | `DetailsSection.scss` |
| Global styles | a single `style.scss` at the `src/` root, imported by each entry point | `src/style.scss` |

6. Use `kebab-case` for component folders. Components are reusable, shared building blocks rather
   than module-specific code, so they follow the same `kebab-case` folder convention as the modules
   and utils around them; the `PascalCase` component files inside still name the React component.
   The reference project currently mixes in some `PascalCase` folders (feature sub-views and wizard
   steps, e.g. `ThreeYearCommitment/`, `DetailsStep/`) — treat those as legacy, use `kebab-case` for
   new work, and migrate opportunistically.

### Use the SDK and design system — do not hand-roll

7. Render UI with design-system components (`Button`, `Select`, `Input`, `InlineNotification`,
   `MediumText`/`RegularText`, etc.). Do not build bespoke equivalents of components the design
   system already provides.
8. Talk to the platform only through the SDK: `http` for backend calls, `useMPTContext` for the
   page context, `useMPTModal` for opening/closing actions. Do not read platform globals or call
   `fetch` directly.
9. When you must deviate from a design-system component (because it assumes a full-page platform
   shell, for example), reuse design-system tokens/icons to match the look **and** document why in a
   comment at the deviation site.

GOOD (deviation is justified and explained at the call site)
```tsx
{/*
  Custom sidebar instead of the SDK's Navigation.SideNav: that component forces
  height: 100vh and mounts its own page shell, but the extension already renders
  inside the platform shell. This reuses the brand-primary active color to match.
*/}
<aside className="extension__sidebar" aria-label="Manage account">…</aside>
```

### Styling

10. Style with colocated SCSS that `@use`s the design tokens; reference spacing, color, and brand
   values through tokens (`var(--spacing-3)`, `var(--brand-primary)`, `$var-gray-2`). Do not
   hardcode hex colors or arbitrary pixel spacing.
11. Use a consistent block/element class convention (`extension__sidebar`, `details-section__label`).
   Keep class names scoped to the component; do not rely on cascading from unrelated modules.

GOOD
```scss
@use '@softwareone-platform/sdk-react-ui-v0/design-tokens' as *;

.extension__content {
  display: flex;
  gap: var(--spacing-3);
  border-left: 1px solid $var-gray-2;
  padding-left: var(--spacing-5);
}
```

BAD
```scss
.extension__content {
  gap: 16px;            /* magic number — use a spacing token */
  border-left: 1px solid #e0e0e0;  /* hardcoded color — use a token */
}
```

> The spacing and color values for a specific UI element come from its Figma mockup. Read the pixel
> spacing and color values there and map each to the matching SCSS design token — don't hardcode the
> raw value.

### Data fetching and async state

12. Wrap every backend call in a custom hook under `shared/hooks/` that returns an explicit state
    object. Model status as a discriminated union — `'idle' | 'loading' | 'success' | 'error'` —
    rather than loose booleans.
13. Always `encodeURIComponent` path segments built from IDs before composing a request URL.
14. Normalize errors: in a `catch`, narrow with `err instanceof Error ? err.message : '<fallback>'`
    so the UI always has a displayable message and never surfaces a raw thrown value.
15. Render each async state explicitly — show a loading notification while `loading` and the error
    message while `error`. Do not leave the user with a blank screen.
16. Get effect dependency arrays right so data is not re-fetched or re-computed needlessly. Reach for
    `useMemo`/`useCallback` only for a measured problem, not by default — these modules are small and
    React's defaults are fine.

GOOD (`shared/hooks/useAdobeCustomer.ts`, abridged)
```ts
export function useAdobeCustomer(agreementId: string) {
  const [state, setState] = useState<AdobeCustomer>({ status: 'idle', error: null, data: null });

  useEffect(() => {
    if (!agreementId) return;
    setState({ status: 'loading', error: null, data: null });
    http
      .get(`/api/v2/agreements/${encodeURIComponent(agreementId)}/customer`)
      .then((res) => setState({ status: 'success', error: null, data: (res.data as { data: AdobeCustomerData }).data }))
      .catch((err: unknown) => setState({
        status: 'error',
        error: err instanceof Error ? err.message : 'Failed to load Adobe customer data.',
        data: null,
      }));
  }, [agreementId]);

  return state;
}
```

### Domain model and pure helpers

17. Place a domain model by its scope:
    - A model used by more than one module goes in `shared/model.ts` — the single home for
      cross-module types. Do not scatter shared models across other files.
    - A model specific to one module lives in a `model.ts` in that module's own folder and must not
      be imported by another module. If a sibling needs it, that is the signal it is actually shared
      — promote it to `shared/model.ts` rather than importing across modules (see the
      no-sibling-import rule).
    - Let `model.ts` grow as the shared surface grows; group it with section comments, and split it
      only when the size genuinely hurts.
18. Read domain types through small, pure helper functions (`resolveAgreementId`,
    `findThreeYearBenefit`, `readParameter`), colocated with the types they operate on. Keep these
    free of React and side effects so they are trivially testable.
19. Treat backend payloads as untrusted shapes: type optional fields as optional, navigate with
    optional chaining and nullish coalescing, and render a consistent placeholder (an em dash, `—`)
    for absent values.

GOOD (a pure resolver reads an untrusted context defensively)
```ts
export function resolveAgreementId(context?: AgreementContext): string {
  return context?.data?.agreement?.id?.trim() ?? '';
}
```

### Authorization and feature gating

20. Express "may this user perform this action" as pure predicates (see `utils/security.ts`) keyed
    on account type, product, and segment. Gate both the entry point (whether the button renders) and
    the action module itself (return `null` early when the predicate fails).
21. Treat UI gating as UX, not security — the backend remains the authority. Never grant an action
    purely because the control was visible.

GOOD (action re-checks the same predicate it was gated on)
```tsx
const canRequest = canRequestThreeYearCommitment(accountType, settings?.products, productId);
if (!canRequest) return null;
```

### TypeScript and quality gates

22. Keep `strict` TypeScript on; do not introduce `any`. Parameterize `useMPTContext<…>()` with the
    exact shape you read instead of casting away types.
23. Confine string→number/null conversions to shared coercion helpers (`toIntOrNull`,
    `toNumberOrNull`) rather than scattering ad-hoc `Number(...)`/`parseInt` calls.
24. Code must pass `npm run check` (type-check plus `eslint --max-warnings=0`) before review. Zero
    warnings is the bar, not zero errors.

### Component design

25. Split presentational components (small, prop-driven, no data fetching — e.g. `DetailsSection`)
    from container views that wire hooks and compose them (e.g. `ThreeYearCommitment`). Push fetching
    and gating up; keep leaf components pure.
26. Expose a `data-testid` (or stable text) on components that tests assert against, rather than
    reaching for brittle structural selectors.
27. Components must not import from sibling or cousin components — only along the parent-child tree.
    Shared objects, classes, types, or helpers belong in `shared/` or `utils/`, where any component
    may import them. Importing from a shared module is not a lateral import; the ban is on
    sibling-to-sibling imports specifically.

BAD (a component reaches sideways into a sibling)
```tsx
// components/upgrade-to-step/UpgradeToStep.tsx
import { formatOffer } from '../details-step/DetailsStep'; // sibling import — tangles the two
```

GOOD (the shared helper is lifted out; both import from a shared location)
```tsx
// utils/offer.ts
export function formatOffer(offer: Offer): string { … }

// components/upgrade-to-step/UpgradeToStep.tsx
import { formatOffer } from '../../utils/offer';

// components/details-step/DetailsStep.tsx
import { formatOffer } from '../../utils/offer';
```

### Testing

28. Every component, hook, and helper ships with a colocated `*.test.{ts,tsx}` (Jest + Testing
    Library + jsdom). Test observable behavior — rendered text, the placeholder for missing data,
    the request URL called — not implementation details.
29. Mock the SDK at the module boundary (`jest.mock('@mpt-extension/sdk', …, { virtual: true })`)
    and drive hooks with `renderHook` + `waitFor`. Assert both the success and the failure path.

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

### Robustness

30. Defend against hostile or restricted browser environments where platform APIs may throw — for
    example install a `localStorage`/`sessionStorage` fallback that degrades to in-memory storage
    rather than letting the module crash on load (see `utils/safe-storage.ts`).

### Modal data flow

31. A plug opens an action with `useMPTModal().open(name, { context, onClose })` — passing the page
    `context` in and receiving the action's result through `onClose`. The action returns its result
    by calling `useMPTModal().close(result)`, or `close()` with no argument to cancel. The plug
    applies the result to its own state. An action must not mutate the plug directly or communicate
    through global/shared state.
32. Treat the `close(result)` payload as the action's contract: type it, keep it minimal (the
    updated entity, not UI state), and have the plug guard the cancel case, where `onClose` receives
    `undefined`.

GOOD (plug opens the action and applies the returned entity)
```tsx
// plug
open('request-commitment-action', {
  context,
  onClose: (data?: { customer?: AdobeCustomerData }) => {
    if (data?.customer) adobeCustomer.update(data.customer);
  },
});

// action — returns the updated entity, or nothing on cancel
const { close } = useMPTModal();
close({ customer: result }); // success
close();                     // cancel
```

### Accessibility

33. Use semantic elements and label the non-obvious ones: real `<button>`/`<nav>`/`<header>`/
    `<aside>` over clickable `<div>`s, an `aria-label` on landmarks and icon-only controls, and
    `aria-hidden` on decorative SVGs. Rely on the design system's own accessible components rather
    than re-implementing their behavior.

GOOD
```tsx
<aside className="extension__sidebar" aria-label="Manage account">
  <svg aria-hidden="true">…</svg>
</aside>
```

### State management

34. Keep state local — `useState` in components, and custom hooks for shared or async state. Do not
    add a global store (Redux, Zustand) or a broad app-wide React context; each module is small and
    mounted independently, so local state plus hooks is sufficient. Lift state only to the nearest
    common ancestor when two children genuinely share it.

### Routing

35. When a module has more than one view, route with `MemoryRouter` — not `BrowserRouter`. The
    module renders inside the platform's own page and does not own the browser URL, so navigation
    must stay in memory. Drive active-link styling with `NavLink`, and end the route list with a
    catch-all redirect to the default view.

GOOD
```tsx
<MemoryRouter initialEntries={[DEFAULT_PATH]}>
  <Routes>
    <Route path="/3-year-commitment" element={<ThreeYearCommitment />} />
    <Route path="*" element={<Navigate to={DEFAULT_PATH} replace />} />
  </Routes>
</MemoryRouter>
```

### Forms and validation

36. Express each validation as a pure function that returns an error message string or `null`, and
    compose them with `??` so the first failure wins. Keep this logic out of the component body (so
    it is unit-testable) and set the resulting message into local error state; do not `throw` for
    validation.

GOOD
```ts
const validationError =
  validateAtLeastOneQuantity(licenses, consumables) ??
  validateAboveMinimum('Licenses', licenses, currentMinimum);

if (validationError) {
  setLocalError(validationError);
  return;
}
```

### Constants

37. Extract magic numbers and configuration literals into a `constants.ts` rather than inlining
    them — `shared/constants.ts` for cross-module values, a module-local `constants.ts` otherwise.
    Name them in `SCREAMING_SNAKE_CASE`.

GOOD
```ts
// shared/constants.ts
export const SCREEN_HEIGHT_FACTOR = 0.85;
export const SCREEN_WIDTH_FACTOR = 0.9;
```

### Error boundaries

38. Wrap each module's root in a React error boundary so an uncaught render error shows a contained
    fallback message instead of a blank surface inside the platform page. Put the boundary in the
    entry point around `<App />`, keep the fallback simple (a design-system notification), and report
    the error where the extension collects diagnostics. Share one boundary component across modules
    rather than reimplementing it per entry point.

GOOD (entry point mounts the app inside a shared boundary)
```tsx
setup((element: Element) => {
  createRoot(element).render(
    <ErrorBoundary>
      <App />
    </ErrorBoundary>,
  );
});
```

## Related Documents

- [extensions-best-practices.md](./extensions-best-practices.md)
- [unittests.md](./unittests.md)
- [packages-and-dependencies.md](./packages-and-dependencies.md)
