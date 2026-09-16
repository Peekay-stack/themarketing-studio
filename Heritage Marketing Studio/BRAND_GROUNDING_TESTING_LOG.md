# Brand grounding modes — user testing log

Running log of user-testing feedback on the Grounded/Independent toggle (BRAND_GROUNDING_MODES_PLAN.md)
and what was done about each round. One entry per round of feedback, in order. Updated after every
round — do not renumber or rewrite past entries, only append.

---

## Round 1

**Feedback (verbatim, with screenshots PIC 1–4):**

> PIC 1,2,3 - The toggle button doesnt seem to be working - both in the header chip and the studio
> settings, when grounded is on - shows heritage; when general is on shows heritage as well. I went
> back to the IMC brief after drafting one with Grounded on and it showed the same text written in
> the prompt, brand and category fields (see PIC 4)

Screenshots showed: the header brand chip ("Heritage Foods") unchanged across both toggle states; the
Studio Settings brand-switcher dropdown (Heritage Foods/Kumkum/Loomwell/Parle G/Sthir) also unchanged;
and the IMC Brief screen's "Describe the brief" / Brand / Category fields still carrying the same
"heritage" / "Heritage" / "Dairy" content after switching to General.

**Root causes found:**
1. The header brand *chip* and the Studio Settings brand *switcher* are a different control (which
   brand is active) from the Grounded/General toggle (whether this piece of work uses that brand) —
   not a bug, but confusing to see side by side with no visual distinction.
2. A real, separate bug: the IMC Brief's own "Draft/Redraft with AI" button calls `/brand-brief-draft`
   → `brief_ai.py`, a completely different code path from the guided Brief Builder's drafting flow.
   It had never been wired to the Grounded/General toggle at all, so flipping the toggle changed
   nothing for this screen — the Brand/Category fields kept sending their typed content regardless,
   and `brief_ai.py`'s own prompt told the model to *"(infer from the ask)"* whenever the Brand field
   was empty, which is the exact behavior that had already been flagged earlier in the project as the
   root cause of a brief inventing "India's favorite Biscuit" as a brand name it was never given.

**Fixed:**
- `draftBrief()` now sends `brand_mode` to `/brand-brief-draft`, and forces `brand:''` in General mode
  regardless of what the field shows.
- `brief_ai.py`'s prompt no longer falls back to "(infer from the ask)" for the brand name in General
  mode — it now explicitly tells the model not to invent or infer one. Verified live: a real draft
  call with brand/category blank came back `"[BRAND NAME REQUIRED — none supplied; this is a
  category-level glucose biscuit template]"` instead of confidently inventing a name.
- Switching to General now clears the IMC screen's own Brand/Category fields (confirmed via direct
  DOM check) — the prompt textarea is deliberately left alone, since it's the person's own analysis
  request, not a brand fact.
- Server-side enforcement added too (`/brand-brief-draft` forces `brand:''` when `brand_mode=general`),
  not just trusted from the client.
- Renamed the toggle's off-state label from "General" to "Independent" everywhere (button text only;
  the internal state value stayed `general`), per a mid-turn request in this same round.

---

## Round 2

**Feedback (verbatim, with screenshots PIC 1–3):**

> PIC 1 - these 2 toggle switches don't sync. PIC 2 - add an "independent" profile in this also which
> moves when the toggle switch is changed to independent. PIC 3 - after toggling from grounded to
> independent - the brand and category went black but the prompt continued to be the same as before

PIC 1 showed the header's toggle pill and the IMC screen's own local toggle pill, visible on the same
screen, showing different states. PIC 2 showed the Studio Settings brand-switcher dropdown, asking for
an "Independent" entry to appear in that same list, with the active marker moving to it when selected.
PIC 3 confirmed Round 1's fix (Brand/Category cleared) while noting the prompt field stayed as-is.

**Decision needed and asked directly** (via a clarifying question, since a wrong guess meant rebuilding
across 4 tabs): should the header pill and each tab's own pill be (a) collapsed into one master
toggle, (b) kept separate but only one shown at a time, or (c) kept separate with better labelling —
and should picking a real brand from the dropdown auto-switch back to Grounded?

**User's answers:** One master toggle only. Yes, picking a real brand auto-switches back to Grounded.

**Fixed:**
- Collapsed four separate toggle states (`briefBrandMode`, `houseBrandMode`, `planBrandMode`,
  `producerBrandMode`) into **one** — `producerBrandMode` — read and written everywhere (Brief,
  Strategy/House, Plan, every Producer).
- Removed all 6 per-tab pill UI blocks (Brief Builder, IMC screen, House create-form, House opened
  screen, Plan create-form, Plan opened screen) — the header pill is now the only one anywhere.
- Removed the now-dead `setBriefBrandMode`/`setHouseBrandMode`/`setPlanBrandMode` functions and their
  bag values; folded their side effects (IMC field clearing, syncing an opened house/plan's own stored
  mode) into the one remaining setter.
- Added "Independent work" as a real, selectable row in the header's brand-switcher dropdown, styled
  and behaving exactly like a brand row (shows "Active"/"Switch", moves when the mode changes). Does
  not call `/brand-active` — the real active brand underneath is untouched.
- Fixed `switchBrand`'s edge case: clicking a brand that's already active server-side (the normal case
  when Independent is on with some brand still active underneath) used to no-op entirely; now it
  correctly snaps the mode back to Grounded even though the active brand itself doesn't change.
- The header chip itself now shows "Independent — no brand attached" (distinct styling) instead of
  continuing to show the previously-active brand's name while Independent is selected.
- Verified live end to end: toggled via the dropdown, confirmed the chip/pill/dropdown all agree at
  every step, confirmed only one pill exists anywhere in the UI (checked on the IMC screen
  specifically, the origin of Round 1's report).

**Still open from PIC 3**: the prompt field is left untouched on purpose when switching to
Independent — flagged to the user as a deliberate choice, not confirmed as final. Revisit if they say
otherwise.

---

## Round 3

**Feedback (verbatim, with screenshots PIC 1–2):**

> PIC 1 independent this is fine and this happens inthe studio setting also - great. PIC 2 Grounded -
> should the brand name and category not appear here automatically ? - or it is a company field at
> header chip level and brand name still needs to be entered? How are we treating this (header panel,
> studio settings and brand profile and the toggle switch for 1. one company-Multi brands 2. 1
> company 1 brand . For the previous changes, i hope the backend are also suitably wired?

PIC 1 confirmed Round 2's fix working correctly, including in Studio Settings. PIC 2 showed the IMC
Brief screen in Grounded mode with Brand/Category fields sitting empty despite Heritage Foods being
the active brand — a real gap, not a misunderstanding: nothing had ever auto-filled these fields from
the active profile, in either mode, since the screen was first built.

**Fixed:**
- Opening the IMC screen while Grounded now pre-fills Brand/Category from the active brand's own
  `name`/`category` — only when both fields are still blank, so an in-progress draft or a deliberate
  override is never overwritten by revisiting the screen.
- Switching back to Grounded from Independent does the same fill (symmetric to Round 1/2's "clear on
  the way into Independent").
- Switching to a *different* active brand via the header/Studio Settings now overwrites Brand/Category
  to match the new brand — deliberately overwrites rather than only-fill-when-blank, since choosing a
  different brand is exactly the "no, a different one now" case (matches `switchBrand`'s own existing
  aggressive-reset pattern for every other piece of stale per-brand state).
- Verified live: fresh IMC screen showed "Heritage Foods" / "Dairy — milk, curd, and value-added
  dairy" pre-filled with zero typing; switching the active brand to Parle G updated both fields to
  "Parle G" / "Biscuits — glucose, mass-market (₹5 price point)" immediately.

**Answered, not a code change** — the mental model for header chip / Studio Settings / brand profile /
toggle, and confirmation that the backend for Rounds 1–2 is genuinely wired (not just UI): see the
reply in-conversation. Summary: the header chip + Studio Settings' switcher are ONE concept (which
brand profile is active — works the same whether a tenant holds one brand or several); the toggle is
a second, independent concept (does this piece of work use that active profile, or none at all); the
brand *profile* screen is where the underlying facts live and get edited. Nothing about this changes
between a single-brand and a multi-brand tenant — a single-brand tenant just never has a reason to use
the "Switch" links, since there's only ever one row plus "Independent work."

---

## Round 4

**Feedback (verbatim, across two messages, the second after a session pause):**

> 1. When I changed from grounded to independent, on the IMC brief screen, the brand field went
> blank, but the prompt continued to be the same as before and the button below still said
> "Re-draft with AI" and not "Draft with AI"
> 2. After the brief "independent" was still on but when i moved to the next tab - strategy - it
> toggled back to grounded. i swtiched it back to "independent" - however, when I entered brand
> details - pulled a brief then moved to core message, then again it toggled back to grounded...
> How do you suggest we handle this?

**Root causes found (two separate bugs):**

1. **Bug 1 — stale draft state on toggle.** Switching modes cleared the IMC screen's Brand/Category
   fields (Round 3's fix) but never touched `im.draft`/`im.status`/`im.message`. So a screen that had
   already been drafted kept showing "↻ Redraft with AI" and the old drafted content underneath, even
   though the fields above now read as if nothing had been entered — internally inconsistent, and
   exactly what was reported.
2. **Bug 2 — `pickBrief` silently flipping the toggle.** The user's own described sequence ("pulled a
   brief then moved to core message, then again it toggled back to grounded") is **one** root cause,
   not two: Round 2's toggle-sync had been added to all five branches of `pickBrief` (Brief/House/
   Idea/Plan/else), reading the picked brief's own `brand_mode` and pushing it onto the master toggle.
   Nearly every brief on file predates this feature and defaults to `grounded`, so pulling almost any
   real brief while Independent silently snapped the toggle back — which is also why it looked like it
   "happened again" on the next tab: the house had already been created in grounded mode because the
   toggle had already flipped before creation ran, not a second bug on the Strategy tab itself.

The distinction that resolved it: `enterHouse`/`enterPlan` (opening a house/plan that **already
exists**, with its own recorded `brand_mode`) legitimately sync the toggle to reflect that document's
own decided truth. `pickBrief` (pulling a brief's *text* into a house/plan/producer piece that does
**not exist yet**) has nothing whose truth needs reflecting — there is no document yet, only the
person's own current, deliberate toggle choice, which pulling in reference text should not override.

**Fixed:**
- `setProducerBrandMode` now also clears `im.draft:null, im.status:'idle', im.message:''` on every
  mode change (either direction), not just Brand/Category. No data loss: `/brand-brief-draft` already
  auto-saves every draft to the brief library server-side on generation, and `draftBrief()` never sends
  a `brief_id` in its payload, so clearing `im.draft` client-side can't cause an upsert collision.
- Removed the `producerBrandMode: mode` sync from all 5 branches of `pickBrief` (Brief/House/Idea/
  Plan/else) — picking a brief now only pulls its text in, never touches the toggle. Confirmed via grep
  that `enterHouse`'s/`enterPlan`'s own sync (correct, since those open an already-decided document)
  was left untouched, and that no other `.brandMode`/`snap.brandMode` references were left dangling.
- Validated: `tools/checkfe.py` all 8 checks passed; LF/NULL-byte scan clean (CRLF:0, lone CR:0,
  NULL:0).
- **Live-verified end to end (15 Sep) in the running app**, not just by reading the code:
  - Started a fresh IMC brief in Grounded (fields auto-filled "Heritage Foods" / "Dairy — milk, curd,
    and value-added dairy" per Round 3), used "Or fill it in manually" to populate a draft — button
    correctly read "↻ Redraft with AI". Switched Grounded → Independent: button reverted to "✦ Draft
    brief with AI" and both fields cleared to `""`, confirmed via direct DOM read of the button text
    and the `#imc-b`/`#imc-c` input values.
  - Saved that Grounded-mode draft to the brief library (a real test document, `Heritage Foods — IMC
    brief`, id `6e667d80e2`, deleted again after the test). Opened Strategy, switched to Independent,
    clicked "Start a house" → "Pull from a brief" and picked that grounded Heritage Foods brief.
    Confirmed via DOM read: the header still showed **Independent** active (chip reads "—", not a
    brand name) and the house panel showed "Heritage Foods — IMC brief · pulled from the brief
    library" — the brief's text came in as intended, without touching the toggle.

**Not yet re-confirmed with the user**: removing the `pickBrief` sync entirely (rather than some other
resolution, e.g. asking before overriding) was a judgment call made from the `enterHouse`/`enterPlan`
vs. `pickBrief` distinction above, not a design question put back to the user the way Round 2's
4-vs-1-toggle question was. Flagged here in case they'd rather it worked differently.

---

## Round 5

**Not a bug report** — the user asked directly for an audit: "find out similar error in other tabs as
well — producers - social, video, POSM, on ground and PR" (report first), then, after the report,
"Fix all of them the same way, one pass and also check the other tabs, though not fully developped yet
but... i would like this to be the default on all tabs, sub tabs and layers."

**What the audit found:** Round 4's fix only ever cleared the IMC screen's own `im.draft`/`status`.
Every other generation surface keeps its own "already drafted" state with its own Redraft/Regenerate
label driven purely by whether that state is non-empty — none of it knew the mode underneath had just
changed. Confirmed present in: Social (`posts`), Carousel (`carousel.routes`/`concept`/`slides`),
Video (`videoConcept`, `fullScript`, every department's `shoot[id]` card, `sceneFrames`, the cast
reference frame), POSM (`pm.options`/`scamps`/`images`/every rendered piece), Onground (`og.ideas`),
PR (the release sub-tool's `release`/`rel`/`relStatus`), and two upstream surfaces not in the original
five: the Idea Platform (`idea.line`/`options`) and the guided Brief Builder used by Media/Digital/
Packaging/PD/PR-format (`state.brief`, via the same `hasContent()`-driven label pattern). The other
bug class from Round 4 (a picker silently flipping the toggle) did **not** recur anywhere else — the
only writers of `producerBrandMode` are the toggle's own setter, `switchBrand`, `enterHouse`/
`enterPlan`, and the already-fixed `pickBrief`.

**Fixed:** `setProducerBrandMode` now clears the AI-generated output on every one of those surfaces,
in the same single pass, on every toggle flip. The rule applied everywhere: the **output** goes,
whatever the person actually **typed** (a prompt, a note, an asset pick) stays.

**A real regression caught by live-testing the fix itself, not by the user:** the first pass reset
`posm`/`og`/`idea` to `null` outright, reasoning that their own accessors already fall back to an
empty shape. Live-tested against Onground: typed a prompt into the activation-idea box, generated real
ideas, switched to Independent — the button correctly reverted to "Generate ideas for me", but the
typed prompt was gone too, because it lives in that same `og` object and a blind reset doesn't know
the difference between a person's words and the model's. This is the exact class of bug this round
exists to fix, just self-inflicted. Rebuilt `idea`/`posm`/`og` as field-by-field clears instead (same
discipline already used for `pr`), re-tested the same way: typed prompt survived, generated ideas and
the button label both correctly reset.

**Deliberately not touched, flagged rather than silently skipped:**
- `state.campaign` — the Idea Platform's own ladder/roles/posts/video handoff hub. Server-persisted
  with its own id and lifecycle, same shape as House/Plan, not an in-progress client draft — needs
  their open-time-sync-plus-backend-route treatment, not a blind client reset.
- House/Plan's per-layer generated-but-uncommitted suggestion rows (`pGenerateLayer`/
  `hGenerateLayer`'s output, merged in via `applyHouse`/`applyPlan`). House/Plan already get
  `/house-brand-mode`/`/plan-brand-mode` server correction on toggle flip (Round 4); whether that also
  invalidates stale unchosen layer suggestions is a backend question, not verified either way.
- Brand-character drafting — checked and confirmed unaffected: `draftCharacter` always requires an
  active brand and never reads `producerBrandMode` at all, so Independent mode doesn't apply to it.
- PR's other rooms (media map, crisis log, coverage record) — left alone on purpose; those are running
  records, not disposable AI drafts the way the release sub-tool's output is.

**Validated:** `tools/checkfe.py` all 8 checks passed (both before and after the regression fix); LF/
NULL-byte scan clean. **Live-verified** two producers end to end with real generation calls: Social
(generated real posts in Grounded, switched to Independent — button reverted "Regenerate" → "Generate
posts", posts cleared) and Onground (generated real ideas in Grounded with a typed prompt, switched to
Independent — button reverted, ideas cleared, **and the typed prompt survived**, confirming the
regression fix). PR-release, Carousel, Idea Platform and the guided Brief Builder were fixed with the
same reviewed, field-by-field pattern and passed static checks, but were not each individually
live-tested with a real generation call in this round.

**Follow-up same day — Video and POSM live-tested on request** ("Live-test video and POSM too"):
- **Video**: picked an objective, typed a brief ("open on a steel glass of milk at dawn"), generated a
  real concept in Grounded — button read "↻ Regenerate concept". Switched to Independent: button
  reverted to "✦ Generate concept", the drafted logline/scene card was gone from the page entirely
  (not just the label), and the typed brief was untouched.
- **POSM**: typed a key-visual brief ("a hero shot of the pack against a dawn kitchen counter"),
  clicked "Develop key visual" in Grounded — got back a real route ("a single tall glass of freshly
  poured product mid-splash…", tagged "Fresh-poured metaphor") and the button read "Develop other
  routes"; Step 2 (Formats) correctly unlocked. Switched to Independent: button reverted to "Develop
  key visual", the generated route/key-visual card was gone, Step 2 correctly re-locked ("Locked until
  a key visual is chosen"), and the typed brief was still there under "FROM TYPED HERE".

**Second follow-up same day — PR-release and Carousel live-tested on request** ("Live-test PR-release
and Carousel too"):
- **Carousel**: typed a brief ("a five-slide story on why fresh milk matters every morning"), clicked
  "Generate carousel concepts" in Grounded — got back three real routes ("The Morning Race", "5 Signs
  Your Milk Isn't Fresh", "The Breakfast That Changed") and the button read "↻ Redraft concepts".
  Switched to Independent: button reverted to "✦ Generate carousel concepts", all three concept cards
  were gone from the page, and the typed brief was still there.
- **PR-release**: opened a real campaign-PR sheet (Heritage Foods · launch), clicked "Draft with AI"
  in Grounded — every release field filled with real, brand-specific press-register copy ("Heritage
  Foods says 500 dairy professionals check its milk daily before 7 a.m.", a Hyderabad dateline, a full
  who/what/when/where/why, quote and boilerplate). Switched to Independent: the release didn't just go
  blank, the whole sub-tool reset to its pre-start state ("No release on this sheet yet — Start the
  release"), confirming `relStatus` (not just `rel`) drives the section's visibility. Clicked "Start
  the release" fresh in Independent — every field came back genuinely empty, no leftover Grounded-mode
  copy.

All six of the originally-flagged producers plus the two upstream surfaces are now live-verified end
to end.

**Third follow-up same day — the guided Brief Builder live-tested on request** ("Live-test the Brief
Builder too"): opened a fresh Media-format brief (a format whose `formatDefaults` pre-seeds
Deliverables/Budget with template text, so the button already read "Redraft" before anything was
typed — a pre-existing `hasContent()` quirk, not something this round introduced or changed). Typed a
real ask into the AI co-writer ("a Diwali media push for Heritage milk across South India") and
clicked Redraft in Grounded — Background and Business objective filled with real, festive/South-India-
specific copy. Switched to Independent: Background and Business objective went back to empty,
Deliverables and Budget went back to exactly their original template seed text (not blanked — matching
`formatDefaults('media')` verbatim, confirming the reset target is right, not just "some text gone"),
and the typed ask was untouched.

Every surface from the original audit that the user asked to be live-tested is now live-verified end
to end with a real generation call: Social, Carousel, Video, POSM, Onground, PR-release and the guided
Brief Builder. The Idea Platform is fixed with the same reviewed, field-by-field pattern and passed
static checks, but was not itself separately exercised with a live generation call in this round —
noted so it's not overstated as proven.

---

## Round 5, continued — Idea Platform live-tested on request

**Request:** "Live-test the Idea Platform too."

**A second, more serious version of the og.idea mistake, caught before testing did any damage:**
opening the real Idea Platform screen to test it landed on an actual production-like record — "The
Head Start", a fully **adopted** platform (name, line, two test verdicts, five language translations,
seven activation-idea drafts across the producers). Adopting a platform calls `adoptIdea()` →
`POST /idea-platform` and gets back a real server id — which makes it a saved document, the same tier
as House/Plan/Campaign, not an in-progress client draft the way `im.draft` is. The fix as shipped in
the first Round 5 pass would have wiped this adopted platform's `line` and `name` — the actual decided
creative work seven other drafts point back to — the instant anyone touched the toggle, with no
warning and no way back, on real data, not a disposable test fixture. This is worse than the og.idea
regression: that one lost an in-progress creative brief nobody had committed to; this one would have
lost a decision already built on.

**Fixed before any toggle was tested against it:** `idea` now checks `curIdea.adopted` first — an
adopted platform is left completely untouched (same treatment as `state.campaign`, House and Plan);
only an unadopted, still-in-review draft gets the field-by-field clear.

**Live-verified:** read "The Head Start"'s name and line, switched Grounded → Independent, re-read
them — byte-identical, `adopted` still true. Deliberately did not push further into generating fresh
content against this same real record (a "Redraft from these sources" call would have added genuine
candidate options to production-like data for no proportionate benefit once the critical case was
proven safe). Tried to reach a disposable, never-adopted platform to also re-confirm the ordinary
clearing path live — opened a different, undecided house ("0 of 8 layers decided") expecting an empty
platform, but the Idea Platform turned out not to be house-scoped on the frontend (`state.idea` is one
global slot, not nested per house/plan id — a pre-existing fact about the data model, not something
this round changed or needs to fix) — so the same adopted "Head Start" record reappeared there too, no
disposable "fresh" state was reachable in this tenant this way. The unadopted-draft branch itself is
unchanged from the first Round 5 pass and reuses the exact same conditional-clear pattern already
live-proven on five other producers (Social, Video, POSM, Onground, Carousel) — code-reviewed and
passing static checks, but not independently re-exercised live for this specific screen.

**Validated:** `tools/checkfe.py` all 8 checks passed after the adopted-platform fix; LF/NULL-byte scan
clean.

---

## Round 5, continued — Sales enabler live-tested on request

**Request:** "Live-test the Sales enabler tab too."

**A different finding from every other tab: nothing to clear, because nothing here is AI-generated
yet — the toggle is currently a no-op on this whole screen.** Traced the two backend routes this tab
could call:
- `/sales-element` → `sales.set_element()` — what the frontend's "Brief it first"/"Develop" button
  actually calls. Pure record-keeping: it saves whatever text the person typed, verbatim, and flips a
  status badge (not started → briefed → agreed). No AI call, no brand facts, no `brand_mode` — there is
  nothing here for a toggle to affect.
- `/sales-generate` → `sales.generate()` — the real AI-drafting route, and it **does** pull brand facts
  unconditionally: `prompt_for()` builds every prompt with `brandprofile.voice_block(brandprofile.resolve(house, s))`,
  no `brand_mode` parameter anywhere in the payload, no Independent-mode branch, no honest "don't
  invent a brand" fallback — the same shape as the `/brand-brief-draft` gap Round 1 found and fixed,
  and the same shape Stages 3–5 closed for House/Plan/every other producer. But **this route has no
  frontend caller at all** — grepped the whole of `app.dc.html`, zero matches for `/sales-generate` or
  any `seGenerate`-style function. It exists server-side and is simply not wired to any button yet.

**Live-verified the no-op empirically, not just from reading code:** typed a real note into a trade
element's brief box in Grounded ("moves fast, no fridge needed, easy resale"), clicked "Brief it first"
— saved verbatim, status flipped to "briefed", label to "Develop". Switched to Independent — text and
status both untouched, exactly as expected, since nothing here was ever brand-conditioned to begin
with. Cleaned up the test entry afterward via a direct `/sales-element` call (the UI itself won't let
you save an empty brief once one exists, by design) — confirmed reverted to `status: "not started"`.

**Not fixed, flagged instead — this is a different kind of gap than the rest of Round 5:** every other
fix this round was "clear stale output the same way IMC already does." This one is "an AI-generation
path with a real grounding leak exists in the backend but isn't reachable from the UI yet" — closer to
Round 1's `/brand-brief-draft` gap than to the stale-draft-label pattern. Fixing it means building new
frontend wiring (a real "Develop with AI" action calling `/sales-generate`) *and* threading
`brand_mode` through both the payload and `prompt_for()` before that wiring ships — new scope, not a
one-pass clear. Left for the user to decide whether to build now.

**Validated:** no code changed for this tab this round, so no new `checkfe.py`/byte-scan run was
needed — this was investigation and live-testing only.

---

## Round 6 — a real grounding leak, found live, checked across every producer, fixed in phases

**How this started:** testing item 3 of the user's own re-confirmation checklist ("where does
independent work get saved") on POS material surfaced something worse than a labelling gap. A real
`/posm-keyvisual` call, Independent selected, came back `"note": "Standing on the house's core
message."` with the actual message text ("Pure milk, strong family.") in the response — a real brand
fact, in a piece marked Independent, from a real API call, not stale state.

**Root cause, once traced:** the Grounded/Independent toggle had only ever gated **voice resolution**
(`brandprofile.resolve()`, `character.for_prompt()`) — never the separate mechanism that pulls a
*bound* house/platform/plan's actual content into a prompt. Two shapes of the same bug:
- An "empty string means don't filter" footgun (the same class already fixed once in `made.py` this
  session): `brand=None` (the General-mode signal) collapsed to `want=""`, which several lookup
  functions treated as "match anything" rather than "match nothing."
- Flat-out unconditional inclusion: `if house: out.append(house_block(...))` with no mode check at all.

**Asked to check breadth before fixing — findings, confirmed by direct code read:**

| Surface | Mechanism | Status found |
|---|---|---|
| POSM (key visual, scene) | `producers.stands_on()`, `producers._ctx()` | **leak, live-confirmed** |
| Onground (activation ideas, adjust, sharpen, elements) | same two functions, 8 call sites | leak (code) |
| Social (posts) + Video (script/concept) + everything via `/complete` | `prompts.house_block()`/`platform_block()`/`plan_channels_block()` via `_resolve_house()`'s `not want` | leak (code) — the shared chokepoint |
| Plan (layer generation) | `plan.prompt_for()`: unconditional `house_block(house, layer_id)` | leak (code) |
| PR (release drafting) | frontend `prDraftRelease()` never reads `producerBrandMode` at all | never wired — same class as Sales enabler, not a regression |
| Idea Platform draft (`/idea-draft`) | loads bound house's core message, no mode check | leak (code) |
| House's own layer generation | `strategy.prompt_for()` | **safe** — checks the house's own `brand_mode` directly, no cross-document lookup |
| IMC Brief / guided Brief Builder | already correct (Round 1, Round 5) | safe |
| Sales enabler | no AI wired to the UI at all | already flagged separately |

**Phase 1 (this round) — the shared chokepoints, requested and completed:**
- `prompts.py`: fixed `_resolve_house()` and `plan_channels_block()`'s identical `not want` bug — empty
  brand now returns nothing, not the newest house/plan in the tenant. Fixes Social + Video + every other
  `/complete` caller in one place.
- `producers.py`: `stands_on()` and `_ctx()` gained a real `brand_mode` check (independent of
  `use_house`/`use_platform`, which govern something else) that skips house/platform content outright
  when General. Threaded through all 6 functions that call them (`key_visual`, `carousel_concept`,
  `activation_ideas`, `adjust_activation_idea`, `sharpen_idea`, `element_brief`) and every one of their
  route handlers and frontend callers in `main.py`/`app.dc.html` — including `developKv` (POSM),
  `generateOgIdeas`/`adjustOgIdea`/`developIdea`/`developElement` (Onground), `generateCarouselRoutes`
  (Social carousel), and `loadSocialStandsOn`/`loadVideoStandsOn` (the "what this stands on" preview
  widgets), none of which had ever sent `brand_mode` before this.

**Live-verified against the exact case that found the bug:** the same "Develop key visual" call, no
typed brief, Independent selected, house still bound — now returns `"stands_on":{"text":"","source":""}`
and the honest `"Nothing to work from... These are the standard treatment routes, ungrounded."` note,
with three generic, brand-free treatment options. Onground: a real "Generate ideas for me" call with
nothing typed correctly 400s ("Nothing to build on..."); with a typed steer note it generates three
real, detailed activation ideas, every one tagged `"stands_on":"typed here"` (not the house or
platform), and the response's own top-level `stands_on` is empty — no brand name, no product claim,
nothing house-specific anywhere in the output.

**Validated:** `py_compile` on `main.py`/`producers.py`/`prompts.py`; `checkfe.py` all 8 checks passed;
LF/NULL-byte scan clean on `app.dc.html`.

**Not yet done — Phases 2 and 3, as scoped in the plan the user approved for Phase 1 only:**
- Phase 2: `plan.py`'s unconditional `house_block()` call in layer generation; `/idea-draft`'s
  unguarded house pull.
- Phase 3: PR's `prDraftRelease()` — needs real `brand_mode` wiring, not a fallback string (new wiring,
  same shape as Sales enabler, not a repair).
- One POSM route, `/posm-image` (the actual hero-cutout render, as opposed to `/posm-keyvisual`'s route
  options), had its backend `stands_on()` call fixed to respect `_posm_image_mode`, but no direct
  frontend caller of `/posm-image` was found in `app.dc.html` to confirm it sends `brand_mode` — likely
  reached indirectly or superseded by the studio-shot pipeline; not independently confirmed reachable
  from the UI, flagged rather than assumed fixed end-to-end.

---

## Round 7 — live-testing Phase 1 surfaced four new issues; all four fixed and verified

**The user tested Phase 1 directly** — Independent IMC brief drafts, Strategy/Plan pickers, a Plan's
Channels layer, and a Social carousel with a real pack shot selected — and reported back seven
screenshots plus two downloaded `.docx` files. Read all of it before touching anything, per the user's
own instruction, then proposed fixes; the user said "fix all 4."

**1 — IMC picker preview leaked the active brand's name (`imcSnapshot()`).** The two docx files and
PIC 1 turned out to be a real design question, not a bug: Independent mode has never (and structurally
should not) override a brand name the *person themselves* typed into the free-text prompt — the skill
correctly stopped inventing anything beyond what was asked, and the prompt asked for "Heritage master
brand" by name. Built a soft, dismissible warning instead of silently drafting it: a whole-word match
against any real brand on file, shown above the prompt only while Independent, explaining the
distinction rather than blocking. PIC 2's actual bug was separate and real: `imcSnapshot()` — the "your
current draft" preview that feeds the picker — fell back to `this.brandLabel()` (the active brand's
real name) whenever the draft's own brand field was blank, with no check on the toggle at all, and
never set `brand_mode` on the object it returned either. `saveImcBrief` right below it already had the
correct logic; the preview function just never got the same fix. Both fixed together in
`app.dc.html`. **Live-verified**: typed a prompt naming "Heritage" while Independent — the warning
correctly named "Heritage Foods" as the real brand on file; drafted anyway; the picker's top row now
reads "Independent — IMC Brief" with the Independent badge, no leaked brand name.

**2 — Plan's Channels layer left `channel`/`medium` blank on every row (PIC 4).** Real bug, but
pre-existing and unrelated to brand-grounding — confirmed it would happen in Grounded plans too. The
prompt told the model to pick "one medium from the served media list" in three places and that list
was never actually built or included anywhere in `plan.prompt_for()`. The model, correctly, would not
invent a channel/medium it had nothing real to choose from, and left both columns honestly blank while
still reasoning generally in Job/Measure/Side. Fixed in `plan.py`: `_column_rules()` now injects the
real seven-id vocabulary (`media.LEGACY_STRATEGY_MEDIA` — the same one the house's own medium layer
already uses) into the channels layer's instructions, and softened the old "not-one-medium option"
line (no such option exists in that vocabulary) to "leave it empty and say why" instead, consistent
with every other empty-cell rule already in the prompt. **Live-verified**: regenerated the exact Plan
layer from PIC 4 — banner now reads "6 OF 6 CHANNELS STATE A MEDIUM" and "6 OF 6 CHANNELS WEIGHTED".

**3 — Carousel pack shot rendered as garbled back-of-pack text, not the real front label (PIC 5–7).**
Traced with real evidence rather than guessing: confirmed the selected pack WAS reaching the image
model as a real reference (`pack_used: true`) by testing `/scene-still` directly — so this wasn't the
wiring gap it looked like. The actual cause was the prompt itself: `pack_clause` in `main.py` asked the
model to reproduce the pack "down to the fine print" — something no current image model can actually
do — while a separate instruction in the same prompt said "No on-screen text ... anywhere in the
frame," two instructions fighting each other. The result the user saw exactly matches that fight: the
back of the pack, nutrition panel facing camera, every word garbled nonsense ("Nutritioal Info",
"Calcoha tsited, Pleochet milk"). Rewrote the clause to ask for what the model can actually hold onto —
colour, proportions, overall label design, shown FRONT-ON so the brand mark reads clearly — and to
explicitly not fabricate legible fine print. **Live-verified** with the real signed-off pack shot
("heritage daily health pack shot.jpg", confirmed `signed_off: true` in the library manifest before
touching anything): two fresh carousel renders both show the pack front-on, "Heritage" and "Daily
Health Toned Milk" clearly legible, no garbled text.

**A live red herring during this same investigation, worth recording:** the first attempt to verify
fix 3 kept coming back `pack_used: false` despite everything about the frontend wiring checking out —
traced via a `fetch` monkey-patch to log the real outgoing request body, which showed `"brand_mode":
"general"`. Not a bug: the toggle had been left on Independent from the fix-1/2 verification, and
Independent mode correctly strips the pack reference by design (Round 6's own fix — only cast/character
is exempted, per the user's own scoped approval, not pack). Switching to Grounded and re-testing gave
the clean result above. Recorded so the same false alarm doesn't get chased again.

**Validated:** `py_compile` on `main.py`/`plan.py`; `checkfe.py` all 8 checks passed; LF/NULL-byte scan
clean on `app.dc.html`. All four fixes live-tested with real generation calls, not just code review.

## Round 8 — two follow-ups from Round 7: simplified IMC warning copy, Social's missing asset mechanism

Two small inputs from the user after reviewing Round 7's fixes. Both were presented as options/choices
first (via a direct question, not assumed), then built once the user picked.

**1 — IMC's Independent warning banner, simplified.** Round 7's fix 1 had built a whole-word
brand-name-match warning (only shown when the free-text prompt actually named a real brand on file).
The user asked for something simpler and offered draft wording; presented as an explicit choice between
that conditional/match-triggered version and an always-on generic reminder. **User picked the always-on
generic reminder.** Replaced the `imcPromptBrandHit` whole-word-match IIFE with a flat
`imcIndependent = s.producerBrandMode === 'general'` flag, and the banner now always reads: "The brief
is grounded entirely in what you write here — it takes nothing from the brand profile. Follow the
prompt guide to cover what the profile would otherwise supply." Shown whenever Independent is active,
regardless of prompt content. **Live-verified**: toggled Independent, opened "Start the IMC brief" —
banner text matches exactly.

**2 — Social's single-post generator had no pack/cast asset mechanism at all (PIC 2 from the last
round of screenshots).** Unlike POSM/Onground/Carousel, a single Social post's `/scene-still` call had
no way to point at a real signed-off pack or cast reference — every render came from a text description
only, in both Grounded and Independent mode, even when a real asset already existed in the library. The
user named two possible fixes (reuse the existing pack-pick mechanism like Carousel/other producers, or
allow a direct upload right in the frame) and asked which to build. **Recommended and the user
confirmed: reuse POSM's own pick-or-upload asset-card pattern** (one control, both a `<select>` of
existing signed-off items and a file `<input>` that uploads + auto-signs-off + auto-selects in one
step) rather than building a third, divergent picker shape. Added a new "Assets for these posts" card
to the Social single-post screen (pack shot pick/upload, plus a "recurring model/cast" checkbox that
reveals the same pick/upload pattern when checked), reusing `carouselAssetOptions()` as the options
source but writing to Social's own `socialPackChoice`/`socialCastChoice`/`socialWantCast` state fields
(deliberately not shared with Carousel's own picks — same "two controls, one real" precedent already
established elsewhere in this codebase). `fetchPostImages`/`regenerateVisuals` now send `pack_id`/
`cast_id` to `/scene-still` when set.

**Live-verified end-to-end with a real generation call**, not just code review: picked "heritage daily
health pack shot.jpg" from the new dropdown, typed an objective, generated posts on all three
platforms. A `fetch` monkey-patch confirmed all 9 `/scene-still` calls carried `pack_id: "34af1f8795"`
and `brand_mode: "grounded"`. Downloaded and viewed one of the actual rendered images: the bottle is
front-on, "Heritage" and "Daily Health Toned Milk" both clearly legible, no garbled text — confirming
the new picker and Round 7's `pack_clause` fix hold up together under a real render.

**A verification false trail during this round, worth recording:** the new card's text first tested as
"not found" via a `document.body.innerText` search immediately after navigating to the screen, while a
same-second `querySelectorAll`/`textContent` check on the same page found it fine. Root cause: the
card's section label is styled `text-transform:uppercase`, and `innerText` reflects the rendered
(transformed) case while `textContent` returns the literal DOM text — searching for the literal-case
string against `innerText` was doomed regardless of whether the markup was correct. Not a rendering bug;
confirmed by reading a large slice of `innerText` around the label and finding the uppercase version
sitting exactly where expected, in the right position on the page.

**Validated:** `checkfe.py` all 8 checks passed; LF/NULL-byte scan clean on `app.dc.html`. Both fixes
live-tested — the warning by reading the rendered banner text, the asset picker by a full real
generation call with network-body inspection and a visual check of the actual output image.

## Round 9 — pack reference rendered as the wrong container entirely (a bottle instead of a pouch)

**The user's feedback, with a screenshot of the real product:** "But daily health pack is like a pouch"
— the Round 8 Social asset-picker demo render (the one used to prove `pack_id` reached `/scene-still`
correctly) showed a milk bottle being poured into a glass. The real signed-off reference
("heritage daily health pack shot.jpg") is a sealed flexible plastic pouch, not a bottle at all.

**Root cause, confirmed by fetching and viewing the actual reference file**: Round 7's `pack_clause`
rewrite (the one that fixed the garbled fine-print bug) asked the model to preserve "colours,
proportions and overall label design" — everything printed *on* the pack — but never named the pack's
own physical form. With nothing pinning the container type, the model faithfully copied the logo,
colours and product name onto the wrong object: a poured glass bottle, the single most common visual
association for "milk" in its training data, rather than the reference's actual sealed pouch. This is
the same prompt/`pack_clause` in `main.py` fixed in Round 7 — the fix there was real but incomplete.

**Fix**: `pack_clause` now explicitly names the container type/format as something to reuse exactly
("pouch, bottle, carton, tub, jar — whichever the reference actually is, never substituted for a
different one"), on top of the existing colour/proportion/label/front-on instructions.

**Live-verified** with the same real pack reference (`pack_id: 34af1f8795`) via a direct `/scene-still`
call (`pack_used: true`, `from_reference: true`): the new render shows a hand holding the pack as a
soft flexible pouch — pinched corners, mid-pour — with "Heritage" and "Daily Health Toned Milk" both
legible and the correct green/white colourway. Matches the real product shape.

**Validated:** `py_compile` on `main.py` — passed. Server restarted (this route has no hot-reload, per
the project's standing gotcha) before testing.

## Round 10 — real user testing of Social's new asset picker surfaced three more issues, all fixed

The user ran the actual workflow this feature was built for: uploaded the pack shot, wrote a real
objective naming the pack and product by hand, generated 6 posts, then adjusted two of them. Reported
three distinct problems from that one session, all investigated and root-caused before any fix, per
the user's own request to report first — then approved all three at once ("Go ahead with all three").

**1 — 1 of 6 posts came back with visibly wrong/cropped dimensions.** Root-caused in code, not
guessed: `/scene-still` tries Google/Gemini first, then falls back to fal.ai if that fails; fal's own
second-tier fallback (a dedicated single-reference "character" model, used when its primary reference
model errors) hardcoded `image_size: "landscape_16_9"` in `creative.py`, ignoring whatever ratio the
caller actually asked for. A 1:1 request that fell all the way through to this path silently came back
16:9, and the post's square frame (`background-size:cover`) then cropped the sides off — exactly
matching the chopped-looking text badge the user saw. Fixed by reading the same `_IMAGE_SIZES` map the
primary fal path already uses, instead of a fixed default. This only bites the rare case that reaches
this specific fallback, so it wasn't reproducible on demand; the six posts regenerated during
verification all came back a clean 1024×1024.

**2 — Adjust drifted the product to a different real SKU ("Pure Milk" instead of "Daily Health"),
even after the user explicitly named the correct one in their note.** Root cause: neither
`generateSocial` nor `adjustPost`'s prompts ever told the model which specific pack/SKU was pinned by
reference — nothing anchored it, so the brand's own house/plan grounding (which centers the flagship
"Pure Milk" line) could and did pull the rewritten caption toward the wrong product, especially on
Adjust where a one-line note carries less weight than the grounding underneath it. Added
`socialAssetAnchor()` — names the exact pinned pack/cast asset by its real file name and says "never
rename it or describe a different product or SKU" — wired into both `generateSocial` and `adjustPost`'s
prompts so the fix applies at both entry points, not just the one that was reported.

**3 — "The entire image re-generates — new setting, new style, cast keeps changing" on every Adjust.**
Two compounding causes, both fixed: (a) the code decided whether to redo the image by checking
`data.visual !== post.visual` — but the LLM was asked to return `visual` every time regardless of
whether the note had anything to do with the image, and it essentially never reproduces a string
byte-for-byte, so this fired on nearly every adjustment including pure caption tweaks. Replaced with an
explicit `visual_changed` boolean the model is asked to judge directly (asking it to reproduce text
exactly was the wrong tool; asking it to judge intent is the right one), with the old string-diff kept
only as a fallback if the model omits the field. (b) When the image genuinely is being redone, the
previous render is now passed to `/scene-still` as an additional identity reference — reusing the
existing reference-image mechanism rather than a new one — so the same people carry across an
adjustment instead of being reinvented from nothing. Named as a partial fix, not a full scene-lock: the
reference mechanism is explicitly permitted to vary setting/camera by design (it's shared with Video's
"next shot of the same film" continuity), so this helps identity, not full framing.

**Live-verified end-to-end**, all three together: generated 6 real posts with the pack shot pinned
(anchor text confirmed reaching the `/complete` prompt verbatim); adjusted one post with a caption-only
note — zero `/scene-still` calls fired, confirming (3a) actually suppresses unwanted re-renders now;
adjusted the same post again with a genuine visual-change note — exactly one `/scene-still` call fired,
carrying both the correct `pack_id` and a `reference_url` pointing at the post's own previous render,
and the freshly-written visual/caption still correctly said "Heritage Daily Health Pack," not "Pure
Milk." The resulting image showed the same woman as the prior render (continuity working) holding a
correctly-labelled "Daily Health Pack" — though its container drifted from the pinned pouch shape to a
carton-like shape in this one instance. Recorded honestly rather than hidden: likely ordinary
generation variance (both references shown to the model were the correct pouch) rather than a
regression of Round 9's shape-fidelity fix, but not chased further this round since it wasn't one of
the three reported issues — worth watching if it recurs.

**Validated:** `py_compile` on `creative.py`; `checkfe.py` all 8 checks passed; LF/NULL-byte scan clean
on `app.dc.html`. Server restarted before testing (backend change, no hot-reload).

## Round 11 — a real Independent-mode leak found in a second, unaudited layer; the pack UX trap removed

The user tested Independent mode directly this time (not Grounded, unlike Round 10): toggled
Independent, uploaded the pack shot via the existing "Inputs to guide generation" uploader, wrote a
real objective naming the pack and product, generated 6 posts. Reported: the header showed Independent
but the panel below still displayed Heritage Foods's own palette/tone as if it were going into the
prompt, and the pack shot still wasn't honored at all. Investigated both before touching anything.

**1 — `brandPreamble()`, the shared preamble builder behind 8 different producers (both brief writers,
Social, Video's script writer and department heads, the campaign lead, measurement), only checked
Independent mode inside its "no brand configured at all" fallback branch — so it did nothing whenever
a real brand was actually active, which is the normal case.** Every Independent-mode call from any of
these 8 opened its prompt with "You are ... for Heritage Foods" plus the brand's full voice block,
regardless of the toggle. Confirmed live via a `window.claude.complete` monkey-patch: `brand_mode:
"general"` reached the call correctly, but the message content itself still named the brand — the
server-side gating this whole 10-round project built never got a real say once the client had already
opened with the brand's name. This predates and sits underneath every prior round's testing, because
Rounds 1–10 verified the *server-side* `/complete` route's own `brand_mode` handling directly, never
through this client-side prompt-builder specifically. Fixed: `allowGeneral` now wins outright, checked
before the active brand is even read, rather than only inside the fallback.

**2 — `inputsContext()` had the identical bug**, found in the same pass: it pulled the active brand's
voice/kit onto the "guidelines" toggle with zero `brand_mode` check. Same fix pattern applied. The
"Brand guidelines" chip itself was also lying — it stayed green and named the active brand regardless
of Independent, exactly the "looks like it worked" failure the code's own prior comment already warned
about for the no-brand case, just for a second case nobody had named. Now reads "Brand guidelines — off
while Independent" and says so in its own explanatory text when Independent is active.

**3 — the pack shot genuinely wasn't reaching the image**, confirmed as UX, not a fresh code bug:
`handleStudioUpload` (the "Inputs to guide generation" uploader the user reasonably used, since it's
the more prominent, pre-existing control) never actually uploads anything — it only remembers the
local file's NAME to mention as text ("Draw on these reference assets for style, tone and continuity:
heritage daily health pack shot.jpg"), never as a real photo reference. The real mechanism (Round 8's
"Assets for these posts" card, wired to `/scene-still`'s `pack_id`) sits further down the screen and
was confirmed still at "Not used in these posts." Per the user's direction ("remove the conflict... if
the attached pic is already wired, then remove the UX trap"): removed the "Upload images / clips"
button from Social's copy of the inputs panel specifically (Video's own copy is untouched — it has no
competing real mechanism, so no trap there), and added a plain-text note pointing at the real card.
The `guidelines` toggle and the `refs` chip-picker (mention an already-signed-off item by name) stay —
real, different, non-conflicting uses once (1) and (2) made them honest.

**Live-verified end-to-end**: reloaded, confirmed the panel now reads "Style and tone context for the
caption — not a photo reference. For the actual pack shot or cast photo used in the render, use
'Assets for these posts' below," no upload button present, chip reads "Brand guidelines — off while
Independent." Generated a real post in Independent mode with the same objective from the report — the
captured `/complete` prompt opened "You are a senior social media writer. No brand profile is attached
to this piece — do NOT invent a brand, category or product," with no "Heritage Foods" or "HERO PRODUCT"
anywhere in it.

**A separate, real, NOT-a-bug finding recorded rather than silently left unexplained**: the actual
generated captions still came back fully Heritage-voiced (tagline, hashtags, FSSAI/cold-chain claims) —
because the objective itself explicitly said "create a post for **heritage milk**," and Heritage is a
real brand the underlying model already knows from its own training, independent of anything this app
injects. Same tension Round 7 named and the user accepted for the IMC screen; Independent mode stops
this app from inventing facts, not from the model recalling real-world facts about a brand named in the
person's own words. Not closed this round — would need a deliberate design call (actively instructing
the model to suppress real-world knowledge of a named brand), not a quick fix.

**Also noted, not fixed**: the Palette/Tone display block (`kitAnything`/`kitColors`) still shows the
active brand's kit regardless of Independent — confirmed it's purely decorative (only read by display
markup, never by any prompt-building function; the prompt-relevant version, `brandKitContext()`, was
already gated in fix 2) — cosmetically stale next to the now-honest chip, not a functional leak, left
for the user to decide whether it's worth a follow-up.

**Validated:** `checkfe.py` all 8 checks passed; LF/NULL-byte scan clean on `app.dc.html`. No backend
files touched this round.

## Round 12 — the real explanation for "only 1/6 posts resembled the pack"; a design-choice option added

Continuing Round 11's investigation, the user reported two more things from a fresh Independent-mode
batch: the "Written against the house's core message" banner (already root-caused and fixed in Round
11's own write-up as display-only) and a new, more concrete finding — of 6 posts generated with the
real pack shot pinned, only 1 actually resembled it; the rest "read it from somewhere in the universe."

**Root cause, confirmed via network capture, not guessed: `/scene-still` was silently dropping the
pack reference on every call while Independent was active — even with an explicit `pack_id` picked
through the real asset card.** Every captured call came back `pack_used: false, references: 1` (cast
only). The code (`main.py`) stripped `pack`/`plate` unconditionally whenever `brand_mode == "general"`,
treating a pack the person explicitly picked exactly the same as an auto-attached "whatever's newest
for the active brand" one — but that blanket rule predates the asset picker and directly contradicts
the precedent already set for cast, which stays available in Independent specifically because "a
person explicitly attached it... is not invented brand voice." A pack picked through the asset card is
the same case. Fixed: an explicit `pack_id` that actually resolves now survives Independent mode; only
an auto-resolved pack (nothing explicit given) still gets stripped. The identical bug existed in
`/posm-scene` (POSM's integrated-scene lane, same asset-card pattern) and was fixed the same way.

**Live-verified**: a direct `/scene-still` call with `brand_mode:"general"` and the real pinned
`pack_id` now returns `pack_used: true` — the exact case that was silently failing before.

**A related idea the user raised, built as a new option**: give the pack dropdown an explicit "Let the
studio design one" choice for when no real pack photo exists yet, rather than the silent default of
saying nothing about the pack at all. Added: a new sentinel value in the dropdown, threaded through as
`pack_generate: true` (only meaningful when no real reference resolves — a real one always wins), and
a new prompt clause in `/scene-still` that explicitly tells the model to design a plausible pack rather
than leaving the product awkwardly absent, while refusing to fabricate specific on-pack claims or
certifications. Response now reports `pack_generated` alongside the existing `pack_used`. Live-tested:
the model designed an obviously-generic "Farm Fresh Milk" pack rather than guessing at what the real
Heritage pack looks like — a safe, non-misleading choice for a case that's explicitly asking for an
invented visual.

**A second frontend bug found and fixed while verifying the `/grounding` fix from Round 11**: even
though the server now returns an honest "This piece is Independent — nothing is grounding it" summary,
`socialGrounding()`'s own JS only ever trusted the server's `summary` field when `grounded` was `true`
— whenever `grounded` was `false` (exactly the Independent case), it discarded the server's real
sentence and substituted its own generic hardcoded text instead, silently swallowing Round 11's fix
before it could ever reach the screen. Fixed to use the server's summary whenever one is sent, keeping
`grounded` only for the banner's colour. Live-verified: the screen now reads "This piece is
Independent — nothing is grounding it but what you write here," reached from the real server summary.

**Validated:** `py_compile` on `main.py`; `checkfe.py` all 8 checks passed; LF/NULL-byte scan clean on
`app.dc.html`. Server restarted before testing (backend changes, no hot-reload).

## Round 13 — a wording fix, plus a clean re-verification of Round 12's pack fix

Two questions from the user after Round 12: what does "the producer is working from memory" actually
mean, and why didn't the pack show up in the first round for 2 of 3 posts — with a direct ask for what
literally reaches the image generator.

**Answered, not a bug**: "working from memory" checks a different layer entirely — whether "The plan
brief" or "The idea platform" is toggled on for this piece, unrelated to Grounded/Independent. With
neither on, the model has nothing studio-structured to draw from beyond the typed objective, so it
falls back on its own general training knowledge — an accurate, meaningful status. The one real issue:
the word "memory" collides with the app's own top-nav "Memory" tab (signed-off assets/ground truth),
a completely different concept. **Fixed**: reworded to "the producer works from general knowledge
alone, not the plan or platform" — same meaning, no collision.

**Re-verified Round 12's pack fix with a fresh batch**, reproducing the user's own scenario (Independent,
real pack pinned, a detailed family-scene prompt, 3 posts on one platform): all 3 calls came back
`pack_used: true`, and all 3 rendered images showed the real pouch correctly — front-on, legible,
correct colours. Confirms the fix is holding; the 2/3-wrong batch the user saw was either from before
the fix landed or ordinary model variance on a given batch, not a live code gap.

**Explained exactly what reaches `/scene-still`** at the user's direct request: the real reference
photo(s) as image bytes (not a description), the style register text, the exact pack_clause instruction
when a real pack is pinned ("Reuse the EXACT product pack... same container type and format... never
redrawn or reimagined..."), and the post's own AI-written scene line. Named the honest limit: even with
a correct reference and correct instructions, current image models don't reproduce a reference
perfectly every single time — a known model-level limitation, not something further prompt engineering
fully closes, though the app now maximizes the odds every time a real pack is picked.

**Validated:** `checkfe.py` all 8 checks passed; LF/NULL-byte scan clean. No backend changes this round.

## Round 13, follow-up — exact wording specified by the user

User specified the precise replacement wording rather than the draft proposed in the round above:
"Nothing selected. Pick at least one, or the producer works from pre-trained knowledge alone, not the
plan or platform." Applied verbatim, live-verified rendering exactly as given. `checkfe.py` clean,
LF/NULL-byte scan clean.

## Round 14 — "Include a recurring model/cast" actually did nothing when unchecked

Following on from the cast-consistency question: confirmed the checkbox's unchecked state never
actually stopped a cast reference from being used. `library.shot_references()` auto-attached the
most-recently-signed-off cast whenever one existed for the brand, with no way for any caller to say
"skip it" — cast has always been unconditional, unlike `pack`'s opt-in `want_pack`. So "Include a
recurring model/cast," left unchecked, still silently pinned the same person (the newest signed-off
"AI-drafted cast" item) to every post — exactly backwards from what the label implies.

**Fixed the behavior, not just the wording**: `library.shot_references()` gained `want_cast` (default
`True`, preserving every existing caller's behavior exactly — Video, continuity, anything that doesn't
know about this yet). `/scene-still` now reads an explicit `use_cast` from the payload (`None` from any
caller that doesn't send it keeps the old default), and only suppresses the auto-fallback when told to.
An explicit `cast_id` still wins regardless, same "a person's own choice survives" rule `pack_id`
already follows. The identical bug existed in Carousel's own "Include a recurring model/cast in this
carousel" checkbox (same unconditional-attach code path) — fixed the same way; its own code comment had
asserted cast was "already opt-in," which was the wrong belief the bug had produced, now corrected.

**Fixed the wording too**: added a plain-text line under both checkboxes stating what actually happens
either way — "Unchecked: no cast reference is used — each post may show a different, unreferenced
person" / "Every post in this batch pins the person below" — rather than leaving the behavior implicit
and easy to misread, which is exactly what led to this round's question in the first place.

**Live-verified**: a call with no `use_cast` sent still auto-attached cast (`references:1`, unchanged
default); the identical call with `use_cast:false` came back `from_reference:false` — no cast reference
at all, confirming the suppression actually works. UI note text confirmed rendering correctly in both
states after toggling the checkbox live.

**Validated:** `py_compile` on `library.py`/`main.py`; `checkfe.py` all 8 checks passed; LF/NULL-byte
scan clean on `app.dc.html`. Server restarted before testing (backend change, no hot-reload).

---

## Consolidated summary — the whole arc, build through Round 14 (11–16 Sep)

Requested by the user as a single place that brings every problem and its solution together, rather
than requiring a read of all 14 rounds above. This section is a recap, not a new source of truth — the
full detail for anything below lives in its own round, referenced by number.

### Where this started

Traced from a real bug report — "generating Parle G still writes Heritage" — through three quick fixes
(`brandprofile.resolve()`'s active-brand fallback, a client-name-override staleness bug) to a much
bigger finding: **the whole app had no way to say "this piece is deliberately not tied to any brand."**
Every text generation (`/complete`) and every image generation fell back to whichever brand was
globally active, full stop — there was no honest "Independent" state anywhere. Separately, Ground Truth
(the reference library) and Learning were architecturally brand-blind — no `brand` field on library
items at all — so even correctly *grounded* work could silently pull another brand's pack shot or house
rule in this account's 5-brand tenant.

### The build (11–12 Sep) — a real Grounded/Independent toggle, 5 stages

1. **Ground Truth brand-scoping** — `library.py`/`learning.py`/`made.py` gained a real `brand` field and
   filter on every read/write, ~15 routes wired.
2. **Brief** — `briefstore`/`needBrand()`/`brandPreamble()` gained an honest "don't invent a brand" path
   for Independent, instead of refusing or inventing one.
3. **Strategy/Messaging House** — `strategy.prompt_for()` checks the house's own `brand_mode` before
   ever resolving a brand; retrieval and locked-copy skip outright for Independent houses.
4. **Producers** (`/complete` + image generation) — `prompts.system_for()` skips brand resolution
   entirely for Independent; `producers._ctx()` and every image route skip reference-image lookups.
5. **Plan** — same before/after pattern as Strategy, `plan.py` gained its own `brand_mode` handling.

Architecture note: this started as **four separate per-tab toggles** (Brief/House/Plan/Producers each
switchable on their own) — collapsed to **one** master toggle (Round 2) after live testing showed two
disagreeing pills on the same screen reads as broken, not flexible.

### Testing rounds — every problem thrown at it, and what fixed it

| Round | What testing found | What fixed it |
|---|---|---|
| 1 | Toggle changed nothing — IMC Brief's own AI-draft path (`/brand-brief-draft` to `brief_ai.py`) was never wired to the toggle at all; the model was told to "infer" a brand name when blank. | Wired `brand_mode` through, both client and server; model now refuses to invent a brand name instead of inferring one. Toggle relabeled General to **Independent**. |
| 2 | Header pill and each tab's own pill disagreed with each other. | Collapsed 4 toggles into 1 master toggle (`producerBrandMode`), shown once in the header; added a real "Independent work" row to the brand-switcher dropdown. |
| 3 | Grounded mode never auto-filled IMC's Brand/Category fields from the active profile. | Auto-fills on entry, on switching back to Grounded, and on switching to a different brand (only when fields are blank, never overwriting a real edit). |
| 4 | Stale "Redraft" label after switching to Independent; picking a reference brief silently flipped the toggle back to Grounded. | Draft state clears on every toggle flip; `pickBrief` no longer touches the toggle (only `enterHouse`/`enterPlan`, which open an *already-decided* document, still sync it). |
| 5 | Round 4's stale-draft bug turned out to be the studio's *default* shape — present on every producer (Social, Carousel, Video, POSM, Onground, PR-release, Idea Platform, guided Brief Builder). | Fixed in one pass, live-tested individually on every single surface with real generation calls. Caught and fixed two self-inflicted regressions along the way: a blind reset deleting a person's own typed text (Onground), and a fix that would have wiped an already-**adopted** Idea Platform record — a real saved decision, not a draft. |
| 6 | A live `/posm-keyvisual` call, Independent selected, came back standing on the bound house's real core message — the toggle had only ever gated *voice*, never the separate mechanism that pulls a bound house/platform's content into a prompt. | Traced and fixed at the two shared chokepoints: `prompts.py` (`_resolve_house`/`plan_channels_block`) and `producers.py` (`stands_on`/`_ctx`), covering Social/Video/POSM/Onground in one pass. Phase 2 (Plan's own leak, `/idea-draft`) and Phase 3 (PR's `prDraftRelease`, never wired) scoped but deliberately deferred — approved Phase 1 only. |
| 7 | User's own live testing of Phase 1 surfaced four issues: a picker preview leaking the active brand's name; Plan's Channels layer leaving every row blank; a carousel pack shot rendering as garbled back-of-pack text; a false-alarm red herring mid-investigation. | All four root-caused and fixed: `imcSnapshot()` given the same toggle-check `saveImcBrief` already had; the real "served media list" injected into Plan's channels prompt; the pack-reproduction instruction rewritten to ask for what a model can actually hold onto instead of "down to the fine print." |
| 8 | Two follow-ups: simplify the IMC warning copy; Social's single-post generator had no way to attach a real pack/cast photo at all. | Warning simplified to an always-on generic reminder (user's choice). Built a new "Assets for these posts" pick-or-upload card, reusing POSM's proven pattern. |
| 9 | The demo pack render came back as a **bottle**, not the real **pouch**. | `pack_clause` named colour/label but never the container's own physical form — added an explicit "reuse the exact container type" instruction. |
| 10 | Real use of the new asset picker surfaced three issues: 1/6 posts with wrong image dimensions; Adjust drifting the product to a different real SKU; Adjust fully re-rendering the image (new setting, new cast) on every note. | A fal.ai fallback path hardcoded the wrong image size — fixed to read the real ratio. Added `socialAssetAnchor()` naming the pinned product explicitly. Replaced a brittle text-diff with an explicit `visual_changed` judgment the model makes directly, plus the previous render passed forward as a continuity reference. |
| 11 | Testing Independent mode *directly* (not Grounded) surfaced a deeper leak: `brandPreamble()` — the shared prompt-builder behind **8** different producers — only checked Independent inside its "no brand at all" fallback, so it did nothing when a real brand was active (the normal case). Also: the pack-upload "Inputs to guide generation" control looked real but never uploaded anything. | Fixed `brandPreamble()` and the identical bug in `inputsContext()` — Independent now wins outright, checked first. Removed the non-functional upload control from Social's screen, pointing at the one real mechanism instead. |
| 12 | The real explanation for "only 1/6 posts resembled the pack": `/scene-still` was silently stripping even an *explicitly-picked* pack reference whenever Independent was active. | Fixed to match cast's own precedent — an explicit pick is the person's own deliberate choice, not invented brand voice, so it now survives Independent mode. Same fix applied to POSM's `/posm-scene`. Added a new "Let the studio design one" option for when no real photo exists yet. Fixed a second bug where the grounding banner discarded the server's own honest summary. |
| 13 | Two questions: what does "working from memory" mean, and why did the pack still miss sometimes. | Explained both plainly; reworded "memory" (collided with the app's own Memory tab) to the user's own specified wording. Re-verified Round 12's fix fresh — 3/3 clean. |
| 14 | "Include a recurring model/cast," left unchecked, did nothing — a cast reference was always auto-attached regardless. | Gave the checkbox a real, working off-state (`want_cast`/`use_cast`, defaulting to the old always-on behavior for every other caller); fixed the identical bug in Carousel's own checkbox; added plain-text notes stating what each state actually does. |

### What this adds up to

Every fix above was **live-verified with a real generation call**, not just code review — the standing
discipline this entire project has followed. The pattern across nearly every round has been the same
shape: a mechanism that looked wired was actually only checked in one of several places it needed to
be, or a UI control implied a behavior the code underneath didn't actually deliver. Each round closed
one such gap, and several rounds (6, 11, 12, 14) surfaced the *next* layer down only once the layer
above it was fixed and put back in front of the user to test again.

### What's still open (unchanged from the last review earlier in this conversation)

- **Phase 2** (`plan.py`'s own house-pull, `/idea-draft`'s unguarded house pull) and **Phase 3** (PR's
  `prDraftRelease` wiring) — scoped, deferred, approved Phase 1 only.
- POSM's downstream compositing routes (`/posm-assemble`/`/posm-artwork`/`/posm-print`) — no
  Independent branch built yet, lower priority.
- Sales enabler's `/sales-generate` — real leak, but latent (no frontend caller exists yet).
- Explicit `cast_id`/`pack_id` overrides aren't brand-ownership-checked even in Grounded mode —
  pre-existing, not introduced by this project.
- Existing library items have no `brand` tag — untagged items stay visible to every brand's Grounded
  work until a manual tagging pass.
- Two open design questions, not bugs: IMC's prompt textarea never clears on Independent (deliberate,
  not reconfirmed); the Palette/Tone display block on Social stays visible regardless of mode
  (confirmed cosmetic-only).
- The "real brand recall" tension: a person's own prompt naming a real, known brand pulls on the
  model's own training knowledge of that brand — not something further prompt engineering can fully
  close, would need a deliberate design call if it's worth pursuing.

**Standing fact, unchanged across all 14 rounds:** nothing from this entire project has been committed
to the actual product code. Every fix above — spanning `main.py`, `library.py`, `creative.py`,
`prompts.py`, `producers.py`, `plan.py`, and `app.dc.html` — remains local, pending the user's own
review and an explicit instruction to ship.
