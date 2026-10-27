# Video coverage (shots within a scene) — full build plan

Status: **PLAN ONLY, nothing built.** Written 27 Oct 2026 for the owner's review. Follows the working agreement in `CLAUDE.md`
(sweep first, plan, minimal diff, verify local then live). Per the owner: **everything is built and tested on localhost first;
nothing reaches the portal until the owner signs off locally.**

## 1. What we are building (and what we are not)

**Words.** A *scene* is the unit of story (a place, people, an action, usually some spoken words). A *shot* is one camera angle of a
scene. A *take* is another attempt at the same shot. Today **one scene = one shot = one frame = one 4/6/8 s clip**.

**Coverage** = a scene can be broken into 2–4 shots (wide, medium, close-up, over-the-shoulder, detail), each with its own
frame, its own camera movement and its own short clip. The film gets faster cuts, camera movement and a multi-camera feel
(the reference film averaged ~1.5 s a shot; ours is 4–8 s).

**In scope (v1):** per-scene "Break into shots" (human approved, editable) → frames per shot → render → voice, music, captions
and Edit room still work. **Not in scope (v1):** takes and single-shot re-roll (next phase, designed for below); coverage inside
Edit-room cutdowns (they keep working as scene-level, exactly as today); true multi-camera continuity (see §9, limit 1).

**The one invariant that keeps this safe:** *a scene's total seconds never change.* Coverage only subdivides the seconds a scene
already has. Everything that works at scene level (voice windows, captions, sound plan, timecodes, roles, continuity, the Edit
room's beats) therefore keeps working untouched.

## 2. The design decision that shapes everything: where do the extra shots live?

| | **A. Each shot is its own script row** | **B. Shots live inside the scene row** (recommended) |
|---|---|---|
| Frames | free: one frame per row | need a key per shot |
| Scene-level consumers (voice windows, captions, sound plan, roles, continuity, docs, Edit room, cutdown rescript, live-action `shots.for_scene`) | **all assume one row = one scene** → every one must learn "these rows are one scene" | **untouched**: still one row per scene |
| Index-keyed frames (`sceneFrames[idx]`, reset on every rework) | inserting a row **shifts every later index** → frames pair with the wrong scenes | master frame stays at `sceneFrames[idx]`; nothing shifts |
| Script table, versions, reworks (`keepSceneExtras`) | row counts change under the user's feet | scene count stable |
| Old saved films | fine | fine (no `shots` key = today) |
| Risk | high: wide, silent breakage | contained: planner + frames + cards + render |

**Choice: B.** It also reuses a mechanism that already exists: `filmcut.plan_by_scene` already turns one scene into several
beats marked `continues`, and `assign_roles` already gives all beats of one moment a single role (this is how a scene longer
than 8 s works today). The render already merges a scene's beats into one VO window by scene number (`_scene_win` in
`_produce_video_sync`). Coverage generalises that: the beats get their own picture and camera.

## 3. Data model (exact)

On a scene row (`full_script[i]`), one new **optional** key:

```
row.shots = [ { id, visual, camera, shot_size, movement_class, secs, frame_note? , include_pack? } , ... ]
```

* `row` itself IS **shot 1 (the master)** — its `visual`, `camera`, `shot_size`, `movement_class`, frame at `sceneFrames["<idx>"]`
  stay exactly as they are. Approved frames therefore stay valid when coverage is added. `row.shots` holds the **extra** angles (2..n).
* `secs` on an extra shot is a *weight*. The planner gives each shot whole seconds, ≥ 2, summing to the scene's seconds (largest
  remainder); the master takes the remainder. A scene that is later re-timed shorter rescales; if it cannot fit ≥ 2 s per shot the
  last shots are dropped from the render **with a visible note** (never silently).
* Frames: master at `sceneFrames["<idx>"]` (unchanged); extras at `sceneFrames["<idx>.<k>"]` (k = 1..). `scene_frames` is
  already persisted as a free dict (`filmscript.save` passes dicts straight through), so **no store change**.
* No `shots` key (every film made so far) ⇒ **byte-identical behaviour everywhere** (tested, §8).
* Render request: rows carry `shots[k].frame_url` (the frontend attaches them, as it does `frame_url` today).
* Render response (additive): `shot_clips: [{no, shot, seconds, url, provider, from_frame}]`. `clips` (bare URLs) is kept for
  back-compat. This is also exactly the per-shot record A3 (Edit-room continuity) and takes/re-roll need — built once.
* New shot sizes: add **`detail`** (macro insert: the pour, the hands, the label) and **`over`** (over-the-shoulder) to `_SHOT_SIZES`
  (main.py) and the Shot-size select (app.dc.html). Existing four unchanged.

## 4. Backend — what changes, module by module

| Module / function | Change | Why / invariant |
|---|---|---|
| `filmcut.plan_by_scene(scenes, per_scene)` | When a row has `shots`, emit one segment per shot instead of `beats_for(secs)`: `seconds` = the shot's whole seconds, `continues` = shot index > 0, `scenes` = `[view_row]` where `view_row = {**row, **shot overrides, "shot": k}` (shot's visual/camera/shot_size/movement_class/frame_url). Rows without `shots`: untouched code path. | **Single source of truth** — every caller (render, `_turn_at_from_rows`, preview) gets the same expansion. Sum of a scene's shot seconds == the scene's seconds. `assign_roles` unchanged (a moment = a scene). |
| `filmvoice` | No change to `allocate/scene_needs/retime/build_segments` (they are scene-level and see one row per scene). New small pure helper `split_shot_seconds(total, weights, floor=2)`. | Voice windows, WPM budget guard, tempo stay per scene. The budget guard in `build_segments` would truncate a line if dialogue sat on a 2 s row — that failure is avoided precisely because we chose B. |
| `gemini.video` | None. Already clamps to 3–8 s; a 2 s shot asks for 3 s and `filmcut._trim` cuts it to 2 s exactly. | Cost of the wasted second ≈ $0.034 (Draft). Verified in Step 0 (§7) that Omni honours the ask. |
| `main._produce_video_sync` | (1) scenes with a signed **live-action** shot (`shots.for_scene`) ignore `shots` (collapse to one segment) — the live clip is per scene; (2) a cap `_MAX_SHOTS = 48` beside `_MAX_SCENES = 24` (cost guard, refuse not truncate); (3) role sentence only on a scene's **first** shot (so shot 2 of the Hook scene does not say "this is the opening shot"); (4) per-shot `errors` wording ("scene 3, shot 2"); (5) response `shot_clips`. `scene_text/segment_prompt/frame_for` need no change — they read `seg["scenes"][0]`, which is the view row. | A dropped shot shortens the film exactly as a dropped scene does today; VO re-window already keys by scene number and merges (verified in code), so a partial scene still lines up. |
| `main._turn_at_from_rows`, `/voice-preview`, `/rescore` | No edit; they call `plan_by_scene` / are scene-level. | Invariant test: cumulative seconds before the first `turn` segment are equal with and without shots. |
| `videoprompt.compile_frame_shot` | Already adds "continues the previous shot from a fresh angle". Add: the shot's own `shot_size` phrase (`_SHOT_SIZES`) and movement are already inputs via the view row. | Prompt shape is the one proven on 27 Oct. |
| **New route `POST /scene-shots`** | Server-side model call (same completion path the other server-side generators use, not the frontend bridge) → returns validated shots for ONE scene. Backstops (deterministic, tested): seconds sum to the scene's, each ≥ 2, 2–4 shots, sizes vary (no two neighbours equal), no spoken words or on-screen text in a visual (reuse `videoprompt.clean_visual` + the existing dialogue-strip), the sign-off (`brand`) scene is never split, `product` size only on the pack scene, people/places must be the scene's own. Pack-in-scene flag from `packscene.mentions_pack`. | Human-gated: the route only *proposes*; nothing is saved until the person accepts. |
| `/scene-still` | **None required** (it already takes `scene_no`, `shot_size`, `match` via `reference_urls`, `pack_check`). The frontend sends the shot's own text and sets the master frame as the sibling reference. | Cast + sibling + pack = the 3-reference cap — fits. |
| `continuity.py` | None. It scores per clip; shot clips arrive with the scene's role (brand/button excluded from the comparison already). More clips = a more reliable median. | |
| `soundplan.py`, `filmaudio.py` | None: scene windows come from the rows' `tc` (scene-level, unchanged). | Music state / SFX "when" are relative to the scene window. |
| `filmscript.py` | None (`full_script` rows and `scene_frames` pass through; verified). | |
| `cut.py` (Edit-room manifest) | None in v1. Additive later: optional `clip_urls` per beat. | See §6, hazard H2. |
| `docs.build_production_bible` | Optional: list extra frames as "Scene 3 · shot 2" (frontend already builds the `frames` list). | Cosmetic. |

## 5. Frontend (`app.dc.html`, LF-only, shared with Claude Design) — what changes

Small anchored edits, `tools/checkfe.py` after each; Design is told which file to base on.

1. **Helpers:** `frameKey(idx, k)` ("3" or "3.2"); `shotFrame(idx,k)`; scene's shots read from `row.shots || []`.
2. **`SCENE_EXTRAS` += `'shots'`** and `keepSceneExtras` rule: carry `shots` onto a reworked row only when that scene's `visual` is unchanged (same rule as `frame_note`); otherwise drop and tell the person. `scriptForPrompt` then strips it from the writer prompts automatically.
3. **Frames:** `generateFrame(idx, k=0)` and `frameBody(idx, k)` use the shot's own `visual/camera/shot_size`, send the master frame as the sibling reference (`reference_urls=[cast, master]`), keep every other input (cast lock, wardrobe, location, camera note, pack, look). `frameRecipe`/`sceneSig`/`frameIsStale` get a per-shot form so editing shot 2 flags only shot 2. `generateAllFrames` loops scenes then their shots.
4. **Counters:** the three "N / M frames" counters (`doneFrames`, `staleFrameCount`, the Key Shots label) count master + extra frames.
5. **Shoot Board / Storyboard card:** under a scene, a collapsed "Coverage" strip: *Break into shots* (calls `/scene-shots`, shows the proposal, **Accept / Edit / Discard**), then compact shot tiles ("Shot 2 of 3 · Close-up · 2 s") each with its own frame, Render/Re-render, shot-size select, camera note, movement, remove. Scenes with no shots look exactly as today.
6. **Script table:** a small "3 shots" badge on a scene; no new columns.
7. **Render requests:** `produceVideo` attaches each shot's `frame_url` (as it does the master's); **`renderCut`/cutdown send rows with `shots` stripped** (v1 guarantee: cutdowns behave as today).
8. **Edit room `startCutFromFilm`:** today it maps `clips[i]` to scene `i`, which is **already misaligned** whenever a scene has more than one beat (hazard H2). Fix with `shot_clips`: the beat's `clip_url` = that scene's first shot clip (identical for single-shot films), plus additive `clip_urls`.
9. **Cost/time line:** the existing quality note adds "N shots · about $X · about Y min" (clips ≥ 3 s each; limiter 7 requests/min).
10. **Persistence:** `scene_frames` + `full_script` already saved; no new state keys beyond a busy flag.

## 6. Wiring map — every consumer, backwards and forwards

**Backward (what already exists must not change):**

| Consumer | Behaviour with coverage | Proof |
|---|---|---|
| Existing saved films (no `shots`) | identical plan, prompts, seconds, frames | **Golden test:** snapshot `plan_by_scene` + the compiled prompts for a corpus of rows *before editing*, assert byte-equal *after* |
| Scene-level voice, tempo, WPM guard | unchanged (one row per scene) | existing tests + invariant |
| VO placement on the real picture | the render already merges a scene's segments by scene number | stubbed-route test with a 3-shot scene: line spans the 3 shots |
| Captions (`caption_cues`), sound plan, `soundplan.resolve` | read the rows' `tc` (scene-level) | unchanged; test |
| Roles / sign-off / button / `music_on_turn` | roles per moment; turn position equal | invariant test |
| Brand endframe hold | the sign-off scene is never split | `/scene-shots` backstop + planner guard |
| Live-action shot per scene | scene with a signed live shot ignores `shots` | test |
| Provocation / no-people films | `shots` are just rows' extras; no-people logic untouched | existing cases |
| 9:16, Draft/Final tiers, fal fallback | per-clip, unaffected | stubbed |
| Cutdown / Edit room / rescript / `renderCut` | `shots` stripped; scene-level exactly as today | test + side-by-side body diff (the audit skipped on 26 Oct) |
| Pack-shape check, frame QA | runs per frame, incl. shot frames | existing |
| Imported films, `/reframe`, `/trim`, `/burn-captions` | pixel ops on a file; unaffected | |

**Forward (so the next features plug in without rework):**

* **Takes / re-roll (B5 part 2):** addressed by `(scene no, shot k)`; `shot_clips` is the record; render gains a re-roll mode that renders only requested `(no,k)` and reuses the others' `url`s.
* **A1/A3 cutdown fidelity:** reuse of original clips/frames is per scene → `shot_clips` grouped by `no`; `clip_urls` on the cut beat.
* **Edit room per-shot trims/reorder:** possible later because each shot is an addressable clip.
* **Engine changes:** per-clip and engine-agnostic; the 3 s generation floor is the only coupling (Omni 3–8, Kling 3–15).

**Existing hazards the sweep found (fix or flag, not silently ignore):**

* **H1** `_MAX_SCENES = 24` counts scenes only → add the shot cap.
* **H2** `startCutFromFilm` maps `clips[i]` ↔ scene `i`; wrong for any scene that already renders as >1 beat (a >8 s scene). Coverage would make it common → fixed in step 8 above.
* **H3** every script rework sets `sceneFrames:{}` (all frames lost). With shots this also loses shot frames — same rule as today, but the cost is higher (more frames) → the rework confirm text says so.
* **H4** `build_segments` truncates a line that does not fit its window; safe under design B (the window is the scene's), unsafe under A.
* **H5** the Edit-room/`cut` clip alignment and the 4 s-floor wording in a few UI notes ("Veo's 4 s floor" — already corrected in text on 27 Oct).

## 7. Build sequence, with local gates (branch `coverage`, nothing on master until sign-off)

**Branching:** all work on a git branch `coverage`; Render deploys only `master`, so pushing the branch is safe. Merge only after
the owner's localhost sign-off. Rollback = do not merge (or revert the merge).

* **Step 0 — trials (local, real credit ≈ $2, no code).** (a) Does Omni obey "About 2 seconds"? (else we always ask 3 s and trim.)
  (b) From the real master frame (scene B and scene A), make a close-up and an over-the-shoulder frame through `/scene-still` with
  the master as sibling reference: do pack, faces, outfits, kitchen hold? run `packqa`. (c) Render 3 shots × ~2 s of one scene and
  stitch: does it read as cutting between angles, or as jitter? **Gate: if (b) fails, we stop and rethink before any build.**
* **Step 1 — planner + data (backend only, no UI).** `plan_by_scene` expansion, `split_shot_seconds`, shot sizes, live-action
  collapse, shot cap, role-on-first-shot. Tests: golden equivalence, invariants (seconds, roles, turn position), live-action,
  partial failure. Gate: selfcheck, golden test green.
* **Step 2 — render route.** `shot_clips`, errors, prompts for view rows. Test: stubbed route (3-shot scene; VO window spans it;
  a dropped shot) → then **one real local Draft render** of a hand-written 6-scene/15-shot payload (no UI), looked at by eye.
* **Step 3 — `/scene-shots`.** Offline tests with a stubbed model (backstops), then 6 real calls on the Heritage script to read the proposals.
* **Step 4 — frontend.** Helpers, extras carry, frames per shot, staleness, counters, coverage strip, cost line, cutdown strip, `startCutFromFilm`
  fix. Verified in the browser pane with the stub recipe (real clicks, stubbed network), `checkfe`, smoke, wiring test.
* **Step 5 — owner acceptance on localhost** (you sign in; I cannot). A click-through script with expected results is part of the handover:
  open the 30 s Heritage film → Break scene 2 into 3 shots → accept → generate frames → render Draft → watch → check VO, captions,
  music, Edit room open, a 20 s cutdown still behaves as before, an old film renders unchanged.
* **Step 6 — rollout:** merge to master as separate commits (planner / render / route / UI), smoke the committed tree, push, wait for
  `live`, `/selfcheck` commit match, scan logs; say plainly what live could not cover (login-only paths). Then takes/re-roll.

## 8. Test plan (files I will add)

`tools/test_coverage_plan.py` (golden equivalence + invariants + live-action + caps + dropped shot), `tools/test_scene_shots.py`
(backstops with a stub model), extension of `tools/test_videoprompt.py` (role-on-first-shot, shot-size phrase), the existing suites
(`test_omni_video`, `test_videoprompt`, `test_packqa`, `selfcheck`, `smoke`, `checkfe`, wiring test) re-run at every step. All offline
except the named real-credit runs in Steps 0, 2, 3.

## 9. Honest limits and risks

1. **Not true multi-camera.** Each angle is generated independently from its own frame. Continuity of *action* between angles
   (milk level in the glass, exact hand position, pouch shape) is approximate. Mitigations: master frame as sibling reference, wardrobe
   lock, location plate, per-frame pack check, shots kept short. Step 0(b) measures how well this holds before we build.
2. **Cost/time up.** ~18 clips for a 30 s film ≈ $1.85 Draft (≈ $1.00 today), ≈ 3× at Final; ~3 min at 7 requests/min; extra frames
   (image cost not measured by me — will be measured in Step 0).
3. **More frames to approve.** Mitigated by human-gated, per-scene coverage (nothing is automatic) and "generate coverage frames" in one click.
4. **Child shots and the Omni safety filter.** Unexplained blocks seen earlier at 6–8 s; the real film passed. Close-ups of a child are a new
   exposure → watched in Steps 0/2; under Auto a blocked shot falls back to Kling with the reason shown.
5. **Claude Design collisions.** The frontend file is shared; edits are small and anchored, merged never replaced.
6. **Rework drops shots** (H3) — same as frames today; stated in the UI.
7. **Unverified until Step 0:** Omni at 2 s, close-up identity hold, image cost per frame.

## 10. Decisions I need from you

1. **Shot sizes:** add `detail` and `over` to the existing wide / medium / close / product. OK?
2. **Limits:** 2–4 shots per scene, shortest shot 2 s, sign-off scene never split. OK?
3. **Trigger:** per-scene *Break into shots* + *Cover all scenes*, always shown as an editable proposal, never automatic. OK?
4. **Cutdowns in v1:** scene-level only (shots ignored), exactly as today. OK?
5. **Dialogue:** a cut may fall mid-line (the scene's words play across its shots). OK?
6. **Branch workflow:** build on branch `coverage`; merge to master only after your localhost sign-off. OK?
7. **Step 0 first:** I run the three cheap trials (~$2) before any code, and stop if close-ups do not hold the pack/cast.
