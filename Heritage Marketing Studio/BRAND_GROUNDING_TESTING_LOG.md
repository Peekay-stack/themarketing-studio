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
