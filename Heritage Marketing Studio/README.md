# Heritage Marketing Studio — your front end + a solid backend

This wraps **your actual Heritage_Marketing_Studio.html** (unchanged logic) with a real
FastAPI backend built on the harness. The backend serves your front end and powers it.

## Why this matters
Your front end calls `window.claude.complete()` for every AI feature (brief fields, Social
Studio, Video Studio, Campaigns, Insights). That function only exists inside Claude's
artifact sandbox — open the file anywhere else and all AI silently falls back to
placeholders. This backend **provides that function for real** via a `/complete` proxy, so
your real UI comes alive against a server.

## Run it (one process)
```
cd api
python -m venv .venv
# Windows:  .venv\Scripts\activate     mac/linux:  source .venv/bin/activate
pip install -r requirements.txt
set ANTHROPIC_API_KEY=sk-ant-...        # PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-..."
uvicorn main:app --reload --port 8000
```
Open **http://localhost:8000** → your real Heritage Marketing Studio, with **live AI**.
Without the key it still runs; AI uses the front end's own placeholder fallback.

Optional: `FAL_KEY` switches the creative gateway (REST API) to real image/video.

## What the backend provides
- **`/complete`** — backs `window.claude.complete` (Anthropic when keyed; graceful empty
  fallback otherwise). Injected into your page via `/bridge.js` with **no edits to your app logic**.
- **Full REST API on the harness** — `domain.py` is the runtime form of the harness's
  `roles_and_approvals.py`: one Creator + a flexible 3-level approval chain, the
  brief-before-generation gate, and the publish gate (all enforced server-side, 409 on
  violation). Endpoints for briefs, deliverables, generation, creative, approval, chat.
  Browse them at **http://localhost:8000/docs**.
- **Creative gateway** — one fal.ai integration exposing Ideogram / Imagen / Nano Banana
  (image) and Veo / Runway / Kling (video); mock assets when no `FAL_KEY`.

## Pages your front end has (all served live)
Home (week schedule + approval queue), Briefs + Brief Editor, Social Studio, Video Studio,
Campaigns (activate/schedule), History, and Insights/Analysis (cohorts, channels, KPIs,
trends), with manager/reviewer modes.

## Honest scope note
Your original bundle keeps its working state **in memory** and isn't wired to persist to the
REST API (doing that means editing the minified bundle). What the backend gives your file
today is **live AI on every screen**. The REST API + approval engine are ready for the
persistence wiring — and a fully backend-connected React rebuild of these screens lives in
`web/` (run `npm install && npm run dev`) if you want a version where briefs, posts, and the
3-level approval are persisted and enforced end-to-end.

## Structure
```
api/
  main.py          FastAPI: serves the front end, /complete, full REST API
  complete.py      window.claude.complete proxy (Anthropic or fallback)
  domain.py        roles + flexible 3-level approval engine (from the harness)
  models.py        SQLAlchemy: User, Brief, Deliverable, ChatMessage
  generation.py    copy generation + brand check
  creative.py      multi-model creative gateway (fal.ai)
  catalog.py       platforms / brief types / content types (from your prototype)
  database.py      engine + seed
  static/
    index.html     YOUR Heritage front end (+ injected bridge script)
    bridge.js      defines window.claude.complete -> /complete
web/               optional fully-wired React rebuild of the screens
```

## Brand Brief Builder (NeedScope + CB/CA → DB/DA + data)
A dedicated intake UI for brand strategy briefs lives at **/brand-brief-builder** (and as a
standalone openable file). It captures everything the comprehensive brand-brief skill needs:

- **NeedScope wheel** — click to place each brand's emotional position; mark the anchor; set the
  strategic bridge into an adjacent territory.
- **CB/CA → DB/DA** — the four quadrants with verbatim consumer quotes and the shift line.
- **Competitive set** — editable competitor table (feeds the snapshot + messaging matrix).
- **Market share & sales (Excel)** — upload .xlsx/.csv; parsed client-side and carried with the brief.
- **Consumer research reports** — attach PDF/PPTX/DOCX; uploaded with the brief request.
- **SMP** — proposition, the "why only this brand can say it" defence, and illustrative unlocks.

**Generate** posts to **`POST /brand-brief`**, which builds the NeedScope and CB/CA → DB/DA figures,
assembles the skill's `brief.json`, runs the bundled `brief_assets/build_brief_docx.js`, and returns a
paginated Word brand brief. "Download brief.json" exports the same payload to run the skill manually.

### Extra setup for the brand brief
```
pip install cairosvg                 # renders the two figures (already in requirements)
cd api/brief_assets && npm install   # installs docx for the Word build script
```
`brand` is the only brief format that routes to the skill (see brief_schema.py); every other format
(Communications, IMC, Media, Digital, Packaging, Product, PR) follows your front end's own sections.

### Research parsing & AI enrichment
Files attached in the builder are uploaded with the request and parsed server-side
(`research_parse.py`): PDF via pdfplumber, DOCX via python-docx, PPTX via python-pptx (text +
speaker notes), XLSX via openpyxl, CSV/TXT/MD as text. The market-share sheet is parsed too.

- **With `ANTHROPIC_API_KEY` set:** `brandbrief.enrich_with_ai()` mines the parsed research +
  market figures into the brief's narrative sections — executive summary, NeedScope reading &
  strategic implication, pricing/distribution/content snapshots, opportunities & threats, and
  recommendations — and pulls verbatim consumer quotes for the CA/DA cells. Quotes are used as-is,
  never paraphrased; recommendations ladder to the SMP.
- **Without a key:** the brief is still produced, using deterministic synthesis from the
  structured inputs. Nothing breaks; the Caveats note what to validate.

## Video Studio — two providers
The Video Studio now has two creative providers, picked by content type:

- **Cinematic / generative** (content type *Video*) → the **fal.ai** gateway: Veo 3.1,
  Runway Gen-4.5, Kling 3.0. One `FAL_KEY`, many models.
- **Avatar / presenter** (content type *Avatar video*) → **HeyGen** (`heygen.py`): a realistic
  presenter speaking the post's script, ideal for explainers, recipes and multilingual
  (Hindi/Telugu/Tamil/English) versions. Set `HEYGEN_API_KEY` for real videos; without it a
  placeholder is returned so the app still runs.

Both route through the same `creative.generate_creative()` gateway — the model's `provider`
field (`fal` or `heygen`) decides where it goes, exactly like the image/video split.

Endpoints:
- `GET /creative-models?kind=avatar` — the avatar model(s).
- `GET /avatar-options` — presenters, voices and aspect ratios (from your HeyGen account when
  keyed, else a curated default set).
- Generation: pass `creative_model="heygen-avatar"` with optional `voice` and `ratio` to
  `POST /briefs/{id}/generate`, or `POST /deliverables/{id}/creative`. The post's caption is
  used as the avatar script.
