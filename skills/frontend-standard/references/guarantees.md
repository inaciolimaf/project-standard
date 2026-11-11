# Guarantees: which machine checks what

| Rule | Guarantee | In Crivo |
|---|---|---|
| Module boundaries | eslint `no-restricted-imports` | yes |
| Component at most 100 lines, file at most 300 | eslint `max-lines-per-function`, `max-lines` | yes |
| Colour only by token | `no-restricted-syntax`, raw colour allowed in one file | yes |
| Numbers and dates formatted in one place | `no-restricted-syntax` on `toLocaleString` | yes |
| Keyboard listened to in one place | `no-restricted-syntax` on `addEventListener("keydown")` | yes |
| A route reads its own params | `no-restricted-syntax` on `useParams({...})` | yes |
| Effects list their dependencies | `react-hooks/exhaustive-deps` as an error | yes |
| One root skeleton per screen | `no-restricted-imports` + `expectOneDocument()` | yes |
| API types not written by hand | generated file, CI fails on a diff | yes |
| API errors readable | single `readProblem()`, client and screen tests | yes |
| Every route opens | e2e over a list compared with the router | yes |
| No horizontal overflow at 390×844 | e2e `scrollWidth > innerWidth` | yes |
| Main paths work | Playwright flows | yes |
| A warning sits on its thing, with its action | whole-screen test with `within(row)` | yes |
| Coverage | Vitest floor of 60% | yes |
| Sound off by default, reduced motion | one test per area | yes |
| No accessibility violation | axe over every route, both themes | yes |
| Text pairs have contrast | unit test over the theme blocks | yes |
| Only cheap properties animate | a script parses `@keyframes` and allows a list | yes |
| Bundle under budget | CI script over `dist/` (`make orcamento`) | yes |
| Focus moves on navigation | flow test | yes |
| Screens do not regress visually | Playwright `toHaveScreenshot` for the skeletons | no, optional, see below |

## Screen tests

- Query priority follows Testing Library: role, label, text, and test ids only when nothing else fits.
- `renderScreen` mounts the real router with `createAppRouter`; `fakeApi` answers 404 naming the missing
  route.
- With lazy routes, `renderScreen` waits for the router to go idle: returning when `main` exists, before
  the chunk loads, makes tests fail at random.
- A visual bug that a test can describe (a class, a data attribute, an overflow) comes with that test.
  One that only the eyes can catch comes with a note in the commit.

## Visual regression

Playwright baselines depend on OS, browser version and even the hardware, and the docs ask to generate
and compare them in the same environment. Worth it only if it runs in a pinned image, on a few screens
(the shell, one screen per skeleton), with animations off and dynamic areas hidden. Not over all routes:
every identity change would rewrite the baselines, and people stop reading the diffs.
