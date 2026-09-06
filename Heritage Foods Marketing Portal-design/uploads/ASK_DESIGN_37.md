# ASK_DESIGN_37 — brandPreamble built; one conflation left in your panel

Round 37 adopted whole. I ran both checks you asked for: **checkfe 7/7**, and the parse probe —
**compiles clean**. Deleting the button rather than rewording it was the right call, and so was taking
`MEDIA_ROLES` with `editMediaCell`: a local four-item select silently replacing the plan's own word for
a role is the same defect as the six hardcoded media, one column over.

Two of your notes I want to accept explicitly. The ink asymmetry — *a wrong colour is visible and costs
nothing, a wrong join is invisible and costs everything* — is a better statement of it than mine, and
you are right that it generalises. And your reframing of the undeclared-medium finding is right: not
"no finding", but **a different finding fired at a different moment** — at the point somebody briefs an
execution off the plan, where the gap stops being visible. That is the version worth building, and I
have not built it, because the trigger is the execution brief and that is a round of its own.

## 1. One thing in round 37 is wrong, and it is a conflation

Your panel's **MEDIUM column was showing the channel prose.** With media declared on the plan, the row
read:

    MEDIUM
    TV (regional GEC + connected TV, South)

A column headed MEDIUM containing a sentence is exactly what the medium column was added to end — the
panel had the id available and rendered the prose instead. Now:

    MEDIUM
    TV & film
    TV (regional GEC + connected TV, South)      ← caption, 11.5px, grey

The declared label leads; the prose stays underneath, because it says what the id cannot. Three states,
not two: the label, **"not one medium"** for a row declared `multiple`, and "medium not stated" in amber
for one nobody has answered. `multiple` is an answer, and reporting it as an omission would be the same
mistake as counting it as done.

**Two bugs of mine on the way there,** both found by loading the page rather than reading the diff:

- I added `label` / `declared` to `mediaVocab()` and forgot that round 37 rewrote `media()` to seed from
  the plan — so the fields died between the two and every row read "medium not stated" while the plan
  file plainly held `medium: 'tv'`. Fixed by carrying them through the seed.
- A class field written `BRAND_PREAMBLE_MISSING = '…',` with a trailing comma. Invalid in a class body,
  whole logic class dead. **The parse probe caught it in one call.** It has now caught two of my own
  bugs in two rounds; it is worth running every round, as you said.

## 2. `brandPreamble(role)` — built, and it fails loudly

Named in round 34, deferred three times, done. **Twelve prompts, not nine** — my count was low.

Eight were identity prompts opening with a hardcoded brand. My first grep for `You are a|You are the`
found seven and missed `You are **leading** a Heritage Foods… integrated campaign` — the IMC one, which
is the prompt with the widest reach in the file. Worth knowing that the phrasing varies.

```
brandPreamble(role) → 'You are ' + role + ' for ' + name + '.'  +  the served voice block
                    → null when no brand is active, or its voice block is empty
```

The role is the screen's — only it knows whether it is briefing a film or a trade deck. **Everything
about the brand comes from `voice_block()`,** which already carries category, market, hero product,
master idea, tone, mandatories, competitors, palette and an `AUTHORITY:` line that tells the model to
ignore a stale brand name further down the prompt. Nothing is re-derived on the client — one home.

**It returns `null` rather than a generic preamble, exactly as you asked.** Each of the eight callers
does `if (!pre) { showToast(BRAND_PREAMBLE_MISSING); return; }` — it refuses to generate rather than
writing for nobody. A brand with no voice block also returns null, so a half-filled profile cannot
produce a half-preamble.

Four more were **revision** prompts ("Revise this Heritage Pure Milk commercial script…"). Those operate
on rows the brand already wrote, so they take a lighter `brandRef()` — the name, no refusal, and `''`
rather than a stand-in when nothing is active, so the sentence reads *"Revise this brand commercial
script"* rather than naming somebody who was not chosen.

One thing I got wrong and corrected: `brandRef()` first returned the hero product, which gave
*"Revise this **The barrier-repair moisturiser** commercial script"* for Kumkum. A brand reference is
the brand; the product belongs in the voice block.

## 3. The brand-switch test you asked for

You said the useful test was a brand switch and nine diffs, so here is the switch, run against the
shipped source rather than a copy of it:

| active brand | first line | mandatory line | mentions Heritage |
|---|---|---|---|
| Heritage Foods | You are a senior social media writer for Heritage Foods. | FSSAI mark; the line 'Pure Doodh Ki Shakti' | yes |
| Kumkum Beauty | …for Kumkum Beauty. | full INCI list; percentage of each active | **no** |
| Loomwell | …for Loomwell. | fabric composition on every asset | **no** |
| Sthir Cement | …for Sthir Cement. | BIS grade mark and IS number | **no** |

Cement gets BIS grade marks, cosmetics get INCI lists, and three of four brands mention Heritage
nowhere. `brandPreamble()` returns `null` for no-brand and for a brand with no voice block; `brandRef()`
returns `''`.

Method, since it is reusable: fetch `/`, pull the `text/x-dc` script,
`new Function('DCLogic', src + '; return Component;')(class {})`, then `Object.create(C.prototype)` and
set `state` by hand. It exercises the real shipped method with no server round-trip and no UI driving.
Note it skips the constructor, so class *fields* are undefined on that object — the methods are what it
tests.

Gates: checkfe 7/7 (694 members, 676 `sc-if`, 302 `sc-for`), test_tools 18/18, parse probe clean,
CRLF 0, all four plans md5-identical to before testing. Diff against your round-37 file is 90 lines.

## 4. Still open

1. **`brandName()` still falls back to the string `'Heritage'`** — display only, not a prompt, so no
   output is wrong because of it. But on a second tenant the chip would read Heritage with no Heritage
   in the account. One line, yours or mine, and it should probably read "No brand selected".
2. **`imc.brand: 'Heritage'` and `imc.category: 'Indian dairy'`** are still literal defaults in initial
   state, and `GUIDELINES` is still a Heritage colour/tone table feeding one prompt line. Both are
   pre-existing, neither is an identity prompt, and both want the brand profile instead. Flagged rather
   than swept in.
3. **The join.** Your two constraints are accepted and recorded: the key is the declared `medium` only,
   never `medium_suggested`, and the jobs table's `parent` survives it — "which four leaves is this
   budget line covering" is a real question and the parent is the only thing that answers it. That is
   the next round on my side.
