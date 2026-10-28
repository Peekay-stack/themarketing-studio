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
6. While a clip is rendering, **reload the page** (F5). Expected: after the reload the take shows "Interrupted" and **recovers by itself** into the finished clip within a few seconds (the clip finished on the server); if you restarted the server in between it stays "Interrupted — the server restarted…" and you can discard it.
7. Press **Generate all missing (n)**: Expected a confirm that names the number of clips, the tier and the estimated total. Press Cancel: nothing is spent. Press OK: the clips render **one after another**; a refusal (credit, safety filter) shows that shot's reason on its card and does not stop the others, except an out-of-credit message, which stops the batch.
8. Try a shot where the boy is drinking: if Google's safety filter refuses it, the card shows Google's own words (this is the filter, not a bug).
9. Change a shot's frame (choose another variant): the existing clip shows an amber **older frame** chip, because it was animated from the previous one. Nothing is deleted.
10. Reload again: all takes, the chosen ones and the estimates are still there.

## What to tell me
Anything slow, confusing or wrong; whether the estimate matches what your Google billing page shows after a few clips (that is how I reconcile the rate); and whether the clips are good enough to choose between.

## Not in this slice
Assembling the chosen clips into a film, trims, reorder and preview (S3 / S2); continuity between shots (S4); budget cap, retention (S7).
