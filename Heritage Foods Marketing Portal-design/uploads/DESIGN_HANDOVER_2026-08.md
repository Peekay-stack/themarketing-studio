# Handover to Claude Design — The Marketing Studio

Five backend capabilities are finished, tested and wired to endpoints. Three of them have only a
plain, functional UI that I built to prove the plumbing; two have almost none. This document is what
you need to design them properly.

**File to edit:** `api/frontend/app.dc.html` — one file, 5,033 lines, ~409KB.
**Do not change:** anything in `api/*.py`. The endpoint contracts below are fixed and tested; if a
design needs a different shape, say so and it will be changed on the backend rather than worked
around in the client.

---

## 1. How this file works

It is a single Claude Design `.dc.html` artifact: `class Component extends DCLogic`, served by
FastAPI with React and a `window.claude.complete()` bridge injected ahead of `support.js`.

### The bag

The template contains **no expressions**. `render()` returns one flat object — currently ~233 keys —
and the markup only interpolates from it. Every colour, label, boolean and handler is computed in JS
first.

```js
// in render(), before `return {`
const rows = (s.things || []).map(t => ({
  ...t,
  badgeBg: t.ok ? '#EAF6EC' : '#FBE3E1',      // colours are computed, never chosen in markup
  open: this.openThing(t.id),                  // handlers are pre-bound
}));
return { things: rows, hasThings: rows.length > 0, noThings: rows.length === 0, /* … */ };
```

### The three primitives

```html
<sc-if value="{{ hasThings }}" hint-placeholder-val="{{ false }}"> … </sc-if>

<sc-for list="{{ things }}" as="t" hint-placeholder-count="4">
  <div onClick="{{ t.open }}" style="background:{{ t.badgeBg }};">{{ t.name }}</div>
</sc-for>
```

Rules that bite if ignored:

- **No `&&`, no ternaries, no `.map()` in markup.** `{{ a || b }}` will not work. Compute it.
- **Booleans need their own key.** There is no `unless`; pair `hasX` with `noX`.
- **`sc-if` and `sc-for` must balance.** Current file: `sc-if` 126/126, `sc-for` 78/78. Keep it so.
- **Loop aliases are scoped** — `as="t"` then `{{ t.field }}`. Nesting works (see the voice picker).
- **Styles are inline.** There is no class system beyond `.hf-scroll` and two keyframes.
- **Unicode:** some strings are stored as literal `—` and others as `—` escapes, inconsistently.
  Match whatever is already on the line you are editing.
- React is available for the few things markup can't express (`React.createElement('audio', …)`) —
  used 9 times; prefer markup.

---

## 2. Brand system — non-negotiable

From `brand-book.html`. Verified against the book's own WCAG table.

| Token | Hex | Role |
|---|---|---|
| Navy | `#17325E` | Primary. Type, dark grounds, buttons, body copy |
| Signal Orange | `#F0561E` | **Accent, rationed.** Currently 3 uses, all the active-nav marker |
| System Mid | `#2E5EA6` | UI layers, gradients, links |
| System Light | `#9DB8E0` | Backgrounds, dividers |
| Paper | `#F7F5F1` | Ground. Preferred over pure white |
| Line | `#DDD9D1` · `#C9CEDA` | Borders, warm and cool |
| Slate | `#6B7280` | Secondary text, captions |

- **Orange is not a text colour** — 3.19:1 on paper, large-text only. Never running copy. It marks
  "the live layer, the thing currently running", which is what the mark itself means.
- **Type is Epilogue**, weights 400/500/600/700, loaded from Google Fonts.
- **Status colours stay green/amber/red** (`#259821` `#E8A93C` `#C0392B`) — the client's explicit
  decision. They are interface signals, not brand expression, and the palette has no equivalents.
- **The logo is artwork, never live type.** Assets in `api/frontend/assets/`: `logo-primary.svg`,
  `logo-stacked.svg` (currently in the header at 72px), `monogram.svg`, `glyph.svg`, `app-icon.svg`,
  plus reversed variants. Minimums: primary 180px wide, stacked 110px, monogram 64px.
- Everything must work offline apart from the font — no CDNs, no remote images.

**Open question for you:** the header is 96px to fit the stacked lockup, which is heavy on every
screen. The brand book's own recommendation for product nav is the **monogram alone**. If you agree,
swap it and give the header back its 74px.

---

## 3. What needs designing

### A. Reference library — `isLibrary` (exists, plain)

Ground truth: uploaded and signed off by a person, **never anything generated**. Twelve kinds:
`pack, logo, brandbook, film, graphic, research, copy, cast, voice, music, actor, plate`.

What I built: a chip row, an upload form, and a two-column card grid. What it needs:

- **A real asset browser.** Media kinds are images, video and audio — it currently shows filenames
  where it should show thumbnails, posters and a play control.
- **Sign-off has to feel like the gate it is.** Unsigned is not an error state — it is "not usable
  yet". Generation genuinely ignores unsigned items; the UI should make that legible at a glance.
- **Locked copy is a different animal** from a file: strings placed verbatim into scripts. It is
  currently squeezed into the same card shape and shouldn't be.
- **The empty state matters more than usual.** Until a pack shot is signed off, every render works
  from a description rather than the real thing — which is exactly why packs drift between shots.

### B. Learning log — `isLearning` (exists, plain)

Three tiers, all computed from the log: **retrieval** (approved work anchors the next generation),
**prompt library** (templates scored by what they earn), **corrections** (each rejection's reason
becomes a house rule).

- **No invented numbers.** Every figure is counted or reported as unknown. A template never judged
  shows "not judged yet", never 0% — *never assessed* and *always rejected* must not look alike.
  Please keep this; a fake metric in a governance screen is worse than a blank one.
- Needs: a promotion/demotion **history** view (the data carries `history[]` with reasons), and a
  clearer separation between what the system does automatically and what it may never touch.
- The guardrail panel ("what learning may never touch") is the most important block on the page and
  currently looks like a footnote.

### C. Green-screen compositor — **no UI at all**

Backend done and measured. Needs a screen: pick a green-screen take (library kind `actor`) and a
plate (kind `plate`), set the key colour and two tolerances, composite, review.

- The response returns `green_left` — the fraction of frame still green. **Surface this.** A
  half-worked key looks fine in a thumbnail and terrible on a big screen.
- Similarity/blend want a live-feeling control, not two number inputs. A before/after comparison at
  the same frame would earn its space.
- Defaults: key `0x00B140`, similarity `0.18`, blend `0.08`.

### D. Edits from an approved master — `hasProduced` panel (exists, minimal)

Six one-click presets under the produced film. Trim and crop only — **never a re-render** — so an
edit inherits the master's approval and costs nothing.

- Needs to read as a **deliverables set**, not a row of buttons: one master, many outputs, each with
  its aspect, duration and where it's going.
- Custom in/out points would be genuinely useful; the backend already takes `start` and `seconds`.

### E. Document round trip — buttons only

"Import edited script" and "Import edited brief" sit beside the Download buttons.

- The response says **`how: "structure" | "interpreted"`** — read from the document's own table and
  headings, or interpreted by a model. These are different levels of confidence and currently differ
  only by toast colour. An interpreted import should ask for a review before it is trusted.

---

## 4. Endpoint contracts

All JSON `POST` unless noted. These are tested and fixed.

```
GET  /library?kind=&signed=0     -> { kinds:[{id,label}], items:[…], summary:{…} }
POST /library-add                -> multipart: kind, name, note, tags, files[]
POST /library-sign               { id, who, on:true|false }
POST /library-remove             { id }
GET  /library-file/{kind}/{name} -> the file

POST /import-doc                 -> multipart: what=script|brief, file=.docx
                                 -> { ok, how:"structure"|"interpreted", rows|fields, detail }

GET  /learning                   -> { tiers, guardrails, decisions, approval_rate|null,
                                      rules, templates_list, recent, empty }
POST /learning-decision          { kind, decision:"approve"|"reject", subject, reason, template }
                                   — a reject WITHOUT a reason returns 400 by design
POST /learning-context           { kind, brief } -> { anchors, anchor_text, rules, rules_text,
                                                      locked_copy, references }

POST /composite                  { footage, plate, key, similarity, blend, label }
                                 -> { url, green_left, clean, detail }
POST /edit-master                { master, seconds, aspect, start, mute, label }
                                 -> { url, label, seconds, aspect, from_master }
GET  /edits                      -> { edits:[{name,url,bytes,seconds}], aspects }
```

`library`, `learning` and `edits` are all empty on a fresh install — **design the empty states
first**, because that is what the client will see on day one.

---

## 5. Things not to undo

These were each a real bug once and the current behaviour is deliberate:

1. **The voice picker renders the backend's answer**, not the local pick. Letting the card show the
   user's choice while the rows showed the cast voice is exactly how they diverged before.
2. **Frames carry a staleness badge.** A still rendered for a 4s beat sitting in an 8s slot is wrong,
   and the card says so.
3. **A scene whose words can't be spoken says so in red** on the Shoot Board — the text reads as a
   stage direction and would render silent otherwise.
4. **Scene counts are a range, not a number** (`sceneRange()`), computed from duration against Veo's
   4s floor. Don't turn it back into a lookup table.
5. **Anything the model cannot do is not implied to be doable.** No "training" language on the
   Learning screen: no weights change, and saying otherwise would stop people checking the output.

---

## 6. How to test

```bash
Start Heritage Studio.bat     # no --reload, so restart it after any Python change
```

Then hard-refresh. The backend must be running for the Library, Learning and Edits screens to have
anything in them — they read from disk on the server, not from local state.
