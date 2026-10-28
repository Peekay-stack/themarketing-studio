# Film builder — plan (shot-by-shot generation, takes, timeline, assemble)

Status: **PLAN ONLY, nothing built.** Written 29 Oct 2026 for the owner's review. Everything is tested on **localhost first**; nothing goes live until the owner signs off.
Inputs: the Flow / Higgsfield research and the two paid trials (memory: `flow-higgsfield-research-and-trials`), the coverage + film-craft work on branch `coverage` (`VIDEO_COVERAGE_PLAN.md`, `VIDEO_CRAFT_FRAMEWORK.md`), and a code sweep done for this plan (section 6).

## 1. What we are building, in one paragraph

Today a film is rendered **all at once**: one button generates every clip, stitches them, adds voice and music, and hands back a finished film. A bad clip means re-rendering everything, and you cannot see or choose anything before the money is spent. Google Flow and Higgsfield both work **shot by shot**: generate a clip, look at it, re-roll it, keep the take you like, arrange the clips on a thin timeline, then export. The **Film builder** gives us that: every shot of the film becomes a card with its storyboard frame and its **takes** (attempts); you generate and re-roll shots one at a time (Draft first), choose a take per shot, trim, skip and reorder, preview the sequence, and only then **assemble** the film through the pipeline we already have (stitch, voice, music, mix). The Film tab's one-button render stays exactly as it is.

What we are **not** copying: Flow's one-scene-per-project limit and its reset-on-leave; Higgsfield's model marketplace; true camera control (our engines do not take it, so camera presets are prompt wording only).

## 2. Findings that shape the design (measured, not assumed)

| Finding | Source | Consequence |
|---|---|---|
| Neither product is a model; both are asset library + per-shot generation + variations + a continuity mechanism + a thin timeline. | research | We already own most pieces (frame-first, references, shot plan, director, frame check, stitch, mix). The missing layer is clip-level objects, takes, timeline. |
| `_produce_video_sync` already contains every stage we need (plan segments → render one segment → stitch → voice → music → mix), and a trial re-assembled a whole film from existing clips (`heritage_redirect.py render --reuse`) with identical results. | code sweep + 28 Oct run | The builder is **not a new pipeline**: it feeds the existing one two new payload keys (section 5). No duplicate prompt/frame/engine logic. |
| Omni **extend** (`previous_interaction_id`) works: identity and light hold, a jump-cut inside an extension works, output is cumulative (4→8→11 s), new seconds cost the same output tokens as a fresh clip plus the history as input. | trial 1 | Worth offering as an optional continuity mode. |
| Omni extend of a clip with a **child** was refused twice by the safety filter (plain clips are fine). | trial 1 | Extend can never be the default; the **last-frame chain** stays the universal fallback and extend must degrade to it automatically. |
| Kling **elements**: ignored on text-to-video; on image-to-video with frontal + reference images a face appeared from a faceless start frame and matched. Slow (2–4 min per clip). | trial 2 | Optional later slice, image-to-video only; never a replacement for frame-first. |
| A joined film could freeze one frame for seconds although every clip moved (fixed on `coverage`, commit "Fix: a joined film could show ONE frame…"). | 28 Oct | Assemble must always run the frozen check; the fix must be on master before builder ships. |
| Omni: 3 s clip floor, 8 requests/minute on our tier, ~20 s per Draft clip, ~$0.034/s Draft and ~$0.101/s Final (measured). | 27–29 Oct | Takes are generated in small queued batches; every button shows an estimate before it spends. |
| No media cleanup exists. `tenants/default/media` is already 646 MB / 661 files on this machine; live has a 10 GB disk. | sweep | Takes multiply files: a retention rule is part of the plan (S7), not an afterthought. |
| A frame saved as `rendering` used to restore as a permanent spinner (fixed with `settledFrames`). In-memory render jobs vanish on a server restart. | earlier lessons | Every take persists its own status; an in-flight take restores as "interrupted — retry", never as a spinner. |

## 3. Principles

1. **Reuse, do not rebuild.** One renderer, one stitch, one mixer. The builder only decides *which clips* and *in what order*.
2. **Films with no builder data behave exactly as today.** Golden tests (existing film + coverage golden) stay byte-identical.
3. **Nothing spends silently.** Each generate button states its estimated cost; batches have a cap the person sets; the film shows "spent so far".
4. **Advisory, never blocking** (the framework's rule): take checks flag, the person decides.
5. **Local first.** Each slice ends with a localhost click-through script for the owner (like `COVERAGE_LOCALHOST_TEST.md`); live only after sign-off, as separate commits with live checks.
6. **One source of truth for order and length:** the script rows (`fullScript`, `row.shots`) — the builder never keeps a second order.

## 4. Data model (one new optional field on the film)

Stored with the film (`filmscript.py` gains `video_builder`, same absent-key guard as `video_camera` / `video_pace` / `video_beat_map`):

```
video_builder = {
  "takes":  { "<scene>.<shot>": [ Take, ... ] },     # "2.1" = scene 2, shot 1 (the master); extras are 2.2, 2.3 ...
  "chosen": { "<scene>.<shot>": "<take id>" },        # the take the film will use
  "trim":   { "<scene>.<shot>": {"in": 0.0, "out": 2.5} },   # optional, seconds into the chosen take
  "budget": { "cap_usd": 5.0, "spent_usd": 1.84 },     # a soft cap the person sets; spent is the sum of takes (estimates until reconciled)
  "version": 1
}
Take = {
  "id": "tk_ab12cd34", "url": "/media/shot-….mp4", "tier": "draft|final", "engine": "omni|kling",
  "seconds": 4.0, "mode": "frame|chain|extend|elements",       # how continuity was done
  "frame": "/media/frame-….jpg",                               # the frame it was animated from
  "sig": "<recipe fingerprint>",                                # prompt + frame + camera + engine + tier: tells when a take is OUT OF DATE
  "interaction_id": "v1_…",                                     # Omni only, perishable (retention undocumented): never relied on without the file
  "status": "done|rendering|error|interrupted",  "error": "", "note": "",
  "checks": [ {"id": "frozen|black|short|…", "verdict": "ok|check", "note": ""} ],
  "est_usd": 0.14, "created": "2026-10-29T10:00:00Z"
}
```
Skipped shots stay skipped (`row.shots[k].skip` already exists); the builder reads it, never duplicates it.

## 5. Architecture (how it plugs into what exists)

**Backend**
- `takes.py` (new, pure): take records, signatures, choose/trim/validate, cost estimates, settle-on-load (`rendering` → `interrupted`), retention picking. No I/O beyond the film store.
- `_produce_video_sync` gets **two optional payload keys**, both inert when absent:
  - `only_shot: "<scene>.<shot>"` — plan segments as today, render **just that segment** through the existing `render(seg)` (same `frame_for`, `segment_prompt`, engines, limiter, safety/credit messages), and return its clip record **before** stitching. This is the per-shot generation path (S1) and is why prompts and engines cannot drift from the full render.
  - `use_clips: { "<scene>.<shot>": {"url", "in", "out"} }` — when present, `render(seg)` returns the chosen clip (pre-trimmed) instead of generating. Everything after (stitch with the frozen check, voice windows re-laid on the real picture, music, mix, loudness, silent master kept) is unchanged. This is "assemble" (S3), and `heritage_redirect.py --reuse` already proved the equivalence.
- New thin routes (all `job: true` capable, like `/rescore`): `POST /shot-render` (one shot → take), `POST /takes-choose`, `POST /takes-trim`, `POST /takes-estimate`, `POST /takes-discard`, `POST /builder-assemble` (builds the `use_clips` payload and starts the existing produce-video job). Names are provisional; checked against the existing 331-route table for collisions (the live-action routes `/shot-take`, `/shot-select` are a different feature and are not touched).
- `filmscript.py`: `video_builder` field.
- Optional later: `gemini.video_extend(...)` (S4), Kling elements in `creative.py` (S5).

**Frontend (`app.dc.html`, LF-only)**
- A new Film step **"Builder"** between Shoot Board and Production (`stepDefs`), built as React elements in the bag (nested `sc-for` leaves ghosts — the known lesson): shot cards grouped by scene; per card: storyboard frame, takes strip, Generate / Re-roll, choose, trim handles, skip, status, estimate.
- A timeline strip (chosen takes in order with trims) and a picture-only preview player (sequential `<video>` playback using clip URLs and in/out clamps; no render, no cost).
- The Production step keeps its one-button render, and gains "Assemble from your takes" when a complete chosen set exists.

**Wiring that must stay true:** `startCutFromFilm` / Edit room read `shot_clips` — the assembled film returns the same record shape, so the Edit room, cutdown strip and "Rework the cut" keep working unchanged. Voice windows already lay each scene's lines over that scene's *actual* picture, so trims and reordered scenes need no new voice logic.

## 6. Code sweep (blast radius, before any change)

| Area | What I found | Impact |
|---|---|---|
| `main._produce_video_sync` (~600 lines) | `render(seg)`, `frame_for`, `segment_prompt`, `_seg_label` are closures over payload-derived state (engines, tier, style, look, aspect). | The two payload keys add early branches in `render(seg)` and one early return; **no extraction/refactor** of the closures (lowest risk). |
| `_RENDER_JOBS` | in-memory dict; a server restart loses running jobs. | Take status persists on the take itself; restore settles in-flight takes. |
| `filmcut.stitch` | frozen-join fix + `_join_filter` (on `coverage`). | Assemble depends on it; the fix must reach master first (separate hotfix decision). |
| `gemini.video` | single image_ref, one shot per call, shared 7/min limiter, specific error messages. | Takes inherit the limiter; batches must be queued, not parallel bursts. |
| `filmscript.py` | FIELDS + `_blank` + `save` absent-key guard pattern. | Same 7–8 wiring sites as `video_pace` / `video_beat_map` (state init, resets, restore, save, `vsig`, bag, template). Known and checked by `checkfe.py`. |
| Frontend `produceVideo`, `renderViaJob`, `startCutFromFilm`, `frameSlots`, `settledFrames`, `RATE`/`tierNow` | all reusable; `RATE` holds the measured $/s. | Builder reads them; it does not fork them. |
| `tenants/<t>/media` | no cleanup anywhere. | Retention rule in S7; takes are the first feature that creates many large files per shot. |
| Auth / tenancy | `/media` is served under the same session; the store is per tenant. | `<video>` tags work same-origin; nothing new in auth. |
| Edit room / cutdowns | consume `shot_clips`. | Unchanged contract. Future: cutdown fidelity (A1–A7) can reuse chosen takes — this plan makes the "reuse clips" recommendation possible. |
| Tests | `test_coverage_plan.py` golden, `selfcheck.py`, `checkfe.py`, `smoke.py`, surfaces wiring. | Each slice adds its own tests and must keep these green. |

## 7. The slices

Sizes are relative (S/M/L), not time promises. Each slice: scope → backend → frontend → wiring → tests → localhost check → exit criterion → rollback.

### S0 — Foundations (no UI) · size S
- `takes.py` + tests; `video_builder` in `filmscript.py`; the two payload keys in `_produce_video_sync` (`only_shot`, `use_clips`) with early branches only.
- **Tests:** golden (`coverage_golden`) byte-identical; `only_shot` returns exactly the clip record `shot_clips` would hold for that shot, with the stubbed generators; `use_clips` produces a film identical to a normal render fed the same clips (stubbed video, real stitch/mix paths); settle-on-load; signature changes when prompt/frame/camera/engine/tier change.
- **Localhost check:** none needed by the owner (internal); I run the suites and a stubbed end-to-end.
- **Exit:** all suites green, a film with no builder data renders exactly as before. **Rollback:** the keys are inert; revert the commit.

### S1 — Takes: generate, re-roll, choose (Draft) · size M · THE CORE
- **Backend:** `POST /shot-render` (job-capable): one shot → a new take (Draft by default), persisted immediately as `rendering` then `done`/`error`; `takes-choose`, `takes-discard`; `takes-estimate` (uses the measured rates, counts the 3 s Omni floor and the shot's seconds).
- **Frontend:** the Builder step: shot cards from the plan (masters + active extras, skipped shots dimmed), frame + takes strip, **Generate / Re-roll** (one at a time or "generate all missing", queued at the limiter's pace), click a take to play it, **Choose**, discard, estimate on every button, running "spent so far", per-card error text in the engine's own words (safety block, out of credit, rate limit). A shot without a frame is held back with the same message the render uses.
- **Wiring:** counters/hand-over gate read frames as today; takes never change frames. In-flight takes settle on restore. Two clicks on one shot cannot double-spend (in-flight lock).
- **Tests:** stubbed generators for success / safety block / credit wall / 429; double-click lock; restart settle; the page driven with stubbed fetch (the established recipe).
- **Localhost check (owner):** open the Heritage film, Builder step, generate shot 1 as Draft, re-roll it, choose the second take, see the estimate and "spent" line. Real spend: two Draft clips, about 8 s of 360p.
- **Exit:** a shot can be generated, re-rolled and chosen without touching any other shot, and the choice survives a reload. **Rollback:** hide the step; data is inert.

### S2 — Timeline, trim, reorder, preview · size M
- **Backend:** `takes-trim`; trim applied at assemble time (never destructive: the take file is untouched).
- **Frontend:** timeline strip of chosen takes with in/out handles; reorder **scenes** (rewrites script order — the single source of truth) and shots inside a scene; skip; picture-only **preview player** for the whole sequence with seams marked; totals (seconds, vs the film's slot).
- **Wiring:** reordering scenes edits `fullScript`, so shoot-board notes, frames (keyed by scene index!) and captions must follow — **this is the risky part**: frame keys `"<idx>.<k>"` are by position, so a scene reorder must re-key `sceneFrames` and `video_builder` together (the same fix `removeShot` already does for shots). Planned as one atomic state update plus a test that frames/takes/notes still match their scenes after a reorder. If that proves too invasive, reorder is limited to shots within a scene in S2 and scene reorder moves to its own later slice.
- **Tests:** re-key invariants; trimmed total equals the sum; preview playlist matches the assemble order; voice windows lay over the trimmed picture (existing logic, new test).
- **Localhost check (owner):** trim a take, drag a shot, play the sequence.
- **Exit:** the timeline total, the preview and the assembled film agree.

### S3 — Assemble (+ Draft → Final) · size M
- **Backend:** `builder-assemble` builds `use_clips` and starts the existing produce-video job (voice, music, sound plan, loudness, silent master, `shot_clips` all unchanged). The frozen check runs on the join. **Promote to Final:** re-render only the *chosen* shots at the Final tier as new takes, then assemble again.
- **Frontend:** "Assemble film" in the Builder and Production; progress through the existing job poll; the result lands in the Production versions list and is a normal film for the Edit room.
- **Tests:** assembled film equals a normal render with the same clips; incomplete sets are refused with the list of missing shots (never a short film handed over as finished); Final promotion only touches chosen shots.
- **Localhost check (owner):** assemble from the chosen Drafts, play it, open it in the Edit room.
- **Exit:** a film built from chosen takes plays, is the right length, has voice and music, and opens in the Edit room. **Rollback:** the Film tab's one-button render is untouched.

### S4 — Continuity: chain and extend · size M
- **Backend:** **chain** (default for any shot that follows another): the frame for shot *n* is the last frame of the chosen take of shot *n−1*, extracted with ffmpeg and used as `image_ref`; **extend** (optional, adults only): `previous_interaction_id`, take only the new tail (the response is cumulative), keep the file ourselves; **automatic fallback** to chain when the safety filter refuses (the child case measured on 29 Oct) with the reason shown.
- **Frontend:** per-shot "Continue from previous" with the mode shown on the take (`frame | chain | extend`).
- **Tests:** tail extraction durations; the safety-refusal fallback; interaction ids never trusted without the stored file.
- **Localhost check:** chain two shots; extend an adult shot; confirm the child shot falls back with the stated reason.
- **Exit:** continuity modes work, and a refused extension never loses the shot.

### S5 — Take QC (cheap checks per take) · size S–M
- Deterministic per take: frozen picture (reuse `frozen_join`'s fingerprint idea), black/near-black frames, duration vs ordered, and the existing near-copy check against the previous shot. Optional one-frame vision check through the existing frame check (anatomy/pasted panels/extra people on the take's middle frame) — advisory chips on the take, never blocking.
- **Why:** the 28 Oct lesson — "ok" from the render is not proof; every take is looked at before the person spends more.

### S6 — Camera presets (prompt steering) · size S
- A small library (push-in, pull-out, pan, tilt, orbit, handheld, locked-off, crane-up…) that writes the camera phrase into the shot and sets `movement_class`; shown per shot. Labelled honestly as **steering, not control**. A 10-clip trial on Omni and Kling comes first to learn which presets the engines actually obey; presets that don't land are not shipped.

### S7 — Housekeeping: budget, batches, retention · size M
- Budget cap with a hard stop on batches, "spent so far" reconciled against the engines' own usage fields (Omni reports tokens per response; Kling is billed by fal and shown as reported/estimated until reconciled).
- **Batch generate** (N takes per shot, queued at 7/min), side-by-side compare.
- **Retention:** unchosen takes of shots in a finished film can be purged on request (never automatically), with a size readout; chosen takes and the silent master are kept. Live disk is 10 GB, so this lands before any live rollout.

### S8 — Elements (Kling, image-to-video) · size M, OPTIONAL
- Only if the owner wants faces that appear mid-shot to hold from reference images: saved cast "elements" (frontal + references) feeding Kling Pro image-to-video. Slow (2–4 min per clip) and priced higher by fal; text-to-video ignores elements (measured), so this is never offered there.

**Suggested order:** S0 → S1 → S3 → S2 → S5 → S4 → S7 → S6 → S8 (a working build-from-takes loop as early as possible; trimming and reordering after the loop proves itself; extend and presets last because they are the least certain).

### Build log

**S0 (29 Oct 2026, commit `26e8624`):** `takes.py`, the `video_builder` film field (normalised at the store), and the two inert render keys. Decisions made while building: (1) **keys are the film's own frame keys** (`"<position>"` for a scene's master shot, `"<position>.<k>"` for extras, position = 0-based place in the script), not scene numbers — the same keys `sceneFrames` already uses, so the existing re-keying logic covers both; (2) `use_clips` means **assembling never generates**: a shot with no chosen clip is reported missing, and no video provider is needed; (3) trims (`in`/`out`) are carried in the payload but applied in S2/S3; (4) a shot's chosen clip is a list (one clip per beat) because a scene longer than 8 s is several continuing beats.

**S1a (29 Oct 2026):** frame variants + choose + the Shots step. Decisions made while building: (1) **a re-render in the Storyboard is now a take too** (the new frame becomes the frame, the previous one is kept in history) — one code path, so the two screens cannot disagree; (2) `sceneFrames[key]` always mirrors the chosen take, so nothing downstream changed; (3) a frame made before the builder existed shows as one chosen "current" take and joins the history on its first change; (4) history is capped at 12 takes per shot (oldest unchosen first, never the chosen), discard removes a take from the list but **never deletes a file**; (5) every place that wipes `sceneFrames` (new concept, cast re-lock, style/engine change, script rework — 15 sites) now also clears the builder, and `removeShot` / `removeAllShots` re-key every builder map; (6) the film's own seed is not reused for variants.
**Trial result that matters (29 Oct, 3 image calls, `tools/engine_trials/frame_variant_trial.py`):** the Google image model **does not honour the seed** — the same seed twice gave two different pictures (mean pixel difference 41.7, as large as seed A vs seed B at 30.4) — so variants differ by themselves (same boy, different framing and pose) and the "fixed seed per film" has never been what keeps the cast consistent on Google: the reference image does that. Variants are therefore a genuine choice, not near-duplicates; if a *small* variation around one composition is ever wanted it needs a different mechanism (edit-from-frame), which is not part of this slice.

**S1b (29 Oct 2026):** clip takes. Decisions made while building: (1) **no new route**: a per-shot clip is `POST /produce-video` with `only_shot` through the existing job + poll (`renderViaJob`), so the prompt, frame, seconds, engine, limiter and error text are the full render's (proved free with the real planner: `tools/engine_trials/shot_render_real.py` shows the engine call for shot "2" is byte-identical to the full render's call for that shot); (2) the full render's request is now built by one function, `filmRenderBody`, shared with the clips (verified body-identical to before the refactor); (3) **an identical single-shot request that is still running joins its job** (no double spend); a finished one starts a new job (a deliberate re-roll); (4) a take stores its `job_id`, and a take that was in flight when the page closed restores as "interrupted" and **recovers itself** by asking `/render-status` (the clip is paid for and on disk); (5) the first good clip of a shot is chosen automatically; (6) a scene longer than 8 s is several continuing beats: the take holds one clip per beat; (7) estimates use the measured Omni rate with the 3 s floor, Kling shows none; (8) *Found while building and fixed:* the master shot's key is the number `0`, which is falsy: `only_shot: 0` would have fallen through to a **full paid render**. The page now always sends a string and the server tests presence with `is not None` (a number 0 means shot "0", an empty string is a 400). Real check: one Draft clip of the Heritage film's scene-3 master (6 s) rendered through `only_shot`, moves, 6.00 s.

**S3 (28 Oct 2026):** assemble from chosen clips + Promote to Final. Decisions made while building: (1) **no new route**: assembling is `POST /produce-video` with `use_clips` through the existing job + poll, so voice, music, sound plan, loudness, silent master and `shot_clips` are the normal render's; (2) **assembling is strict**: a missing chosen clip or a missing clip file is a 400 that names the scene and shot ("Can't assemble yet — scene 2, shot 2: no chosen clip…"), never a short film handed over as finished; (3) **the film is as long as the pictures really are**: a chosen clip more than 0.25 s shorter than its planned beat shrinks that beat to the real length, says so, and the voice follows; (4) **Draft and Final clips can be joined in one film**: the demuxer cannot join different sizes, so `filmcut.stitch` uses the concat filter at the largest size when sizes differ; (5) Promote to Final re-renders only the chosen shots at tier standard as NEW takes, chooses each when it finishes, keeps the Drafts, and stops on a billing wall; (6) assembling when a chosen clip is from an older frame asks first; (7) the strip reports Draft / Final / Mixed and the version carries that quality. Verified: python tests (strict 400s, file-missing, duration reconcile, mixed-size join to 640x360 at 11 s, number-0 and empty-string only_shot), and the real page driven with stubbed fetch (refusal sends nothing, 3 Final requests at tier standard, `use_clips` keys and urls, no `only_shot`, version quality, player). NOT verified: a real signed-in assemble, and a real paid Promote to Final.

**S2a (28 Oct 2026): TRIM.** Decisions made while building: (1) **the cut is made at assemble time into a NEW file** (`trim-<id>.mp4` in the media folder via `filmcut.trim_window`); the take's own file is never touched, so a trim can always be changed; (2) the window is re-encoded, not stream-copied (a copy can only start on a keyframe); (3) **the beat becomes the window's length** when the window is shorter than the plan (the film and the voice follow the trimmed picture, and the note says "trimmed to ..."); a window LONGER than the beat is cut to the beat and the note says so; (4) **a trim that cannot be cut falls back to the whole clip and says so** (never silently ignored); an unusable window (inverted, under 0.2 s, not numbers) is ignored; (5) a trim belongs to the clip it was set on: choosing another take, a new auto-chosen take or Promote to Final clears it; a multi-beat shot cannot be trimmed; (6) the Trim row previews with a `#t=start,end` media fragment (no extra code), and the assemble strip gained a Timeline line (kept seconds vs planned). Tests: `tools/test_builder_s2.py` (20 checks: real ffmpeg cut length/start/source untouched, the assemble path with a stubbed cutter). Page driven with stubbed fetch: sliders, clamp, reset, choose clears, payload carries in/out only for the trimmed single-clip shot. NOT verified: a real signed-in assemble with a trim. **S2b (reorder shots within a scene) and S2c (reorder scenes, the risky re-key) and S2d (whole-sequence preview player) are NOT built.**

**S2b + S2c (28 Oct 2026): REORDER shots within a scene, and scenes.** Front end only (no new route). Decisions made while building: (1) **the same in-place re-key `removeShot` already does**, generalised: `rekeyPlaces` renames the keys of `sceneFrames` and all five builder maps (frames, frame_chosen, takes, chosen, trim) together with the script order, in ONE `setState`; (2) **S2b moves only the extra shots among themselves** (up/down); shot 1 is the scene's own shot and stays first (swapping it with an extra would mean swapping row-level fields with a shot object: a separate, larger change); (3) **S2c is a swap with the neighbour** (up/down on the scene header, on the Storyboard card and the Shots step); the two rows exchange their `no`, so numbering stays 1..N in order, and the two rows' timecodes are re-laid; (4) **everything keyed by a scene NUMBER follows its scene**: the sound plan's per-scene choices and key sounds, and each row's `match_no` ("match this to another scene's frame"); (5) **what is derived from the order is cleared** like a script rewrite does it: director's read, flow review, editor's notes, voice plan, planned seconds (the toast says to run them again); a flow review is also cleared by a shot move; (6) **a move refuses** when a frame, a frame variant or a clip is being made for either scene/shot (the result would be filed under the wrong place), and when a SIGNED live-action shot exists for either scene (that store is global and keyed by scene number: checked with `GET /shots?all=true&scene=N`, and a failed check also refuses); (7) approval of the script is kept (the content did not change, only the order). Known limits: a frame whose recipe includes a matched scene's number may show "out of date" after that scene moves (honest but not always necessary); a pending, unaccepted shot proposal for a moved scene is orphaned (it was keyed by number + text). Tests: `tools/page_checks/builder_reorder_invariants.js` (18 checks on the real page with the network stubbed: every frame/take/chosen/trim/sound/match link read back by identity tag after each move, refusals, edge no-ops, exact round trip). NOT verified: a real signed-in reorder followed by a real assemble. **S2d (whole-sequence preview player) is NOT built.**

**S2d (28 Oct 2026): PREVIEW the sequence.** Front end only, no new route, no cost. A **Preview sequence** button in the assemble strip opens a picture-only player: the chosen clips in script order, each from its trim's start for as long as the film will use it, with a segment bar (seams; trimmed segments lighter; click to jump), Previous / Next / Replay, an elapsed-of-total readout and a note naming shots with no chosen clip. Decisions made while building: (1) **one length rule for the preview, the Timeline line and the assemble**: a clip plays for min(its trimmed window or own length, the shot's planned seconds), a multi-beat shot plays its beats in order capped at the planned seconds; the preview total is asserted equal to `assembleStatus().kept` in the page check; (2) **no custom video engine**: each clip is one `<video>` whose src carries a `#t=start,end` media fragment, and the page advances on `timeupdate` / `ended` (so a seam is accurate to about a quarter of a second, and the last clip may rest a fraction past its end: it is a preview, the assembled film is frame-exact); (3) the clips are muted (pictures only: the voice, music and sound are laid at assemble); (4) a stale end event from a clip that is no longer playing is ignored, the last clip stops (does not wrap); (5) the player is not saved. Tests: `tools/page_checks/builder_sequence_preview.js` (14 checks) plus one real-playback run with three generated clips (played 0-4 s, the trimmed clip from its trim start for 2 s, then 4 s: about 9.8 s of a 10 s total). **Caveat:** the planned seconds come from the script's timecodes; the server may re-time the scenes by dialogue at render (voice windows), so the assembled film can differ from the preview by that re-timing; the strip's Timeline line has the same basis. NOT verified: a real signed-in assemble compared to the preview. **S2 is now complete (S2a trim, S2b/S2c reorder, S2d preview); next in the order: S5 take QC, S4 continuity, S7 budget/retention, S6 presets, S8 elements.**

**S5 (29 Oct 2026): TAKE QC.** Two new routes, one new module, a chip on every clip take. Decisions made while building: (1) **thresholds are measured, not guessed**: `tools/engine_trials/takeqa_calibration.py` ran 37 real clips (Omni, Kling, Veo, Wan, Seedance, MiniMax; 29 of them are the regression set in the test) and synthetic known-bad ones: real clips never move less than a first-vs-last span of about 4 (a frozen picture is 0.0), never average below brightness 74 (black is 2), and clips animated from the SAME frame start within 1-8 of each other while genuinely different shots start 56+ apart; so `still` < 2.0, `black` < 15 (a `dark frame` < 12 at any sampled point), `repeat` < 15 on the FIRST frame (the middle frame was tried first and separates badly: two clips from one frame still differ by ~30 there); (2) **`POST /take-check` is deterministic and free** (ffmpeg, a second or two): readable, still, black, shorter than ordered, repeat of the previous shot's clip; it runs on its own when a clip finishes and from a Check / Re-check button; (3) **`POST /take-look` is the optional model look** (one paid call, the same look a storyboard frame gets) on the clip's MIDDLE frame, extracted in memory (nothing written to disk), reusing `framecheck`; it is a button (Look), never automatic; (4) **advisory, never blocking**: chips ("! n" / "checked") and notes on the take, a line in the assemble strip, an Accept button per take (`check_accepted`, reset by a re-check); Use, Assemble and Promote are never disabled by a check; (5) a re-run of the free checks KEEPS an earlier model look, and a new look replaces only the earlier look; (6) a multi-beat take is checked beat by beat (notes say which part; the repeat check only on the first beat); (7) a check that fails (no ffmpeg, no key, unreadable reply) leaves the take untouched and says why (never a made-up result). `takes.py` keeps `check_accepted` and up to 12 checks. Tests: `tools/test_takeqa.py` (26 checks: synthetic known-bad clips, the routes with the model stubbed, and 29 REAL clips with no false alarm plus same-frame pairs flagged and different shots not), `tools/page_checks/builder_take_qa.js` (19 checks on the real page). NOT verified: the checks on a real clip from a real signed-in session (the routes sit behind login); the model look against a real model reply (stubbed). A real defect that no rule here can see (a wrong face, a limb that only breaks in motion) still needs your eyes or the Look button.

## 8. Blast radius summary

| Touches | Slices | Notes |
|---|---|---|
| `main.py` `_produce_video_sync` | S0, S3, S4 | early branches only, keyed on new optional payload keys |
| `main.py` new routes | S1–S7 | route-table collision check; job-capable like `/rescore` |
| `filmscript.py` | S0 | one field, absent-key guard |
| `takes.py` (new) | S0+ | pure logic, unit-tested |
| `filmcut.py` | S2, S3 | trim helper; stitch already fixed |
| `gemini.py` | S4 | `video_extend` |
| `creative.py` | S8 | elements |
| `framecheck.py` | S5 | reused as is |
| `app.dc.html` | S1–S7 | new step, new bag elements, the 7–8 known wiring sites; LF-only; `checkfe.py` after every edit |
| Edit room / cutdowns | none | `shot_clips` contract unchanged |
| Film tab one-button render | none | stays |

## 9. Risks and what I'll do about them

1. **Scene reorder re-keys frames and takes** (S2): one atomic update + invariants test; fallback = shots-within-a-scene only.
2. **Spend surprises:** estimates on every button, a budget cap, batches capped, Draft by default, "spent so far" visible; I will ask before any paid verification run (small, Draft only).
3. **Rate limit 7/min:** one queue for the whole app; the UI shows "waiting for the engine" instead of failing.
4. **Child-safety refusals:** surfaced per shot in the engine's words; extend falls back to chain; plain generation unaffected.
5. **Server restart mid-take:** takes settle to "interrupted — retry" (the spinner lesson).
6. **Disk growth:** retention (S7) before live; nothing is deleted without a click.
7. **Two tabs / two people:** per-shot in-flight lock; last-write-wins is not acceptable for `video_builder`, so saves merge by take id (takes are append-only).
8. **Frozen/corrupt joins:** the stitch fix + the S5 checks; the hotfix to master is a decision for the owner (it is probably live-affecting).
9. **Omni interaction retention is undocumented:** ids are a convenience; the file is the truth.
10. **Complexity creep in `app.dc.html`** (30k lines, LF-only): everything new is React elements in the bag; no nested `sc-for`; `checkfe.py` after each edit; browser-verified with the stub recipe.

## 10. Test strategy and localhost protocol

- **Per slice:** unit tests with stubbed generators; golden equality for films without builder data; `selfcheck.py`, `checkfe.py`, `smoke.py` (boots the COMMITTED tree), surfaces wiring; the page driven in the browser pane with stubbed network.
- **Real runs** only where the question is about the engine (S1 Draft takes, S4 extend/chain, S5 checks, S6 trial): each is a small Draft run on the owner's Heritage film, announced first, spend reported afterwards.
- **Owner click-through:** a `FILM_BUILDER_LOCALHOST_TEST.md` is written per slice (exact folder `C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio`, run `run-local.bat`, `http://localhost:8000/app`, exact clicks, expected result). The preview server I start stops after ~30 min, so the owner runs their own.
- **Verification rule:** every produced film gets the 1-frame-per-second contact sheet and the frozen check before I say it works.
- **Branches:** work continues on `coverage` until the owner says otherwise, or I cut a new branch `builder` from the `coverage` head (cutting it changes no files, but the owner's server serves the working tree, so I will not switch silently — your call). Merge order: `coverage` (with the stitch fix) first, then `builder`, each as separate commits with live checks, only after localhost sign-off.

## 11. Cost model (measured; no guessed prices)

- Omni Draft ≈ $0.034/s, Final ≈ $0.101/s (measured 27 Oct). A shot is generated at ≥ 3 s and trimmed, so a 2 s shot costs a 3 s clip. Omni's usage block reports tokens (≈ 1,930 video output tokens per second); an extension re-reads the earlier video as input tokens (6,805 for 4 s): input price not yet quantified in dollars, to be read from the billing page before S4 ships.
- Kling 3.0 Pro via fal: reported $0.112/s (no audio), $0.168/s (audio), $0.336/s (elements + audio) — **reported, not measured by us**; fal bills, so the page labels it an estimate until the dashboard is read.
- Typical first-slice verification: two to four Draft clips (≈ 8–16 s, well under $1).

## 12. Decisions needed from the owner

1. **Scope of S1:** takes + choose only (recommended), or timeline trim/reorder in the same first release?
2. **Placement:** a new Film step "Builder" between Shoot Board and Production (recommended), or its own top-level tab beside Film / Live action / Edit room?
3. **Replace or beside:** keep the Film tab's one-button render permanently (recommended) or retire it once the builder is proven?
4. **Cost model:** Draft first, Final only on chosen shots (recommended), or Final-only?
5. **Branch:** keep working on `coverage`, or cut `builder` from its head?
6. **Scene reorder in S2:** attempt it with the re-keying (recommended) or limit S2 to shots within a scene?
7. **S8 elements and S6 presets:** keep as optional later slices (recommended) or drop?
8. **The stitch hotfix:** cherry-pick the frozen-join fix to master now (it is probably live-affecting), or wait for the whole `coverage` sign-off?

## 13. Out of scope (for now)

Generating audio inside the clips (the soundtrack stays a separate layer), live-action takes (separate feature), cutdown fidelity A1–A7 (will reuse chosen takes later), a model marketplace, true camera/lens control, multi-user real-time collaboration.
