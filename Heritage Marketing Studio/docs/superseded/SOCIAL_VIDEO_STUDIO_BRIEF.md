> ⚠️ **SUPERSEDED — use `CLAUDE_DESIGN_HANDOVER.md` instead.** That doc is the current handover for
> Claude Design: same scope, but with verified code anchors, the finished `/produce-video` contract,
> cost figures and an acceptance checklist. This file is kept only as history.

# Design brief — Heritage Marketing Studio: Social & Video Studio upgrades

**For:** Claude Design (edit the existing `Heritage Studio.dc.html` component)
**From:** Claude Code — the backend endpoints below are already built and live.
**Scope:** Social Studio + Video Studio only. Do not touch Briefs, Campaigns, or Insights.

The backend is done. Your job is the UI + the client-side wiring described here. Keep the app's
graceful-degradation style: every network call is a plain `fetch`/`apiJson` that already falls
back cleanly, and text AI goes through `window.claude.complete({messages:[{role:'user',content}]})`.

---

## Backend contracts (already implemented — wire the UI to these)

**`POST /scene-still`** — one image. Now accepts style + character consistency:
```json
{ "prompt": "<what to depict>", "ratio": "1:1" | "16:9" | "9:16",
  "style": "real" | "product" | "infographic" | "vector",   // default "real"
  "characters": "<shared character sheet — keep people identical across a film>",  // optional
  "seed": 12345 }                                            // optional int; SAME seed => consistent look
```
Returns `{ "image_url": "..." }`, or HTTP 501 when no image key is configured (keep the branded
placeholder), or 500 with a `detail`.

**`POST /produce-video`** — `{scenes, aspect, duration, music, voice, note}` → `{video_url}` (or 501/500 with `detail`). No change needed; see §B4.

Video models cap at 8s per render, so the backend now splits the film into 8/6/4s shots, renders one
per beat, and joins them into a single MP4 served from `/renders/...`. `video_url` is still one URL —
nothing to change — but the response also carries `shots` (how many clips), `seconds` (total length),
and `clips` (the individual URLs). Worth showing as *"3 shots · 20s"* next to the player, and a
`detail` may be present as a warning even on 200 (e.g. one shot failed).

**`window.claude.complete(...)`** — all text generation/rework (scripts, captions). Returns a string; strip ``` fences and `JSON.parse`.

---

## A. Social Studio

### A1 — "Rework & iterate" prompt window (refine, don't regenerate)

Today the only action is **Generate posts**, which always starts from scratch. Add a **rework**
panel below the Live previews (visible only once posts exist):

- A labelled textarea: *"Refine these posts — e.g. 'punchier hooks', 'add a festive angle', 'shorten the LinkedIn one'."*
- A button **`↻ Rework posts`** (white/outline "regenerate" style, not the green hero).
- On click: call `window.claude.complete` with a prompt that includes **the current posts** and the
  user's instruction, asking for revised posts in the *same JSON shape* (`{platform: {caption, hashtags, visual}}`),
  keeping platforms unchanged. Replace the captions/hashtags/visual in place (keep each post's `id`,
  `imageUrl`, engagement numbers). Do **not** wipe existing images unless the visual description changed.
- Keep the existing **Generate posts** button as the from-scratch path.

Prompt skeleton:
> "Revise these existing Heritage Pure Milk social posts per the instruction. INSTRUCTION: "<user text>". CURRENT POSTS: <JSON>. Return ONLY the same JSON shape with the revised posts; keep the platform keys identical."

### A2 — Visual style selector (clearly marked options)

Add a **Visual style** control on the Social screen (a row of chips, above or beside Generate),
with these mutually-exclusive options and short helper labels:

| Chip | Sends `style=` | Use |
|---|---|---|
| **Real (people)** | `real` | Photoreal lifestyle image with real people |
| **Product only** | `product` | Pack / glass hero shot, no people |
| **Infographic** | `infographic` | Flat data-viz / claims graphic in brand colours |
| **Vector** | `vector` | Flat vector illustration |

- Store the choice in state (default **Real (people)**).
- Pass it to every `/scene-still` call as `style`. (The existing `fetchPostImages` helper already
  calls `/scene-still`; just add `style: <selected>` to its body, and a `ratio:'1:1'`.)
- Add a small **`↻ Regenerate visuals`** link on the previews that re-runs `fetchPostImages` for all
  posts with the currently-selected style (so the user can flip Real → Product and refresh images
  without regenerating copy).

---

## B. Video Studio

### B2 — Script FIRST, then frames; frame count follows the script/duration  (most important)

**Current (wrong) order:** Concept (always 4 scenes) → frames render from those 4 concept scenes.
**Required order:** **Concept → Full script → Storyboard frames (one per script scene) → Shoot Board → Production.**

Changes:
1. **Duration drives scene count.** When writing the full script, tell the model to produce a number
   of scenes appropriate to the chosen duration — suggested mapping: **10s → 3, 15s → 4, 20s → 5,
   30s → 6–7, 60s → 9–10** scenes (let the model choose within reason). The full-script table
   (`state.fullScript`, rows `{no, tc, visual, camera, dialogue, supr}`) becomes the single source of truth.
   **Also scale the `vo` field with duration.** The concept prompt currently asks for *"a one-line
   voiceover"*, which is right for 10s but leaves a 30s+ film as almost pure music — the whole `vo`
   string is now performed as one continuous read across the finished film (see §B4), so ask for
   roughly **2–3 words per second** of film (~60 words for 30s, ~140 for 60s).
2. **Frames come from the script, not the concept.** `generateAllFrames` / per-frame generate must
   iterate **`state.fullScript`** (one storyboard frame per script row), not `videoConcept.scenes`.
   The storyboard should show N cards = N script scenes.
3. **Gate frames on an approved script.** Keep frame generation (and Shoot Board / Production) locked
   until the full script is written/approved — which is already the pattern; just make frames depend on
   `fullScript` existing rather than the 4-scene concept.
4. Each frame's `/scene-still` call should use the row's `visual` (+ `camera`) as `prompt`, `ratio:'16:9'`.

### B1 — Consistent characters across all frames

Text-to-image makes different people each call unless you pin them. Do both:
1. **Derive a character sheet once.** After the script is approved (or from the Cast department text),
   build a short, reusable description of the recurring people — e.g. *"Lead: warm Indian mother, late
   20s, shoulder-length hair, mustard kurta; daughter ~7 in school uniform; grandmother in white saree."*
   Store it as `state.videoCharacters`. Offer an editable field so the user can tweak it.
2. **Pass it to every frame.** Send `characters: state.videoCharacters` and a **fixed per-film `seed`**
   (generate one integer when the script is approved, e.g. `state.videoSeed`, and reuse it for every
   frame) on each `/scene-still` call. Same characters text + same seed → consistent look across frames.
   (The backend already accepts `characters` and `seed`.)

### B3 — "Rework & iterate" windows for script, frames, and edit

Add a small refine panel (textarea + `↻ Rework` button) in **three** places — same pattern as A1:

- **Scripting:** refine the full script from a note ("tighten scene 2", "add a farm beat", "make VO Hinglish").
  Rework via `window.claude.complete` passing the current `fullScript` + instruction → revised rows.
- **Frame generation:** a note that re-renders a single frame or all frames with extra direction
  ("more warmth", "wider shot") — append the note to that frame's `/scene-still` `prompt`. Keep the
  same `characters` + `seed` so consistency holds.
- **Production / edit:** the revise field already exists (`state.prodPrompt` → `note` on `/produce-video`).
  Surface it clearly as a **"Rework the cut"** panel with a textarea + `↻ Re-render` button, shown once a
  first cut exists.

### B4 — Draft video won't play / download  (FIXED in the backend — small UI asks remain)

Two real bugs, both fixed:
1. The fal endpoint slugs were malformed (`fal-ai/veo/3.1` → 404 `Application 'veo' not found`), so no
   video ever rendered. Correct slugs are now in place and verified against the account.
2. Only ONE 8s clip was rendered regardless of the chosen duration, so a 20s film came back as an 8s
   fragment. The backend now renders one shot per script beat and joins them (see the contract above).

Renders default to **Veo 3.1 Fast** on cost grounds. Pass `model: "veo-3.1"` for the Standard tier —
worth exposing as a **Draft / Final quality** toggle on the Production screen.

| Film | Shots | Fast (default) | Standard |
|---|---|---|---|
| 10s | 2 | ~$1.00 | ~$2.00 |
| 20s | 3 | ~$2.00 | ~$4.00 |
| 30s | 4 | ~$3.00 | ~$6.00 |
| 60s | 8 | ~$6.00 | ~$12.00 |
| 120s | 15 | ~$12.00 | ~$24.00 |

Plus a few cents for VO + music. (Cheaper than it was: silent renders are ~half price per second.)

**Audio is one continuous track, not per-shot.** Shots render SILENT; the voiceover is then generated
in a single TTS call for the whole film and the music as one instrumental bed, mixed over the finished
cut with the bed ducked under the voice. One TTS call = one voice, one performance, continuous across
every join. The `voice` field is mapped onto a real ElevenLabs voice (gender + language are read out
of the free text, and typing an actual voice name like "Sarah" passes straight through). Response
carries `audio: "vo+music" | "music" | "vo" | "none"`.

UI asks:
- Show `detail` from the response in a toast — on non-200 **and** on 200, since a 200 can carry a
  partial-failure warning ("music generation failed", "showing the first shot only"). Note `apiJson`
  currently returns `null` for any non-200, so it needs to pass the body through for this to work.
- Surface `shots` / `seconds` next to the player (*"3 shots · 20s"*).
- Keep the simulated-render placeholder as the fallback when there's genuinely no URL.
- No player/download rewrite needed. `video_url` is now same-origin, so `downloadMp4`'s `download`
  attribute actually names the file (it was being ignored on cross-origin fal URLs).

### B5 — Long films (60s / 120s) need a polling flow

The backend supports up to **120s** and renders shots 4-at-a-time, but a single HTTP request is the
wrong shape for the longer ones:

| Film | Waves of 4 | Rough wall-clock |
|---|---|---|
| 10–30s | 1 | ~1–2 min — fine as a normal request |
| 60s | 2 | ~3 min — borderline |
| 120s | 4 | ~5–7 min — will likely outlive the fetch |

So: the duration chips can gain **60s** and **120s**, but if they do, `/produce-video` should move to
a job pattern (POST returns an id → poll for status → URL on completion) with a progress readout
("shot 6 of 15"). Flag this and I'll add the job endpoints to match whatever shape you build.
Until then, keep the chips at 10/20/30.

---

## States & style (keep consistent with the app)

- Palette: Heritage green `#259821` / deep forest `#14331F` / ghee gold `#E8A93C` / cream `#FBF6EA`.
  Fonts: Bricolage Grotesque (display), Plus Jakarta Sans (text).
- Buttons: green = create, white/outline = regenerate/rework, gold = the one hero action per screen.
- Every generate/rework action: show a spinner + inline status; never block on failure (toast + fallback).
- Rework panels are secondary/quiet until content exists, then reveal.

## One-paragraph summary to paste at the top of the design prompt

> In Heritage Marketing Studio's Social and Video studios: (1) add a "Rework & iterate" prompt panel
> (textarea + regenerate button) that refines the *existing* generated posts/script rather than starting
> over; (2) add a Visual-style selector — Real (people) / Product only / Infographic / Vector — passed to
> the image endpoint as `style`; (3) reorder the Video flow so the full script is written first and the
> storyboard renders one frame per script scene (count driven by the chosen duration), not a fixed 4;
> (4) keep characters consistent across frames by sending a shared character sheet + a fixed seed to the
> image endpoint; and (5) add rework panels for script, frames, and the produced cut. The backend
> endpoints (`/scene-still` with style/characters/seed, `/produce-video`, `window.claude.complete`) are
> already built — wire the UI to them. Warm, on-brand, one hero action per screen, graceful fallbacks.
