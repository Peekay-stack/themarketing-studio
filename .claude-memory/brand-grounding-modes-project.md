---
name: brand-grounding-modes-project
description: "All 5 stages built and live-tested (11-15 Sep 2026) — Brief/Strategy/Plan/Producers share one Grounded/Independent toggle so \"no brand attached\" is a real, honored choice instead of an accident. Architecture collapsed from 4 per-tab toggles to 1 after user testing; 5 rounds of testing feedback fixed, incl. a studio-wide stale-draft-on-toggle bug across every producer — see the testing log."
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-15T09:29:21.689Z
---

**Start here for this thread**: `BRAND_GROUNDING_MODES_PLAN.md` (repo root) has the full technical
plan. **`BRAND_GROUNDING_TESTING_LOG.md`** (repo root) has every round of user-testing feedback and
its fix, prompt by prompt — see [[brand-grounding-testing-log]], a standing instruction to keep
appending to it. This memory is the status/continuity layer on top of both.

## Current shape (as of 12 Sep, after 2 rounds of user testing)

**One toggle, not four.** Started as four separate per-tab toggles (Brief/House/Plan/Producers each
independently switchable) per the original design call — collapsed to a single `producerBrandMode`,
shown once in the header next to the brand chip, after live testing showed two pills on the same
screen (the header's and a tab's own) disagreeing reads as broken, not as flexible. Full story in the
testing log's Round 2. The header's brand-switcher dropdown now also carries a real "Independent
work" row alongside the actual brands — picking it sets the mode without touching which brand is
server-side active; picking any real brand (even one already active) always snaps back to Grounded.

## Why this exists

Traced from the user's original bug report ("generating Parle G still writes Heritage") through three
rounds of fixes that session (`brandprofile.resolve()`'s active-brand fallback in three places,
client-name-override-class staleness in the header/settings flow) to a much bigger finding: the whole
app had **no way to say "this piece is deliberately not tied to any brand."** Every text generation
(`/complete`, the shared chokepoint nearly all producers use) and every image generation fell back to
whichever brand was globally active, full stop. Separately, traced that **Ground Truth (the reference
library) and Learning (corrections/retrieval) were architecturally brand-blind** — no `brand` field on
library items at all, tenant-wide only for learning — so even *correctly* grounded work could silently
pull another brand's pack shot or house rules in this account's 5-brand tenant (Heritage Foods, Kumkum
Beauty, Loomwell, Parle G, Sthir Cement).

## Build status — all 5 stages done

- **Stage 1 — Ground Truth brand-scoping.** DONE, live-verified. `library.py`/`learning.py` gained a
  `brand` field + filter on every read/write function (additive — empty `brand` keeps old tenant-wide
  behavior). `made.py`'s `list_entries()` gained the same filter. ~15 real generation/status routes
  wired across `main.py`/`posm.py`/`shelf.py`/`continuity.py`.
- **Stage 2 — Brief.** DONE, live-verified both directions of the save round-trip.
  `briefstore.put()`/`/brief-save` carry `brand_mode`; `needBrand()`/`brandPreamble()` gained an
  `allowGeneral` bypass reaching `voice_block(None)`'s honest "don't invent a brand" instruction.
- **Stage 3 — Strategy/Messaging House.** DONE, live-verified with a real before/after `/house-prompt`
  comparison (Independent → honest no-brand instruction, zero leakage; Grounded Parle G → real brand
  facts, same test). `strategy.prompt_for()` checks `house.get("brand_mode")` before ever calling
  `resolve()`. `/house-generate`'s T1/T3 retrieval and locked-copy skip outright for Independent
  houses.
- **Stage 4 — Producers (`/complete` + image generation).** DONE, **live-tested 12 Sep morning**: real
  `/complete` calls in both modes came back correctly contrasted (Independent → "I don't know, no
  brand profile has been provided"; Grounded → "Heritage Foods, a dairy brand..."); a real
  `/scene-still` call in Independent mode came back `from_reference:false` with no reference pulled.
  `prompts.system_for()` skips `resolve()` entirely for `brand_mode="general"`. `_brand_line()`
  redesigned to accept `brand`/`brand_mode` instead of always resolving itself.
  `producers._ctx()` defaults from the bound house, skips character lookup when Independent.
  `/posm-image`/`/posm-scene`/`/scene-still` skip reference-image lookups entirely in Independent mode.
- **Stage 5 — Plan.** DONE, live-verified with the same before/after `/plan-prompt` method as Stage 3.
  `plan.py`'s `prompt_for()` and `set_brand_mode()`, new `/plan-brand-mode` route, `/plan-generate`
  skips T1/T3/locked-copy for Independent plans.

**Two real incidents caught mid-build, both by compile-checking immediately rather than batching:**
(1) `library.items()`'s `brand=""` silently means "don't filter," not "brand-agnostic only" — fixed
via a sentinel value. (2) One edit corrupted `main.py` with two literal NULL bytes (an odd string-
literal encoding fluke) — caught by `py_compile` right after the edit, fixed, then swept every touched
file for null bytes.

**Then, after shipping Stage 4/5, five rounds of real user testing found and closed further gaps** — a
completely separate code path (`/brand-brief-draft` → `brief_ai.py`) that had never been wired to the
toggle at all; the 4-toggles-not-1 architecture problem above; the IMC screen never auto-filling
Brand/Category from the active profile (Round 3); Round 4 (15 Sep), two bugs — `im.draft`/`status` not
clearing on toggle change (stale "Redraft" label after switching to Independent), and `pickBrief`
silently syncing the master toggle to a picked brief's own stored `brand_mode` (nearly every brief
predates this feature and reads `grounded`, so pulling one while Independent snapped the toggle back).
Fixed by clearing draft state on every toggle flip, and by removing `pickBrief`'s sync while
deliberately keeping `enterHouse`/`enterPlan`'s (those open an already-decided document; a picked
brief is just reference text for something not yet created).

**Round 5 (15 Sep, same day):** the user asked for an audit of the other producers, then "fix all of
them the same way, one pass... default on all tabs, sub tabs and layers." Round 4's stale-draft bug
turned out to be the studio's *default* shape, not a one-off — audited and confirmed present in Social
(`posts`), Carousel (`routes`/`concept`/`slides`), Video (`videoConcept`/`fullScript`/every
department's `shoot` card/`sceneFrames`/cast reference), POSM (`pm.options`/`scamps`/`images`/every
rendered piece), Onground (`og.ideas`), PR's release sub-tool (`release`/`rel`/`relStatus`), plus two
upstream surfaces not in the original ask — the Idea Platform (`idea.line`/`options`) and the guided
Brief Builder used by Media/Digital/Packaging/PD/PR-format (`state.brief`). Fixed all of it in one
pass in `setProducerBrandMode`: AI output clears, whatever the person typed stays. A first pass reset
`posm`/`og`/`idea` to `null` outright — live-testing the fix itself (not the user) caught that this
also deletes real typed input living in the same namespace (`og.idea`, the person's own activation
sentence); rebuilt as field-by-field clears instead, re-tested, confirmed fixed. Live-verified end to
end with real generation calls on Social and Onground (including the regression), then Video and POSM
on a follow-up request (Video: real concept generated, toggle-cleared, typed brief survived; POSM:
real key-visual route generated, toggle-cleared, Step 2 correctly re-locked, typed brief survived),
then Carousel and PR-release on a further follow-up (Carousel: three real routes generated,
toggle-cleared, typed brief survived; PR-release: real press-register copy drafted for a live sheet,
toggle reset the whole sub-tool to its pre-start "No release on this sheet yet" state — not just
blanked fields — and a fresh Independent-mode start came back genuinely empty), then the guided Brief
Builder (real AI-drafted Background/Business-objective copy for a Media-format brief cleared on
toggle, while Deliverables/Budget correctly reverted to their exact `formatDefaults` template seed
text rather than blanking, and the typed ask survived), then the Idea Platform itself — which surfaced
a second, more serious version of the og.idea mistake: live-testing it landed on a real **adopted**
platform ("The Head Start", saved via `adoptIdea()` → `POST /idea-platform`, a real server id, the
same document tier as House/Plan/Campaign). The shipped fix would have wiped its `line`/`name` — real
decided creative work seven activation drafts point back to — on the next toggle touch, no warning, no
way back. Fixed by gating the whole clear behind `curIdea.adopted` (adopted = left alone entirely,
same as House/Plan/Campaign; only an unadopted in-review draft still clears). Live-verified the
adopted platform survives a toggle flip byte-identical. Could not reach a disposable unadopted
platform to re-confirm the ordinary clearing path live in this tenant (`state.idea` turned out not to
be house-scoped on the frontend — one global slot, a pre-existing data-model fact, not something this
round changed); that branch is unchanged from the original fix and reuses the same pattern already
live-proven on five other producers.

**Sales enabler checked, a different kind of finding:** nothing to clear because nothing here is
AI-generated yet. The frontend's only action (`/sales-element`) is pure record-keeping — saves typed
text verbatim, no brand facts, no toggle involvement — live-confirmed (typed text, toggled, text and
status untouched). The real generation route, `/sales-generate`, DOES exist server-side and DOES pull
brand facts unconditionally (`prompt_for()` → `brandprofile.voice_block(brandprofile.resolve(...))`,
no `brand_mode` param anywhere) — the same shape as Round 1's `/brand-brief-draft` gap — but has zero
frontend caller, so the leak is latent, not live. Not fixed: this is new wiring (a real generate
action plus threading `brand_mode` through it) rather than a one-pass clear, left for the user to
decide on.

## Round 6 (15 Sep, same day) — a real, live grounding leak found and fixed in phases

Verifying #3 of the user's own re-confirmation checklist ("where does independent work get saved") on
POS material surfaced a genuine leak: a real `/posm-keyvisual` call, Independent selected, came back
standing on the bound house's real core message ("Pure milk, strong family."). Root cause: the toggle
had only ever gated **voice resolution** (`brandprofile.resolve()`/`character.for_prompt()`) — never
the separate mechanism that pulls a *bound* house/platform/plan's content into a prompt. Two shapes:
an "empty string means don't filter" footgun in `prompts._resolve_house()`/`plan_channels_block()` —
`brand=None` collapsed to "match anything" instead of "match nothing" — same class already fixed once
in `made.py` this session), and flat-out unconditional inclusion (`plan.prompt_for()`'s
`if house: out.append(house_block(...))`, no mode check at all).

**Asked to check breadth before fixing.** Confirmed by direct code read across every tab: POSM +
Onground leak via `producers.stands_on()`/`_ctx()` (8 call sites); Social + Video + everything through
`/complete` leak via `prompts.py`'s `house_block`/`platform_block`/`plan_channels_block`; Plan's layer
generation leaks via an unconditional house pull; PR's `prDraftRelease()` was simply never wired to
the toggle at all (new-wiring class, like Sales enabler, not a repair); Idea Platform's own `/idea-draft`
leaks the same way. House's own layer generation (`strategy.prompt_for()`) is safe — checks its own
document's `brand_mode` directly, no cross-document lookup. IMC/Brief Builder already correct.

**Phase 1 (completed, user-approved scope: the shared chokepoints only):** fixed
`prompts._resolve_house()`/`plan_channels_block()` (covers Social/Video/everything via `/complete` in
one place) and `producers.stands_on()`/`_ctx()` plus all 6 functions and every route/frontend caller
that reaches them (covers POSM + Onground together). Live-verified against the exact failure case: the
same `/posm-keyvisual` call now returns empty `stands_on` and generic ungrounded routes; Onground's
"Generate ideas for me" correctly 400s with nothing typed and, with a steer note, generates real ideas
every one tagged `stands_on:"typed here"`, no house/platform facts anywhere in the response.

**Not yet done — Phase 2 (`plan.py`'s house pull, `/idea-draft`'s unguarded house pull) and Phase 3
(PR's `prDraftRelease` — new wiring, not a repair)** — scoped but intentionally not built this round;
the user approved Phase 1 only. Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 6.

## Round 7 (15 Sep, same day) — user tested Phase 1 live, found 4 more issues, all fixed

User tested Phase 1 directly (Independent IMC drafts, pickers, a Plan's Channels layer, a Social
carousel with a real pack shot) and sent 7 screenshots + 2 docx files. Read everything before touching
code, proposed fixes, user said "fix all 4":
1. **`imcSnapshot()`** (the picker's "current draft" preview) fell back to the active brand's real name
   with no toggle check and never set `brand_mode` — same bug class as `saveImcBrief` already had fixed
   next to it. Fixed to match. Also built a soft warning (not a block) for when the free-text prompt
   itself names a real brand while Independent — that's a genuine design tension (the toggle stops
   invented facts, not facts you typed yourself), not a bug, and the two docx files the user sent both
   confirmed it: same prompt naming "Heritage master brand" explicitly, both drafts thoroughly grounded
   in Heritage Foods, because that's what was asked for.
2. **Plan's Channels layer left `channel`/`medium` blank on every row** — pre-existing, unrelated to
   brand-grounding (would happen in Grounded plans too). The prompt asked the model to pick from a
   "served media list" that was never actually built anywhere in `plan.py`. Fixed: inject the real
   `media.LEGACY_STRATEGY_MEDIA` vocabulary into the channels layer's instructions.
3. **Carousel pack shot rendered as garbled back-of-pack text.** Confirmed via a direct `/scene-still`
   test that the reference WAS reaching the model (`pack_used: true`) — not a wiring bug. The prompt's
   `pack_clause` asked for the pack "down to the fine print," which no current image model can do, while
   fighting a separate "no on-screen text" instruction in the same prompt — exactly the fight the
   garbled output showed. Rewrote to ask for colour/proportions/front-facing brand mark instead of fine
   print. Live-verified: two real carousel renders, front-of-pack, "Heritage" and "Daily Health Toned
   Milk" both clearly legible.
4. **A self-caught false alarm mid-investigation**: fix 3's first verification attempt kept showing
   `pack_used: false`. Traced with a `fetch` monkey-patch (not a guess) to the real request body, which
   showed `brand_mode: "general"` — the toggle was still on Independent from testing fixes 1–2, and
   Independent correctly strips the pack reference by Round 6's own design (only cast is exempted).
   Switched to Grounded, re-tested clean. Recorded in the log so this isn't re-chased as a regression.

All four live-verified with real generation calls. Full detail: `BRAND_GROUNDING_TESTING_LOG.md`
Round 7. Deliberately left
untouched, not silently skipped: `state.campaign` (the Idea Platform's own ladder/roles/posts/video
hub — server-persisted like House/Plan, needs that same treatment, not a client reset) and House/
Plan's own per-layer generated-but-uncommitted suggestion rows. Full detail: see
[[brand-grounding-testing-log]] and `BRAND_GROUNDING_TESTING_LOG.md`.

## Not yet built / lower priority, still open

- **POSM's `/posm-assemble`/`/posm-artwork`/`/posm-print`** (downstream compositing/export, as opposed
  to `/posm-image`'s fresh generation) still call `library.reference_url(..., brand=_gen_brand)`
  unconditionally — no Independent-mode branch built for these three yet. Lower priority: they operate
  on an already-generated hero image, not fresh brand-fact generation. `/posm-artwork`'s own
  `brandprofile.resolve()` call is also still the blind, no-docs form. The `brand=""` empty-string
  gotcha (see above) applies here too if this gets built without care.
- **Explicit `cast_id`/`pack_id` overrides in `/posm-image`/`/scene-still`** are not brand-ownership
  checked even in Grounded mode (a caller naming a specific id bypasses the filter) — pre-existing,
  not introduced by this project, lower priority than the automatic-fallback bug this project targets.
- **Sales enabler's `/sales-generate` route** — real AI generation, pulls brand facts unconditionally
  via `brandprofile.voice_block(brandprofile.resolve(...))`, no `brand_mode` param anywhere. Not yet a
  live bug only because it has no frontend caller at all (the tab's only wired action,
  `/sales-element`, is pure manual record-keeping with no AI or brand involvement). Whoever wires a
  real "Develop with AI" button to this route needs to thread `brand_mode` through it first — see
  [[pr-sales-enabler-producer-roadmap]].
- **Existing library items have no `brand` tag** (the field didn't exist before Stage 1) — until
  someone tags them, they stay visible to every brand's Grounded generation (the safe default for the
  transition). Worth a manual tagging pass at some point.
- **The IMC Brief prompt textarea is never cleared** when switching to Independent (only Brand/
  Category are) — a deliberate choice (it's the person's own analysis request, not a brand fact),
  flagged to the user, not yet confirmed as final either way.
- Nothing in this feature has been committed or pushed as of 12 Sep — still sitting local pending the
  user's own review.

## Related

`CLAUDE.md` already covers the hot-reload gotcha hit repeatedly this project ("backend edits need a
server restart... despite `--reload` being set") — no separate memory needed, just keep obeying it.
