# Accessibility: WCAG 2.2 AA

The target is level AA. The identity never overrides it: a designed checkbox, a stamp or a hand-drawn mark
still has a name, a role and a keyboard path.

## What level AA asks, in numbers

| Criterion | Requirement | Note |
|---|---|---|
| 1.4.3 Contrast (Minimum) | 4.5:1 for text | 3:1 for large text |
| 1.4.11 Non-text Contrast | 3:1 for controls, states and meaningful graphics | a pale border is fine only if the control is identifiable some other way |
| 2.4.7 Focus Visible | focus can be seen | |
| 2.4.11 Focus Not Obscured (Minimum) | a focused item is not entirely hidden by author content | set `scroll-padding` for sticky bars |
| 2.5.8 Target Size (Minimum) | 24×24 CSS px, with exceptions (spacing, inline, equivalent) | |
| 4.1.3 Status Messages | status reaches assistive tech without moving focus | |

Above AA, adopted anyway: a solid focus outline of at least 2 px at 3:1 (from 2.4.13, AAA), 44 px for the
main touch actions, and the reduced motion of `motion.md`. A translucent token is never the only focus
indicator: Crivo's `--ring`, at 30% alpha, measured about 1.7:1.

## In a React SPA

- **Route change.** Keep `document.title` per route, and move focus to the screen's `h1` (`tabIndex={-1}`,
  no outline on that heading). Without this, a screen reader user hears nothing after a navigation. Do
  it once in the shell, not per route.
- **Skip link** as the first focusable element, to the main content.
- **Landmarks and headings.** One `h1` per screen, a `main`, labelled `nav`s. The skeleton provides them,
  so a screen cannot forget.
- **Dialogs.** Focus trap, Esc, and return of focus: a headless primitive does it.
- **Async results** (saved, wrong answer, time warning) use a persistent `role="status"` region;
  `role="alert"` only for what interrupts.
- **Forms.** A real `label`, errors tied by `aria-describedby`, focus on the first error.
- **Custom controls.** A native element underneath, styled, whenever one exists. A combobox follows the
  ARIA pattern for arrows, Home/End, letters and Esc.
- **Own shortcuts** are ignored inside text fields and listed in a visible legend.
- **Decorative marks** are `aria-hidden`; a mark that means something has a name or text beside it.
- **Zoom and reflow.** 200% zoom and 320 px width work without horizontal scrolling. The 390 px rule
  gets most of the way.

## Guarantees

- `@axe-core/playwright` over every route of the e2e list, tags `wcag2a`, `wcag2aa`, `wcag22aa`, in both
  themes. Fails on any violation; a known exception is listed with its reason.
- A route opened with a fake id only shows its error state to axe, so also open at least one screen with
  real data.
- Contrast test: a unit test reads the theme blocks of `styles.css` and checks a declared list of text and
  control pairs in both themes. axe only sees what is rendered at that moment; this covers all states.
- Screen tests use `getByRole` first, which fails when a control has no name.
- A flow test checks focus after navigation.

Automated tools catch part of the problems. Before a redesign ships, go through the main path once with
only the keyboard, and once with a screen reader.
