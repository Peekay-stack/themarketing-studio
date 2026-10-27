# Coverage (shots within a scene) — localhost acceptance script

Branch: **`coverage`** (already checked out in this folder). Nothing here is on `master` or the portal. Plan: `VIDEO_COVERAGE_PLAN.md`.

## Start it
1. Double-click **`C:\Users\punie\Heritage-Marketing-Studio-OPUS\Heritage Marketing Studio\run-local.bat`** — the studio opens at http://localhost:8000. **Use exactly this folder: the machine also holds older copies of the project (`Heritage-Marketing-Studio-FULL297`, `...FULL-297v2`, `Heritage_Marketing_Studio_FULL_*`) whose `run-local.bat` starts an OLD version with no coverage.** Only one server can use port 8000, so close any other studio console window first. **Restart it if it was already running** (backend edits do not hot-reload), then **hard-reload the page** (Ctrl+Shift+R).
2. Sign in yourself; pick the Heritage brand. Local keys in `api/.env` are used (Google for images/video/voice, Claude for the shot proposals).
3. Spend while testing (Draft, 360p): proposals a few cents; each extra frame one image; a 30 s film with ~6 extra shots ≈ $1.5-2 of video.

## The checks (tick each; note anything that looks wrong)
**A. Nothing changed for a normal film**
1. Video → open your 30 s Heritage film (script approved, cast locked). The Shoot Board badge reads `N / N frames` where N = number of scenes. No "Coverage" clutter beyond a small `＋ Break into shots` line under each scene card.
2. Production → render a **Draft** exactly as you always do. Same length, same behaviour, no shot-related messages. (This is the regression check.)

**B. Break a scene into shots**
3. On the Storyboard cards: the **sign-off** scene says "always one shot"; a scene under 4 s says so; others show `＋ Break into shots`.
4. Click it on a scene that has a few seconds (a 6 s+ scene gives the best proposal). A **Proposed coverage** panel appears after a few seconds: each shot has a size, seconds, a camera-position sentence and any warning. Read them: do the angles make sense for the scene? (If the sentence is nonsense, tell me which scene.)
5. **Accept**. Tiles appear under the scene: each with its own frame area, size, seconds, text, camera. The script stays "Approved". The counters now include the extra frames (`x / y frames`).

**C. Frames for the extra angles**
6. Click **Render shot frames (N)**. (Try it first on a scene whose shot 1 has no frame: it must refuse and say to render shot 1 first.)
7. Look at each new frame: same people, same clothes, same kitchen, the real pack if it is in the shot? Is the angle genuinely different from shot 1? A tile may say **"This looks the same as shot 1"** (near-copy) — click Re-render, or edit the camera-position sentence, and try again. A wide shot says **"Location is not locked"** unless you picked a location photo.
8. Edit one shot's text: only that frame gets the amber "out of date" dot. Re-render shot 1 (the scene frame): its extra frames go out of date too (they were matched to it).
9. Remove one shot (✕) when you have two: the other keeps its own frame.

**D. Render the film with coverage**
10. Hand over to Production: it should refuse until **all** frames (including the extra ones) are rendered and current.
11. Production shows the normal cost line **plus** "Coverage adds N shots … about $X and about Y min". Render a **Draft**.
12. Watch it: the film is exactly the length you chose; the scene cuts between its angles; the scene's spoken line plays **across** the cuts (not only on the first shot); music and captions as usual; the sign-off is one shot.
13. Edit room opens on the film; a **20 s cutdown** renders as it always did (scene-level, coverage is ignored there).

**E. Reworks**
14. Regenerate the full script: all frames clear (as always). A scene whose words did not change keeps its shots; a changed scene loses them.

## What is NOT in this build (deliberately)
Takes / single-shot re-roll (next), the wide + tight location plates (B4, after coverage), coverage inside cutdowns, a "N shots" badge in the script table (the storyboard card and filmstrip show it).

## If something looks wrong
Tell me the scene, the step number, and what you saw. Roll back = stay off the `coverage` branch (`git checkout master`) — nothing on master changed.
