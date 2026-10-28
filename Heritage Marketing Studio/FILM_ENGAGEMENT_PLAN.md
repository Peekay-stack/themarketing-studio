# Film engagement — the three "boring" levers: sweep, what was built, plan for the rest

Written 29 Oct 2026. Source: `FILM_PIPELINE_MAP.md` Part 4 (the proposed process) checked against the code. Branch `coverage` (unmerged, not live).

Why these exist: the 28 Oct film was mechanically fine and creatively wrong ("okay, less repetitive, **boring as hell**"). The craft panels (director's read, flow review, editor's notes), the "be entertaining" writer rule and the builder fix *rendering* problems. These three levers move the judgement of "is it boring" **earlier**, to where changing it is free.

## 1. What the sweep found (it shrank the work)

| Lever (Part 4 row) | What the proposal assumed | What the code actually does | Real gap |
|---|---|---|---|
| **#3 Director's read on the draft, before approval** | Runs only after approval | The panel, **Break into shots** and **Flow review** are *already visible and usable on a drafted, unapproved script* (checked on the real page: all three present at `scriptStatus: drafted`) | **Sequence and visibility, not capability.** Nothing told the person to use them before approving, and nothing showed what they found next to the Approve button |
| **#5 Plan shots as text before frames** | Needs to be moved earlier | Frames cannot be drawn before approval anyway (the cast sheet and lock come from approval), so frames are never drawn before the shot plan *can* exist. The tools exist now | Same: a nudge and a summary, not a rebuild |
| **#2 Concept routes carry hook / surprise / turn / memorable moment** | Not built | **Confirmed not built.** The concept prompt asks only for a name, a one-line reason, a logline, a voiceover and 4 plain "concept beats". The "be entertaining" rule exists only in the *full-script* writer (`VISUAL_RULES`), after a route is already chosen | **Real.** Entertainment is not chosen at the idea |
| **#7 Single-person cast references** | A trial decides | Not built. One `POST /cast-reference` makes one image of the whole cast; the frame check is the backstop for pasted panels | **Real, needs a paid image trial first** |

## 2. Built: "Before you approve" (levers #3 and #5, narrowed)

A panel above the **Approve script** button, shown only on a drafted script, hidden once approved:

| Row | Shows | Action |
|---|---|---|
| Director's read | Boredom risk (low / medium / high) and the first finding; "(+n more)"; says when the script changed since the read | Read the film / Read again (existing `/film-direct`) |
| Shot plan | How many scenes have extra angles planned; says angles planned now cost nothing until frames are drawn | none (use **Break into shots** on a scene card) |
| Flow review | "Would a viewer stay? (risk)" and the reason; says when out of date | Review the flow / Review again (existing `/film-review`) |

Advisory only: **Approve is never blocked**, high risk included. Front end only; reuses the existing reads (each is one model call, as before). Tests: `tools/page_checks/film_pre_approve.js` (11 checks on the real page, the two reads stubbed). Not verified: the reads' wording on a real script (they are the existing, already-built reads).

Owner click-through:
1. Open Video, write a concept and a full script, **do not approve**. Above the Approve button you should see **Before you approve** with three rows, all "not read yet".
2. Press **Read the film**. Expected: a boredom risk and the first finding.
3. Press **Review the flow**. Expected: "Would a viewer stay?" with a reason.
4. Edit a scene's visual. Expected: both rows say the script has changed since the read.
5. Press **Approve script** with a "high" risk showing. Expected: it approves anyway, and the panel goes away.

## 3. Plan: lever #2, the concept carries its own entertainment (NOT built, needs your go)

**What:** each of the three routes also returns four short fields, so the idea is judged on entertainment before a script exists:
- `hook` — what the first 3 seconds show (an action or something unexpected, never a quiet establishing view)
- `surprise` — what the viewer does not expect
- `turn` — the moment something changes
- `memorable` — one image or action a viewer would repeat to a friend

**Where:** the concept prompt in `generateVideo` (frontend); the route cards show the four lines; the chosen route's fields are passed into the full-script writer prompt as "these must appear as scenes" and into the director's read as the intended turn. Saved with the film (`video_concept` is stored whole), so it is additive: films without the fields behave exactly as before.

**Blast radius (swept):** 9 uses of `conceptRoutes` / `pickConceptRoute` and 7 reads of the concept's `scenes` / `vo` / `logline` in the frontend; `fallbackVideo`; the refine path (it re-sends the previous route as JSON, so the new fields ride along); `writeFullScript`'s prompt; the created-log item. **Not touched:** the backend system prompt (`prompts.system_for(film=True)`), which `tools/golden_prompts.py` pins, so no golden changes. **Open:** the provocation path (`writeProvocationRoute`) has its own route structure: add the same four fields there, or leave it (a provocation is *already* a deliberate departure)? My recommendation: leave it for now.

**Test:** page checks with the model stubbed (parsing, display, hand-off to the script prompt, old films unchanged) **plus one real model call** on a real brand to see whether the four fields actually come out specific rather than generic. That call is about a cent or two; I will not run it without your OK.

**Risk to name:** the fields only help if they are *specific*. If the model fills them with generic lines ("a surprising reveal"), they add noise. The real call is how we find out before shipping.

## 4. Plan: lever #7, single-person cast references (NOT built, needs a paid trial and your go)

**Today:** one reference image of the whole cast, often a multi-panel character sheet; frames are drawn from it and the image model sometimes pastes its panels into a frame (the scene-5 collage). The frame check catches it afterwards, the builder lets you re-draw it.

**Proposal:** one single-person reference per recurring character plus a place plate, fed to frames as separate references; a frame draws only the characters in that scene.

**Trial first (decides it):** the same 6 scenes of one real film, drawn two ways (today's single sheet vs per-character references), scored on: panels pasted in, wrong or merged people, identity held across scenes. About 12 image calls; cost to be quoted from the measured image rate before I run it. Only a clear win justifies the build, which touches `buildCastReference`, `/cast-reference`, `frameBody` (which reference goes to which frame), the recipe fingerprint ("out of date" detection) and the cast lock UI. **I will not build it on the strength of reasoning alone** (the lesson of the pack-designer, 21 Sep).

## 5. What I need from you

| Decision | My recommendation |
|---|---|
| Build lever #2 (concept fields)? | Yes, with one real model call to check the fields are specific |
| Provocation path gets the same four fields? | Not now |
| Run the lever #7 trial (about 12 images)? | Yes, after #2; I will quote the cost first |
| Keep "Before you approve" advisory only? | Yes (as built); a hard gate would block people |
