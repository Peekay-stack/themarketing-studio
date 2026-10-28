# Film builder — localhost click-through (slice S1a: frame variants)

Run it from the **exact folder** (several old copies of the project on this machine serve an old page — see memory `project-copies-use-the-opus-folder`):

1. Open `C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\` and double-click **`run-local.bat`**. (If something already owns port 8000, close it first: only one server can.)
2. Open `http://localhost:8000/app` and **hard-reload** (Ctrl+Shift+R). Sign in.
3. The branch must be `coverage` (it is; nothing has been merged or deployed).

## What S1a is
Frames used to be **overwritten** by every re-render. Now each render is kept as a **take** (a variant) in a history per shot; you choose which one the shot is animated from. A new Film step **Shots** sits between Shoot Board and Production. The Storyboard in Scripting is unchanged and shows the same chosen frames. No video is rendered or paid for in this slice; each variant costs **one image**.

## Click-through (about 10 minutes, a handful of images)
1. Open the Heritage film (or any film with an **approved script and a locked cast** and at least one rendered frame). The stepper now shows five steps: Brief · Scripting · Shoot Board · **Shots** · Production.
2. Click **Shots**. Every scene is a group; every shot is a card. A frame you already had shows as one thumbnail marked **CHOSEN**.
3. On one shot press **＋ Generate variant**. Wait for it (one image). Expected: the new picture appears next to the old one; the old one **stays chosen**; the shot's frame in Scripting is unchanged.
4. Press **×3** on the same shot (three more variants, one after another). Expected: up to four thumbnails; they differ in framing and pose but it should be the same boy / mother.
5. On a variant press **Check**: a model looks for pasted panels, wrong anatomy, extra or missing people, unwanted text. Expected: a ✓ Checked mark, or an amber `!` badge with the reason under the thumbnail.
6. Press **Use** on the variant you like. Expected: it becomes **CHOSEN**; go to Scripting → Storyboard: that shot now shows the chosen picture. Out-of-date flags on that scene's extra shots may appear (they are matched to shot 1's frame).
7. Press **✕** on a variant you do not want: it leaves the list (the file stays on disk). The **chosen** variant has no ✕.
8. Go to Scripting and press **Render** on a frame the old way. Expected: the new frame becomes the frame **and the previous one is kept** in Shots (it used to be lost).
9. Reload the page (F5). Expected: the Shots step shows the same variants and the same chosen frame.
10. On a scene with extra shots, remove one in Scripting (✕ on its card). Expected: the other shots keep their own frames and variants (no frame jumps to the wrong shot).
11. Skipped shots appear dimmed and offer no actions.

## What to tell me
Anything that looks wrong, confusing or slow; whether the variants are "different enough" (the image engine ignores the seed, so every variant is a fresh picture of the same prompt — see the trial note in `FILM_BUILDER_PLAN.md`); and whether the Shots step feels like the right place.

## Not in this slice
Video clips, takes of clips, the timeline, the preview and assembling from chosen clips (S1b–S3). Nothing here touches the Film tab's render, the Edit room, voices or sound.


---

# Slice S1b: clip takes (this one spends real video credit, at Draft size)

Same set-up as above (run `run-local.bat` from the exact folder, hard-reload, sign in). **Each Draft clip costs about $0.034 per output second at the measured Omni rate (a 4 s shot is about $0.14; the engine never makes less than 3 s).** Every button shows its estimate before you press it; the header shows what the clips made so far were estimated to cost. Final (720p) costs about three times as much. Kling (if you pin fal) is billed by fal and shows no estimate.

## What S1b is
Each shot card in **Shots** now has a **Clip** layer under its frame: you generate that one shot's video on its own (from the frame you chose), watch it, **re-roll** if you do not like it, and **choose** the take the film will use. Nothing is stitched yet (that is the next slice). The Film tab's one-button render is unchanged.

## Click-through (about 15 minutes, a few Draft clips, under about $1)
1. Open **Shots** on the Heritage film (frames chosen). The header has **Draft 360p | Final 720p** (leave Draft), a take counter and **Generate all missing (n)** with its estimate.
2. On one shot press **Generate clip (Draft) · about $0.xx**. Expected: a card appears saying "Rendering…" (20–60 s), then a playable clip with a **CHOSEN** badge (the first good clip of a shot is chosen automatically) and chips for Draft, seconds and cost.
3. Press **↻ Re-roll** on the same shot. Expected: a second take; the first **stays chosen**.
4. Play both; press **Use** on the second. It becomes CHOSEN. Press ✕ on the first: it leaves the list (the file is kept). The chosen take has no ✕.
5. Double-click Generate quickly on another shot: Expected: **one** clip, not two (the server joins an identical request that is still running).
6. While a clip is rendering, **reload the page** (F5). Expected: after the reload, when you open **Shots** again, the take shows "Interrupted" and **recovers by itself** into the finished clip within a few seconds (the clip finished on the server); if you restarted the server in between it stays "Interrupted — the server restarted…" and you can discard it.
7. Press **Generate all missing (n)**: Expected a confirm that names the number of clips, the tier and the estimated total. Press Cancel: nothing is spent. Press OK: the clips render **one after another**; a refusal (credit, safety filter) shows that shot's reason on its card and does not stop the others, except an out-of-credit message, which stops the batch.
8. Try a shot where the boy is drinking: if Google's safety filter refuses it, the card shows Google's own words (this is the filter, not a bug).
9. Change a shot's frame (choose another variant): the existing clip shows an amber **older frame** chip, because it was animated from the previous one. Nothing is deleted.
10. Reload again: all takes, the chosen ones and the estimates are still there.

## What to tell me
Anything slow, confusing or wrong; whether the estimate matches what your Google billing page shows after a few clips (that is how I reconcile the rate); and whether the clips are good enough to choose between.

## Not in this slice
Assembling the chosen clips into a film, trims, reorder and preview (S3 / S2); continuity between shots (S4); budget cap, retention (S7).


---

# Slice S3: assemble from your chosen clips, and Promote to Final

Same set-up as before (run `run-local.bat` from the exact folder, hard-reload, sign in). **Assembling spends no video credit**: it only joins the clips you chose and lays the voice and music on them (the voice and music calls are the same ones a normal render makes). **Promote to Final** DOES spend: it re-renders every chosen clip at 720p (about $0.101 per output second at the measured Omni rate, shown before you confirm).

## What S3 is
At the top of **Shots** there is now an assemble strip: how many shots have a chosen clip, whether the chosen ones are Draft, Final or Mixed, a **Promote to Final** button and an **Assemble film** button. Assembling builds the film from exactly the clips you chose, in script order, and adds it to Production as a normal version (it opens in the Edit room like any other). The Film tab's one-button render is unchanged.

## Click-through (about 10 minutes; assembling is free, promoting is about a few dollars for a 30 s film)
1. Open **Shots** on a film where some shots have no chosen clip. The strip says "n of N shots have a chosen clip". Press **Assemble film**. Expected: nothing is sent; a message names the shots still missing a clip.
2. Choose a clip for every shot (Generate all missing, or choose by hand). Press **Assemble film**. Expected: a progress state, then "Assembled from your takes" and a player with the film right under the strip; it also appears in Production's versions.
3. Check the film: right length, voice and music present, clips in script order, no frozen stretch.
4. Change one shot's frame so its chosen clip becomes "older frame", then press **Assemble film**. Expected: a confirm that names how many clips were animated from an earlier frame. Cancel sends nothing; OK assembles anyway.
5. Press **Promote to Final**. Expected: a confirm with the number of clips and the estimated total. Cancel spends nothing. OK: each chosen clip is re-rendered at Final one after another; each new Final take becomes the chosen one, the Draft takes stay in the list. The strip then says Final. An out-of-credit message stops the batch and keeps what finished.
6. Mix on purpose: leave one shot Draft, the rest Final. The strip says **Mixed**; assemble still works (the film is made at the largest size).
7. Assemble again after Promote: the new film is labelled Final.
8. If a chosen clip is shorter than its planned beat (the script's seconds changed after the take was made) the result says which shot is shorter and by how much; the film and the voice follow the real picture.
9. Open the assembled film in the **Edit room**.

## What to tell me
Anything confusing in the strip or the wording of the confirms; whether the assembled film matches what you expected from the chosen clips; and whether the Final estimate matches your Google billing after a promote.

## Not in this slice
Trimming, reordering and a preview timeline (S2); take QC (S5); continuity between shots (S4); budget cap and retention (S7). The assembled film is joined with the existing stitch, including its frozen-picture check.

# Slice S2a — Trim a chosen clip (28 Oct 2026)

Same set-up as before (run `run-local.bat` from the exact folder, hard-reload, sign in). **Trimming spends nothing**: the clip file is never changed; the cut is made when you assemble.

## What S2a is
Under a shot's clip cards, once a clip is chosen, there is a **Trim** row: a Start and an End slider (0.1 s steps, at least 0.5 s kept), what is kept ("Keeping 1.0-3.0 s, 2.0 s of 4.0 s"), a small player that plays ONLY the kept part, and **Reset**. The assemble strip now shows a **Timeline** line: the film's length from your chosen, trimmed clips against what the script plans. Not in S2a: reordering shots/scenes and the whole-film preview player (next).

## Click-through (about 5 minutes, no spend)
1. On **Shots**, pick a shot with a chosen clip. Drag **Start** to about 1 s. Expected: "Keeping 1.0-x s", a player appears that starts at 1 s and stops at the End; the **Timeline** line drops and says "1 clip trimmed".
2. Drag **End** below Start. Expected: End stops at Start + 0.5 s (never an empty window).
3. Press **Reset**. Expected: back to "Keeping all"; the player disappears.
4. Trim a shot, then **Use** another take of that shot. Expected: the trim is cleared (a trim belongs to the clip it was set on). Other shots' trims stay.
5. Trim two shots, press **Assemble film**. Expected: the film is shorter by what you cut; the result notes which shots were trimmed and by how much; the voice follows the trimmed picture; open it in the Edit room.
6. A shot made of several continuing beats (a scene longer than 8 s) says "Trim is not available" - each beat is its own clip.

## What to tell me
Whether the sliders feel right (or you want exact-second boxes), whether the preview player is clear, and whether the Timeline wording makes sense.

# Slice S2b + S2c — Reorder shots and scenes (28 Oct 2026)

Same set-up as before. Reordering spends nothing. **Know this before you try it:** moving a scene clears the director's read, flow review, editor's notes and voice plan (they depend on the order); your frames, clips, trims and sound choices move WITH their scene.

## What it is
- **Shots inside a scene:** each extra shot (shot 2 onward) has small up/down arrows on its Storyboard tile and on its Shots card. Shot 1 (the scene's own shot) stays first.
- **Scenes:** each scene has up/down arrows next to its name, on the Storyboard card and on the Shots step.

## Click-through (about 8 minutes, no spend)
1. On a film with frames and some chosen clips, open **Shots**. Click the **down arrow** beside Scene 2. Expected: Scene 2 and Scene 3 swap; the numbers stay 1, 2, 3 in order; each scene still shows ITS OWN frames and clips (check by eye: the picture under "Scene 2" is now the old Scene 3's).
2. Trim a clip in the scene you are about to move, move the scene, then look at its clip again. Expected: the trim moved with the clip.
3. In a scene with extra shots, click a shot's **down arrow**. Expected: the shots swap, and each keeps its own frame, clips and trim.
4. Look at the assemble strip's **Timeline** line: a reorder does not change the total. Then assemble the film: the scenes play in the NEW order, with the voice following.
5. Try to move a scene while a frame is rendering. Expected: a message says to wait.
6. If you have signed live-action footage for a scene, try to move it. Expected: a message says the footage is tied to the scene number and to detach it first.
7. After a scene move, the Storyboard's Director's read / Flow review / Editor's notes panels are empty; run them again when you want them.
8. Move a scene down and back up: everything is exactly as before (except the cleared panels).

## What to tell me
Whether swap-with-neighbour feels right or you want drag-and-drop; whether you want to be able to move shot 1 (the scene's own shot) too; and anything that looked attached to the wrong scene after a move.

# Slice S2d — Preview the sequence (28 Oct 2026)

Same set-up as before. Previewing spends nothing and makes no file.

## What it is
In the assemble strip (top of **Shots**) there is a **Preview sequence** button. It plays your chosen clips one after another in script order, from each clip's trim start, as the assembled film will join them. **Pictures only**: no voice, music or sound (those are laid when you assemble).

## Click-through (about 5 minutes, no spend)
1. With some chosen clips (and a trim or two), press **Preview sequence**. Expected: a player appears under the Timeline line and starts playing the first clip; at its end the next clip starts by itself.
2. Watch the **segment bar** under the player: one segment per clip, as wide as its seconds; trimmed clips are lighter; the playing one is dark with a green outline. Click a segment to jump to it. Use **Previous / Next**.
3. A trimmed clip starts at its trim's start and stops at its end (compare with its Trim row).
4. The readout says "x s of y s"; y should equal the **Timeline** line above. After the last clip the player stops; **Replay** starts again.
5. Reorder a scene (S2c) with the preview open: the bar follows the new order.
6. With a shot that has no chosen clip, the preview skips it and says which. With no chosen clips at all, the button is disabled.
7. Compare with **Assemble film**: the film should run in the same order and about the same length. The seams in the preview are accurate to about a quarter of a second; the assembled film is frame-exact. If the assembled film is a different length from the preview, tell me which shot: the server can re-time scenes by dialogue at render.

## What to tell me
Whether the preview is clear enough to judge pace and order without assembling, and whether you want the voice line shown as text over each segment.
