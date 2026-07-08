# Extension UI Best Practices

## Owner
Sirius Team

## Scope

Applies to:
 - frontend (browser) UI shipped inside MPT extensions

## Purpose
Define how extension UI must be structured and built so that screens rendered inside the
MPT Marketplace platform shell are consistent, on-brand, type-safe, and maintainable. UI testing
rules live in a separate standard (see Related Documents).

## Definitions

- A `module` is a self-contained UI surface under `src/modules/<name>/` with its own `index.tsx`
  entry point. Each module is bundled into a separate output and mounted independently by the platform.
- A `plug` is a module rendered inline within a platform page (for example the agreement view).
- An `action` is a module opened as a modal from a plug (for example `request-commitment-action`).
- A `socket` is a named mount point in the platform UI where a plug is rendered; a plug targets a
  socket, while an action is opened by id.
- The `SDK` refers to `@mpt-extension/sdk` (framework-agnostic: `setup`, `http`) and
  `@mpt-extension/sdk-react` (React bindings: `useMPTContext`, `useMPTModal`).
- The `design system` refers to `@softwareone-platform/sdk-react-ui-v0` — the shared component
  library and design tokens.

## General Rules

### Project structure

1. Every UI surface must live under `src/modules/<name>/` with an `index.tsx` entry point. The build
   auto-discovers one entry point per module directory, so the directory name defines the bundle.
2. Code shared across modules must live under `src/modules/shared/` (domain model, hooks, domain
   constants); generic, domain-agnostic helpers must live under `src/modules/utils/` (coercion,
   storage, pure predicates).
3. A component's `.tsx`, its `.scss`, and its `.test.tsx` must be colocated in the same folder,
   following the file and folder naming conventions below.
4. Entry points must stay thin: they must only mount React and import global styles; all logic must
   live in `App.tsx` and below.

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

5. Files and folders must be named by role per the table below, matching case exactly (the build,
   imports, and test discovery all depend on it): folders and all non-component `.ts` files are
   `kebab-case`, except hook files under `shared/hooks/`, which are `camelCase` named after the hook
   (e.g. `useAdobeCustomer.ts`); component files are `PascalCase`.

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

6. Component folders must use `kebab-case` (like the modules and utils around them); the `PascalCase`
   files inside name the React component. New component folders must not use `PascalCase`; existing
   `PascalCase` folders (e.g. `ThreeYearCommitment/`, `DetailsStep/`) may be renamed to `kebab-case`
   when a component in them is already being changed.

### Use the SDK and design system — do not hand-roll

7. UI must be rendered with design-system components (`Button`, `Select`, `Input`,
   `InlineNotification`, `MediumText`/`RegularText`, etc.). Bespoke equivalents of components the
   design system already provides must not be built.
8. Code must talk to the platform only through the SDK: `http` for backend calls, `useMPTContext` for
   the page context, `useMPTModal` for opening/closing actions. Code must not read platform globals or
   call `fetch` directly.
9. A component may deviate from a design-system component only when that component assumes a full-page
   platform shell; such a deviation must reuse design-system tokens/icons to match the look and must
   document the reason in a comment at the deviation site.

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

10. Styles must be colocated SCSS that `@use`s the design tokens, and must reference spacing, color,
   and brand values through tokens (`var(--spacing-3)`, `var(--brand-primary)`, `$var-gray-2`). Hex
   colors and arbitrary pixel spacing must not be hardcoded.
11. Class names must follow a consistent block/element convention (`extension__sidebar`,
   `details-section__label`) and must be scoped to the component; styles must not rely on cascading
   from unrelated modules.

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

12. Every backend call must be wrapped in a custom hook under `shared/hooks/` that returns an explicit
    state object; status must be modelled as a discriminated union — `'idle' | 'loading' | 'success' |
    'error'` — not loose booleans.
13. Path segments built from IDs must be `encodeURIComponent`-encoded before composing a request URL.
14. Errors must be normalized: in a `catch`, narrow with `err instanceof Error ? err.message :
    '<fallback>'` so the UI always has a displayable message and never surfaces a raw thrown value.
15. Each async state must be rendered explicitly — a loading notification while `loading` and the error
    message while `error`; the user must not be left with a blank screen.
16. Effect dependency arrays must be correct so data is not re-fetched or re-computed needlessly.
    `useMemo`/`useCallback` should be used only for a measured performance problem, not by default.

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

17. A domain model must be placed by scope. A model used by more than one module must live in
    `shared/model.ts` (the single home for cross-module types). A model specific to one module must
    live in a `model.ts` in that module's own folder and must not be imported by another module; if a
    sibling needs it, it must be promoted to `shared/model.ts` (see the no-sibling-import rule).
    `model.ts` may grow with the shared surface, grouped with section comments, and should be split
    only when its size genuinely hurts.
18. Domain types must be read through small, pure helper functions (`resolveAgreementId`,
    `findThreeYearBenefit`, `readParameter`), colocated with the types they operate on; these helpers
    must be free of React and side effects so they are trivially testable.
19. Backend payloads must be treated as untrusted shapes: optional fields must be typed as optional,
    navigated with optional chaining and nullish coalescing, and absent values must render a
    consistent placeholder (an em dash, `—`).

GOOD (a pure resolver reads an untrusted context defensively)
```ts
export function resolveAgreementId(context?: AgreementContext): string {
  return context?.data?.agreement?.id?.trim() ?? '';
}
```

### Authorization and feature gating

20. "May this user perform this action" must be expressed as pure predicates (see `utils/security.ts`)
    keyed on account type, product, and segment; both the entry point (whether the button renders) and
    the action module itself (an early `return null`) must be gated.
21. UI gating must be treated as UX, not security — the backend remains the authority; an action must
    not be granted purely because the control was visible.

GOOD (action re-checks the same predicate it was gated on)
```tsx
const canRequest = canRequestThreeYearCommitment(accountType, settings?.products, productId);
if (!canRequest) return null;
```

### TypeScript and quality gates

22. `strict` TypeScript must stay on and `any` must not be introduced; `useMPTContext<…>()` must be
    parameterized with the exact shape read instead of casting away types.
23. String→number/null conversions must be confined to shared coercion helpers (`toIntOrNull`,
    `toNumberOrNull`) rather than scattered ad-hoc `Number(...)`/`parseInt` calls.
24. Code must pass `npm run check` (type-check plus `eslint --max-warnings=0`) before review; zero
    warnings is the bar, not zero errors.

### Component design

25. Presentational components (small, prop-driven, no data fetching — e.g. `DetailsSection`) must be
    split from container views that wire hooks and compose them (e.g. `ThreeYearCommitment`); fetching
    and gating must be pushed up and leaf components kept pure.
26. Components that tests assert against should expose a `data-testid` (or stable text) rather than
    forcing tests to reach for brittle structural selectors.
27. A component must not import from sibling or cousin components — only along the parent-child tree.
    Shared objects, classes, types, or helpers must live in `shared/` or `utils/`, where any component
    may import them; importing from a shared module is not a lateral import — the ban is on
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

### Robustness

28. Modules must defend against restricted browser environments where platform APIs may throw — for
    example they must install a `localStorage`/`sessionStorage` fallback that degrades to in-memory
    storage rather than letting the module crash on load (see `utils/safe-storage.ts`).

### Modal data flow

29. A plug must open an action with `useMPTModal().open(name, { context, onClose })`, passing the page
    `context` in and receiving the action's result through `onClose`. The action must return its result
    by calling `useMPTModal().close(result)`, or `close()` with no argument to cancel. The plug applies
    the result to its own state; an action must not mutate the plug directly or communicate through
    global/shared state.
30. The `close(result)` payload must be treated as the action's contract: it must be typed and kept
    minimal (the updated entity, not UI state), and the plug must guard the cancel case, where
    `onClose` receives `undefined`.

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

31. Semantic elements must be used and the non-obvious ones labelled: real
    `<button>`/`<nav>`/`<header>`/`<aside>` over clickable `<div>`s, an `aria-label` on landmarks and
    icon-only controls, and `aria-hidden` on decorative SVGs. The design system's own accessible
    components should be reused rather than re-implemented.

GOOD
```tsx
<aside className="extension__sidebar" aria-label="Manage account">
  <svg aria-hidden="true">…</svg>
</aside>
```

### State management

32. State must be kept local — `useState` in components, and custom hooks for shared or async state. A
    global store (Redux, Zustand) or a broad app-wide React context must not be added; each module is
    small and mounted independently, so local state plus hooks is sufficient. State should be lifted
    only to the nearest common ancestor when two children genuinely share it.

### Routing

33. A module with more than one view must route with `BrowserRouter`. The SDK synchronises the module's
    route with the platform URL — the platform page path is suffixed with `/-/` followed by the
    extension's internal path — so browser navigation and deep links work. Use `react-router` as usual:
    declare routes and read `useParams`/`useNavigate`. A redirect to a default view on mount must pass
    `{ replace: true }` so it does not leave a dead history entry that traps the back button; active
    links should use `NavLink`, and the route list should end with a catch-all redirect to the default
    view.

GOOD
```tsx
<BrowserRouter>
  <Routes>
    <Route path="/:tab" element={<View />} />
    <Route path="/" element={<View />} />
    <Route path="*" element={<Navigate to={DEFAULT_PATH} replace />} />
  </Routes>
</BrowserRouter>
```

### Forms and validation

34. Each validation must be a pure function that returns an error message string or `null`, composed
    with `??` so the first failure wins. This logic must stay out of the component body (so it is
    unit-testable) and must set the resulting message into local error state; validation must not
    `throw`.

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

35. Magic numbers and configuration literals must be extracted into a `constants.ts` rather than
    inlined — `shared/constants.ts` for cross-module values, a module-local `constants.ts` otherwise —
    and must be named in `SCREAMING_SNAKE_CASE`.

GOOD
```ts
// shared/constants.ts
export const SCREEN_HEIGHT_FACTOR = 0.85;
export const SCREEN_WIDTH_FACTOR = 0.9;
```

### Error boundaries

36. Each module's root must be wrapped in a React error boundary so an uncaught render error shows a
    contained fallback message instead of a blank surface inside the platform page. The boundary must
    be placed in the entry point around `<App />`, the fallback should stay simple (a design-system
    notification) and report the error where the extension collects diagnostics, and one boundary
    component should be shared across modules rather than reimplemented per entry point.

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

### Plug declaration

37. Every plug must be declared in the backend registration. For SDK-based extensions the Python
    `PlugRouter` is the single source of truth for which plugs exist: registration should be organised
    per entity (one router per entity — orders, subscriptions, agreements, and so on); there must be no
    orphan bundle without a registration and no registration without a bundle; and each plug's `href`
    must resolve to the built module bundle, or the platform cannot load the iframe.

### iframe compatibility shims

38. Extensions run in an isolated cross-origin iframe, so the design system's assumptions about a host
    environment do not all hold. The gap must be bridged with a small, shared set of shims, documented
    in one place: global base typography and `box-sizing`, wizard step sizing that relies on inherited
    line-height, modal layout (header/content/actions) for plugs rendered inside platform modals, and
    the in-memory `localStorage`/`sessionStorage` fallback (rule 28). These are expected to move into
    the UI SDK over time.

## Related Documents

- [extensions-ui-testing-best-practices.md](./extensions-ui-testing-best-practices.md) — UI testing rules (Jest + Testing Library)
- [extensions-best-practices.md](./extensions-best-practices.md)
- [unittests.md](./unittests.md)
- [packages-and-dependencies.md](./packages-and-dependencies.md)
