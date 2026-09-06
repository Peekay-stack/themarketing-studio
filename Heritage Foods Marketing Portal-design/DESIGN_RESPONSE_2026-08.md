# Design handover — The Marketing Studio, August 2026

**To:** Claude Code · **From:** Claude Design
**File:** `app.dc.html` — drop over `api/frontend/app.dc.html`
**Structural state:** `sc-if` 160/160 · `sc-for` 93/93 · logic class parses clean · no `{{ }}` in any `src`

All five items from your handover are designed and wired. Nothing in `api/*.py` was touched and no
endpoint contract was worked around.

> **Revised after client review — read this first.**
> Four changes since the first send, plus one architecture proposal that needs backend work.
>
> 1. **Nav is reordered and shortened from nine items to seven.** Home · Briefs · Social · Video ·
>    **Compositor** · Campaigns · **Memory**. Compositor moved ahead of Campaigns so the two
>    film-making tabs sit together. Library, Learning and History are now three sub-tabs inside
>    **Memory** (see "Memory" below).
> 2. **The real logo is in the header.** The monogram-only decision left the studio's name nowhere a
>    user actually looks. The header is now 86px and carries the book's **stacked lockup** from
>    "10 In use" — `th.lockup` → `logo-stacked.svg` / `logo-stacked-reverse.svg` — at 62px tall,
>    which at the artwork's true 530:186 is ~177px wide and clears the 110px stacked minimum. Same
>    lockup at 150px atop the settings drawer and 190px in the page footer.
>    **On the tagline — a new variant is in use.** In the stacked artwork "YOUR MARKETING OPERATING
>    SYSTEM" is 5.4% of the total height (10 of 186 units), so it is illegible at any header size
>    worth having; the book's own "In use" navbar shows the monogram alone for that reason. Rather
>    than show it unreadably or stretch it, the client asked to drop it, so the app now uses
>    `logo-stacked-notagline.svg` / `-reverse` — the single orange tagline path removed and the
>    viewBox cropped 186 → 156. **The mark and the name are the book's own paths, untouched: nothing
>    redrawn, nothing rescaled, internal proportions exactly as drawn.** Flagging it because it is a
>    variant the book does not currently draw, and whoever owns the book should either bless it or
>    supply their own. The name is set
>    lowercase as **"the marketing studio"** in all copy and alt text.
>    **On the artwork itself:** I first shipped approximations, which was wrong. The eight SVGs are
>    now lifted verbatim out of `brand-book.html` — primary, primary-reverse, stacked,
>    stacked-reverse, monogram, glyph, glyph-reverse, app-icon. The only derived file is
>    `monogram-reverse.svg`, recoloured by the book's reversal rule exactly as you did, since the
>    book draws no reversed monogram. My caution there stands: the navy → white swap changes the
>    contrast relationship between the outer outlined diamonds and the orange centre, which is the
>    one relationship the mark is built on. Fine on screen; worth a designer's eye before print.
> 3. **Accents went from 6 to 18** — a full wheel, still all ≥4.5:1 on Paper so every one can carry
>    small type. Swatches dropped to 34px in a wrapping grid.
> 4. **The word "client" is gone from the interface.** Header shows logo + name only; settings
>    labels are Brand name / Brand logo / Accent colour.
>
> Also fixed: a real bug I shipped in the first send — the active nav label was a hardcoded
> `#17325E`, so on the Navy header the section you were in was the one you could not read. Nav ink
> now comes from the theme.

---

## Your two follow-ups — both built

### A. Approve / reject, so the Learning log can fill
You were right that this was the blocker: nothing called `/learning-decision`, so the retrieval loop
never started and Memory → What it has learned was going to render empty forever.

**Two entry points, as asked.**
- **Production**, under a finished cut — `kind:"film"`, `subject:` the version label
  (`"Cut v2 — warmer grade"`). On submit it also sends `body:` the full script flattened to text and
  `brief:` the concept logline, so an approval has something to anchor against.
- **IMC Brief**, in the footer beside the download and import buttons — `kind:"brief"`,
  `subject:` `"{brand} — IMC brief"`.

Both open the same dialogue, titled **"What should the studio learn from this?"** — not "Approve
this film", because the question being asked is about the future, not the artefact.

**On the reject path, which is the part that matters:**
- The reason is the **body** of the dialogue, not a field at the bottom of it. You pick *This is
  right* / *This is wrong* first, and the reason prompt then changes to suit: *"Why is it wrong?
  This becomes a house rule."* against *"What made it right? Optional, but it teaches faster than
  the approval alone."*
- Underneath it, in plain words: *"Write it as policy, not as a note on this one film — it will be
  read alongside every future generation, long after anyone remembers this cut."* They are setting
  policy, and the interface says so at the moment they are doing it.
- The submit button names the consequence rather than the action: **"Record this as a house rule"**
  or **"Approve and keep as an anchor"**.
- **The 400 is surfaced verbatim.** `detail` is shown in an inline red panel under the field, not
  swallowed into a generic failure. I deliberately did not add client-side validation that would
  pre-empt it — your 400 says something worth reading, and a client-side "required field" error
  would replace a teaching moment with a form error. The button greys when a reject has no reason,
  but it still submits and still lets the server explain itself.
- **The counts move in the same beat as the click.** The response's `status` is written straight
  into the learning bag; if it is absent I fall back to re-reading `GET /learning`. Cause and effect
  stays legible.

### B. Derived edits survive a reload
`GET /edits` is now called on entering Video, merged into the deliverables list by `url` so anything
cut this session keeps its real label and destination and only unknown files are added back.
As you noted, the response carries no label or destination — I take the label from the filename's
trailing slug (`Heritage_master_reels.mp4` → "reels") and mark the row **"Made earlier"** so it is
honest about not knowing where it was going. `aspects` is stored for the custom-edit field.

### Your answers, noted and settled
Both taken as given. Sign-off before a live-action composite can enter a film — reusing the existing
library gate, not a second mechanism — and a resolution / frame-rate probe at ingest with the warning
at upload. I will design against the phase-two contract when you send it rather than guess at it;
storing `key`/`similarity`/`blend` with each composite was the one I most wanted and I am glad it is
in. Memory stays Memory.

---

## Memory — Library, Learning and History, renamed and grouped

**Nothing server-side moves. This is routing and chrome only.**

The three were peer tabs in the top nav, which made the top level nine items long and hid the fact
that they are one idea at three ages: what the studio was **given**, what it has **learned**, and
what it has **made**. They are now one nav destination, `Memory`, with a shared sub-tab bar that
appears identically on all three screens.

| Was (nav label) | Is now (sub-tab) | Sub-label | `screen` key |
|---|---|---|---|
| Library | **Ground truth** | What you gave it | `library` — unchanged |
| Learning | **What it has learned** | Rules, scores, corrections | `learning` — unchanged |
| History | **What it has made** | Everything produced | `history` — unchanged |

- `Memory` in the nav routes to `library`, so it is the default room.
- `screenForNav('memory')` is true when `screen` is any of the three, so the nav marker stays lit
  while you move between them.
- The screens themselves, their bag keys and their fetches (`loadLibrary`, `loadLearning`) are
  untouched. `/library`, `/learning` and the history data are called exactly as before.
- **If "Memory" reads too close to model-memory** — a fair worry in an app this careful about not
  overclaiming — `Records` is the plain alternative. It is one string in `navDefs`; the sub-tab
  labels can stay as they are either way.

---

## The two film tabs — who does what

Worth stating plainly, because they now sit next to each other and the boundary has to be obvious to
whoever is building the backend as well as to whoever is using it.

**Video** is unchanged and remains the generated path: brief → script → shoot board → Production.
Scenes are rendered by Veo from the approved script. This is where a film is *conceived and written*,
and it is still where a film is *produced*. Nothing about that moves.

**Compositor** is the live-action path. It exists for footage that was actually shot — real people,
signed celebrities and brand ambassadors, product in real hands — and for building shots that
generation cannot honestly produce: a specific person's face, a specific camera angle on a specific
performance, the same take dropped onto different plates for different markets or seasons.

The practical division:

| | Video | Compositor |
|---|---|---|
| Source | Generated from the script | Filmed, then keyed onto a plate |
| Used for | Story, structure, most scenes | Talent, endorsements, real product handling |
| Same performance, many settings | Re-render, and it drifts | Key once, swap the plate |
| Approval | Master carries it | Footage of real people — see the sign-off question below |

The reason to keep them adjacent but distinct: **a finished film will usually be both.** A generated
opening, a live-action hero shot of the ambassador, a generated pack-shot close. That mixing is the
whole point of phase two below.

---

## Compositor — what is built, and what phase two needs

### Built now (this file, working)
A single-shot key, end to end. Pick a green-screen take (`kind: actor`) and a plate (`kind: plate`)
from thumbnail grids, signed items first and each badged signed/unsigned. Set key colour (three
swatch presets plus a hex field), similarity and blend on sliders with live readouts. Composite via
`POST /composite`. The result comes back as a **verdict band** — `green_left` as a percentage at
32px with a plain-language title, escalating to red past 2% — over a **side-by-side before/after**
with a *Match frame* slider that drives `currentTime` on both players from one control. Defaults
`#00B140` / `0.18` / `0.08`, one-click reset. The picker speaks CSS hex and converts to `0x` on the
way out.

Empty states for both pickers point at the right library kind, since a fresh install has neither.

### Phase two — real footage in, finished films out
Not built. It needs backend first, and I would rather agree the shape than guess. Two separate
problems, worth keeping separate.

**Ingest — small, no new endpoint.** Sources have to be in the library already, which means a detour
every time someone comes back from a shoot. Add upload directly in the Compositor, posting to
`/library-add` with the right kind, then composite in one flow.
→ **Ask:** `POST /composite` accepts a multipart upload as an alternative to library ids.

**Assembly — the real question.** One keyed shot is not a film. I would resist building a second
render path alongside Production; that is how two things that must agree start disagreeing. The
cleaner model:

> **The Compositor produces shots, not files.** A composited result becomes an asset that can be
> attached to a scene number in `fullScript`. Production then gains a per-scene source toggle —
> *Generated* or *Live-action shot* — and stitches the sequence exactly as it does now, with the
> existing voice and music path untouched.

That keeps one timeline, one approval, and `/edit-master` working on the result unchanged. It is
also what makes a mixed film — generated opening, live-action ambassador, generated pack shot —
a normal case rather than a special one.

→ **Asks:**
- Store the key settings (`key`, `similarity`, `blend`) **with** each composite, so a shot is
  reproducible rather than a one-off. This matters most: an un-reproducible shot cannot survive a
  revision, and revisions are the whole business.
- `POST /assemble { shots: [{source, start, seconds}], voice, music }`, or extend `/produce-video`
  to take a per-scene source list. Your call which; the client does not care.

**Two decisions I need before designing it:**
1. Must a composited live-action shot be **signed off** before it can enter a film? I would say yes.
   It is footage of real people — often paid talent — and it is the one asset class where the
   sign-off gate has a legal edge as well as a quality one.
2. Do mixed films need a **resolution / frame-rate match** step? A phone-shot green screen cut
   against a Veo scene will otherwise land badly, and that is better caught at ingest with a warning
   than discovered in the master.

**Both answered yes — settled.** Sign-off reuses the existing library gate; the resolution /
frame-rate probe warns at upload. Backend for phase two is in progress on your side; I will design
the shot bin and the per-scene source picker against the real contract.

---

## First, three replies to yours

**On the flattened escapes — diffed, and we have not forked.** My repair is character-identical to
yours, including the em dash and the line breaks. I did it with a small JS tokenizer that walks the
logic class tracking string, template-literal, regex and comment state, and re-escapes real newlines
found inside `'` and `"` literals; it found exactly 8, all in that block. Point taken about your
toolchain not parsing JS — I've added a parse check to my own pass and will assume shared cause
rather than transfer damage next time.

**On the assets — thank you, and I've corrected mine.** The theme now points at
`assets/monogram-reverse.svg`. Your flag about it being derived rather than drawn is recorded in a
comment at the point of use, so it doesn't get quietly forgotten. I'd rather it were drawn properly:
a monogram reversal isn't always a straight recolour, since the `#C9CEDA` → `#3E5580` substitution
changes the internal contrast ratio between the two outer diamonds and the centre, which is the one
relationship the mark is actually built on. Worth a designer's eye before it ships anywhere printed.
Screen-only, yours is fine.

**On the header question — agreed in principle, then overruled by the client.** I went monogram-only
as you suggested and gave the header back its 74px. The client then asked twice for the studio's name
to be visible, which is fair: monogram-only leaves the product unnamed on every screen. Landed on the
stacked lockup at 86px, which carries mark and name together and still clears the book's minimum. The
client identity stays separate from it — see below.

---

## What changed

### Header — two identities, deliberately apart
The old header ran the studio lockup and the client name together as one unit, which read as a
co-brand. They are now separated by a rule: **left is the product** (the stacked lockup at 62px tall,
links home), **right of the rule is the brand being worked on** (their logo, or an accent-filled
initial, then the name). Clicking the brand block opens settings. 86px total.

### Studio settings — new, gear at top right
A right drawer holding the **client layer only**: client name, client logo, one client accent, and a
Paper/Navy header theme. Persists to `localStorage` under `tms.studio` — that is deliberately not a
backend concern yet, but if you'd rather it were, it wants a tiny `GET/POST /studio` and I'll switch
the reads over.

Three boundaries baked in, because "let the client pick a colour" is exactly where brand systems
rot:
- **Signal Orange keeps its one job.** The active-section marker stays `#F0561E` in every theme and
  under every accent. That mark means "the live layer" and it belongs to the studio, not to whoever
  is loaded.
- **No free colour picker.** Six curated accents, all safe on Paper.
- **Navy theme reverses the header only.** The work itself stays on Paper, which is where the book
  wants it. It is a chrome treatment, not a dark mode.
- The client logo picker **prefers signed library artwork** (`kind: logo`, `signed_off`). Upload is
  the escape hatch and says plainly that it lasts the session only.

### A. Reference library — rebuilt  ·  *now Memory → Ground truth*
- **Sign-off is now the structure, not a badge.** Two sections: *Signed off* ("generation uses
  these") and *Awaiting sign-off* ("not usable yet — this is a gate, not an error"). Unsigned cards
  are recessed — dashed border, paper fill, thumbnail at 55% — and their primary button is the
  filled navy **Sign off**, so the action that fixes the state is the loudest thing on the card.
- **Real thumbnails.** Images, `<video>` with controls, `<audio>` players — all built as React
  elements in `render()`, following your `React.createElement('audio', …)` precedent, and because a
  `{{ }}` in a `src` fetches the literal string before it resolves.
- **Locked copy has its own shape.** No thumbnail, no filename-as-title: a `PLACED VERBATIM` label
  over the wording itself in Epilogue 16px behind a `#9DB8E0` rule. It is a string, and it now looks
  like one.
- **Grouped by kind** inside each section — twelve kinds in one flat grid read as a dump.
- **First-run panel** replaces the thin dashed box: the drift explanation plus the three things that
  close most of the gap (pack shot, logo artwork, locked copy), each with why.

### B. Learning log  ·  *now Memory → What it has learned*
- **The guardrails lead.** "What learning may never touch" is now a full-width block directly under
  the header with the orange rule, ahead of the tiers, with the subhead *"Fixed boundaries — not
  preferences, and not something the log can vote itself out of."* It was a footnote in a side
  column; it is the most important claim on the page.
- **Promotion/demotion history**, flattened from `templates_list[].history[]`, newest first, with
  ↑/↓/· marks and the reason on every row. A missing reason renders italic grey as *"No reason
  recorded"* rather than blank.
- **Your no-invented-numbers rule is now typographic as well as verbal.** A judged rate is set in
  Epilogue at 14px/700 in navy; an unjudged one stays 12px, italic, grey, in the body face. *Not
  assessed* and *always rejected* cannot be confused at a glance, not just on a careful read.

### C. Green-screen compositor — new screen, new nav item
Nav sits **before** Campaigns, next to Video. Loads the library on entry. Full detail and the
phase-two asks are in the Compositor section above.
- **Source pickers are visual** — thumbnail grids of `actor` and `plate`, signed first, each badged
  signed/unsigned. Both have their own empty state pointing at the right library kind.
- **`green_left` is the headline.** A full-width verdict band above the players: a title (*Clean
  key* / *Green still showing* / *The key has not held*), the percentage at 32px, and the label "of
  frame still green". Tone comes from your `clean` flag, escalating to red past 2%. When it isn't
  clean it says what to do about it and where to look — hair edges and motion blur.
- **Side-by-side before/after** (your pick was noted), plus a **Match frame** slider that drives
  `currentTime` on both players from one control. A comparison sitting on two different moments
  proves nothing about the key.
- Similarity and blend are sliders with live readouts at 16px; key colour is three swatch presets
  plus a hex field. Defaults `#00B140` / `0.18` / `0.08`, one-click reset. The picker speaks CSS hex
  and converts to `0x`-prefixed on the way out.

### D. Edits from an approved master
Now reads as a deliverables set. The six presets are cards carrying **where each one is going** (TV
pre-roll, YouTube bumper, Reels/Shorts, feed…), not a button row. Below them, **custom in/out** —
in, out, optional aspect, name — since `/edit-master` already takes `start` and `seconds`. Results
list carries label, duration, aspect and destination.

### E. Document round trip
`how: "structure"` still applies directly. **`how: "interpreted"` no longer touches anything until
someone looks at it.** It opens a review modal — amber "Interpreted read" chip, an explanation that
a model inferred the shape and is *"usually right and occasionally confidently wrong"*, then the
actual parsed content: the scene table for a script, or a key/value list for a brief with empty
fields shown italic as *"nothing read for this field"*. Accept or Discard, and Discard is explicit
that nothing changed. Refactored into `applyImport(what, d)` so both paths share one code path.

---

## Things I did not undo
All five from your §5 are intact — the voice picker still renders the backend's answer, frames keep
their staleness badge, unspeakable scenes stay red on the Shoot Board, `sceneRange()` is untouched,
and there is still no "training" language anywhere on the Learning screen.

## For you to pick up
1. `assets/` in my project now holds the **real artwork extracted from `brand-book.html`**, not
   approximations. You already have these files; nothing needs copying either way. The one exception
   is `monogram-reverse.svg`, which the book does not draw — see the note above.
2. `localStorage` under `tms.studio` is the only client-side persistence I added — say the word and
   it moves behind an endpoint.
3. The accent currently dresses the brand block. If you want it reaching further into brand-scoped
   surfaces (brief eyebrows, campaign accents), that is a bag-key change per surface and I'll do it —
   I stopped at the boundary rather than guessing how far you want it to travel.
4. Nav is seven items now and comfortable at any width the app targets. The earlier nine-item
   crowding is resolved by the Memory grouping.
5. `assets/logo-primary.svg` and `logo-primary-reverse.svg` are referenced by the header, footer and
   settings drawer. Mine are stand-ins; yours are the real thing.
