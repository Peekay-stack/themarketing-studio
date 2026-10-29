# Fixing "it is a boring film": development plan (29 Oct 2026)

Status: **PLAN ONLY, nothing built.** Source: the owner's second localhost test, film `de25a0df2b` ("Nothing Left To Test", Telugu, 30 s), verdict "a boring film". Read from the saved film `filmscripts/dece64e70d.json` and the rendered mp4. Evidence level per line: *seen* (in the film or saved data), *code* (read in the source), *inferred*.

## 1. Why it was boring (what the saved film shows)

| # | What happened | Evidence |
|---|---|---|
| W1 | The concept promised a lively beat ("quick cuts: she smells it, watches it boil, holds it to light" and a surprise of "a lifetime of purity tests"). The script made it ONE 6 s medium shot of her sipping. | Seen (concept beat 2 against scene 2); 0 extra shots on all 5 scenes |
| W2 | The concept voiceover's spine ("For fifty years she checked every drop, because she had to…") never reached the film. 13 spoken words against a 32-word target; scenes 2 and 5 are silent; no line names the product; the stakes are never said. | Seen. The writer prompt DOES send the concept VO (`VO: "…"`, app.dc.html ~15977), so it was ignored, not missing. |
| W3 | The premise is a non-event: the ritual quietly stops. Hook, turn and memorable are all gentle. The director's read scored scene energy 1, 1, 2, 2, 0. | Seen |
| W4 | One kitchen, five scenes, similar framing. The writer rule "change the place… instead of staying in one room" already exists in `VISUAL_RULES` and was ignored. | Seen + code |
| W5 | The sign-off is a near-still pack hero in silence (about 6 s). The writer prompt already asks for "a short payoff line" with the pack shot and it was ignored. | Seen + code |
| W6 | Our own tools predicted all of it (director's read: risk medium, findings `slow-hook` and `same-place`) and nothing acted on it. They are advisory and the findings never mention the dropped concept. | Seen + code (`filmdirect.py` `engagement`) |

**The pattern:** the rules already exist in prose, the model skips them, and nothing checks the result. So the fix is mostly *checking what the writer delivered* and *only then* more prose. A second prose rule alone would fail the same way.

## 2. The plan, in build order

Each slice is small, ships alone, and is checked before the next starts. Slices 1-2 need no model call to build or test.

### Slice 1: Check what was delivered, with no model (front end)
Add rows to the existing **Before you approve** panel (and the same lines wherever the director's read shows):
- **Voice floor:** spoken words in the script against the target (`secs × ~1.1`, the target the editor already uses). Under half: "Only 13 spoken words for a 30 s film (target about 32)".
- **Silent sign-off:** the pack scene has no spoken line.
- **Silent scenes:** count and list scenes with no audio.
- **Concept voiceover carried?** compare length only (the concept VO is English even in a Telugu film, so text matching is unsafe): if the script's spoken words are under half the concept VO's word count, say so.
All are plain counts on `fullScript`, language-free. Advisory, same as today.
Tests: extend `tools/page_checks/film_pre_approve.js`. Verify on this film's saved data: it must fire on all of these.

### Slice 2: Writer prompt: carry the voice and give the ending a payoff (prompt)
Where: the `writeFullScript` prompt (app.dc.html ~15977) only, NOT the shared `VISUAL_RULES` (that string also feeds the single-scene rewrite at ~16580 and the provocation path, so changes there reach three prompts).
- "The concept VO is the film's spine: spread its sentences, in order, across the scenes as voiceover or as the characters' own lines. Do not drop it."
- "The sign-off scene carries the payoff line spoken aloud, not only on screen."
- "At least one concept beat that says quick cuts / a sequence is written as a scene that will be covered with several short angles (mark it in the visual)." (feeds slice 4)
Check: re-run the writer once on THIS film's saved concept and measure the same numbers as slice 1 (spoken words, silent scenes, sign-off line).

### Slice 3: Director's read checks the concept was filmed (backend prompt + front end)
Where: `filmdirect.py` `build_prompt` and its `engagement` block. The read is by meaning, so it works in any language.
- New per-moment result: for the concept's hook, surprise, turn, memorable and each beat: which scene delivers it, or `missing` / `flattened` (a sequence turned into one static shot).
- New finding kind `concept-flattened`, listed first, with the beat's own words.
- New per-scene flag `sequence` (true when the story means several quick different actions inside one moment). **Not** the same as the existing `time_mode: montage`, which means time passing by repetition and bans extra angles (D5). The two must not be mixed up.
All fields additive: films saved before this keep working (same pattern as `parts`). `video_beat_map` is saved whole.
Check: run the read on this film; it must flag the flattened beat 2 and the missing "lifetime of tests".

### Slice 4: A `sequence` scene proposes its own coverage (backend prompt + front end)
Where: `sceneshots.py` `build_prompt` / `validate` and the **Break into shots** button.
- For a scene flagged `sequence`, the planner is told to give DIFFERENT actions (smell, boil, hold to light), not the same moment from new angles, and to use short shots.
- The coverage strip on that card shows a proposed plan up front (text only, no frames, no image or video cost until the owner draws them).
Check: plan scene 2 of this film; expect 3 distinct actions, within `max_extras`.

### Slice 5: Concept gate: a stake, not a non-event (prompt)
Where: the concept prompt in `generateVideo` (app.dc.html).
- New field `stake` ("what is won or lost if it goes one way or the other") and the rule: the turn must be a visible reversal by a person or an object, not something that "gently stops" or "quietly" happens.
- At least one beat is high energy.
Check: 2 real runs, one Heritage, one other category (same method as lever #2), reading the routes myself for specifics and for non-events.

### Slice 6: Make the warning hard to miss (front end)
Approve stays allowed (the earlier decision, kept). When risk is high, or any `concept-flattened` or voice-floor finding exists, **Approve script** asks one confirm that lists them (same pattern as the A4 confirm). Tests as in `film_stale_frames.js`.

## 3. Order, branch, cost

- **Branch:** `film-engagement-2` in the `hms-fixes` worktree, off `coverage-fixes` (`8495974`+). Linear history, one merge later. Known: `coverage` and `coverage-fixes` have two rehearsed merge conflicts; this adds more edits in the same frontend file, so I will keep every edit small and reload-checked.
- **Order:** 1, 2, 3, 4, 5, 6. Slices 1 and 6 are free to test. Slices 2-5 each need ONE real model call to check (writer, director's read, planner, three concept routes). Each costs cents; **I will quote before each run, not after.**
- **Not touched:** the backend system prompt (`prompts.system_for(film=True)`), so golden prompts stay pinned; `VISUAL_RULES` shared text; the provocation writer; any frame, clip or render (no image or video spend at all in this plan).
- **Blast radius to sweep before each slice:** `VISUAL_RULES` users (3 prompts + `tools/test_video_agnostic.py`), `video_beat_map` readers (director's panel, Before you approve, flow review, editor's notes), `sceneshots.validate` callers, the saved-film shape.

## 4. Done means

On THIS film's concept, with the new build: the script has at least 70% of the target spoken words, the sign-off speaks, scene 2 is planned as three different actions, the director's read lists any beat it could not find, and the concept stage would have refused "the ritual stops quietly". Then the owner makes a new film and says whether it holds attention. **That last step is the real test; my checks only prove the mechanics.**

## 5. Coverage check against BOTH test rounds (added after the owner asked)

| Item | Round | Status | Where |
|---|---|---|---|
| Frames "out of date" after department notes (no bulk fix, banner, reason, warning) | 1 and 2 (repeated) | **Built** (A1-A4), on `coverage-fixes`, not merged. The owner has NOT yet tested the fix: round 2 ran on `coverage` without it. | Section 5 of `FILM_LOCALHOST_FINDINGS.md` |
| Concept turn undeliverable (split screen) | 1 | Built (A5 prompt); not yet checked on a real model call | same |
| Shot-plan decline reason vanished; scenes silently re-timed; cast-lock wording | 1 | Built (A6, A7, A8) | same |
| Arm across face in motion (scene 1 shot 2) | 1 | **Waiting (B1, B3).** Round 2 had no such action, so no repeat evidence. | not in the slices above |
| Pack smeared / defocused on the sign-off master | 1 | **Waiting (B4).** Round 2's pack hero was clean. | folded into slice 7 below |
| One-button render runs no take checks | 1 | **Waiting (B2).** | not in the slices above |
| Boring film (premise, flattened beat, dropped voice, one room, silent ending) | 2 | **Slices 1-6** | sections 1-2 |
| Slow held open; near-still last 6 s; about 1.7 s silent tail | 2 | Slice 1 flags silence, slice 2 gives the ending a spoken line. **The near-still picture itself was not covered**, so slice 7 is added. | slice 7 |
| English narration line in a Telugu film | 2 | Question only | section 6 |
| Shots step "appeared after the rendering" | 2 | **Unexplained, not in the plan.** Needs the owner's screenshot of the step bar BEFORE a render. | section 6 |
| "Voice and music in production details" (picture 3) | 2 | Read as a comment on what is shown; no change requested that I can identify. Not in the plan. | section 6 |
| Shared frames between Storyboard and Shoot Board | 2 | Works; no work | none |

### Slice 7 (added): the ending has to move and the pack has to stay sharp
Round 1's smeared pack and round 2's near-still ending are two faces of one problem: the sign-off master.
- Prompt: the sign-off scene needs one motion (a hand takes or pours, a slow push, a reveal) and the pack stays sharp and out of a defocused foreground (this is B4).
- A free check after rendering: a scene whose motion measure stays near zero for most of its length gets flagged on its card ("this shot barely moves"), measured with ffmpeg on the clip, no model call. It generalises the motion measure I ran by hand on the round-2 film.

### Conflict to settle: B3 against slice 5
Slice 5 asks for a "visible reversal by a person or an object" and lever #2 already asks the hook to be "a visible action". Round 1's broken clip was exactly a risky action (an arm crossing a face at close range). So **B3 (no arm or hand crossing a face, no hands near the lens on key shots) must ship together with slice 5**, written into the same prompt, or the new rule pushes the writer back into the round-1 defect.

### Still waiting, deliberately
B1 (motion check on each clip by a model) and B2 (quality check after a normal render) wait for the defect to repeat on a new film. If the owner wants them anyway, they are a separate batch after slice 7 and need a vision-call calibration first (cents, quoted before running).

## 6. Open questions for the owner

1. Where did attention drop: the start, the middle, or the pack end? (changes which slices matter most)
2. Is the English narration line in the Telugu film intended?
3. Slice 6: a confirm on Approve when risk is high, or keep it a pure warning?
4. Check against this film's saved concept (cheapest), or a fresh concept?
5. Shots step "appeared after rendering": a screenshot of the step bar BEFORE a render would settle it.
6. Picture 3 (voice and music in production details): was that a change request or a comment?
7. Add slice 7 (moving, sharp ending) and ship B3 together with slice 5?
