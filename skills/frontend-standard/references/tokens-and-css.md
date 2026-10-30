# Tokens and CSS

## Tokens

Plain CSS custom properties are the source, in `src/styles.css`, by `data-theme` on `<html>`. The exposed
names are roles (`surface`, `ink`, `ink-muted`, `primary`, `on-primary`, `error`, `error-soft`,
`error-text`), never hues.

- **Two tiers are enough:** a raw value lives inside the theme block, components use roles. Add a third
  component tier only when one component has several states to theme (the avatar metals, for instance).
- **The `-soft` / `-text` trio.** A status colour has its solid, its tint, and a text colour safe on that
  tint. This is what kept every text pair in Crivo above 4.5:1 in both themes.
- **A control edge token.** A decorative border may be pale, but the edge that alone identifies an input,
  select, checkbox or radio is a token of its own at 3:1 or better on every surface (Crivo's
  `--control-edge`).
- **`on-*` over any solid colour.** `text-white` disappears in dark mode, where solids get lighter.
- **Each theme is designed on its own.** Same roles, different decisions. Inversion is forbidden.
- **Theme application.** The stored value is written only when the user chooses; until then follow the
  system and its changes. Values stored in the browser are not renamed (Crivo keeps `claro`/`escuro`).
- **Hues computed for many categories:** fix lightness and chroma per theme in OKLCH and vary only the hue,
  so all categories have the same contrast (Crivo's discipline areas).
- **Content colours** that do not follow the theme (avatar skin) live in one allowed file.

Design Tokens format (DTCG): skipped on purpose. It is a community report, not a W3C standard, and it pays
off when tokens cross tools or platforms. One web app with one stylesheet does not need it. Revisit when a
design tool or a native app enters.

## Tailwind v4

- `@theme inline` for tokens that reference other variables, otherwise utilities may resolve to the wrong
  value. This is what lets `--color-surface: var(--surface)` follow `data-theme`.
- Variables that should not create a utility stay in `:root`.
- `@custom-variant dark (&:where([data-theme="..."], [data-theme="..."] *));` so `dark:` follows the app,
  not the system.
- Own composition classes go in `@layer components`, so a utility still wins.
- An area's CSS goes in `src/styles/<area>.css`, imported by `styles.css`.
- Container queries are built in: `@container` on the parent, `@md:` on the child.

## Traps already paid for

| Symptom | Cause | Fix | Commit or spec |
|---|---|---|---|
| Override does nothing | a rule in `@layer components` loses to any unlayered rule | an override of unlayered CSS stays outside the layer, next to it | `9221a72` |
| Long content overflows on the phone | a `1fr` grid track grows with its content | start at `grid-cols-[minmax(0,1fr)]` | spec 13 |
| Page gets wider during an animation | a sliding mark extends the scrollable area | `overflow-x: clip` on the parent of the sliding layer | `cfe0f8f` |
| Fields squeezed in a two-column layout | the viewport breakpoint does not know the column width | each part is its own container, with container queries | `99de53d` |
| Footer below the fold on the phone | `100vh` ignores the browser bars | `100dvh` minus the bar | spec 06 §9 |
| Gap inside a rolling number (`21 2`) | a column is as wide as its widest digit | each digit window as wide as the digit it shows | `47ab822` |
| Rolling number clipped | row height differs from the window | rows with the window's exact height | `3e0c003` |
| Stretched SVG stroke draws in fragments | `vector-effect: non-scaling-stroke` makes Chrome measure dashes in screen units while `pathLength` stays in user units | no `vector-effect` on a dash-animated stroke | `543ce1e` |
| Stale screen after filter change | `placeholderData` with the filter in the query key | keep the last answer in the component and dim it while `isFetching` | spec 06 §3 |
| Effect restarts every render | a callback in the dependency array | callbacks enter effects through a `ref` | spec 06 §3 |
| `Invariant failed` only in production | `useParams({ from })` to a route that is not active | `Route.useParams()`, enforced by lint | spec 06 §2 |
| A lint rule silently stops applying | in flat config the last matching `no-restricted-imports` wins | one composed rule per file group | `web/eslint.config.js` |
