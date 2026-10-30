# Identity: what makes a product look like itself

## The skeleton

Each screen is one instance of the product's own root component, not a page title over a stack of cards.

- One root per route. Secondary information goes inside it (a column, the margin, the foot), not into
  another box.
- The header of the screen says what this thing is. No grey subtitle explaining the screen.
- A small set of primitives builds every screen. In Crivo: `Document`, `DocumentHeader`, `Field`, `Rule`,
  `Columns`, `Margin`, `DocumentFoot`.
- `Card` and `PageHeader` survive only for floating surfaces (modal, drawer) and internal tools. Admin is
  a tool and may look like one.
- No card inside a card.

Guarantee: `no-restricted-imports` for the generic pieces, and `expectOneDocument()` (or the project's
equivalent) in each whole-screen test.

## Layers

Decide which layers exist and who produces each. Crivo has two: the printed layer (the printer: type,
numbering, rules, columns) and the handwritten layer (someone's gesture: the student's pen, the
corrector's pen). Objects sit on the sheet or on its edge, never as boxes beside it. Asking "who put this
here?" is a good test for any element in any identity.

## Colour with meaning

Write a table of colour → meaning. A colour used against its meaning is a bug: the confidence selector
in green, amber and red read as a verdict, so it became pen blue (`9221a72`).

| Role | Crivo | Rule |
|---|---|---|
| the user's own marks | blue pen | selection, active navigation, what they did |
| brand and main action | green | one solid block per screen |
| alarm | correction red | only what needs action now; a past mistake in a list is neutral |
| emphasis | highlighter | only where the user or the moment earns it |

- State that does not change what the user does is plain text. Metadata never becomes a badge.
- A badge is a stamp of state: it appears only when it changes what the user does next.
- Each figure has one encoding. Not a circle, a badge and a ruler for the same rate.
- Colour is never alone: an icon, a word or a mark says the same thing.

## Type

- About five sizes as tokens. Fixed, not per screen. Crivo: small, body, heading, title, figure.
- A display face for titles and the numbers that are the point of a block; a neutral text face for
  interface and long reading.
- Numbers that are compared use tabular figures.
- Prefer cutting text to shrinking it: what is not worth reading at body size goes away.
- No all-caps label with an icon over every block. An overtitle only says what the title does not.
- Body size is settled on the running app. Theory said 16 px; the user chose 15 px.

## Generic look to avoid

Recurring signs of a template, in the community guides and in Crivo's own history: identical rounded
cards in a grid, four KPI tiles on top, a purple gradient, an icon list as an admin sidebar, a pill badge
on every row, small grey text everywhere, a dark theme that is the light one inverted, an entrance
animation on everything.

Those guides also list Inter as an overused face. Crivo keeps it for the interface on purpose: the
character comes from the display face and the skeleton. A neutral text face is fine, a neutral everything
is not.

## Own components, on purpose

- Icons drawn in the project: one grid, one stroke width, a common prefix. No icon library means the
  icons match the identity and the bundle stays small.
- Charts drawn in the project when the identity needs them to be part of it. A value is written beside
  the mark, so no series lives on colour alone.
- Headless libraries only for behaviour that is hard to get right (focus trap, Esc): Radix under `Modal`
  and `Drawer`, no visuals from it.
- Shared states are part of the identity: `<QueryView>` for loading, error and data; an empty state says
  what to do next; an error shows the API's `detail` and a retry; the 404 and the route error are designed
  screens. They speak in the product's voice.
- `Button` is `type="button"` by default; submit declares it.

## Phone

- Every screen is born at 390 px and grows.
- Desktop and phone have the same map.
- A single floating element per screen, and it knows about the fixed footer through a shared CSS variable.
- In a focused task (an exam), the bottom bar leaves.
- Truncate only with an ellipsis and a `title`.
