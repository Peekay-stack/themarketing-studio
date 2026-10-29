---
name: render-holds-signoff-locked-still
description: the render step deliberately holds the sign-off pack shot locked and still; never ask a script rule or a check to make the sign-off camera move
metadata:
  type: project
---

In `api/main.py` (the from_frame branch for a `brand` role scene that is the last scene, with no explicit movement chosen) the video prompt says: `Hold the shot locked and still - a steady product hero. Keep the pack at the exact same size, scale and position in frame from the first frame to the last; the camera does not push in, pull out, zoom or drift`. `videoprompt.py` also keeps the pack's shape and label (_KEEP_PACK) and says the closing shot is the pack clean, front-facing, with empty space around it. It was added for an artefact where the pack grew through the clip (a push-in scales it up). An explicit movement_class chosen by the person wins over it.

**Why it matters:** on 29 Oct I wrote a writer rule that made the sign-off scene 'move' (even suggesting a slow push-in; the real model took it) and a Render check that called every held sign-off 'barely moves'. Both fought this hold, and the 'near-still silent ending' the owner called boring in round 2 was this hold plus no spoken line, not a render fault. Found only by reading the render path in the second audit.

**How to apply:** for the sign-off scene, give it life from what is IN the frame (a hand takes or pours from the pack, a glass fills, steam) and a spoken payoff line, with a locked-off camera cell; never a push-in, zoom or drift on the pack. Before adding any script-level rule about a scene, read what the render path already does with that scene role (main.py ~1340-1420, videoprompt.py, packscene.py). The Render check now reports a held sign-off in its own words (filmqc.findings, the `signoff` argument). Related: [[film-engagement-2-plan]], [[judge-the-film-not-the-pipeline]].
