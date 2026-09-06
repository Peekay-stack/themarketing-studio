# Ask Design 34

Round 33 is adopted. First clean adopt in four rounds — nothing of mine was reverted, and your
counts matched exactly on the gate: 630/630 `sc-if`, 292/292 `sc-for`, 2332/2332 `<div>`, 686
members, 19 bag methods, 294 handlers. Both §1 fixes are right (`our_share`, `impressions_weekly`
plus the per-cell pair).

Before anything else, three corrections that are mine.

---

## 1. You were right, and my round-32 instruction was wrong

I told you: *"You already have the affordance for this — the Social producer's 'Prompt guide ▾'.
Extend that pattern."*

I checked that against `ASK_DESIGN_33.zip`. Six `data-prompt-guide` shells — `briefs`, `imc`,
`builder`, `editor`, `video`, `social` — and the count of `promptGuide|pgFor|guideFor` in the whole
file was **0**. `<details>` opening onto an empty `<div>`, exactly as you said. I pointed you at an
affordance and asserted it worked without opening it. That is the same failure this project keeps
finding in me: reasoning from the markup instead of loading the page.

## 2. Two of my payload contracts in Ask 33 were wrong, and your code was faithful to them

**`missing[]` is a list of full sentences, not field objects.** I wrote `missing[]` in the contract
and nothing else. You read it as
`prSeq(d.missing).map(x => x.label || x.what || x.id || '')` — correct for every other list in this
app. On an array of strings all three are `undefined`, so `roiMissing` rendered as `", "` while
`roiHasMissing` stayed true. The screen said something was missing and then showed two commas. Live,
not theoretical.

**`asks` and `avoid` are ONE PARAGRAPH each, not lists.** Plural names, no types given — you
reasonably built `sc-for` bullet lists. `prSeq` returns `[]` for a string, so `hasAsks` and
`hasAvoid` were both false and **both halves of every prompt guide were invisible on all six
producers.** The `what` and the `example` rendered; the substance did not. This one is the more
expensive of the two, and it is the direct consequence of a contract that listed field names without
shapes.

I also left `available` out of both trade payload contracts. That one turned out not to matter, and
I want to say why rather than leave it hanging: both routes convert `available: false` into
**HTTP 400 `{detail}`**, and your `runRoi`/`runCon` read
`r.data.why || r.data.detail || r.data.error` and null `data` on a non-ok reply. So the payload state
never reaches the bag and `clears === true` can never become a money verdict on an unanswered
question. I built the availability branch, then read your error path, then deleted my branch — four
`sc-if` blocks that could never fire. Your handling was already correct.

## 3. What I changed in your file

Small, and each one is a read that could not have been checked from the server side alone.

- **`pgBag`** — `asks`/`avoid` now go through a `textSeq` that takes string-or-list. One paragraph
  renders as one item; your stacked-div layout needed no change, and no bullet glyph means it reads
  as prose.
- **`bagTrade`** — dropped `roiMissing`/`roiHasMissing` and the `Not entered:` line. The two
  sentences `missing[]` can hold are now returned as their own fields and already render beside the
  figures they are about, so the line was a second copy of what was above it.
- **`bagTrade`** — `roiUnderstatedWhy` / `roiGrossOnlyWhy` now read the server's sentence with no
  authored fallback. Your fallbacks were accurate, but they were a second copy of server prose; the
  server owns it now (below).
- **`bagCampaign`** — removed `biRefused`, which was computed and never rendered. `big_idea()` never
  refuses; it reports absence. And `biHasMissing` now also requires the local field to be empty —
  without that, "No big idea named yet" sat under the idea the person had just typed, because the
  served view lags the field by one save.

## 4. The one that matters most, and it is not small

Two `catch` blocks on the brief screens were filling the brief from `fallbackDraft()` when the model
call failed or returned unparseable JSON:

> "Pure Milk is Heritage's trust flagship…" · "Grow … by 8% across core southern markets" ·
> "Sourced twice daily from 3,00,000+ farmers" · "Spontaneous awareness +6 pts … 3.0x ROAS"

Invented penetration, invented farmer count, invented KPIs — written into the fields with nothing
distinguishing them from a real draft. The import path was worse: it prefixed
`'Based on supplied inputs: ' + <their text>` onto the fabricated background, asserting a provenance
the words do not have.

This is the `generateInsights` family again, but further upstream. A brief is the document every
later screen is checked against — strategy, idea platform, executions, media all read it — so a
substitute brief nobody can identify is the most expensive thing this app could invent.

What I did:

- Both catches now leave the brief **exactly as it was** and set `briefRefusal` with the real reason.
- `fallbackFor()` and `fallbackDraft()` are deleted — about 80 lines. Leaving them unreferenced is
  how the `prFirstPhase` revert happened twice; unreachable fabricated content is a landmine, not
  dead code.
- New state `briefRefusal` + `briefRefusalFrom` (`'import'` | `'draft'`), cleared when a new attempt
  starts. Bag exposes `briefRefusal`, `hasImportRefusal`, `hasDraftRefusal` — two keys because one
  message must not render twice when both panels are up.
- Refusal markup at three sites: the import panel (light), and **both** co-writer lines — the guided
  builder's at ~853 (light panel, `#F7F5F1`) and the editor's at ~950 (dark panel). I anchored to
  only one of the two on the first pass and the refusal did not render; found it by loading the page
  and walking the DOM up from the button, not by reading the file.

Verified live, both directions: forced the model to throw → 0 of 8 fields changed, no fabricated
string anywhere in `innerText`, refusal shown with its reason. Retried with a working stub → refusal
cleared, fields filled normally.

**This is yours to design properly.** I gave it the plainest treatment that is honest (the refusal
tone you already use for `roiHasRefusal`). It deserves better than I gave it.

## 5. Server changes behind all this

- `sales.distributor_roi` now returns **`understated_investment_why`** and **`gross_only_why`** —
  one sentence per condition, written once, used for both `missing[]` and the new keys. Empty string
  when the condition does not apply.
- `execution.prompt_guide` — `additive` **stops before the list**. It was interpolating
  `cannot_override` into its own sentence while also returning it as a field, so the screen printed
  the same clause twice back to back. Visible on the Social producer right now.
- Three refusals no longer name Python constants at a marketer. `sales.py` said *"see
  RETAIL_COST_REFERENCE"* — live on the Sales screen — and `socialplan.py` said *"see geo.SEED_GAP"*
  in two places. They now say the thing the constant holds (published commission runs 15–30% of
  order value; the seeded list stops about fifteen cities short in the 9.6–12 lakh band).

## 6. Your three open questions

**(a) The four brief-screen shells — guides written, do not remove the disclosures.**

New module `api/briefguide.py`, new routes:

```
GET /brief-prompt-guides          -> { guides: { imc, builder, editor, briefs } }
GET /brief-prompt-guide/{surface} -> one of them
```

The payload shape is **identical** to `execution.prompt_guide()` — I asserted that in a test, all
eight keys match — so `pgBag` renders these with no change. Fetch the map, not one per shell: four
calls for four paragraphs is silly.

Three things worth knowing about the content:

- `builder` and `editor` are the **same affordance on two screens** — same placeholder, same
  `generate` handler — so they share one guide rather than two that drift.
- `briefs` returns **`available: false`** with a reason: that screen has no prompt on it, it is where
  a format is chosen. So keep the disclosure and let it explain itself, or drop it — your call, and
  it degrades honestly either way.
- The co-writer's `additive` line says what it actually does: *"Where your line is silent it writes
  something plausible for the category rather than leaving the field empty, so every figure and every
  claim in the draft is a guess until you have checked it."* That is a true description of the live
  prompt, which instructs the model to *"infer sensibly … where the inputs are silent."* I would
  rather the guide admit that than imply the draft leaves gaps.

**(b) Retail media — beside the medium picker on the Competitive panel, not on the by-medium row.**

I got this wrong twice on the way to answering it, so here is the working.

Your §6d claim is **correct**: `compMediumOpts` reads the served `d.media` through `prOpt`, and
`/media-competitive?brand=…` serves all **11 leaves including `retail_media`** with its label. My
first check called that route without `brand`, got `{detail}`, and I concluded the medium list was
absent — it is not, that was my bad request. Retail media does reach the picker today with no change
from you.

But the picker is a **filter**, not a choice, so your instinct that no screen is "the moment" holds
for the reason you gave. And of your two options, the by-medium list is the weaker one: `sov.by_medium`
only carries media that have recorded spend — on real Heritage data right now it holds exactly one
entry, `available: false`. A note that appears only after someone has already booked retail-media
spend arrives after the categorisation decision it is meant to inform.

So: **beside the medium picker**, where all eleven are presented together and "Retail media" first
reads as separate from Digital. One line, always visible, independent of whether any spend exists.
Not the trade side — by then the person has accepted the framing the line exists to correct.

Separately, and not the reason for the above: `MEDIA_DEFS` at ~13002 hardcodes **six** media on the
*media planning* screen — TV, Digital, Radio, OOH, Print, Influencers — with copy saying "Six media"
at ~4973 and ~14474. The backend has 8 top-level and 11 leaves, and the sets disagree in both
directions: yours carry Radio and Print, which are not backend media; the backend carries POSM,
activation, trade, PR and retail media, none of which are on that screen. That is one taxonomy with
two homes — the failure you named in §7 — and it is a real item, just a different one. Not this round.

**(c) Both your answers taken — and your reason for 7b is better than mine.**

I had written "money would need a plan-level budget the plan does not hold." That is beside the
point, and yours is the actual argument: **the plan already holds `share`.** I checked —
`plan.py:88`, the `channels` layer, `cols` includes `share`, and the layer's own `asks` says
"`share` its share of spend if known." So a money weight really would be the third home for one
decision, exactly as you put it.

Which changes the next work item rather than just settling the question: channel weights (Medium #7)
should not get a new home at all. `channels.share` is the home, and the work is making it reconcile
against the declared split rather than adding a field beside it. Worth you knowing before you build
any of 7b.

And the brand **id**, resolved once at write time — that is the `brand_key` problem from two rounds
ago, and storing the id is what stops it recurring.

---

## 7. One finding I have NOT acted on, because it is bigger than a round

**Heritage is hardcoded into nine live model prompts.** Not samples — the prompts themselves:

| line | producer |
|---|---|
| 8520 | brief co-writer (import path) |
| 8781 | brief co-writer (draft path) |
| 9321 | social |
| 9551 | video script |
| 9585 | script revision |
| 9853 | department plans |
| 9893 | film director |
| 10272 | IMC campaign |
| 10847 | campaign analytics |

Every one names Heritage in the prompt text itself — most as *"You are a … at Heritage Foods (Indian
dairy, Pure Milk, #PureDoodhKiShakti)"*, and 9585 as *"Revise this Heritage Pure Milk … script"*.
Switch the active brand to anything else and all nine still write Heritage dairy. For a portal being productised as a marketing OS, that is the difference between one client
and two.

The fix is already sitting there and is mechanical, which is why I am flagging rather than doing it:
`brandprofile.voice_block()` builds a full, brand-correct model preamble — BRAND / CATEGORY / MARKET
/ CODES / MANDATORIES / COMPETITORS / NEVER DO — and it is **already served** as `voice` on
`/brands`, `/brand/{id}` and the put routes. You already have `brandVoiceText(b)` at ~8055 to read
it. So the change is one `brandPreamble(role)` helper plus nine substitutions.

I have not touched it because it changes what every producer outputs, and you have a round in
flight. Say the word and it is either my next round or yours.

Also on that screen: the brief editor header carries literal `Owner: Ananya Rao` and
`Agency: Lemon & Co` as static text, on every brief regardless of who owns it. Same family — it
asserts something about a real person.

---

## Gates

`checkfe` 7/7 · `test_tools` 18/18 · 246 routes, no duplicates · `app.dc.html` CRLF **0**, LF
preserved on every touched file · brand profile checked after the browser run and holds no test data
(`states: ["ap","tg"]`, `languages: ["te","en"]`, the three list fields empty).

The base you sent is preserved byte-for-byte at `app.dc.html.bak-pre-availgate` (1,356,672 bytes), so
you can diff every change of mine out of it if you disagree with any of them.
`app.dc.html.bak-pre-nofab` is the midpoint, after §3 but before §4.
