---
name: brand-grounding-modes-project
description: "All 5 stages built + Phases 1-3 of the grounding-leak fix all now done, 15 rounds of live user-testing feedback fixed (11-16 Sep 2026) — Brief/Strategy/Plan/Producers share one Grounded/Independent toggle so \"no brand attached\" is a real, honored choice instead of an accident. Every scoped gap closed; still 100% local, to be shipped together once user testing is satisfied — see the testing log."
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-16T08:20:14.029Z
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

## Round 8 (15 Sep, same day) — two follow-ups from Round 7, both offered as choices first

User sent 2 more screenshots after Round 7 with two small inputs, each presented as an explicit choice
(via a direct question) rather than assumed:
1. **IMC's Independent warning, simplified.** User offered draft wording for something simpler than
   Round 7's whole-word brand-match warning. Choice offered: keep the match-triggered version, or an
   always-on generic reminder. **User picked always-on generic.** Replaced the `imcPromptBrandHit`
   match logic with a flat `imcIndependent` flag; banner now always reads (while Independent): "The
   brief is grounded entirely in what you write here — it takes nothing from the brand profile. Follow
   the prompt guide to cover what the profile would otherwise supply." Live-verified the exact text
   renders.
2. **Social's single-post generator had no pack/cast asset mechanism** (unlike POSM/Onground/Carousel)
   — `/scene-still` rendered from text description alone even with a real signed-off asset on file, in
   both modes. User named two options: reuse the existing pick-mechanism like Carousel/other producers,
   or a direct upload in the frame. **Recommended and user confirmed: reuse POSM's pick-or-upload
   asset-card pattern** (one control, both a select-from-signed-off and a file-upload-that-auto-signs-
   off-and-selects) rather than a third divergent shape. Built as a new "Assets for these posts" card
   on Social's single-post screen — pack-shot pick/upload plus a cast checkbox that reveals the same
   pattern — using `carouselAssetOptions()` as the options source but writing to Social's own
   `socialPackChoice`/`socialCastChoice`/`socialWantCast` (not shared with Carousel's own picks, same
   "two controls, one real" precedent already used elsewhere).

**Live-verified end-to-end with a real generation call**: picked the real "heritage daily health pack
shot.jpg", generated posts on all 3 platforms, a `fetch` monkey-patch confirmed all 9 `/scene-still`
calls carried `pack_id`/`brand_mode:"grounded"` correctly, then downloaded and visually inspected one
rendered image — pack front-on, "Heritage · Daily Health Toned Milk" clearly legible, no garbled text
(confirms Round 7's `pack_clause` fix and this new picker hold up together under a real render). A
verification false trail along the way: `document.body.innerText` said the new card's text wasn't on
the page while `textContent` found it fine — root cause was `text-transform:uppercase` on the label
(`innerText` reflects rendered case, `textContent` doesn't), not a rendering bug; confirmed by reading
a wider slice of `innerText` and finding the uppercase text exactly where expected.

Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 8.

## Round 9 (15 Sep, same day) — pack reference rendered as the wrong container (bottle instead of pouch)

User caught it from the Round 8 demo render itself: the real "heritage daily health pack shot.jpg"
reference is a sealed flexible **pouch**, but the render showed a **bottle** being poured. Confirmed by
fetching and viewing the actual reference file. Root cause: Round 7's `pack_clause` rewrite (`main.py`)
preserved everything printed *on* the pack (colours/proportions/label) but never named the pack's own
physical form/container type — so the model faithfully copied the logo and colours onto a bottle, the
default "milk" visual in its training data, since nothing pinned the actual shape. Fixed by adding an
explicit container-type clause ("pouch, bottle, carton, tub, jar — whichever the reference actually is,
never substituted"). Live-verified with the same real pack id via a direct `/scene-still` call
(`pack_used:true`): new render shows a correctly-shaped pouch, pinched corners, mid-pour, brand and
product name legible. Same chokepoint as Round 7's fix — the earlier fix was real but incomplete, not
wrong. Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 9.

## Round 10 (16 Sep) — real use of the Social asset picker surfaced three more issues, all fixed

User ran the actual intended workflow (uploaded pack, wrote a real objective, generated 6 posts,
adjusted two) and reported three problems together; investigated and root-caused all three before
touching code, then the user approved all three at once. All in `app.dc.html` unless noted:
1. **1/6 posts had wrong/cropped dimensions** — `creative.py`'s fal fallback path (`ideogram/character`,
   used only when fal's primary reference model errors) hardcoded `image_size:"landscape_16_9"`
   regardless of the requested ratio; a 1:1 request that fell through got a 16:9 image back, cropped by
   the post frame's `cover` fit. Fixed to read the same `_IMAGE_SIZES` map the primary fal path uses.
2. **Adjust drifted the product to a different real SKU** ("Pure Milk" instead of "Daily Health," even
   after the user named the right one explicitly) — neither `generateSocial` nor `adjustPost` ever told
   the model which pack/SKU was actually pinned by reference, so the brand's own house/plan grounding
   (centered on the flagship line) pulled text toward the wrong product. Added `socialAssetAnchor()` —
   names the pinned asset's real file name, says never to rename/substitute it — wired into both prompts.
3. **Every Adjust fully re-rendered the image** — "new setting, new style, cast keeps changing," even on
   caption-only notes — contradicting the UI's own "keep everything else the same" promise. Root cause:
   the code decided whether to redo the image via `data.visual !== post.visual`, but an LLM told to
   return a field is not going to reproduce it byte-for-byte, so this fired on nearly every adjustment
   regardless of intent. Replaced with an explicit `visual_changed` boolean the model judges directly
   (old string-diff kept only as a fallback). When a redo IS warranted, the post's own previous render is
   now passed to `/scene-still` as an extra identity reference (existing mechanism, not a new one) so the
   same people carry across rounds — a partial fix, not a full scene-lock, since that reference mechanism
   is explicitly allowed to vary setting/camera by design (shared with Video's continuity use).

**Live-verified end-to-end**: real 6-post generation with the anchor text confirmed reaching the prompt
verbatim; a caption-only adjust fired zero `/scene-still` calls (confirms 3 actually suppresses
unwanted re-renders now); a genuine visual-change adjust fired exactly one call, correct `pack_id` +
`reference_url` pointing at the prior render, caption/visual still said "Daily Health," and the
resulting image showed the same woman as before (continuity working). One honest caveat recorded, not
chased further: that same render's container drifted from the pinned pouch shape to a carton shape —
likely ordinary generation variance rather than a Round 9 regression (both references shown were the
correct pouch), worth watching if it recurs. Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 10.

## Round 11 (16 Sep) — a real Independent-mode leak in a second, previously-unaudited layer

User tested Independent mode directly (not Grounded) this time. Found: **`brandPreamble()`** — the
shared client-side preamble builder behind 8 producers (both brief writers, Social, Video script +
department heads, campaign lead, measurement) — only checked `allowGeneral`/Independent inside its
"no brand configured at all" fallback branch, so it did NOTHING whenever a real brand was actually
active (the normal case): every Independent-mode call from any of these 8 still opened "You are ...
for Heritage Foods" plus the full voice block. This predates and sits BELOW everything Rounds 1-10
verified, because those rounds tested the server-side `/complete` route's own `brand_mode` handling
directly, never through this specific client-side prompt-builder. Confirmed live via a
`window.claude.complete` monkey-patch. Fixed: `allowGeneral` now wins outright, checked first.
**`inputsContext()`** had the identical bug (unconditional brand-guidelines pull on the "guidelines"
toggle) — same fix. The guidelines chip itself was also lying (stayed green/branded regardless of
Independent) — now reads "Brand guidelines — off while Independent."
**Pack shot still not reaching the image**, root-caused as UX not a new bug: the user (reasonably)
uploaded via the pre-existing "Inputs to guide generation" uploader, which never uploads anything real
— `handleStudioUpload` only remembers the filename as TEXT context, never a real photo reference. The
real mechanism (Round 8's "Assets for these posts" card) sat unused. Per the user's direction, removed
the misleading upload button from Social's copy of that panel specifically (Video's own copy is
untouched — no competing mechanism there) and pointed at the real card in its place.
**Live-verified**: panel now reads honestly, no upload button; a real Independent-mode generation's
captured `/complete` prompt opened "No brand profile is attached to this piece... do NOT invent a
brand" with zero "Heritage Foods"/"HERO PRODUCT" leakage.
**Separate, NOT-a-bug finding, recorded not hidden**: captions still came back fully Heritage-voiced
(tagline, hashtags, FSSAI claims) because the objective itself said "create a post for heritage milk"
— a real, well-known brand the model already knows from training, independent of anything this app
injects. Same tension Round 7 named for IMC and the user accepted; not closed this round, would need a
deliberate design call. Also noted, not fixed: the Palette/Tone display block still shows the active
brand's kit regardless of mode — confirmed purely decorative (display-only, never read by any prompt
function), cosmetic not functional. Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 11.

## Round 12 (16 Sep) — the real "only 1/6 posts resembled the pack" cause; a new design-choice option

Continuing Round 11: user reported only 1 of 6 Independent-mode posts resembled the real pinned pack
shot. Root cause confirmed via network capture: `/scene-still` stripped `pack`/`plate` unconditionally
whenever `brand_mode=="general"`, treating an EXPLICITLY-picked pack (via the real asset card) exactly
like an auto-attached one — contradicting the precedent already set for cast. Fixed: an explicit
`pack_id` that resolves now survives Independent; only auto-resolved packs still get stripped. Same fix
applied to `/posm-scene` (POSM's integrated-scene lane, identical bug). Live-verified: direct call with
`brand_mode:"general"` + real `pack_id` now returns `pack_used:true`.
**New option built, at the user's suggestion**: pack dropdown gained "Let the studio design one" for
when no real photo exists yet — threaded as `pack_generate:true` (only engages when nothing real
resolves), with a new prompt clause telling the model to design a plausible pack rather than leave the
product absent, without fabricating specific claims/certifications. Live-tested: model designed an
obviously-generic "Farm Fresh Milk" pack rather than guessing at the real Heritage design — safe,
non-misleading.
**A second frontend bug found while verifying Round 11's `/grounding` fix**: `socialGrounding()` only
trusted the server's `summary` when `grounded` was true — when false (the Independent case), it
discarded the server's real sentence for its own generic hardcoded text, silently swallowing Round 11's
fix before it ever reached the screen. Fixed to always use the server's summary when sent. Live-
verified: banner now correctly reads "This piece is Independent — nothing is grounding it but what you
write here." Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 12.

## Round 13 (16 Sep) — wording fix + clean re-verification of Round 12

User asked two questions: what "the producer is working from memory" means, and why the pack still
missed on 2/3 posts in a batch, with a direct ask for what literally reaches the image generator.
"Working from memory" is a real, accurate status (checks the separate "plan brief"/"idea platform"
toggles, not brand mode) but collided with the app's own "Memory" tab — reworded to "the producer works
from pre-trained knowledge alone, not the plan or platform" (user specified this exact final wording,
replacing an initial draft), same meaning, no collision. Re-ran the user's
exact scenario fresh: 3/3 posts came back `pack_used:true` with the real pouch correctly rendered,
confirming Round 12's fix holds — the earlier 2/3-wrong batch was pre-fix or ordinary model variance,
not a live gap. Explained the literal prompt reaching `/scene-still` (reference photos as real image
bytes, style register, the exact pack_clause text, the post's own scene line) and named the honest
limit: even a correct reference doesn't guarantee 100% model fidelity every render. Full detail:
`BRAND_GROUNDING_TESTING_LOG.md` Round 13.

## Round 14 (16 Sep) — "Include a recurring model/cast" did nothing when unchecked

User noticed identical-looking cast across a batch and asked if that's expected. Confirmed:
`library.shot_references()` auto-attached the most-recently-signed-off cast whenever one existed, with
no way to suppress it — cast has always been unconditional (unlike `pack`'s opt-in `want_pack`), so the
checkbox unchecked still silently pinned the same person to every post. **Fixed the actual behavior**:
`shot_references()` gained `want_cast` (default `True`, every existing caller unaffected); `/scene-still`
reads an explicit `use_cast` from the payload, `None` (nothing sent) keeps the old default. An explicit
`cast_id` still wins regardless, same rule `pack_id` already follows. Same fix applied to Carousel's
identical checkbox/bug (its own code comment had wrongly asserted cast was "already opt-in"). **Fixed the
wording too**: added a plain-text line under both checkboxes stating what actually happens either way.
Live-verified: no `use_cast` sent → cast still auto-attaches (old default preserved); `use_cast:false` →
`from_reference:false`, no cast at all. Full detail: `BRAND_GROUNDING_TESTING_LOG.md` Round 14.

## Round 15 (16 Sep) — the last three known gaps closed: cosmetic display, Phase 2, Phase 3

User asked for these three, in order, held locally until a final ship decision after more testing:
1. **Palette/Tone display block hidden while Independent** — `kitAnything`/`kitNothing` now gated on
   `!glIndependent`, with a new `kitIndependent` explanatory line instead of an unexplained gap.
2. **Phase 2** — `plan.py`'s `prompt_for()` gained the same `brand_mode` gate on `house_block()` that
   `voice_block` two lines above it already had. `/idea-draft` (route + `ideas.py`'s `draft_prompt`/
   `draft_lines`) gained real `brand_mode` handling — the house is never even loaded for General, and
   `brandprofile.resolve()`'s own active-brand-fallback footgun is blocked with it; the frontend
   (`ideaDraft()`) now actually sends `brand_mode`, which it never did before.
3. **Phase 3** — PR's `prDraftRelease()` has no typed-brief fallback the way Social/Video do, so the
   correct fix is a clean refusal (not a half-working generic mode): Independent now short-circuits
   before any brand/house pull, with an honest message, matching `draft_lines()`'s own "never invent
   from nothing" pattern.

**Live-verified all three**: the display block confirmed both directions; Phase 2 confirmed on a real
already-Independent plan — a `/plan-generate` call came back with a row correctly marked "HELD: no
sourced RTBs exist" (the model refusing to invent a proof it no longer had real house facts for) and
zero "Heritage"/"Pure Doodh" leakage, plus `/idea-draft` correctly refusing with no typed brief and
succeeding generically with one; Phase 3 confirmed on a real campaign PR sheet — zero `/complete` calls
while Independent (checked twice), one real call firing normally in Grounded (no regression).

This closes every item that was on the "still open" list — Phase 2/3 were the last scoped-but-deferred
gaps, the display block was the last known cosmetic inconsistency. Full detail:
`BRAND_GROUNDING_TESTING_LOG.md` Round 15.

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
- Nothing in this feature has been committed or pushed as of 16 Sep (15 rounds in) — still sitting
  local, by the user's own explicit choice: ship it all together in one render once satisfied with
  further user testing, not incrementally.

## Related

`CLAUDE.md` already covers the hot-reload gotcha hit repeatedly this project ("backend edits need a
server restart... despite `--reload` being set") — no separate memory needed, just keep obeying it.


**UPDATE 19 Sep -- the "nothing committed" standing fact above is no longer true.** The 13 backend modules
(brandprofile, complete, continuity, creative, ideas, learning, library, made, plan, posm, producers, prompts,
shelf) were shipped with the owner's go-ahead after live began returning HTTP 500s (committed `main.py` was
calling into uncommitted modules -- 60 mismatched calls found by `api/selfcheck.py`). Live now runs the whole
feature. Later the same day: the Social/Carousel pack dropdown was made honest (Automatic / Never / a picked
pack / design one; an explicit pick always attaches) -- **PENDING the owner's live confirmation**: Social batch on
Automatic, on Never, with a picked pack on a scene that doesn't mention a pack, and a Carousel on Never. The
owner said they will confirm later; do not treat the front-end behaviour or real image output as verified until
they do. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "19 Sep -- Social pack dropdown".


**UPDATE 21 Sep (pack dropdown):** owner confirmed the picked-pack path on live; Never/design-one/Carousel results were
understood, not bugs (Never = no reference photo attached; the scene text may still make the model draw a pack, e.g.
"his face on the pack"). Found and fixed a gap: Automatic did not recognise "pouch"/"sachet"/"bag of milk". Scoped to
Social+Carousel via `pack_mode:"auto"` so Video and /shot-reference are unchanged. PENDING the owner's live check
(Automatic + Regenerate visuals on a "pouch" scene). Deferred: per-post label of whether a real pack was used.
Changing the dropdown does NOT re-render existing posts -- the owner must click "Regenerate visuals" (noted UX gap).
Full entry: BRAND_GROUNDING_TESTING_LOG.md, "21 Sep -- follow-up to the pack dropdown".


**UPDATE 21 Sep (later) -- pack-shot rules decided; the pack designer was built, tried and DROPPED.** Owner's rules: Social
posts always carry a pack shot (on the side), a Carousel's CTA slide always does and middle slides only if described,
all visual styles, explicit opt-out, no silent default pack, the real pack. To serve a product with no pack shot I built
a pack designer (describe + optional reference photo, own store outside the library); the owner's first real try (real
Nourish+ photo attached) returned a generic pouch, so it was dropped -- patch parked at C:/Users/punie/parked-work/
pack-designer.patch, tree back at b2a7746. Real need = upload the real pack photo. NEXT: bring the owner a re-plan for
the always-a-pack rules with REAL packs only (chooser by name, no silent default, "no pack in these posts", Social then
Carousel, live confirmation between); do not build before they approve it. Full entry: BRAND_GROUNDING_TESTING_LOG.md,
"21 Sep -- pack shots". Lesson recorded: prove the risky generation step on the owner's real example before wiring.


**UPDATE 21 Sep (latest) -- library naming SHIPPED (commit 331fa94, live-gated).** Memory uploads now take a Name, every card has
Rename (`/library-rename`), file type is read from the stored file not the name, AVIF references are converted to PNG. Owner
confirmed the screen locally. PENDING the owner on live: rename the two live pack items (Nourish+, Happy Full Cream/"Heritage
milk.avif"); note "Heritage milk.avif" is now the newest signed-off pack = the default wherever nobody picks one. STILL OPEN:
the always-a-pack re-plan awaits the owner's answers (Step 0 wording trial ~8 image credits on the Nourish+ photo; brand
scoping of the pack list; CTA slide always an image slide; session-only working reference photo; writer-suggested "no pack";
whether to keep an "illustrative pack" rung). Full entry: BRAND_GROUNDING_TESTING_LOG.md, "21 Sep -- library naming".

**UPDATE END OF 21 Sep -- Deploy 1 (Social pack-in-scene) BUILT and HELD (owner: "hold it for the day").** Live = e94e92a
(library naming/rename + AVIF live). The Social pack work is UNCOMMITTED in the working tree and saved as a patch:
C:/Users/punie/parked-work/deploy1-social-pack-in-scene.patch (main.py, app.dc.html, tools/README.md, both tools tests,
new api/packscene.py). Proven today: the wording on the owner's real Nourish+ photo (13 image credits over 3 trials; static
placements faithful, in-use garbles, an invented mark and invented printed facts are intermittent and scene-driven); the
owner's real 9-post local batch (all carry the real pack). Built to fix what the batch showed: front-only/one-pack/no-facts
wording, a scene backstop (`packscene.clean_scene`), writer instruction. Tests: pack 54, naming, tools 18, audit 1,172/0.
UNPROVEN on pictures: the backstop and the writer instruction. RESUME: restart the local server (backend never hot-reloads),
review `git diff`, rerun the tests, then ask the owner for the go-ahead; on yes: commit, push, wait for the deploy, live
gate (/selfcheck commit, /selfcheck/deep, logs), record. OPEN decisions: ship Deploy 1 with known limits; optional 1-credit
check of the sanitised scene; keep the "pack in use" option; the brand-idea badge over each image (white on 16% white,
unreadable on bright photos: dark background or remove); pack size (add "about a quarter/third of the frame" and trial,
2-3 credits). NEXT after Deploy 1: Deploy 2 Carousel -- CTA slide always an image slide, and ask the services for 3:4 not
4:5 (they silently turn 4:5 into 16:9/1:1 and the slide is then cropped; found in code, not yet seen live). The owner still
has to rename the 2 live pack items (Nourish+, Happy Full Cream = "Heritage milk.avif", the newest pack = current default).
Full entry: BRAND_GROUNDING_TESTING_LOG.md, "21 Sep (later) -- pack in scenes". Related: [[drive-the-real-page-with-stubs]].

**UPDATE 22 Sep -- Deploy 1 (Social pack-in-scene) SHIPPED, commit 170eade, live-gated clean (dep-dap116rncjis739qnvd0,
05:24 UTC 22 Sep).** Resumed from the 21 Sep hold on "spend a few credits and get to a stage where you can live
deploy": ran the two remaining trials (2 credits -- nutrition-scene backstop proven clean, side placement now
sized "about a quarter of the frame's height" and reads as a supporting element, not pasted-on), fixed the
unreadable overlay badge (dark background, zero cost), kept "Pack in use" as an option, shipped with the stated
known limits (pouring can still draw a second pouch; an invented mark/garbled claim is intermittent, human eye
still needed). Full Deploy 1 scope (brand-scoped chooser, session reference photo, per-post role+label, packscene.py
wording, scene backstop, Rename Enter/Escape) is now live. NOT verified on live: a real Social batch with the owner's
own login and credits (proven so far only on this session's trials + the owner's LOCAL batch); the reference-photo
path on live; Rename-by-Enter on live. Owner still to rename the 2 live pack items ("Heritage milk.avif" = Happy
Full Cream is still the default pack wherever nobody picks one). NEXT: Deploy 2, Carousel -- CTA slide always an
image slide, and the 4:5-silently-becomes-16:9/1:1 ratio fix (use 3:4, proven by trial T8) -- not yet re-planned,
bring a short plan before building. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Deploy 1 ... SHIPPED".

**UPDATE 22 Sep (later) -- Deploy 2 (Carousel pack-in-scene) SHIPPED, commit 9a6e64d, live-gated clean
(dep-dap1cdv40ujc73bt1uqg, ~05:49 UTC).** Carousel now has the same real-packs-only chooser as Social, plus
its own shows_pack-driven per-slide role (writer suggests, position decides the CTA slide, person always
overrides). Fixed the 4:5->3:4 ratio bug (proven with a real generation + simulated crop) and a latent
use_cast bug in single-slide regenerate. Both pack-shot deploys (Social 22 Sep morning, Carousel 22 Sep
later) are now live. NOT verified on live: a real Carousel batch with the owner's own login/credits. Owner
still to rename the 2 live pack items and try Carousel for the first time since this shipped. Full entry:
BRAND_GROUNDING_TESTING_LOG.md, "22 Sep (later) -- Deploy 2 ... SHIPPED". No further pack-shot work planned;
next open items are unrelated (PR-release export+footer, competitor-notes, PPTX/DOCX native-shape charts).

**UPDATE 22 Sep (Round 16) -- first live batches tried, commit 3bc4393 shipped and live-gated clean
(dep-dap264u7bikc73bb5ht0, ~06:43 UTC).** Social: clean, no defects. Carousel: CTA pack-size fix shipped
(proven on a real hand-off generation); the added-slide identity mismatch traced to the cast checkbox being
off (no code fix -- existing mechanism, owner's call to use it); a nav-overflow bug (Memory clipped at
mid-large widths) found and fixed, unrelated to packs. STILL OPEN: "except the last slide, random packs"
not yet reproduced from what was shown -- awaiting a concrete example (which carousel, which slides) from
the owner. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 16".

**UPDATE 22 Sep (Round 16 follow-up) -- finding 4 confirmed + fixed, finding 3 clarified as an architecture
limit. Commit 3a9102a, live-gated clean (dep-dap2dg0u01pc73d2qp10).** The owner's concrete example (3 slides,
each a different invented pouch) confirmed shows_pack was landing false on delivery/hand-off scenes that
plainly put the product in frame. Reworded the writer instruction to "visible at all, even carried/handed
off" and verified on the REAL model (14/15 slides correctly true on a similar milkman objective, up from
effectively 0 before). Finding 3 (added slide's man not matching) has no code fix -- "Include a recurring
model/cast" is one choice for the WHOLE carousel, and this concept mixes a recurring milkman with different
households per slide, so turning it on would be wrong for the other slides; true per-slide cast control does
not exist yet, flagged as a real gap, not built without the owner's go-ahead. Full entry:
BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 16 follow-up".

**UPDATE 22 Sep (Round 16, the real answer) -- the cast feature's only entry point was invisible, now
fixed. Commit 0474a11, live-gated clean (dep-dap3a4qjnfac73bdgub0).** "AI-draft a cast reference, from this
concept" -- the ONLY way to create a cast reference for Carousel (no upload button on this card) -- was an
inline ternary inside a `{{ }}` hole that this template engine does not evaluate; it rendered as an EMPTY,
invisible span whose click handler worked perfectly underneath. The whole feature has been unusable since
round 93. Fixed, plus a second live instance in the same card (the route-picker's selection ring never
visibly updated), plus a permanent checkfe.py guard against this whole bug class (already named twice
before in this file's own comments). The owner can now actually draft and sign in a cast reference. Full
entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 16, the real answer".

**UPDATE 22 Sep (Round 16, final) -- age unlocked (scoped to shots whose own words call for it), CTA pack
size sharpened, both proven on real generations. Commit 3117ed2, live-gated clean
(dep-dap42c2jnfac73be9lbg).** Age in the identity-lock prompt now follows the shot's own words exactly like
clothing already does -- the owner's own scoping: only for multi-year-transition slides, same cast
elsewhere for face fidelity. CTA pack size got a concrete "no larger than a real pack in an average adult's
hand" anchor, the owner's own tested wording. `tools/test_identity_lock.py` closes a real gap (this prompt
had no test coverage at all before today). **Round 16 is closed out clean** -- every real finding from the
owner's first live batches (Social clean; Carousel's pack sizing, shows_pack, the invisible cast-draft
link, and now ageing) is shipped and live-verified. Only per-slide cast control remains genuinely open,
deliberately deferred, owner's call. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 16, final".

**UPDATE 22 Sep (Round 16, side-role size) -- the `side` placement gets the same real-world size anchor as
`cta`. Commit 5a1aa4e, live-gated clean (dep-dap4miu8bjmc73ape4mg).** Owner ran two carousels back to back
to stress-test the age and size fixes: ageing held in both; pack size held on CTA but was "completely off"
on `side` role slides in the carousel with tighter close-ups. Root cause: a frame-height FRACTION doesn't
scale correctly across compositions the way a real-world size anchor does. Fixed with the identical wording
already proven on `cta`, verified on a real generation of the exact close-up composition that failed.
**Round 16's pack-shot work is now complete** -- both `side` and `cta` proven on real generations in their
actual failure compositions. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 16, one more".

**UPDATE 22 Sep (Round 17, pack personalization) -- the carousel writer was independently inventing a
"face printed on the pack" idea in two different concepts, which fought packscene's own "reproduce it
exactly" fidelity instruction and produced garbled, oddly-proportioned packs. Commit d48f548, live-gated
clean (dep-dap57eou01pc73d5on1g).** Fixed both layers: the writer prompt (producers.carousel_concept) now
forbids describing the pack's printed design changing, and packscene.clean_scene gained a `_PERSONALIZED`
strip pattern as a backstop, same mechanism as the existing back/nutrition-panel fix. Verified on a real
generation of the owner's own exact scene text -- pack now renders unaltered. Separately checked and ruled
OUT as a bug: "forcing a pack into every slide" on the other concept -- the per-slide role resolver
correctly respects the writer's own shows_pack:false; that concept's writer just judged nearly every beat
of a milkman story as product-adjacent, a legitimate per-slide call, not a wiring defect. Full entry:
BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 17".

**UPDATE 22 Sep (Round 18, pack size in hero poses) -- wording alone could not fix an oversized pack in
two "advertising hero shot" poses (presented at arm's length; freestanding centrepiece on a table).
Commit 169e004, live-gated clean (dep-dap5gqjncjis739v62tg).** Tried strengthening packscene.py's size
wording (absolute paperback-book anchor + explicit pose ban) first -- proven to FAIL on 2 real generations
(fal fallback, local Gemini credits exhausted). The actual fix: stop producers.carousel_concept's writer
proposing these poses at all (same lever as the personalisation fix) -- verified directly via 2 real
writer calls, 6 routes, zero hero-pose phrasing on any pack-visible slide. Documented as a third
wording-cannot-remove limit in packscene.py's own docstring, alongside `in_use` and the fssai slip.
Image-level proof of the actual fix still needs the owner's next live carousel run. Full entry:
BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 18".

**UPDATE 22 Sep (Round 19, crate = two packs) -- owner redrafted a FRESH concept to retest Round 18's
hero-pose fix; it held (correctly sized, no presenting poses). New defect found instead: a "milk crate"
scene drew TWO sharp packs, breaking the existing "exactly one pack" rule -- same clash class as
nutrition-panel/personalisation, just not one the wording named. Commit e9ab704, live-gated clean
(dep-dap5p7u7bikc73ber9hg).** Fixed: FRONT_ONLY_ONE_PACK now explicitly handles crate/shelf/stack scenes
(one real pack, rest blurred). Verified on the owner's own exact scene, real generation. Also separated
out and explained two non-bugs the owner flagged in the same message: an invented prop in a no-pack slide
(unrelated to packscene, model's own liberty on an empty-handed portrait) and shows_pack attaching a pack
to a "crate" mention with no literal word "pack" (the writer's own explicit judgment call, by design, not
the regex heuristic). Ruled out "Social vs Carousel cross-contamination" -- they share one pipeline, not
two. Full entry: BRAND_GROUNDING_TESTING_LOG.md, "22 Sep -- Round 19".
