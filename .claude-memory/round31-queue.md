---
name: round31-queue
description: "The consolidated task list / A-B test / experiment board pulling together every open item from Carousel's brand-grounding work, the Image and Video Engine Playbook, and the Format Signal Study — check this before scoping any next round of work"
metadata:
  node_type: memory
  type: reference
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-10-01T13:02:12.180Z
---

**LIVE DOCUMENT**: [Round 31 Queue](https://claude.ai/artifact/UpSArgACG53yWTUCPVwFSV)

Built 25 Sep by consolidating every still-open item across four threads into one operational board:
[[brand-grounding-modes-project]] (Carousel, Rounds 21-30), [[image-gen-engine-research]] (the Image and
Video Engine Playbook artifact), [[cross-category-format-study]] (the Format Signal Study artifact), and
the [[studio-work-inventory]]/[[pending-work-list]] backend/platform items paused when Carousel work
began (measurement ledger phase 2, Video plan-binding, multi-brand concurrency risk, beta deploy Phase 4,
POSM/Onground brand-voice gap, brand-character's reference photo, PR/Sales-enabler parity, Video's
doc-layer gap + Sales-enabler channel economics). 33 items total, sorted into three buckets, not just one
flat list:

- **Task list (23)** — nothing blocked on an experiment. Items 1-15 are the creative-pipeline items; 4 of
  those are genuinely ready to build now (headline-safe negative space beyond the CTA, a defensive
  no-typography style cue, fixing the writer's own few-shot inconsistency, and Video's narrowly-scoped
  negative_prompt wiring). Items 16-23 are the platform/infrastructure items from the pending list, all
  needing scoping — the two flagged as the most concretely scoped starting points are #16 (measurement
  ledger phase 2) and #20 (POSM/Onground brand-voice gap).
- **A/B tests (3)** — Kling 3.0 vs Veo 3.1 on a multi-shot same-character sequence (tests Kling's claimed
  strength against this project's known weakness); current CTA wording vs a further revision (Round 29's
  fix reduced but didn't eliminate oversizing — is wording at its ceiling?); composited vs fully-prompted
  CTA, once a compositing prototype exists.
- **Experiments (5)** — three Carousel defects that only have one confirmed data point each and need more
  before they're treated as systemic (the cast-ticked-unselected unreliability, the slide-1 child→adult
  override, the invented-product defect); plus two quick video-pipeline checks (does Seedance's
  region-level editing actually work on a label, and does a storyboard→video ratio mismatch silently
  distort the way Round 22 found for stills).

Update the artifact directly as items move (same URL, republish with `url` set) rather than tracking
progress only in chat — this is meant to be the actual working board for whatever gets picked up next,
not a one-off summary. Update the three source documents' own findings first if something here turns out
to be wrong; this board should always agree with them, not drift from them.

## UPDATE 28 Sep, later same session — item 20 (POSM/Onground brand-voice gap) built + tested locally, NOT shipped
Traced the full blast radius rigorously before touching anything (per the user's own ask): `producers._ctx()`
is the SHARED context-builder behind not just POSM/Onground but also **Social's own carousel-concept
writer** (`producers.carousel_concept()`, behind `/social-carousel-concept`) — a wider, previously
undisclosed blast radius than first proposed. All 3 never called `brandprofile.voice_block()` at all,
unlike Social/Video's own single-post path (`prompts.system_for()`).

**Built** (uncommitted, local only): `_ctx()` now includes `voice_block()` — skipped only in
Independent/General mode (matching the character-reference precedent already in this function), with
mandatories dropped only when nothing at all is bound (reusing the function's own existing "no strategy
attached" check, no new parameter threaded through 6 functions/5 routes). Full design reasoning and exact
diff in the conversation; `py_compile`/`selfcheck.py` clean, no frontend change needed (this function's
output never reaches the screen).

**Tested locally with real generation, before vs after, 3 real API calls each** (house 063785d77c /
"Nothing Cut", real Heritage Foods brand profile with real mandatories/competitors/tone): confirmed
deterministically via a direct `_ctx()` call that the brand block is now present, AND confirmed in real
LLM output — most clearly on Social's carousel, where every CTA slide across all 3 routes went from a
bare hashtag to the brand's own mandatory line + FSSAI mark stated almost verbatim, plus market-correct
delivery-context imagery that wasn't there before. POSM/Onground showed a softer but real shift toward
more literal, market-grounded claims. No regressions found (no competitor leaks, JSON parsing intact
across all 6 calls).

**Then: user asked to compare old (live) vs new (local) using their REAL live content** ("Heritage IMC" /
"The Morning Pour", which they'd just tested live). Confirmed local and live tenants are genuinely
separate storage (`STUDIO_DATA_DIR` unset locally → falls back to the repo folder; set to `/data` only on
Render) — grepped the local tenant to be sure rather than just citing the config; the user's real content
is NOT present locally. Proposed pulling it down via the live site's own read-only routes, which needs the
user to actually log into live themselves first (no tool here can read Render's disk directly, and I don't
handle live credentials). **User deferred this to tomorrow morning, and downgraded to the faster option**
(local dev-tenant data, pattern-level comparison, not an exact-content pull-down) — so tomorrow starts with
that quicker local test, not the live-data mirror.

**Status: code sits uncommitted in `producers.py`, nothing pushed, nothing live-affected.** Pick up
tomorrow morning with local-only testing using the existing local dev-tenant content (house `063785d77c`
"Nothing Cut" already proven to show a clear before/after). The real before/after examples from today are
in this session's own transcript if a fuller write-up is needed before shipping.

## UPDATE 29 Sep — item 20 superseded, shipped as part of a much larger rebuild
What started as the item-20 brand-voice fix grew into the full [[prompt-priority-framework-gate-territory-task-evidence]]
initiative: a Gate/Territory/Task/Evidence prompt-priority framework built for the producers, then wired the
same way into Brief/Messaging House/Idea Platform/Campaign/Plan (four phases). **Shipped 29 Sep, pushed to
`master`, deployed.** See that memory file and its artifact for the full record — this line just marks item
20 done and points onward rather than duplicating the account here.

## UPDATE 1 Oct — Video grouped and fully scoped (see [[staleness-tracking-thread]]'s sibling Video work,
same session), two board corrections found, Phase 1 shipped

Asked to revisit the task list and club it by tab; Video was picked up next. Two stale listings corrected
by checking the live code directly rather than trusting this board's own 25 Sep text:
- **Item 17 ("Video plan-binding") was already Done** — built end-to-end 6 Sep (`bagVideoExec`, full
  field-selector form, `createVideoExecution`), confirmed still live in code. This board never got
  updated after that build landed. Marked Done.
- **Item 23's Video half was scoped wrong.** The old record said the fix (`cut.py`'s manifest) was
  "already built, just orphaned" — checked directly: `cut.py` IS now fully wired (all 7 routes called),
  but it only ever covers the post-production edit pass, not the pre-production script/department-card/
  character-sheet/scene-frame layer that was actually the gap. Rescoped fresh.
- **Item 5 (camera-movement gating) reframed** — no dropdown exists to gate (checked); the real,
  previously-unknown finding is that every script row's own free-text `camera` field is written, shown,
  and silently discarded at render time. Smaller, more correct fix than building a new control.

**Full Video scope, 5 phases** (negotiated with the owner before building, per the "scope it fully
including phases" ask):
- **Phase 1 — shipped, live (commit `011e193`).** New `filmscript.py`: one draft per house (not a new
  project id — nothing upstream gives a video script one), persists script/department-cards/character-
  sheet/scene→frame-mapping, all of which were pure React state with zero backend route before this —
  a real reload mid-scripting lost it outright. Verified live against the real Heritage house: set a
  realistic complete draft, confirmed autosave landed server-side, did a genuine page reload, confirmed
  everything came back exactly as written; confirmed the hydration itself doesn't wastefully re-save,
  and a real edit after reload still saves correctly.
- **Phase 2 — shipped, live (commit `6eaed99`).** Wire Veo's `negative_prompt` (item 4): new
  `VIDEO_NEGATIVE_PROMPT` constant ("text, typographic letters, watermark, logo, warped geometry"),
  fixed and unconditional, added to the one `params` dict `gemini.video()` already builds. Verified
  without spending real API credits — `httpx.post` monkeypatched to capture the real request body
  before a forced failure, confirming `negativePrompt` reaches the exact same request shape a live call
  would send, alongside the existing `aspectRatio`/`durationSeconds`.
- **Phase 3 — shipped, live (commit `823cdd5`).** The camera-movement reframe above (item 5): the
  script's own per-scene `camera` field now actually reaches `segment_prompt()` (previously captured
  and shown on screen, never used), and the `from_frame` branch (the one with a real locked face to
  protect, by construction) always appends an identity-protecting qualifier. Verified by calling the
  real `/produce-video` route function with a monkeypatched `gemini.video()` capturing the exact
  prompt text for two shot types — no API spend.
- **Phase 3b — shipped, live (commit `d79e522`).** The owner answered the open question: build the
  picker, but as a pure OPT-IN boost, never a default -- unset, behaves byte-identical to Phase 3;
  chosen, the person's own classification REPLACES the blanket "no rotation" caveat with "stay
  recognisable through whatever this movement does" instead, which is the actual boost (a genuinely
  dynamic shot can now be asked for without the default phrase arguing against it in the same
  breath). New optional per-row `movement_class` field, no backend persistence change needed (Phase 1
  already saves rows whole). Full backward/forward blast-radius sweep done afterward, per the owner's
  own request -- nothing upstream depends on this field at all (backward: none); forward, checked
  every consumer of a script row by hand: `rewriteScene` correctly preserves it across an AI rewrite
  (merge-order confirmed), a full regenerate correctly resets it (expected), the Word export/import
  round-trip silently drops it back to default (confirmed this is the SAME pre-existing shape the
  `audio` field already has, not a new gap), the still-image generation step deliberately does NOT
  read it (movement has no meaning for a static frame), and no other producer touches `fullScript` at
  all -- fully contained to Video. Verified (zero API cost) with three direct cases against the real
  route function: unset identical to Phase 3, a safe class replacing the caveat, the risky class
  honoured with identity still named. Then live: real dropdown rendering, the risk note showing only
  on "orbit", a real UI pick persisting through the existing Phase 1 autosave untouched.
- **Phase 4 — experiment first, not yet run.** Storyboard→video ratio-mismatch check — confirmed no
  dimension check exists; run a real mismatched test before writing any fix.
- **Phase 5 — trials, lowest commitment, last on purpose, not yet run.** Kling 3.0 vs Veo on cast
  consistency; Seedance 2.5's region-level editing on a real product label (possible shortcut past the
  parked Veneer Technique CV pipeline). Confirmed low-effort: `model_id` already flows as a plain string
  straight through to `creative.video_from_image()`.

The live artifact (same URL) was republished to reflect all of this directly, per this board's own
standing instruction to update it as items move rather than only recording progress in chat.

**Phase 4 blocked, same day: the Gemini API key is out of money.** Attempting the real ratio-mismatch
test (owner approved the ~$0.20 spend first) failed immediately on the very first call —
`402 RESOURCE_EXHAUSTED — "Your prepayment credits are depleted."` This is the SAME `GOOGLE_API_KEY`
configured in the local `.env`; if Render uses the same key (likely, no evidence of a separate one),
**every real image/video generation on the live site is failing the same way right now**, not just
this test. Owner is topping up credits at https://ai.studio/projects and will say when done — Phase 4
resumes then. See also [[beta-deploy-plan]]'s own open Phase 4 (spend caps) -- this is a live instance
of exactly the gap that item names.

**PICK UP HERE: owner is doing live testing of Phases 1-3b tomorrow, 2 Oct 2026.** Nothing further to
build until that feedback arrives -- check this file first for anything the owner reports before
assuming it's a new, unrelated issue. What's live to be tested: Phase 1 (script/department-card/
character-sheet/scene-frame persistence across a reload), Phase 2 (Veo's negative_prompt), Phase 3
(the script's own camera field reaching generation + the automatic identity qualifier), Phase 3b (the
optional movement-class picker per script row, including the "orbit" risk note and that it persists
through Phase 1's autosave). Phase 4 (ratio-mismatch experiment) and Phase 5 (Kling/Seedance trials)
remain blocked/unscheduled respectively -- Phase 4 specifically waiting on the owner confirming the
Gemini billing top-up above before any further real API spend.

## UPDATE 5 Oct — owner's live test of Video Phases 1-3b came back; four fixes SHIPPED live (`96ab123`)
Live test findings: camera-movement dropdown works; cast fidelity good; but (a) the closing frame came back
with a green/ghee-gold pack, not the real orange "Happy Full Cream Milk" one; (b) one scene rendered as a
3-panel collage; (c) department drafts contained questions addressed to the owner; (d) only a global
re-render, no single-frame correction. All four shipped, confirmed live via `/selfcheck`.
- **Root cause of (a), not what it looked like:** the storyboard card's "Include the locked pack" checkbox was
  gated on `posm.packChoice` (POSM's pick), not Video's own `videoPackChoice` -- so with a pack picked in Video's
  assets panel the checkbox never appeared, and `pack_id` was never sent. A scene whose words pulled a pack in
  attached the tenant's NEWEST signed-off pack instead. Fixed: gated on `videoPackChoice`; the closing scene
  defaults to carrying the pack (`packOnFrame()`); `pack_pref` (the pick) rides every frame and only decides
  WHICH pack; `pack_mode:'auto'` lets "pouch"/"sachet" count; explicit un-tick sends `include_pack:false`.
- **Colours:** model obeys scene text over the reference photo (known lesson). Writer rule `VISUAL_RULES`
  (full script + scene rewrite: call it "the pack", never its colours; one scene = one view), plus backend
  `video_frame`-gated sentence + `packscene.scrub_pack_colours()` (narrow: colour words attached to a pack noun).
- **(c)/(d):** `frame_note` on the script row (doesn't reset approval), input per storyboard card, appended LAST
  in that frame's prompt; `plainDept()` drops "?" sentences at draft time and at every read site.
- All new `/scene-still` behaviour sits behind `video_frame`/`pack_pref`, sent only by Video; Social/Carousel/
  POSM/shot-reference prompts byte-identical (verified by prompt capture, zero API cost).
- **NOT verified:** a real render. The local tenant has no real pack photo, so whether the pack now comes back
  orange needs the owner's live re-test (needs Gemini credits -- see Phase 4 note above; don't spend without
  approval). Local filmscripts store was empty, so the colour-scrub was tested on representative text, not the
  owner's real scene-6 wording.
- Noticed, not fixed: literal `…` shows in the storyboard card's "Match this to another shot…" option
  (HTML template, not a JS string, so the escape isn't decoded) -- pre-existing, one-char fix, ask first.
- Still open from before: Phase 4 (waiting on owner's Gemini top-up), Phase 5 unscheduled; Word export/import
  drops `movement_class` (same as `audio`); Shoot Board read-only script ref doesn't show movement class.
- **5 Oct blast-radius sweep of `96ab123` (clean, nothing broken; three pre-existing gaps now matter more, none fixed):**
  (1) `/scene-still` caps references at 3 and fills caller refs first (cast ref + chosen "match to another shot" sibling = 2)
  then library cast -> the pack is silently DROPPED when a sibling is picked and a signed-off cast exists (response says
  `pack_used:false`, the card ignores it, and the new pack-colour guard only fires when `pack_used`). (2) `sceneIncludePack`
  is index-keyed, never reset on a new script/house and never persisted -- explicit ticks leak across scripts in a session and
  vanish on reload (default "closing scene carries the pack" returns). (3) Old department drafts that contain questions are
  still SHOWN in the textareas and exported raw in the production-bible Word doc; only prompt reads are cleaned.
  Also: `frame_note`/`movement_class` ride in whole rows into the script-rework, cast-sheet and dept-draft LLM prompts, and a
  script rework replaces rows wholesale, so both can be dropped by the model (same limit as movement_class).
- **5 Oct, owner's screenshot -- two more items logged (PLAN only, nothing built):** after the Cast/Location department notes were
  drafted and "Re-derive from script" pressed, "Real references" still read "Describe in words instead" (Cast/actor) and "Nothing
  signed off yet." (Location). Traced: NOT a wiring break -- those pickers choose real signed-off library PHOTOS (`videoCastChoice`/
  `videoPlateChoice`, `videoAssetOptions` filters `signed_off`); Derive only writes the text cast sheet (`videoCharacters`), and the
  Location note is read raw at "Lock location and cast" (`plainDept(shoot.location)` -> `/cast-reference` `location` -> "in this
  setting: ..."). The labels read like unresolved/blocking states though the words ARE used. Related real issue: dept notes are
  production PLANS (markdown `**`, "Secure a single practical home...", "Cast four roles...") yet go raw into the lock call and
  into EVERY frame prompt (Location+DoP+Props+Wardrobe). Also no staleness signal when the notes/sheet change after the lock.
  Plan: A+B honest status lines (frontend only), C a derived short visual location line alongside the cast sheet (needs owner's
  yes), D optional "locked image out of date" marker.
- **5 Oct, later: owner asked for an AI cast generator in Video's "Real references" (as in Social/Carousel/POSM) + a revised plan that
  includes the blast-radius findings. Plan only.** New finding while reading: `generateFrame` never sends `cast_id`/`plate_id` (only
  `buildCastReference` does), and `/scene-still` defaults `use_cast` to true, so every Video frame ALSO attaches the library's NEWEST
  signed-off cast (+ plate) regardless of the pickers -- it spends one of the 3 reference slots and can mix in a different person; it is
  also what crowds out the pack. Candidate fix = a "reference budget" (lock image > pack > sibling > plate; library cast only if picked).
  Social/Carousel/POSM generator = `/cast-reference` n=3 -> pick -> `/library-adopt` kind cast sign:true; Video's lock makes ONE composite
  (cast+location) image, 4 roles in the screenshot, not signed in. Signing a group shot into the library would pollute Social/POSM's cast
  list and, via newest-wins, silently re-cast other pieces -> recommend candidates become the lock image, "save to Memory" optional.
- **5 Oct: Phase 0 of the revised Video plan SHIPPED live (`d75c791`)** -- reference-slot priority. Frames now send explicit cast_id/plate_id picks and
  use_cast/use_plate:false when nothing is picked; `/scene-still` (video_frame only) fills slots pack > plate > library cast; a frame ticked for the
  pack that came back without it shows a card warning. Verified by reference-set capture (8 cases incl. legacy controls) + real page with stubs; NOT
  verified on a real render. Watch-for on retest: dropping the auto-attached library cast could change face/wardrobe fidelity (cast was "good"
  before) -- one-line revert in `generateFrame` (`use_cast`). Owner decisions: (1) cast generator = picked option becomes the lock directly, optional
  "Save to Memory" (YES); (3) start Phase 0 (DONE). (2) clean old question drafts: not understood -> my default = leave boxes alone, clean Word export,
  small "contains a question" hint (awaiting nod). Remaining: Phase 1 (persist/reset pack ticks+sibling per scene, rework keeps row extras, question
  drafts), Phase 2 (status lines, Location line, 3-option cast+location generator, out-of-date lock marker), Phase 3 (`…`).
- **5 Oct: Phase 1 of the revised Video plan SHIPPED live (`78d8498`)** -- frontend only. Pack tick + "match another shot" moved from index-keyed state
  maps (`sceneIncludePack`/`sceneSiblingRef`, now removed) onto the script row (`include_pack`, `match_no` = scene number) so they save with the script and
  a new script starts clean; `SCENE_EXTRAS` (frame_note, movement_class, include_pack, match_no) stripped from rework/cast-sheet/dept-draft/rewrite prompts
  (`scriptForPrompt`) and carried onto reworked rows by scene number (`keepSceneExtras`; frame_note only if the scene's visual is unchanged, also dropped on
  single-scene rewrite when visual changes); question-style dept drafts cleaned on load (`cleanShootDrafts`, toast; all-question draft -> idle/empty) and in
  the production-bible export. Owner approved cleaning ("go ahead"), so the "hint only" default was NOT used. Tested on the real page with stubs (load,
  autosave carries the tick, sibling, no leak into a new script, rework, rewrite, export). Remaining: Phase 2 (status lines, Location line, 3-option
  cast+location generator, out-of-date lock marker), Phase 3 (`…`).
- **5 Oct: Phase 2 of the revised Video plan SHIPPED live (`6d7eb60`)** -- status lines under Cast/Location pickers (say what is used); `videoLocationLine`
  (new filmscript field `video_location_line`, derived by the same "Re-derive from script" button via `deriveLocationLine`, editable, used by the lock and every
  frame via `locationText()` -- falls back to the Location note cleaned by `stripMd`+`clipText(320)`); "Show me 3 options" (`generateCastOptions`, `/cast-reference`
  n=3, NO backend change) -> "Lock option N" (`pickCastOption`) makes the pick the lock directly; optional "Save to Memory as cast" (`saveCastLockToMemory`,
  `/library-adopt` sign:true) -- never automatic; out-of-date lock marker (`castLockSig` taken before the render wait vs `castSig()` now); plainDept bug fixed
  (it dropped unpunctuated lines from texts containing a "?"). Tested on the real page with stubs (zero API spend); NOT tested on a real render -- the 3-option
  draw costs 3 image renders, needs Gemini credits + owner's go-ahead. Left: Phase 3 (`…` in the sibling dropdown), Video Phase 4/5, and the owner's
  retest of Phases 0-2 on real renders.
- **5 Oct: Phase 3 + full wiring sweep SHIPPED live (`97dd462` dropdown `…`, `9a6445e` POSM "Not assembled —" same bug class -- 2 visible instances in the
  template, 3 more only inside HTML comments; `cddebea` sweep fixes).** Sweep of Phases 0-3 found + fixed: (1) three clears of the lock image (Grounded/Independent
  switch, image-engine change, Look change) left `castOptions` showing -> now cleared; (2) a stale page (opened before the Location line existed) would blank
  `video_location_line` on autosave -> `filmscript.save` keeps the saved value when the key is absent (explicit "" still clears). Verified: `tools/test_pack_choice`,
  `test_identity_lock`, `test_library_naming`, `test_carousel_concept`, `test_tools` (18) all pass, `selfcheck` 1250 calls 0 problems, `smoke`, tenants untouched.
  Known, NOT fixed (pre-existing): `castRefUrl` is never persisted (lock must be redone after a reload while `scene_frames` persist); switching HOUSE inside Video
  doesn't clear the previous house's lock/options; mode-switch reset keeps `videoCharacters`/`videoLocationLine` on purpose (typed overrides). Gotcha: the Edit tool
  turns a literal backslash-u sequence into the real character on both sides -> use a Python script with `chr(92)` for those.
  Nothing real-rendered yet; owner's retest of Phases 0-3 needs Gemini credits.
- **5 Oct (evening): owner's live test of Phases 0-3 on real renders -- FINDINGS, PLAN ONLY (nothing built).** Phase 2 UI worked (Location line, 3 options,
  lock, Save-to-Memory). Frame defects traced mostly to the SCRIPT, not the renderer: (1) the 30s script has scenes 5-6 duplicating 1-2 (writer is told
  5-7 scenes via `sceneRange` -- min 5 -- "do not pad", concept has fewer beats) so scene 6's "pack shot" row carries "the boy grows... school uniform, cricket
  kit, exam books" -> tall son + extra people around the pack; (2) taglines/supers sit in `visual` ("One standard, one source." in rows 2 and 6, title +
  FSSAI in row 4) -- origin not verifiable locally, likely signed-off locked-copy (`library.locked_copy`, injected by `learningContext('script')` as
  "place exactly as written") or approved anchors; (3) scene 2 pack shows no milk flowing: Video's `pack_clause` forces FRONT-ON, `packscene` 'in_use' role
  exists only for Social; (4) scene 3 older mother in green not cream: cast sheet says "(cream-draped when older)" as a parenthetical, lock image holds
  both ages as two people, scene text silent on wardrobe; (5) Video frames have NO reference-role labels (Social's `_ref_labels` proved to help, Round 20).
  Also: "Inputs to guide generation" panel is nearly inert on the Video concept step (`inputsContext()` only adds attached ref NAMES + a duplicate
  guidelines clause; `brandPreamble` already carries the voice; default `guidelines:false`); 12 identical "Carousel cast" chips (Carousel adopt never numbers
  names; POSM does -- "AI-drafted cast #N"; my Video Save-to-Memory name also repeats); Location line can silently drift from the Location note (no
  source-note marker). Proposed order: script fixes (S1 scene count, S2 repeat warning, S3 visual = camera only, S4 wardrobe/age continuity) -> frame fixes
  (F1 role labels, F2 pack-in-use wording) -> panel logic + unique cast names -> Location-line sync marker.
