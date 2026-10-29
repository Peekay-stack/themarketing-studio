# Film tab — the owner's first localhost test (28 Oct 2026): findings and the consolidated change list

Source: the owner ran the whole Film flow on localhost on branch `coverage` (head `bb9aa48`), on the Heritage Foods film, and sent 16 screenshots plus the rendered film `C:\Users\punie\Downloads\film-275783e0e9-scored.mp4`. This file records what was seen, what was read from the code, and the changes proposed. **Nothing in sections 3-4 is built yet.** Evidence level is stated per item: *seen* (in a picture or the film), *code* (read in the source), *inferred* (a reasoned cause, not traced).

## 1. What the test confirmed works
| Area | Evidence |
|---|---|
| Concept routes carry Hook / Surprise / Turn / Remember (lever #2) | Seen: all three routes + the chosen concept under its logline; specific and Hyderabad-grounded |
| The script writer delivered the concept | Seen: scene 1 = the hook (boy drains the glass, milk moustache), scene 2 = the surprise (hard cut to the lab) |
| Craft panels | Seen: director's read (turn = scene 5, message = scene 6), flow review ("would a viewer stay? medium"; pace 1.9 shots / 10 s below the Calm band), editor's notes (start the line 0.5 s in; scenes 5 and 6 hold 4 s) |
| Shot coverage | Seen: extra shots for scenes 1, 2, 4, 6; none for the montage (scene 3); scene 5 declined with a reason |
| Render + voice controls | Film = 30.0 s, 640x360 Draft, 24 fps, picture + audio; **no frozen stretch** (the stitch fix held); Slow / Steady / Fast and the line-landing controls work |
| "Before you approve" panel | Not visible in the pictures **because the script was already approved** (the panel shows only on a draft) |

## 2. What went wrong, with evidence
| Where | What | Level |
|---|---|---|
| Scene 1 shot 2 (about 2-4 s) | The forearm stretches across the face and ends in a stump at the mouth, no hand. It is the scene's SECOND shot (Insert / Detail, "isolates the white film on his lip and sleeve"), not the opening gulp. The storyboard frame was fine: it only breaks in motion. | Seen (enlarged frames at 2.3 / 3.3 / 3.9 s); cause inferred (an arm crossing a face at close range is a known weak spot) |
| Scene 6 master (about 27 s) | The pack sits in the near foreground, defocuses, looks soft and swollen while the camera drifts; the boy walks away from camera (that part is SCRIPTED: "sends him toward the door"); then a clean pack hero shot (correct). The label smears for a moment on the sign-off scene. | Seen (frames at 26.2 / 27.4 / 28.4 / 29.4 s); cause inferred (focus drift) |
| Every frame "out of date" after the department notes were drafted | The frame prompt includes "Supporting direction from the departments" (DoP, lighting, props, wardrobe), so writing them AFTER frames exist changes every recipe. By design, but there is no bulk fix and no warning. | Code (`frameBody`, `frameRecipe`); the page text itself says departments "fold into every rendered frame, once written" |
| Scene timings changed between screens (0-5s, 5-11s, 11-18s... became 0-4s, 4-10s, 10-16s...); scene 6 3 s -> 6 s; scene 1 master hold 3 s -> 2 s | The free voice-plan step re-times scenes by dialogue and copies the timecodes back into the script rows (`loadVoicePlan`, run on approve and on entering the Shoot Board / Production). Nothing tells the person. | Code for the mechanism; **which click triggered it was not traced** (inferred) |
| The concept's turn could not be delivered | Route 1's turn = "a split screen snaps the two rooms together"; the script writer's rules forbid a split screen (one scene = one frame), so the director's read put the turn elsewhere (scene 5). | Seen + code (`VISUAL_RULES`) |
| The one-button render ran no take checks | The take checks run only on clips made in the Shots step, and they never check anatomy. The film came from the Production render. | Code |
| Scene 5 reason vanished | The shot planner's reason for declining ("hold the one crane") was a toast; the card goes back to "One shot today, Cut between camera angles?". | Seen |
| Cast-lock warning wording | "Lock location and cast in **Live action** first" may point at the wrong place. | **Unverified** |

## 3. The consolidated change list (NOT built)
### A. Frames, shoot board, script flow
| # | Change | Layer | Size |
|---|---|---|---|
| A1 | **"Re-render out-of-date (n)"** button that re-renders only the stale frames (today the only bulk button, "Generate all frames", re-renders ALL), on the Storyboard and the Shoot Board | Front end | Small |
| A2 | A **banner** on the Storyboard and the Shoot Board: "n frames out of date" (the count today appears only in the Production pre-flight / hand-over gate) | Front end | Small |
| A3 | Show **why** a frame is stale (department notes, look, cast, script words) on the banner and chip | Front end | Small |
| A4 | A **nudge** before drawing frames while DoP / lighting / props / wardrobe notes are empty, and a **confirm before drafting those notes when frames exist** ("10 frames will go out of date") | Front end | Small |
| A5 | **Concept prompt:** all four moments (hook, surprise, turn, memorable) must be single-camera, single-frame filmable: no split screens, montages, overlays | Prompt | Small |
| A6 | Keep the shot-plan "declined because..." reason on the scene card | Front end | Small |
| A7 | **Say so when scenes are re-timed** by the voice plan (before / after) | Front end | Small |
| A8 | Verify the "Lock location and cast in Live action first" wording against where the lock actually is | Front end | Tiny |

### B. Rendered-film quality
| # | Change | Layer | Size |
|---|---|---|---|
| B1 | **Motion check on a clip:** extend Look (`/take-look`) to read THREE frames (25 / 50 / 75 %) for stretched or missing limbs and a smeared pack; one model call per clip | Backend + front end | Medium |
| B2 | **QC after a normal render:** run the free checks + the motion check on every shot clip of a one-button render and list problems beside the version (the "render-stage limb check" owed since 28 Oct) | Backend + front end | Medium |
| B3 | **Risky-action rule** in the writer, the shot planner AND the concept prompt: no arm or hand crossing a face, no hands near the lens on key shots; use a wider framing or a different action. (My own lever-#2 "hook = a visible action" rule pushes toward exactly this kind of action.) | Prompt | Small |
| B4 | **Pack lock on the sign-off master:** keep the pack sharp and out of a defocused foreground | Prompt | Small |
| B5 | This film's two bad clips: **no build**. Shots step -> x3 on scene 1 shot 2 and on the scene 6 master (about $0.10 per Draft clip) -> Compare -> choose -> Look -> Assemble | Owner | — |

## 4. Suggested order and what I need
1. **A1-A4** (one batch): the shortest path to the owner's complaint, and it saves money.
2. **B1 + B2** (one batch): catches the whole class of defect. **Calibrate on this film first**: 2-3 small vision calls (cents) on the two bad clips (cut from the delivered film at 2-4 s and 26-28 s) against good ones, so the check does not cry wolf. Ask before running.
3. **A5, B3, B4** prompt rules: check each with one real model call before shipping (the model key loads only after `import main`).
4. **A6, A7, A8** polish.

Open owner decisions: go-ahead on the order; OK for the 2-3 vision calls; whether B3 / B4 also apply to the provocation writer (recommended: no, for now).

## 5. Build status (29 Oct): batch 1 built on branch `coverage-fixes` (commit `c0b06ac`, off `coverage` at `a503b13`; NOT merged, NOT live)
The owner is running a second, wider localhost test on `coverage`, so the fixes that do not depend on a model's output on one run were built in a separate worktree/branch and the owner merges them when they choose.
| # | Status | What it does now |
|---|---|---|
| A1 | Built | "Re-render out-of-date (n)" redraws only the stale frames (a scene's own frame first; its extra angles join when their match changes). Storyboard, Shoot Board and Shots step. |
| A2 | Built | Banner: "n of N frames are out of date". |
| A3 | Built | The banner lists WHY with counts ("a department note (4) · the look (2)"); each card says why in words; a frame drawn before this existed says "something changed". Implemented as a per-kind fingerprint (`parts`) stored on each frame and kept by `takes.py`. |
| A4 | Built | One confirm the first time frames are drawn with all four crew notes empty (wording differs before/after script approval); a confirm naming the count before drafting DoP/lighting/props/wardrobe when frames exist. |
| A5 | Built (prompt only) | The concept prompt requires each moment to be filmable by one camera in one shot of one place. **Not yet checked with a real model call.** |
| A6 | Built | The shot planner's reason for keeping a scene as one shot stays on the card. |
| A7 | Built (trigger traced) | `approveScript` -> `loadVoicePlan` (also entering the Shoot Board / Production when no plan exists, and any voice change) overwrote each scene's timecode with the voice plan's. A dismissible note now lists scenes whose length changed. |
| A8 | Built | Verified wrong ("Live action" is a different tab); the hint now points at the "✦ Lock location and cast" button in the Scripting step. |
| B1-B4 | **Waiting for the second test** | Prompt rules and the motion check should be set from defects that repeat, not from one film. |

Checks: 32 new page checks (`tools/page_checks/film_stale_frames.js`) + the 9 earlier suites on the same build (all pass), 3 new takes tests, the Python suites, selfcheck 1498/0, golden prompts 75 unchanged, smoke passed on the committed tree. Not verified: a real model call, a real signed-in session.

Working-agreement reminders: plan + blast radius first even for "small" items (full sweep of backend + frontend + siblings); minimal diff; verify on the real page with the network stubbed, then ask the owner to click through; commit explicit files only; mirror memory.

## 6. The owner's SECOND localhost test (29 Oct, a new film: the grandmother's steel-plate milk test, Telugu), read from 7 screenshots + `film-de25a0df2b-scored.mp4`
The owner ran it on `coverage` (without the batch-1 fixes).
- **Stale frames: REPEATED.** After the department notes were drafted every frame showed "out of date" again; the owner re-rendered all 5 (frames at 14:11, then all 5 again at 14:45). The cause is the same as the first test, so it is confirmed as real, not one film. Batch 1 (section 5) addresses it. The saved film has no `parts` on its frames (it predates the fix), so those frames would only say "something changed" until re-rendered.
- **Works as designed (owner noticed):** re-rendering a frame in the Scripting storyboard also updates the Shoot Board (one shared frame state).
- **Shots step:** works; the owner said it "appeared after the rendering of the film". The code lists Shots as step 4 of 5 as soon as a script exists (locked until approval), so the reason is NOT known: most likely a page loaded before the branch/bundle changed, to be confirmed with a screenshot of the step bar before a render. "0 of 5 shots have a chosen clip" is correct: the film was rendered with the one-button Production render, not from the Shots step. Saved state checked: each shot has 2 frame takes (the first batch kept as an unchosen take, the post-department one CHOSEN); the chosen frames are the sharp ones and match the film (the soft look of the CHOSEN thumbnails in the screenshots is the screenshot scale).
- **The film (judged as an audience, then measured):** 30.0 s, 1284x716 24 fps Draft, five scenes, hard cuts at 4/10/14/16/24 s. A coherent story (test the milk with a steel plate; the daughter-in-law gently retires the habit; she drinks; the pack lands), consistent faces, a clean pack hero, NO limb or smear defects (the first film's problems did not recur; that script had no arm-across-face action, so this is weak evidence about B1-B4, not proof). Weak spots: the open is a slow held close-up (motion step 0.5-1.0 vs 6-14 in scene 2), the last 6 s (pack hero) is a near-still (step 0.08, 4 identical frames of 144; NOT a frozen join) and the sound ends in about 1.7 s of near silence; only 13 spoken words against a 32-word target (about 6 s of speech in 30 s; scenes 2 and 5 carry none), and no spoken line names the product; scene 4 has an English narration line ("Now, only the drinking is left.") after the Telugu line in a Telugu film (owner to confirm that is intended; it may be the old 'English gloss' tidy-up).
- **Not yet done:** the A5 prompt wording on a real model call; B1-B4 still wait (this film did not show the limb/smear defects).
