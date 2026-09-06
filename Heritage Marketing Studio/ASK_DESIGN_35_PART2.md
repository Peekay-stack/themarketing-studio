# ASK_DESIGN_35, part 2 — your round 35 integrated, and both your questions answered

Your round-35 file is adopted as the base. `MEDIA_DEFS` is gone, `mediaVocab` / `MEDIA_INK` /
`medNumWord` are all as you sent them, and both derived count sites are kept. I changed six lines of
your media code and re-applied two hunks of mine; the whole diff against your file is 60 lines.

## 1. Your two questions, answered — and there is a third answer you did not have

**"Real leaf ids."** Eleven, in taxonomy order:

    tv · social · influencer · owned · performance · ooh · posm · activation · trade · pr · retail_media

`social`, `influencer`, `owned` and `performance` are the four children of `digital`; the other seven
are top-level and their own leaf. `digital` itself is **not** a leaf — it has no rung of its own, which
is `media.py`'s stated reason for splitting it. Your `MEDIA_INK` guesses were good: `retail_media`,
`posm`, `activation`, `trade` and `pr` are all real. `radio`, `print`, `search`, `cinema`,
`influencers` (plural) and `onground` are not in the taxonomy — harmless as extra keys, but they will
never be hit.

**"Are `/media-strategy`'s channels top-level media or leaves?"** Neither, and this is the finding.
**They are free text.** `mediaplan.channels()` returns `str(r.get("channel"))` straight off the plan's
`channels` layer, which stores prose. The live plan's seven read:

    TV (regional GEC + connected TV, South)
    Social (15s vertical reel — '500 before 7am' counter)
    On-ground (RWA / apartment activation, promoter)
    Digital ('Track your milk' shoppable landing + home-delivery sign-up)
    OOH (hero freshness visual + '500 before your morning' line)
    POSM (fridge-edge shelf strip, general trade)
    Trade (distributor + retailer sell-in)

So the grain question has a worse answer than either of the two you offered: the panel was planning
weight against sentences. They join to nothing — not to this taxonomy, not to the jobs table, and not
to a second plan. Two plans that both mean `tv` produce two different media.

**And the consequence for round 35 specifically: `MEDIA_INK` was unreachable code.** Both your
vocabulary sources hand `mediaInk` a display string rather than a key — the plan's prose on the primary
path, and on the fallback `o.label` ("TV & film") rather than `o.v` ("tv"). Neither is a key, so *every
row on both paths* fell through to the palette. Your instinct that leaf ids were needed "so nothing
falls through to the palette" was right, but it was not a few rows: it was all of them, always.

## 2. Server — the prose now resolves, or says why not

`media.resolve_text(text)` is new, in `media.py` because that file is the single source for what a
medium is. It resolves the head of the string — everything before the first bracket — against leaf ids,
leaf labels and retired names. **Exact match only** after casefolding and whitespace collapse: no
stemming, no first-word-of-a-longer-phrase, no similarity score. A medium filed under the wrong leaf is
worse than one filed under none, because the weight, the ink and the join all follow the id and a wrong
id is invisible while a missing one is not.

A head that resolves to a **parent** is refused rather than pushed onto a child. `digital` is the whole
reason the taxonomy split; returning `owned` would be `NEEDS_REVIEW` applied silently, which
`normalise` already documents as a bug it made once.

`channels[]` rows now carry, beside the untouched `channel` prose:

| key | meaning |
|---|---|
| `medium` | the leaf id, or `''` — **never a hedge** |
| `medium_label` | the taxonomy's own label |
| `medium_confident` | whether `medium` can be relied on |
| `medium_why` | when it cannot, the reason in a sentence |

`strategy_view` also gained `leaves` (all eleven with `key`/`label`/`parent`, so no screen needs a local
list) and `unresolved` (the channels this could not place, each with its reason), plus
`counts.with_medium`. The vocabulary sits on the same payload as the rows it describes rather than
behind a second call, because a vocabulary fetched separately from its rows is how the two disagree.

On the live plan: **six of seven resolve**, and the seventh is `Digital`, refused with
*"Digital is a budget line, not a medium — it covers social, influencer, owned, performance, and those
carry different rungs. Which one this channel means is a reading of the row, not something this can
infer."*

## 3. Your file — six lines, and two hunks re-applied

- **`mediaInk(id, name, i)`** takes an id first, display name second, palette last.
- **`mediaVocab()`** rows carry `id`: `x.medium || ''` on the primary path, `o.v` on the fallback (the
  label stays as `name` — a person reads the label, the ink and any join need the key).
- **`media()`** carries the id onto a seeded row, so ink survives an edit.
- **Both `mediaInk` call sites** pass it.
- **One new band**, `mediaUnplacedLine`, in the same amber treatment as your drift band and directly
  after it: how many channels carry no medium, which they are, and the desk's own reason. I added it
  rather than leave `unresolved` served-and-unrendered, since that is the exact pattern I complained
  about in part 1 §5. **Styling and placement are yours to change** — the content is the point, not the
  band.
- **Re-applied, and this is the second time one of them has been lost:** `COL_HINT` / `pCols` and
  `balBasisFg`. Your round-35 file was built on the pre-change base, so both were gone. Both now carry
  a `RE-APPLIED` line at the site, as you asked for in round 30.

## 4. Verified in the page

Media planning panel, live, seven rows. The swatches now read:

    #17325E  #2E5EA6  #3F814C  #E8A93C  #E8A93C  #8A6410  #B07A12
      tv      social  activation (none)    ooh      posm     trade

Rows 6 and 7 are the proof: palette-by-index would have given `#F0561E` and `#7A5FA6`. Row 4 is the
unresolved `Digital`, correctly taking a palette colour — it has no id to key on, and that is now
stated on screen rather than merely coloured. `matches_taxonomy_ink: true`, `still_palette: false`.

The unplaced band renders its full sentence. "Seven media" still derives. Console carries only the four
pre-existing `{{ w.d }}` / `{{ p.x }}` SVG placeholder warnings from the NeedScope wheel.

One bug of my own, worth recording because the gate did not catch it: I first inserted the new `sc-if`
**inside** your drift `sc-if`, so it rendered only when there was also drift. `checkfe` passed — the
tags were balanced, just nested wrong. Balanced is not correct, which is the seventh check's blind spot.

Gates: checkfe 7/7 (693 members, 671 `sc-if`, 300 `sc-for`), test_tools 18/18, CRLF 0 on all four
touched files, all four plan files md5-identical to before testing.

## 5. Two things for you, one of them possibly serious

1. **"Save the media plan" does not save the media plan.** `produce` posts `{id}` to
   `/execution-produce` and nothing else; `state.media` — the names, roles, weights, flights and owners
   in that table — is read only by `media()`, `editMediaCell` and the bag, and is never sent anywhere.
   So the weight column the panel exists to collect is client-only and dies on reload. This is
   pre-existing, not from round 35, and I have not touched it: persisting it needs a route and a
   decision about where a media plan lives, which is a proper ask rather than a sync. But it is the
   reason the panel cannot yet answer the question it is shaped around.
2. **The grain is still not fixed, only reported.** Six of seven resolving is good; it is not the same
   as the plan carrying an id. The real repair is a `medium` column on the plan's `channels` layer,
   drawn from the eleven leaves, so the plan states the medium instead of having it inferred from prose
   — and then `resolve_text` becomes a migration path for existing rows rather than a permanent
   dependency. That changes what the plan skill drafts, so I would rather propose it than build it.
   Say the word and it is my next round.

Also still open from part 1, unchanged: where a running weight total wants to live, and whether
`sum` / `weighted` get a home. And from round 34: `brandPreamble(role)` failing loudly — still mine,
still not done.
