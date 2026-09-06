# ASK_DESIGN_27 — round 26 reviewed and synced

The PR desk is in. It is a big, careful round and most of it was right — the funnel's refused row with its
`why`, the three message states, the tier cards, the "prepared, no incident" state reading as good, the
overdue rail beside a ready statement, and every "what NOT to build" rule held.

**Nothing to build in this ask.** It is a report on what was fixed and two things to change next time.

## Build on the file in this zip

```
app.dc.html      1,190,404 bytes
sha256           447cc1475270f6575099c91183f514bee8000970bad5f8e690f339e4153cdd60
```

Base confirmed byte-identical to the round-26 zip; nothing on this side had touched the frontend since,
so nothing was reverted. checkfe **7/7**. Cross-fragment bag-key sweep: no new collisions. Zero literal
`\uXXXX` escapes in markup.

---

## The one root cause behind most of it: every vocabulary is a DICT

You asked about payload shapes, and this is the answer to nearly all of them at once. **Every vocabulary
the PR backend sends is a dict keyed by id, not a list** — modes, phases, standalone kinds, languages,
tiers, trade categories, release parts, kit elements, prominence, sentiment, roles, notice elements,
descent.

You handled that correctly in three places (`rungs`, `five_w`, `translations`) and not in the rest. The
consequences split two ways:

- `(dict || []).map` — **`.map` is not a function**, which threw and took the panel down. The PR screen
  **whitescreened on open** with `((st && st.phases) || []).map is not a function`.
- `(dict).length` — undefined, so the code fell through to a hard-coded default and **silently ignored
  the server**. `parts` did this: the release rendered your fallback pyramid instead of the payload's own
  parts, including which are required and what each is for.

Fixed with one normaliser, `prSeq(d)`, next to `prOpt` — dict or list in, list of `{id, ...}` out —
routed through **twelve** sites. Worth keeping as the default way to read any vocabulary from this
backend.

## The rest

| what | why it needed fixing |
|---|---|
| `cr.signatures \|\| cr.signed` | The field is **`signoff`**. Neither name exists, so `sigRaw` was always `{}` and **every role read "not signed" even immediately after someone signed**. Your dict→list normalisation just below it was already right. |
| `cs.roles` and `cs.notice_elements` | Both dicts. `.forEach` / `.map` on them threw — the crisis panel could not render at all once a `/pr-crisis-status` response arrived. |
| `st.descent` | A dict of `{stance, why}`. Passed to `prLines` it became one object with no `text`/`what`/`note`/`why` at the top level, filtered to nothing, and the chips never appeared. Now built from the entries. |
| `/pr-kit` bodies | Sent a bare string for b-roll, stills, profile and release, and for soundbite when no speaker was typed. The route refuses a bare string, so **the kit form 400'd every time**. Now always `{url}` / `{url, who}`. |
| `/pr-map-drop` | You flagged this and you were right — it keys on the record's **id**, and the links sent the name. The route matched nothing and returned 200 with the map unchanged, so the link looked like it worked. A silent no-op is worse than an error. |
| the jurisdiction control | A `<select>` whose options came from the entered frameworks — and a framework row carries no `id`/`name` for `prOpt` to read, so the only option was the placeholder and **an incident could never be opened from this screen**. Jurisdiction is free text on the backend (deliberately: an incident can be opened before legal has confirmed anything, and the panel is built to say so). Now an input, with the confirmed jurisdictions as a hint line. |
| `by_outlet` names | Rows carry `outlet` (the id, empty for an off-map title) *and* `name`. `r.outlet \|\| r.name` printed a hex id for every outlet that was in the map. |
| the "signatures cleared" band | Gated on `body.statement`, but the server clears every signature when **product, risk or action** changes too — so editing one of those wiped three signatures with no toast and no band, which is the one thing this panel was asked to make unmissable. Now read off the response: signatures before, none after → announce. |

## Two answers to your remaining questions

- **`/pr-coverage-drop` sends `item: row.id`** — correct, no change needed.
- **`prominence` and `sentiment` appear under the same names in two payloads with two shapes.** On
  `/pr-coverage-status` they are the *vocabulary* (objects with `label`/`what`); on `/pr-report` they are
  *counts* (`{headline: 2, lead: 1}`). You handled both correctly. Flagging it because it is a trap:
  same key, same screen, different meaning.

## For next round

1. **`prSeq` first.** Any new vocabulary from this backend is a dict. Reach for it before `.map`.
2. **A `.length` fallback hides a shape error.** `parts` fell through to a hard-coded list and looked
   fine — no crash, no console error, just the server quietly ignored. Where you write a fallback,
   consider whether a wrong shape would be visible at all.

## What we checked, and how

Every panel driven in a real browser against the live backend, not read: the funnel against the Heritage
plan's own three-level ladder (business refused with its `why` on screen, marketing contributing,
communication owning, and the `verify` job suggested off the matched cues); the media map with the tier
cards and all thirteen languages; the crisis panel end to end — framework entered by name with a source
against each obligation, Class I set by a named person, the 24-hour Schedule I duty showing overdue
beside an 18.3h-left public notice, three signatures, and a notice edit clearing all of them and saying
so.

`tools/contract.py` was also widened: its find-by-name heuristic had started reading your translation and
signature lookups as layer lookups and reporting four confident mismatches about fields no layer carries.
It now scopes to lookups where `layers` appears within three lines, and reports how many it skipped. The
real check still bites — verified by breaking the layer lookup on purpose and watching it fail.

18/18 `test_tools.py`, contract clean, checkfe 7/7, **220 routes**, page loads with only the four
pre-existing SVG placeholder warnings, and the tenant tree, library, renders and edits all byte-identical
afterwards with all three PR stores left empty.
