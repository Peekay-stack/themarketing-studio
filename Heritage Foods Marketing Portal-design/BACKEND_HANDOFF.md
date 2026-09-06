# Heritage Marketing Studio — Backend Handoff

Frontend entry: **`Heritage Studio.dc.html`** (readable source; runs with `support.js` + `image-slot.js` + `assets/heritage-logo.png`).
`Heritage Marketing Studio.html` is the inlined standalone build (for offline preview only — build against the `.dc.html` source).

The app is a single Design Component. All logic lives in the `class Component` block: `state`, handler methods, and `renderVals()`. To wire a backend you replace the client-side AI calls and the in-memory sample data with fetches.

## 1. AI touchpoints — all use `window.claude.complete({messages:[{role:'user',content}]})`
Every call already has a graceful fallback (so the UI works offline). Point each at your endpoint (e.g. `POST /complete` → Claude). All expect a JSON string back that the code strips of ```-fences and parses.

| Method | Purpose | Returns |
|---|---|---|
| `generate` | Draft a brief from a one-line ask (AI co-writer) | object keyed by `aiKeysFor(format)` |
| `convertToBrief` | Turn uploaded docs/links/notes into a primary brief | object keyed by `aiKeysFor(format)` |
| `generateSocial` | Platform-adapted posts | `{facebook,instagram,linkedin:{caption,hashtags,visual}}` |
| `generateVideo` | Script (logline, 4 scenes, vo) + iterative refine | `{logline,duration,vo,scenes[]}` |
| `generateCampaign` | Posts + film together | `{facebook,instagram,linkedin,video}` |
| `generateInsights` | Campaign-analysis insights | array of `{kind,text}` |
| `produceVideo` | Simulated render (no AI) — swap for a real render/job queue | version list |

## 2. Brief data contract (keep wire-stable)
- **Format ids:** `brand, comms, imc, media, digital, pack, product, pr` (see `FORMATS`).
- **Section sets:** `SECTIONS[format]` — Comms & IMC use the comprehensive set; Media/Digital/Pack/Product/PR use tailored sets. `brand` (and Comms/IMC in "brand mode") route to the **brand-brief skill** → `POST /brand-brief`.
- **Field keys:** each brief field is stored in `state.brief[key]`; every builder/editor textarea carries `data-field="<key>"`. Persist these keys 1:1 to your Brief columns (your INTEGRATION_NOTES `fx_<key>` mapping applies unchanged).
- Handoff Builder→Editor shares the same `state.brief`, so no mapping on send.

## 3. Sample data to replace with API reads
In-memory arrays in the logic class — swap for fetches:
- `BRIEF_LIBRARY`, `recentBriefs`, `queue`, `allHistory` (History + approval queue)
- `REF_LIBRARY` (studio inputs), `CREATIVE_DRIVE` (cross-check corpus — point at your creatives drive)
- `ANALYSIS`, `COHORTS` (campaign analysis + cohort linkage across Meta/Alphabet/Q-comm)
- `OBJECTIVES` (campaign objective dropdown → your `/catalog`)

## 4. Persistence / workflow endpoints (suggested)
- `POST /briefs`, `POST /briefs/:id/submit`, `/approve`, `/request-changes` — `submit/approve/requestChanges` methods set `status` (Draft/Pending/Approved/Changes).
- Generated posts/videos/campaigns call `addCreated(...)` → feed a `POST /assets`.
- Studio uploads (`handleStudioUpload`, `handleImportFiles`) — currently client-only; wire to blob storage and pass URLs into the prompts.
- Creative cross-check (`runCreativeCheck`) is a client-side token-overlap heuristic — replace with an embedding/similarity search over your creatives drive.

## 6. IMC Brief — the brand-brief skill flow (v3)
**Brand Strategy + Communications + IMC are now one format: `imc` ("IMC Brief", `skill`).** Media, Digital, Packaging, Product and PR are unchanged. The old "Guided vs Comprehensive" mode toggle is gone.

Screen `state.screen === 'imc'`. Flow: **prompt + files → `✦ Draft brief with AI` → review & refine (4 tabs) → `Generate IMC brief (.docx)`**. The user can skip the AI and fill in manually ("Or fill it in manually") — same fields.

### `POST /brand-brief-draft` — run the skill (multipart/form-data)
- `payload` (JSON string): `{ brand, category, prepared_for, prompt, market_data, household_data }`
  where `market_data` / `household_data` are `{ sheet, rows }` (parsed client-side via SheetJS/CSV) or `null`.
- `research`: repeated file field — **all** uploaded files across the five slots.
- **Returns** the builder payload: `{ brand, category, prepared_for, competitors[], needscope{pins[],bridge_territory,bridge_label,reading}, cb_ca_db_da{cb[],db[],ca_quote,ca_declarative[],da_quote,da_declarative[],shift_from,shift_to,caption}, smp, smp_defence[], smp_unlocks{} }`.
- **HTTP 400** → client shows the amber "needs an Anthropic API key" message from `detail` and drops into manual editing. Any other failure → red message, still editable. Never blocks.

### `POST /brand-brief` — render to Word (multipart/form-data)
- `payload` (JSON string): the reviewed builder payload **plus** `date`, `sources_note`, `market_data`, `household_data`, `needscope.reading`, and `cb_ca_db_da.shift_line` (`"From {from} to {to}."`) — the client adds these.
- `research`: the same files.
- **Returns** the `.docx` stream → saved as `{brand}_IMC_Brief.docx`. On failure the client downloads a locally-built `.doc` so the user is never stuck.

### NeedScope wheel geometry
Canvas **800×640**, centre **(400, 320)**; `x = 400 + r·cos(θ)`, `y = 320 + r·sin(θ)`. Territory centre angles: **Power 270, Freedom 330, Vitality 30, Belonging 90, Security 150, Discernment 210** — clockwise from 12 o'clock, never reorder. Pins are click-to-place (select a pin chip, then click the wheel); `anchor:true` marks the focal brand. Radii guide: anchor ≈125, competitors ≈140, fringe ≈150.

### Prompt-guide slots
Still present and empty for you to populate: `data-prompt-guide` = `imc` / `briefs` / `social` / `video` / `builder` / `editor`. The `imc` slot sits in Card A of the IMC Brief screen, directly under the prompt textarea — it is the primary prompt-writing surface, so put the richest guidance there.

## 5. Approval roles
`this.props.reviewerMode` toggles reviewer vs manager actions in the editor. Map to your auth roles (L1–L3 per your notes).

## 6. Video pipeline & document endpoints (v2 rework)
The Video Studio is now a gated 4-step pipeline (`state.videoStep`: scripting → shootboard → production) with `state.scriptStatus` (none → concept → drafted → approved). Shoot Board & Production stay locked until the full script is approved. All calls are plain `fetch()` (POST, JSON) via `apiJson`/`apiBlob`, and every one degrades gracefully (network fail or HTTP 501 → client-side fallback, never a broken page).

| Endpoint | Body | Expected response | Fallback if unavailable |
|---|---|---|---|
| `POST /scene-still` | `{scene_no, prompt, ratio:"16:9"}` | `{image_url}` | frame slot stays a gradient placeholder with a quiet "Retry" link |
| `POST /produce-video` | `{scenes, aspect, duration, music, voice, note}` | `{video_url}` | simulated render → gradient player (Download MP4 shows a toast) |
| `POST /video-script-docx` | `{title, logline, scenes[]}` | `.docx` blob | client-side `.doc` (Word-openable) built from the script table |
| `POST /brief-docx` | `{title, format, objective, fields}` | `.docx` blob | client-side `.doc` built from `SECTIONS[format]` |

- `state.fullScript` is the editable script table: one row per scene `{no, tc, visual, camera, dialogue, supr}`. `supr` = on-screen super (final row carries the pack-shot "Heritage — Pure Doodh Ki Shakti"). Persist 1:1.
- `state.sceneFrames` is `{ [sceneIdx]: {status, url} }` — shared between the Scripting storyboard and the Shoot Board Key Shots strip (not regenerated between steps).
- Department AI drafts (`draftDept`) pass the **approved script** in the prompt; wire to `/complete`.
- Word downloads name files `Heritage_Film_Script_<date>.docx` / `Heritage_Brief_<title>_<date>.docx`.
