# Performance and how fast it feels

## Targets

| Metric | Good | How it is read |
|---|---|---|
| LCP | ≤ 2.5 s | 75th percentile of page loads, mobile and desktop apart |
| INP | ≤ 200 ms | same |
| CLS | ≤ 0.1 | same |

These are field numbers. In a logged-in SPA the public tools see nothing, so collect them with the
`web-vitals` package when the product has real users. INP is the one that matters here: a question app
lives on clicks.

Build budget (proposal to confirm): initial JS at most 250 KB gzip, checked in CI by a script over
`dist/` or `size-limit`. A route that needs a heavy library loads it on its own.

## Bundle

- **Split by route.** With code-based TanStack routes:
  `createRoute({...}).lazy(() => import("./x.lazy").then((d) => d.Route))`, and `createLazyRoute` in the
  file. Component, error, pending and not-found components are split; path, search validation and loaders
  stay in the main chunk. `autoCodeSplitting` only works with file-based routing.
- Heavy libraries (KaTeX, `motion`) live in their own chunks and load only where used.
- A pending state that matches the final layout, so the lazy load does not shift anything.
- **Fonts.** Self-host with `@fontsource`, preload what the first screen uses, `font-display: swap`,
  metric-compatible fallback. Variable axes cost bytes: load only the axes the identity actually uses.
- **Images.** `width` and `height` always, lazy below the fold.

## Feeling instant

- Move through the router, never a full reload: a reload drops the query cache (`d0647ed`).
- `defaultPreload: "intent"`.
- Prefetch the obvious next step with the same query key, and warm the figures of the neighbours
  (`474e52f`).
- Apply a mutation's response with `setQueryData` when the API returns the new object.
- Long lists are virtualised or paginated, never rendered whole.
- Long tasks on the click path are the first suspect for a bad INP. Break them up, or move them to the server.

## State that survives

Reloading any screen rebuilds what the user saw from the server. A resumed practice lost the chosen
option and the correction until the API sent them back (`d12250a`). Guarantee: a test reloads the screen
mid-task. Unsent input (a mock exam draft) is saved on the device and sent later, debounced.

Filters live in the URL, so a screen can be shared and restored.
