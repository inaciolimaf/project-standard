# Known gaps

Where Crivo does not meet this standard yet, measured on 2026-10-30. When one is resolved, delete it.

| # | Gap | Evidence | Fix |
|---|---|---|---|
| 1 | Focus indicator too faint | `--ring` at 30% alpha is about 1.7:1 on the sheet, and it is the only `:focus-visible` outline in `bank.css`, `library.css` | outline in `pen`, solid; keep `--ring` as the soft halo |
| 2 | No code splitting by route | no `lazy` in `web/src`; main chunk of 830 KB uncompressed in `dist/assets` | `.lazy()` on routes |
| 3 | Focus does not move on navigation, no skip link | no `.focus()` in the shell; only `document.title` | shell moves focus to the `h1` |
| 4 | No axe in the e2e | not in `package.json` | `@axe-core/playwright` on `routes.spec.ts` |
| 5 | A keyframe breaks the motion rule | `handwrite-in` animates `filter` in `motion.css` | drop the blur |
| 6 | No bundle budget, no field metrics | not in CI | `size-limit` or a script, then `web-vitals` |
| 7 | Control borders below 3:1 | `border-strong` on `surface`: 1.98:1 light, 1.84:1 dark. It only fails 1.4.11 where the border alone identifies the control | audit inputs and checkboxes |
| 8 | Fraunces with every axis | `full.css` and `full-italic.css`, about 150 KB per file | keep only the axes in use |

Already fine, measured: all 15 text and solid colour pairs checked pass in both themes, and all 16
stylesheets with `@keyframes` declare `prefers-reduced-motion`.
