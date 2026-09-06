# Ask — a "next layer" control on every layer, in the house and the plan

## The problem, from a real session

Someone finished the core message — four options offered, one chosen, their own line added and tagged
*written here*. Then they stopped, and asked how to get to layer 2. There is no next-layer control
anywhere on the screen, so the rail is the only way through, and they did not read it as navigation.

That is not a bug. It is the eight-layer sequence having no forward motion at the one moment somebody has
just finished something and is looking for what to do next. The rail is a table of contents; it is not a
next step.

Worth saying plainly: the person who could not find it is the person who commissioned the product. If it
is invisible to them it is invisible.

## The ask

**A "Next: <layer name> →" control at the bottom of the options block, on every layer of both the
messaging house and the IMC plan.**

Under the option cards and the *Not the right lines?* panel — after the work, where somebody looks when
they have finished it. Not in the header; the header is for the whole document.

## Behaviour, including the cases that are not obvious

**When it appears.** Once **at least one option is chosen** in the current layer. Before that, moving on
is not a neutral act: every layer below is written against the choice above it, so a next button on an
undecided layer would invite somebody to skip the thing that makes the next layer mean anything.

Before a choice exists, put the reason there instead of the button — one quiet line: *"Choose at least
one line — the next layer is written against what you pick here."*

**"Next" means the next in sequence, not the only one open.** This is the case that will catch you out:
`H_LAYERS` is already in the right order and `i + 1` is the answer, but **two layers unblock at once**.

| after choosing | what opens |
|---|---|
| Core message | Emotional **and** Functional both |
| Both messages | Emotional RTBs **and** Functional RTBs both |

So "the next unblocked layer" is ambiguous twice over. Sequence order resolves it, and the rail stays as
the way to jump if somebody wants functional before emotional.

**On the last layer.** Layer 8 *By medium* has nothing after it. Show the document's own next step —
*"Start a plan from this house →"*, which already exists in the header — rather than a dead control or a
disabled button.

**If the next layer is still blocked.** It should not be, if a choice was just made here, but the plan's
`Governance` has no parents and `Balance` is a number rather than rows, so do not assume. If the target
is blocked, say what is missing rather than navigating into a wall.

## The same gap in the plan

The IMC plan has seven layers, the same rail, and the same absence. `objectives → audiences → channels →
balance → phases → measures → governance`. Same control, same rules. Please do both in one pass —
somebody who learns the pattern in the house will look for it in the plan.

## Two smaller things while you are there

1. **A hover state on the rail rows.** They carry `cursor:pointer` and an `onClick`, but they read as
   status text. A background shift on hover would have prevented this entire report.
2. **"1 of 8 decided" could name what is next** rather than only counting. *"1 of 8 decided — Emotional
   message is open"* does the same work as the button, in the place people already look.

## What not to do

- **Do not auto-advance on choosing.** More than one option per layer is legitimate, and a screen that
  jumps away mid-decision takes the decision with it.
- **Do not add a Back button.** The rail already goes anywhere, and a linear pair implies the sequence is
  stricter than it is.
- **Do not disable and grey the control when there is no choice yet.** A disabled button with no reason is
  the version of this that generates the next confused message. The sentence is better than the greyed
  button.

## Backend

Nothing needed. Everything this requires is already in `status.layers[]`:

```
layer / key / id     the layer name — all three carry it
label / name         what to print in the button
chosen[]             whether a choice has been made here (length > 0)
ready                whether the target layer can be worked on
blocked_because      the sentence to show if it cannot
```

`H_LAYERS` in your file is already the sequence, so `H_LAYERS[i + 1]` is the target and its label is the
button text. The plan's `P_LAYERS` equivalent likewise.
