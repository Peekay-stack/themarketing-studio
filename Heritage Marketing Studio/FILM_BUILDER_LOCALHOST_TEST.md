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
