---
name: frontend-standard
description: Inácio's frontend standard for React (Vite + TS + Tailwind v4 + TanStack) products: how to give a product its own visual identity and keep it, design tokens, typography, colour with fixed meanings, screen skeleton, motion, accessibility (WCAG 2.2 AA), performance budgets, CSS traps and the lint and tests that guarantee each rule. Use when creating or redesigning screens, defining or changing a visual identity, adding a new screen or component to a project that follows this standard, reviewing frontend quality, or when the user says "padrão de front", "aplica o padrão de front", "deixa com a cara do crivo", "melhora o visual". Works with project-standard, which owns the repository, CI and backend.
---

# Frontend standard

Extracted from nine specs and about 160 commits of Crivo's `web/`, then checked against primary
sources (WCAG 2.2, web.dev, framework docs). Crivo is the living reference, not the template: **its
rules are general, its look is not.** Do not copy the exam-sheet identity into another product.

This skill owns how screens are designed and built. `project-standard` owns folders above `web/`,
Makefile, CI, Docker and the backend contract. It also repeats the frontend basics (stack, eslint, test
setup) so that it works alone. Where the two disagree on a frontend subject, this skill wins, and a rule
kept in both is changed in both.

## Principles

1. **A rule without a guarantee does not exist.** Each rule below names its lint, test or design
   constraint. A design rule that cannot be checked by a machine is written in the identity spec and
   reviewed on the running app.
2. **Identity lives in the skeleton, not in the ornaments.** Crivo restyled the same dashboard skeleton
   three times (specs 13, 18, 19) before spec 20 changed the skeleton itself. If the layout of a screen
   could belong to any admin panel, a new palette will not fix it.
3. **Every visual element has one meaning.** A colour, a mark or a motion says one thing across the whole
   product. If it means nothing, it is decoration, and it needs a reason to stay.
4. **Boldness has a budget.** One dominant element per screen, one solid main action, the alarm colour
   only for what needs action now. The rest stays quiet so these can speak.
5. **The verdict comes from the running app.** Design decisions are judged by the user on the real
   screen, on one pilot screen, before they spread. See `references/process.md`.
6. **Fixed mechanics, free identity.** The table below separates them.

## What is fixed and what each project decides

| Fixed in every project | Decided per project, in its identity spec |
|---|---|
| The token system and its naming roles | The palette and how many inks it has |
| Two themes, each designed on its own | What the dark theme is (Crivo: a chalkboard) |
| A type scale of about five sizes, tabular figures; no Inter in a new project | The typefaces (the user picks them on a real screen) |
| One root skeleton component per screen, enforced by a test | What that skeleton is (Crivo: a printed document) |
| Motion rules: what may animate, reduced motion, tokens | How much motion exists, and its material |
| Accessibility (`references/accessibility.md`) | Nothing: this is not negotiable by identity |
| Performance budgets, 250 KB gzip of initial JS (`references/performance.md`) | Nothing, unless the spec justifies a change |
| The stack, the module boundaries, the shared states | Which objects, mascots or signatures exist |

## Reference map

| Subject | File |
|---|---|
| Creating or changing an identity, the pilot, reverting, working with agents | [references/process.md](references/process.md) |
| Concept, skeleton, colour meanings, type, budgets, components | [references/identity.md](references/identity.md) |
| Tokens, Tailwind v4 and the CSS traps already paid for | [references/tokens-and-css.md](references/tokens-and-css.md) |
| Motion, sound, vibration | [references/motion.md](references/motion.md) |
| WCAG 2.2 AA in a React SPA | [references/accessibility.md](references/accessibility.md) |
| Loading, bundle, navigation feel, screen state | [references/performance.md](references/performance.md) |
| Which lint or test guarantees what | [references/guarantees.md](references/guarantees.md) |
| What Crivo itself does not meet yet | [references/gaps.md](references/gaps.md) |
| Where the recommendations came from, and how solid they are | [references/sources.md](references/sources.md) |

Ready to copy: [templates/identity-spec.md](templates/identity-spec.md), the skeleton of a project's
identity spec.

## How to use it

**New screen in a project with an identity.** Read the project's latest identity spec and the most
similar existing screen. Reuse the skeleton, shared states and tokens. Start at 390 px. Add the route to
the e2e list. Run the project's frontend check.

**New identity or redesign.** Follow `references/process.md`: brief, concept, pilot screen, user verdict,
then area by area. Do not start by restyling.

**Review or audit.** Build a table *rule → met / missing / diverges* from the checklist below, with
evidence (file, measurement). Show it before changing anything.

## Checklist

**Identity**
- [ ] an identity spec states the concept, the skeleton, what each colour means and what is forbidden
- [ ] the concept changes the layout of the screens, not only their surface
- [ ] each screen renders exactly one root skeleton, and a test counts it
- [ ] one solid main action per screen; the alarm colour has a written budget
- [ ] colour never carries meaning alone: an icon, text or mark goes with it

**Tokens and CSS**
- [ ] colour only through tokens with a value in each theme; lint blocks raw colours elsewhere
- [ ] each theme designed on its own; a contrast test over text and control pairs runs on both
- [ ] no `text-white` over a colour: an `on-*` token
- [ ] a type scale of tokens, tabular figures where numbers are compared
- [ ] a stylesheet per area; composition classes in `@layer components`
- [ ] grid tracks with `minmax(0, 1fr)`; container queries for parts placed in variable columns
- [ ] `100dvh`, never `100vh`; every screen starts at 390 px

**Motion**
- [ ] durations and easings are tokens, mirrored in one TS file
- [ ] only `transform`, `opacity` and SVG stroke dashes animate; a test parses every `@keyframes`
- [ ] `prefers-reduced-motion` gives an instant swap, including motion driven by JavaScript timers
- [ ] nothing loops except loading; no motion blocks the next key
- [ ] sound and vibration off until the user turns them on

**Accessibility**
- [ ] axe in the e2e over every route, in both themes
- [ ] route change moves focus and updates `document.title`; a skip link exists
- [ ] focus outline solid, at least 2 px and 3:1 in both themes, never hidden by a sticky bar
- [ ] pointer targets at least 24×24 CSS px, 44 px for the main touch actions
- [ ] everything works by keyboard; dialogs trap and return focus; live regions for async results

**Performance**
- [ ] routes split; initial JS at most 250 KB gzip, or CI fails
- [ ] only the font axes and subsets in use are loaded
- [ ] LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at the 75th percentile, measured in the field
- [ ] client navigation, prefetch on intent, neighbours warmed where the next step is obvious
- [ ] reloading any screen rebuilds its state from the server

**Code and tests**
- [ ] everything in the frontend checklist of `project-standard`
- [ ] `getByRole` first in screen tests; test ids only as the last resort
- [ ] a whole-screen test for each screen with logic; a visual fix comes with a test or an e2e assertion
- [ ] new route in the e2e list, new main path in a flow
- [ ] removed design pieces leave with their components, CSS and motion

## When the user asks to change the standard

Change the skill and the project in the same pass, as `project-standard` describes. A rule that the
project does not meet yet goes into `references/gaps.md`.
