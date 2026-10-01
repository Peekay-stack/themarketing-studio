---
name: round31-queue
description: "The consolidated task list / A-B test / experiment board pulling together every open item from Carousel's brand-grounding work, the Image and Video Engine Playbook, and the Format Signal Study — check this before scoping any next round of work"
metadata:
  node_type: memory
  type: reference
  originSessionId: 60d5a7b2-1e0f-4999-a432-7547cc82bb56
  modified: 2026-10-01T11:02:49.345Z
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
