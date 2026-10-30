# Motion

## The rule

Every motion answers something the user did, or shows that a state changed. Each identity names the
material things move as (Crivo: paper, ink or chalk). A motion that fits no material does not exist.

| Rule | Value |
|---|---|
| Direct gesture feedback | 150–400 ms |
| Reward moments | up to 900 ms |
| Looping | only loading |
| Blocking | no motion blocks the next key; input stays live during it |
| Animated properties | `transform` (or `translate`, `rotate`, `scale`), `opacity`, SVG stroke dashes |
| Forbidden to animate | `width`, `height`, `top`, `left`, `box-shadow`, `filter`, `background-position` |
| Flashing | never more than three times per second |

The ranges are Crivo's, tuned on the running app. The property list follows Chrome's motion guidance:
those properties skip layout and paint, so a weak phone keeps its frame rate and nothing shifts.

## How it is built

- Timings live in `--motion-*` and `--ease-*` tokens, mirrored by one TS constant (`DURATION`). A screen
  never invents a timing.
- Primitives first: a shared hand-drawn stroke, marks, a rolling number. Each area's motion goes in its
  own stylesheet.
- A motion that plays once a day is a helper (`onceToday`), not local state.
- Routes and in-page swaps use view transitions (`defaultViewTransition`, `withViewTransition`), with the
  fallback being the instant change.
- If a route or an async step waits for an animation to end, the reduced-motion path skips the wait.
- Remove what a later spec replaced: confetti and looping rewards were deleted, not hidden (`ccfddce`).

## Reduced motion

`prefers-reduced-motion: reduce` turns each motion into an instant swap, including state that a timer
drives. WCAG 2.3.3 is level AAA, but here it is a requirement: the app is motion-heavy and users with
vestibular problems have no other way out. Motion carries no information that the final state lacks.

Guarantee: one test per area exercises the reduced path. `reducedMotion()` guards a missing
`matchMedia`, which jsdom does not provide.

## Sound and vibration

Off by default, turned on in the profile, through a single `playSound` and `haptic`. Synthesised with Web
Audio, so no files enter the bundle.
