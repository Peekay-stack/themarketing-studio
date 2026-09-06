# Heritage Marketing Studio — Backend Integration Prompt (for Claude Code)

You are wiring a **FastAPI** backend to a finished frontend. The frontend is a single Design Component:
**`Heritage Studio.dc.html`**, which runs with `support.js`, `image-slot.js` and `assets/heritage-logo.png`.

**Do not redesign the UI.** Your job is to make the existing buttons and flows talk to real endpoints,
and to fill the empty prompt-guide slots. Read `FRONTEND_DELIVERY.md` first — it lists exactly what the
frontend already does.

---

## Golden rules — keep the frontend's approach intact

1. **Every network call is a plain relative `fetch()`** and already **degrades gracefully**: on a network
   error, a non-200, or a `501`, the UI falls back to placeholder behaviour or a locally-built document.
   Implement the contracts below so the real path is taken. Never make a failure a dead end.
2. **AI text calls go through `window.claude.complete({messages:[{role:'user',content}]})`.** Point this at
   your `POST /complete` → Claude. Each call expects a JSON string back; the client already strips
   ```-fences and parses, and falls back to sensible defaults if parsing fails.
3. **The video pipeline is artifact-gated client-side.** Do not gate it server-side. The client owns
   `scriptStatus` (`none → concept → drafted → approved`) and unlocks Shoot Board / Production only on
   `approved`. Just return artifacts.
4. **Wire-stable keys.** Persist the field and state keys exactly as listed — do not rename them.
5. Keep responses small and exactly shaped; the UI reads specific keys.

---

## 1. IMC Brief — the brand-brief skill (primary brief surface)

Brand Strategy + Communications + IMC are **one format**: `imc`, labelled "IMC Brief", tagged `skill`.
Flow: **prompt + files → `✦ Draft brief with AI` → review & refine (4 tabs) → `Generate IMC brief (.docx)`**.

### `POST /brand-brief-draft` — run the skill  (`multipart/form-data`)
- `payload` (JSON string):
  ```json
  { "brand":"Heritage", "category":"Indian dairy", "prepared_for":"…", "prompt":"the marketer's ask",
    "market_data":   { "sheet":"…", "rows":[[…]] } | null,
    "household_data":{ "sheet":"…", "rows":[[…]] } | null }
  ```
  Spreadsheets are parsed **client-side** (SheetJS for .xlsx, native split for .csv) into `rows`.
- `research` — repeated file field carrying **all** files from the five upload slots. Images
  (NeedScope / CB-CA charts) are for vision; docs and sheets parse server-side.
- **Returns** the builder payload that populates the review tabs:
  ```json
  { "brand":"…", "category":"…", "prepared_for":"…",
    "competitors":[{ "name","hero_brands","positioning","recent_moves" }],
    "needscope":{ "pins":[{ "brand","x","y","anchor" }], "bridge_territory":"Belonging",
                  "bridge_label":"Pure Doodh Ki Shakti", "reading":"…" },
    "cb_ca_db_da":{ "cb":["…"], "db":["…"], "ca_quote":"…", "ca_declarative":["…","…"],
                    "da_quote":"…", "da_declarative":["…","…"],
                    "shift_from":"…", "shift_to":"…", "caption":"…" },
    "smp":"One sentence.",
    "smp_defence":[{ "competitor","why_collapses" }],
    "smp_unlocks":{ "brand_line","mass_line","activation","product" } }
  ```
- **HTTP 400** (no API key) → return `{ "detail": "…add ANTHROPIC_API_KEY…" }`. The client shows it as an
  amber inline message and drops into manual editing. Any other failure → red message, still editable.

### `POST /brand-brief` — render the reviewed brief to Word  (`multipart/form-data`)
- `payload` (JSON string): the **same builder payload** the review tabs hold, plus `date`, `sources_note`,
  `market_data`, `household_data`, `needscope.reading`, and `cb_ca_db_da.shift_line`
  (`"From {from} to {to}."`). The client adds all of these.
- `research` — the same files.
- **Returns** the `.docx` stream. Client saves `{brand}_IMC_Brief.docx`. On failure it downloads a
  locally-built `.doc` instead.

### NeedScope wheel geometry (for placing / reading pins)
Canvas **800×640**, centre **(400, 320)**. `x = 400 + r·cos(θ)`, `y = 320 + r·sin(θ)` (θ in degrees).
Territory centre angles: **Power 270, Freedom 330, Vitality 30, Belonging 90, Security 150,
Discernment 210** — clockwise from 12 o'clock, **never reorder**. Radii: anchor ≈125, competitors ≈140,
fringe ≈150. Exactly one pin carries `anchor:true`.

---

## 2. Other brief formats (guided builder — unchanged)

`media, digital, pack, product, pr` still open the guided Brief Builder. Fields live in
`state.brief[key]`; every textarea carries `data-field="<key>"`; section sets are `SECTIONS[format]`.

### `POST /brief-docx`
- Body: `{ "title", "format", "objective", "fields": { …all brief field keys… } }`
- Returns a `.docx` blob → `Heritage_Brief_<title>_<date>.docx`. Falls back to a client-built `.doc`.

---

## 3. Video pipeline

Gated 4-step pipeline (`state.videoStep`: `scripting → shootboard → production`).

| Endpoint | Body | Response | Fallback |
|---|---|---|---|
| `POST /scene-still` | `{scene_no, prompt, ratio:"16:9"}` | `{image_url}` | gradient placeholder + quiet "Retry" |
| `POST /produce-video` | `{scenes, aspect, duration, music, voice, note}` | `{video_url}` | simulated render, placeholder player |
| `POST /video-script-docx` | `{title, logline, scenes[]}` | `.docx` blob | client-built `.doc` |

- **`state.fullScript`** — the editable script table, one row per scene:
  `{ no, tc, visual, camera, dialogue, supr }`. `supr` = on-screen super; the final row carries the
  pack-shot super "Heritage — Pure Doodh Ki Shakti". Persist 1:1.
- **`state.sceneFrames`** — `{ [sceneIdx]: { status, url } }`, **shared** between the Scripting storyboard
  and the Shoot Board Key Shots strip. Do not regenerate between steps.
- **Departments** (Cast, Location, Lighting, Music, Dialogue/VO, Key Shots) — AI drafts are already
  grounded in the approved script; the client passes `state.fullScript` into the prompt.

---

## 4. Prompt-guide slots — populate these

Empty containers render inside a "Prompt guide ▾" dropdown. Inject HTML by attribute:

- `data-prompt-guide="imc"` — **Card A of the IMC Brief screen, under the main prompt textarea.** This is
  the primary prompt-writing surface; give it the richest guidance.
- `data-prompt-guide="briefs"`, `"social"`, `"video"` — page-level guides (light background).
- `data-prompt-guide="builder"`, `"editor"` — inside the AI co-writer panel (**dark** background, use light text).

Keep guidance short and Heritage-specific: name the product / occasion / audience, the single key message,
the tone, and mandatories (#PureDoodhKiShakti, FSSAI).

---

## 5. Sample data to replace with API reads

In-memory arrays in the logic class: `BRIEF_LIBRARY`, `recentBriefs`, `queue`, `allHistory`,
`REF_LIBRARY`, `CREATIVE_DRIVE`, `ANALYSIS`, `COHORTS`, `OBJECTIVES`.

## 6. Approval roles

`this.props.reviewerMode` toggles reviewer vs manager actions in the brief editor. Map to your auth
roles (L1–L3).

## 7. Delivery

Serve `Heritage Studio.dc.html` + `support.js` + `image-slot.js` + `assets/` as FastAPI static files.
The page also loads SheetJS from jsDelivr for client-side spreadsheet parsing — vendor it locally if you
need a fully offline deployment. Do not edit the `.dc.html` except to swap the in-memory arrays for
fetches and to fill the prompt-guide slots.
