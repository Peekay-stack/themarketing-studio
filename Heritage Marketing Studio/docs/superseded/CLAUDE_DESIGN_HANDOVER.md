# Handover — Heritage Marketing Studio: Social & Video Studio frontend

**To:** Claude Design
**From:** Claude Code
**Scope:** Social Studio + Video Studio screens only.
**Backend status:** All endpoints below are built, deployed and verified live against the fal.ai
account. Nothing on this list is waiting on me — this is purely frontend work.

---

## 0. The file you are editing — please read this first

Edit **`api/frontend/app.dc.html`** from the zip/folder accompanying this doc.

> ⚠️ **Do not start from an older `Heritage Studio.dc.html`.** The current file already contains
> backend-wiring fixes (Social Studio pulls the latest brief, images display correctly, `/complete`
> bridge). Starting from an earlier copy silently reverts them. Take a backup of the current file
> before you begin so we can diff.

### House conventions in this file — keep them

It is a Claude Design component served **standalone** (not in the artifact sandbox). React, ReactDOM
and `window.claude.complete` are injected into `<head>` at serve time. So:

- Markup uses `sc-if` / `sc-for` with `{{ }}` bindings; the bottom `render()` returns one flat props
  bag (`~line 3270+`). New UI must follow that pattern — handlers and values go in the bag.
- Text AI goes through `window.claude.complete({messages:[{role:'user',content}]})` → returns a
  **string**; strip ``` fences then `JSON.parse`. There is an existing helper pattern in
  `generateCampaign` / `writeFullScript` — copy it.
- Network calls go through `async apiJson(path, body)` (`~line 2528`).
  **Caveat that matters for B4:** it returns `null` for *any* non-200 **and** for 501, so the
  server's `detail` message is currently unreachable. See B4 for what to change.
- Toasts: `this.showToast(text, tone)` where tone is `'info' | 'ok'` (`~line 2524`).
- Never block on failure — every generate path must degrade to a placeholder + toast.

### Brand

Heritage green `#259821` · deep forest `#14331F` · ghee gold `#E8A93C` · cream `#FBF6EA` ·
Heritage red `#E2231A`. Fonts: Bricolage Grotesque (display), Plus Jakarta Sans (text).
Buttons: **green = create**, **white/outline = regenerate/rework**, **gold = the one hero action per
screen**. Rework panels stay quiet until there is content to rework, then reveal.

---

## 1. Backend contracts (live — wire to these exactly)

### `POST /scene-still` → `{ image_url }`
```json
{ "prompt": "<what to depict>",
  "ratio": "1:1" | "16:9" | "9:16",
  "style": "real" | "product" | "infographic" | "vector",   // default "real"
  "characters": "<shared character sheet>",                  // optional
  "seed": 12345 }                                            // optional int — same seed = same look
```
`501` when no image key is configured (keep the branded placeholder), `500` with `detail` on error.

### `POST /produce-video` → single joined film
```json
{ "scenes": [...fullScript rows], "aspect": "16:9", "duration": "20s",
  "music": "Warm strings", "voice": "Warm female (Telugu-accented English)",
  "note": "<revision note>", "model": "veo-3.1-fast" }
```
Returns:
```json
{ "video_url": "/renders/heritage-film-xxxx-scored.mp4",
  "shots": 3, "seconds": 20, "audio": "vo+music", "clips": [...], "model": "veo-3.1-fast",
  "detail": "<present ONLY on partial failure — show it even on 200>" }
```
`video_url` is **one same-origin URL** — no playlist handling needed, and `downloadMp4` works as-is.

**How it renders (context for your UI copy):** video models cap at 8s per call, so the backend splits
the film into 8/6/4s shots, renders them **silent** 4-at-a-time, joins them, then generates the
voiceover in **one** TTS call plus **one** instrumental music bed and mixes them over the finished
cut. The VO is therefore a single continuous performance across all cuts — it does not restart at
shot boundaries. `audio` reports what actually made it in: `"vo+music" | "vo" | "music" | "none"`.

Cost per render (relevant to B5 and the quality toggle):

| Film | Shots | `veo-3.1-fast` (default) | `veo-3.1` (Standard) |
|---|---|---|---|
| 10s | 2 | ~$1.00 | ~$2.00 |
| 20s | 3 | ~$2.00 | ~$4.00 |
| 30s | 4 | ~$3.00 | ~$6.00 |

### `window.claude.complete(...)`
All copy/script generation and every rework action.

---

## A. Social Studio

### A1 — "Rework & iterate" panel (refine, don't regenerate)

Today the only action is **Generate posts**, which always starts from scratch.

Add a rework panel **below the Live previews, visible only once `state.posts.length > 0`**:

- Labelled textarea: *"Refine these posts — e.g. 'punchier hooks', 'add a festive angle', 'shorten
  the LinkedIn one'."*
- Button **`↻ Rework posts`** — white/outline, not the green hero.
- On click, call `window.claude.complete` with the **current posts** + the instruction, asking for the
  same JSON shape back:

  > "Revise these existing Heritage Pure Milk social posts per the instruction. INSTRUCTION: `<user
  > text>`. CURRENT POSTS: `<JSON>`. Return ONLY the same JSON shape with the revised posts; keep the
  > platform keys identical."

- Replace `caption` / `hashtags` / `visual` **in place**. Keep each post's `id`, `imageUrl` and
  engagement numbers. Do **not** wipe images unless `visual` actually changed.
- Keep **Generate posts** as the from-scratch path.

### A2 — Visual style selector

Add a **Visual style** chip row on the Social screen (above or beside Generate):

| Chip | Sends `style=` | Use |
|---|---|---|
| **Real (people)** | `real` | Photoreal lifestyle with real people *(default)* |
| **Product only** | `product` | Pack / glass hero, no people |
| **Infographic** | `infographic` | Flat data-viz / claims graphic in brand colours |
| **Vector** | `vector` | Flat vector illustration |

- Store in state, default **Real (people)**. Mutually exclusive, clearly marked as selected.
- `fetchPostImages` (`~line 2300`) already calls `/scene-still`; add `style: <selected>` to the body
  (it already sends `ratio:'1:1'`).
- Add a small **`↻ Regenerate visuals`** link on the previews that re-runs `fetchPostImages` for all
  posts at the current style — so Real → Product can be flipped without regenerating copy.

---

## B. Video Studio

### B2 — Script FIRST, then frames (most important change)

**Current (wrong):** concept always yields 4 scenes → storyboard frames render from those 4.
**Required:** **Concept → Full script → Storyboard frames (one per script row) → Shoot Board → Production.**

1. **Frames must come from the script, not the concept.** Right now `generateFrame` (`~line 2640`)
   reads `this.state.videoConcept.scenes[idx]`, and `generateAllFrames` (`~line 2649`) loops over
   `videoConcept.scenes`. Both must iterate **`state.fullScript`** — the rows
   `{no, tc, visual, camera, dialogue, supr}` — so the storyboard shows **N cards for N script
   scenes**. `state.fullScript` becomes the single source of truth.
2. **Prompt per frame** = that row's `visual` (+ `camera`), with `ratio:'16:9'`.
3. **Gate on an approved script.** Frames / Shoot Board / Production depend on `fullScript` existing
   (`scriptStatus` is already `none | concept | drafted | approved`) rather than on the 4-scene concept.
4. **Duration drives scene count.** When writing the full script, ask for a scene count that suits the
   chosen `prodDuration` — suggested **10s → 3, 20s → 4–5, 30s → 6–7** scenes.
5. **Write real spoken lines in the script rows — they become the voiceover.** The backend builds the
   VO by concatenating each `fullScript` row's **`dialogue`** field into one continuous read (stage
   directions like `VO:` / `Voiceover –` are stripped automatically, and rows with `—` or empty
   dialogue are skipped). So the `dialogue` column is now load-bearing audio, not just a script
   annotation — rows left empty produce a **music-only film**.
   Ask the model for roughly **2–3 words per second** of film across all rows (~60 words for 30s), as
   one flowing narration rather than disconnected fragments. The concept prompt (`~line 2723`) asks
   for *"a one-line voiceover"*, which is fine for the concept card but should not be the whole film's
   VO. If you'd rather send an explicit whole-film VO string, add `script: { vo: "...", logline: "..." }`
   to the `/produce-video` body — the backend prefers `script.vo` when present and falls back to the
   rows otherwise.

### B1 — Consistent characters across frames

Text-to-image invents different people every call unless pinned. Do both:

1. **Derive a character sheet once**, after the script is approved (or from the Cast department text) —
   e.g. *"Lead: warm Indian mother, late 20s, shoulder-length hair, mustard kurta; daughter ~7 in
   school uniform; grandmother in white saree."* Store as `state.videoCharacters` and expose it as an
   **editable field** so the user can tweak it.
2. **Pass it to every frame** — send `characters: state.videoCharacters` **and a fixed per-film
   `seed`** (one integer generated when the script is approved, stored as `state.videoSeed`, reused
   for every frame) on each `/scene-still` call. Same characters text + same seed → consistent look.

### B3 — Rework panels for script, frames and the cut

Same pattern as A1 (textarea + `↻ Rework`), in **three** places:

- **Scripting** — refine the full script from a note ("tighten scene 2", "add a farm beat", "make VO
  Hinglish"). Pass current `fullScript` + instruction to `window.claude.complete` → revised rows.
  (`state.refinePrompt` already exists at `~line 1578` for the concept step.)
- **Frame generation** — a note that re-renders one frame or all frames with extra direction ("more
  warmth", "wider shot"): append the note to that frame's `/scene-still` `prompt`, keeping the same
  `characters` + `seed` so consistency holds.
- **Production** — `state.prodPrompt` (`~line 1580`) already feeds `note` on `/produce-video`. Surface
  it properly as a **"Rework the cut"** panel (textarea + `↻ Re-render`), shown once a first cut exists.

### B4 — Surface what the render actually did

Both original B4 bugs are **fixed in the backend** (malformed fal endpoint slugs, and only one 8s clip
being rendered regardless of duration). What's left is making the result legible:

1. **Show the server's `detail`.** `produceVideo` (`~line 2744`) currently does
   `if (res && res.video_url) finish(res.video_url); else setTimeout(() => finish(null), 2000);` —
   so a real failure is indistinguishable from preview mode. Because `apiJson` returns `null` on
   non-200, give `/produce-video` a call path that keeps the body (or have `apiJson` return
   `{ok, status, data}` and update its ~6 call sites consistently — your choice, but don't half-do it).
   Then toast `detail` on failure **and on success**, since a 200 can carry a partial warning
   ("music generation failed", "showing the first shot only").
2. **Show `shots` / `seconds` / `audio`** next to the player — e.g. *"3 shots · 20s · VO + music"*.
   The rendering spinner copy at `~line 1192` already says "Assembling shots, VO & music", which is
   now literally true; a live *"shot 3 of 4"* readout would need B5.
3. **Replace the stale download message.** `downloadMp4` (`~line 2764`) says *"Render isn't wired to a
   file in preview"* — that's the message the user kept hitting. `video_url` is now same-origin so the
   `download` attribute genuinely names the file.
4. Keep the simulated-render placeholder as the fallback when there is genuinely no URL.
5. **Add a Draft / Final quality toggle** on the Production screen: Draft → omit `model` (defaults to
   `veo-3.1-fast`), Final → send `model: "veo-3.1"`. Show the cost difference from the table above;
   each render spends real money and users should know which tier they just bought.

### B5 — Long films: leave the duration chips at 10 / 20 / 30 for now

`state.prodDuration` currently offers `['30s','20s','10s']` (`~line 3165`). The backend supports up to
**120s**, but a single HTTP request is the wrong shape for the long ones:

| Film | Waves of 4 shots | Rough wall-clock |
|---|---|---|
| 10–30s | 1 | ~1–2 min — fine as a normal request |
| 60s | 2 | ~3 min — borderline |
| 120s | 4 | ~5–7 min — will outlive the fetch |

`apiJson` has no timeout, so a 2-minute film would hang then look like a silent failure. **Please
don't add 60s/120s chips as part of this pass.** If you want them, say so and I'll add job endpoints
(POST → id → poll status → URL) so you can build a real progress readout against them.

---

## 2. Please do NOT touch

- Briefs / IMC Brief builder, Campaigns, Insights screens.
- The `<head>` inject block marked `HF_HEAD_INJECT`, `support.js`, `image-slot.js`, or the
  `window.claude.complete` bridge — the standalone build depends on them.
- Endpoint paths, request field names, or response field names. If you need a new field, flag it
  instead of inventing one; I'll add it server-side.

---

## 3. Acceptance checklist

- [ ] Social: rework panel appears only once posts exist; reworking preserves ids/images/engagement.
- [ ] Social: style chips change `style` on `/scene-still`; `↻ Regenerate visuals` refreshes images
      without touching copy.
- [ ] Video: storyboard card count equals `fullScript` row count (not a fixed 4).
- [ ] Video: script rows carry real spoken `dialogue` (that text becomes the voiceover).
- [ ] Video: frames/Shoot Board/Production gated on the script, not the concept.
- [ ] Video: every frame call sends the same `characters` + `seed`; the character sheet is editable.
- [ ] Video: rework panels present for script, frames and the cut.
- [ ] Video: server `detail` is visible in a toast on both failure and partial success.
- [ ] Video: player shows shots · seconds · audio; Draft/Final toggle sends the right `model`.
- [ ] Duration chips still 10/20/30.
- [ ] Nothing outside Social/Video changed; app still runs standalone with no console errors.

## 4. What to hand back

The edited **`app.dc.html`**, plus a short note of anything you implemented differently from this doc
(or couldn't). I'll verify the endpoint wiring — field names and shapes are the usual place a design
pass and a backend pass drift — then integrate, run the pipeline end-to-end and repackage.

## One-paragraph version to paste at the top of your prompt

> In Heritage Marketing Studio's Social and Video studios: (1) add a "Rework & iterate" panel that
> refines the *existing* generated posts rather than starting over; (2) add a Visual-style selector —
> Real (people) / Product only / Infographic / Vector — passed to the image endpoint as `style`;
> (3) reorder the Video flow so the full script is written first and the storyboard renders one frame
> per script row (count driven by the chosen duration), not a fixed 4; (4) keep characters consistent
> by sending a shared, editable character sheet plus a fixed per-film seed to the image endpoint;
> (5) add rework panels for script, frames and the produced cut; and (6) surface what a render
> actually did — the server's `detail` message, shots/seconds/audio, and a Draft/Final quality toggle.
> The backend (`/scene-still` with style/characters/seed, `/produce-video` returning one joined,
> scored MP4, and `window.claude.complete`) is already built and verified — wire the UI to it. Warm,
> on-brand, one hero action per screen, graceful fallbacks everywhere.
