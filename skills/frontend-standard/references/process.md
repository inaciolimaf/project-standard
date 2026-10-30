# Process: how an identity is made and changed

Crivo's identity took five specs, and two of them undid part of the previous one. That history is the
reason for this file.

| Spec | What it did | What it taught |
|---|---|---|
| 13 notebook | new palette, type, own icons and charts | stayed on the surface: same cards, same dashboard |
| 18 exam sheet | moved the metaphor into the question sheet; inks with meanings | a strong centre with a generic app around it reads as unfinished |
| 19 paper, ink and chalk | metaphor everywhere, plus motion | stickers on a dashboard skeleton are noise; each detail was good, the sum was not |
| 20 one printed document | one skeleton per route, two layers, objects removed | the skeleton change worked; removing the objects by theory went too far |
| 21 the objects come back | the objects return, on the document | the user felt the loss only on the running app |

Reversals outside the specs tell the same story: the booklet header of spec 19 went back to the sidebar
(`47ab822`) and the 16 px body of spec 20 went back to 15 px (`99de53d`). Both looked right on paper.

## The steps

1. **Brief.** Who uses it, for how long, in what state of mind, on which device. What the product must
   never feel like. Write what is wrong with the current screens using counts ("`PageHeader` in 25
   routes", "2,800 px of Hoje on the phone"), not adjectives.
2. **Concept.** One real-world object or situation the user already knows, tied to what they do in the
   product. Test it: does it change the layout of at least three screens? If it only changes colours,
   it is a theme, not a concept.
3. **Identity spec** from `templates/identity-spec.md`: skeleton, meanings, budgets, what is forbidden,
   screen by screen table.
4. **Primitives first.** Tokens, type, skeleton components, shared states.
5. **One pilot screen**, the one that is opened most. The user judges it on the running app, in both
   themes and on the phone. Nothing else moves until then.
6. **Then area by area**, one commit each, with the user able to stop at any commit.
7. **Lock it.** Turn what was approved into lint and tests (`guarantees.md`), and keep `docs/system/`
   as the description of what is actually on screen.

## Rules that came from the reversals

- **Do not remove by theory.** Removing a visual element is a design change like adding one. Show it on
  the pilot before removing it everywhere. If it is removed, delete it for real (components, CSS, motion),
  and keep the commits small so it can come back.
- **A reversal is recorded.** A new spec says "this changes spec NN" and why. `docs/system/` states what
  won. Old specs are not rewritten.
- **When the user prefers what was there, that is the answer.** Do not argue a scale or a layout from
  theory after they have seen it running.
- **Typefaces are the user's call.** Crivo's user rejected Newsreader and Plex and restored Fraunces +
  Inter. Show options on a real screen, and once chosen, never change them as part of another task.

## What to show the user

- Screenshots or the running app, at 390 px and at desktop width, light and dark.
- For a choice between directions: two working versions of the same screen, not descriptions.
- A count of what changes, so they can tell a pilot from a rewrite.

## Working with agents

- Redesigns touch many files: split by area, disjoint files, worktrees, and the main agent owns the
  shared primitives and commits them before the agents start.
- Each agent gets the identity spec, the pilot screen as the model and the screen's row of the table.
- An agent worktree has no `web/node_modules`. With a symlink the tests run, but Vite does not serve the
  `@fontsource` files, so type falls back to a system serif in its screenshots. Judge type in the main
  checkout.
