---
name: video-edit-consolidated-build-list
description: "MASTER LIST (26 Oct) — every Video + Edit-room change discussed that day, de-duplicated into 3 workstreams + trials + owner decisions + parked options. NOTHING BUILT. Build after the weekly quota resets. Start here, then open the detail files."
metadata:
  node_type: memory
  type: project
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-26T09:40:42.811Z
---

**Status: consolidated 26 Oct. Owner then said "start with the build for video improvement first ... we will pick the editor later" (quota reset). BUILT + PUSHED so far: B1 + B2 in commit `8f750c8` (see note below). Everything else NOT built — Workstream A (editor) deliberately waits until the owner picks it.** This file is the single ranked view; the detail (code lines, evidence, measurements) lives in [[cutdown-fidelity-build-plan]] (A), [[video-generation-upgrade-queue]] (B + Remotion), [[ai-filmmaking-course-audit]] (handout + Mahabharat + prompt comparison) and [[video-editor-build-plan]] (26 Oct cutdown investigation + VN review). Sizes are MY estimates (S ≈ hours, M ≈ a session, L ≈ several). Follow [[change-discipline-working-agreement]] and [[audit-sibling-entry-points-not-just-my-diff]] on every item (diff `produceVideo` vs `renderCut` vs `/rescore`, Google vs fal paths).

## Owner decisions needed BEFORE building
- **D1 — how the cutdown keeps the real pack/cast/location (A1).** (a) reuse the ALREADY-RENDERED original clips for scenes that survive the cut (cheapest, keeps the pack by construction), plus (b) generate frames only for genuinely new scenes (image-gen spend) — my recommendation; or (c) reuse-only, new scenes flagged "no frame — pack won't hold".
- **D2 — scope of Workstream B** (items B1-B7) and whether the engine trials (T1) run first.
- **D3 — whether C (VN-inspired extras) is in this round.**

## A. Edit-room cutdown fidelity (Priority 1 — fixes the 30s-vs-20s failure)
| # | Change | Size | Notes |
|---|---|---|---|
| A1 | Cutdown carries pack/cast/location: reuse original clips/frames for surviving scenes; generate frames for new scenes via `/scene-still`; brand endframe always reuses the original pack frame | L | root cause: `renderCut` sends rows with no `frame_url`; `characters` is never read in the picture path. Spends image credit for new frames (D1) |
| A2 | Pre-flight warning when a cut has frameless shots (like the Production stale-frame guard) | S | |
| A3 | Record per-shot refs/provider/from_frame at render; persist clip list with the cut; run continuity check on a cutdown's own shots | M | `/produce-video` returns bare URLs; `startCutFromFilm` passes no refs; `prodClips` lost on reload → "No frames could be measured" |
| A4 | VO pause: normalise em/en dashes before TTS (ellipsis, or Chirp `[pause]` markup), steer the rescript prompt off dashes | S | measured: em dash = 0 pause, ellipsis 0.47s, `[pause]` 0.8s; Telugu untested (T4) |
| A5 | Captions on the REAL picture timings + `fontsdir` to bundled Noto (fixes Telugu boxes) | M | captions use draft `secs`; picture cuts at 4/10/16s; `burn_captions` hard-codes Arial |
| A6 | Send `sound_plan` on the cutdown render | S | `renderCut` omits it, `produceVideo`/`rescoreCutdown` send it |
| A7 | Verify: side-by-side request-body diff + owner re-renders the 20s trigger case | — | acceptance = real orange pack holds, VO pauses, captions on cuts, Telugu readable |

## B. Video generation quality (Priority 2 — main film)
| # | Change | Size | Notes |
|---|---|---|---|
| B1 ✅ DONE `8f750c8` | Per-film "camera & lens" block (body, lens logic, DOF, handheld intensity, grade, "no VFX/slow-mo/flare/readable signage/brand logos") restated in EVERY shot prompt, **injected at the FRAME stage (`/scene-still` craft) as well as `segment_prompt`**; add shot-variety rule to `VISUAL_RULES` | M | frame look is "advertising photograph, DSLR 50mm, crisp, ultra-detailed" = clean AI look; keep the `brand` endframe HOLD |
| B2 ✅ DONE `8f750c8` | Stop the spoken line leaking into the VIDEO prompt (`scene_text` joins `visual: dialogue`; also carries the timecode) — pass visual only | S | affects every film; effect unverified → test first (T3) |
| B3 | Per-element reference tagging for cast + location (pack stays first-frame) | L | blocked on trial T1 (does Veo 3.1 take multiple references? fal Kling/Seedance elements?) |
| B4 | Location sheet with a wide + a tight angle | S build | **owner content task: sign a Heritage location plate** (continuity check: PLATE MISSING) |
| B5 | More shots per scene / per-shot takes (2-3 rolls) / single-shot re-roll instead of full re-render | L | depends on T1; reference film ≈1.5s/shot vs our 4-8s |
| B6 | Test the Final-tier `VIDEO_NEGATIVE_PROMPT` ("text… logo…") against the pack's printed label | S test | hypothesis only (T2) |
| B7 | Music drop/swell placed on the real turn beat; snap cutdown trims to beats | M | today "swell at the turn" is a prompt request only |

## C. Editor extras from the VN review (Priority 3 — candidates)
| # | Change | Size | Notes |
|---|---|---|---|
| C1 | Auto-captions from speech for IMPORTED films (today: manual "start end text") | M | needs speech-to-text; cost unverified |
| C2 | Fade in/out at head and tail (dissolves between shots only with sync compensation — overlap shortens the timeline and breaks VO sync) | S/M | picture has hard cuts only today |
| C3 | Denoise / stabilise / silence-trim | parked | only if imported client footage becomes common |
Not worth copying from VN: free multi-track timeline, keyframes, collage, template library, filter packs, image tools.

## Trials / tests to run first (cheap, de-risk)
T1 Veo 3.1 multi-reference + fal engine element tagging (docs + one small trial) · T2 Final render with/without the negative prompt · T3 draft shot with vs without the dialogue text in the beat · T4 Telugu pause (`[pause]`/ellipsis) · T5 cause of the shot-3 letterbox (crop 1280×608: text-to-video artefact vs engine).

## Parked options (no action unless the owner decides)
- **Remotion** (animated end-cards/supers/explainers): skill pack DOWNLOADED, NOT INSTALLED (`C:\Users\punie\Downloads\remotion-skills`); owner will experiment first and change nothing meanwhile. Before adopting: read the licence (free ≤3 employees; "Automators" per-render tier) and verify headless-Chromium hosting. Telugu caption boxes do NOT need Remotion (A5).
- Reference-film lessons NOT to copy: its props were text-free and its signage text was gibberish — keep the first-frame pack lock; don't prompt real brand signage.

## Suggested build order (when the quota resets)
1. Decide D1-D3 → 2. A (A1-A6, then A7 with the owner's re-render) → 3. B2+B1+T3/T2/T4 (cheap) → 4. T1 → B3/B4/B5 → 5. B7 → 6. C1/C2.
Carried over unchanged from before today (not re-discussed): scene-5 two-glass re-roll, spoken English gloss after a dash, the "Eleritage" badge, TMS brand book.
Infra note: the project `render` MCP (mcp.render.com) was DNS-dead 23-26 Oct — use the claude.ai Render connector (id 2edd1d5f-…) for deploy/log checks.

## 26 Oct — BUILT: B1 + B2 (`8f750c8`, pushed; deploy poll started)
**B2:** `scene_text()` (main.py ~1171) no longer joins `desc or dialogue`; the video prompt gets the visual only (dialogue kept only for a row with NO visual). Proven by capturing real prompts with the generators stubbed: 3/3 carried the spoken line before, 0/3 now; rows without dialogue are byte-identical to the committed code (a trailing colon is deliberately kept for parity). **B1:** film-wide optional "Camera & lens" note — state `videoCamera`, backend key `camera_notes`, saved as `video_camera` in `filmscript.py`; UI textarea + "Use suggested notes" (452 chars, brand-neutral, cap 600) beside the Look reference; reaches `/scene-still` frames (`craft` — told it OVERRIDES the generic DSLR/crisp wording), no-frame video shots (spine sentence), frame-animation shots (replaces the generic "restrained" camera default; explicit `movement_class` and the brand-endframe HOLD still win — verified), BOTH `produceVideo` and `renderCut`, 6 new-film resets, restore/save, and the frame out-of-date fingerprint (appended ONLY when set so no existing frame is reflagged). Also a shot-variety sentence appended to `VISUAL_RULES` (wide/medium/close-up/macro). Empty = byte-identical prompts (verified frame + video). **Lessons applied:** the wardrobe-lock sibling wiring list was the checklist; `openVideoFromCampaign` (app.dc.html ~18339) is a 6th reset site my first grep truncated — assertions with exact counts caught it; `frameRecipe` is a fixed JSON array so a new slot must be appended only when set. **NOT verified:** any real render (does handheld wording actually change a Veo clip? unknown — needs an owner draft render with the notes ON vs OFF), and the new field on a signed-in screen (needs login; served shell carries it, no JS errors). T3 (dialogue-leak real effect) is therefore still untested — the fix is logically safe but unmeasured. REMAINING in B: B3 (needs T1), B4 (owner signs a plate), B5 (needs T1), B6 (paid Final render), B7.
