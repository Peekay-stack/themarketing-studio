# Heritage Marketing Studio — start here

The **front end is your Claude Design build** (`app.dc.html` + the dc-runtime), served by the
backend at `http://localhost:8000`. The backend supplies AI to the whole app through a bridge
(`window.claude.complete` → `POST /complete`), so the brief builder (guided + comprehensive
brand-brief for Comms/IMC + external input + AI co-writer), Social, Video, Campaign and Insights
all generate real content when a key is set.

## Run it
### Windows
Double-click **`run-local.bat`** (needs Python 3.10+; Node 18+ only for the brand-brief Word export).
### mac / Linux
```
./run-local.sh
```
Then open **http://localhost:8000**.

Two things to know on first run:
- The front end loads React from a CDN (unpkg), so the machine needs **internet** for the first paint.
- Without a key, every AI action uses the front end's built-in **fallback** sample content. To get
  real AI, put your key in **`api/.env`** (`ANTHROPIC_API_KEY=sk-ant-...`) and restart.

## What's wired now
- **All AI touchpoints** — brief `generate`, `convertToBrief`, `generateSocial`, `generateVideo`
  (+ refine), `generateCampaign`, `generateInsights` — route to `POST /complete`.
- **Brand-brief skill** endpoint (`POST /brand-brief`) is live for Brand and for Comms/IMC in
  comprehensive mode (Word brief).
- Legacy original bundle still at **/studio**; API docs at **/docs**.

## What's next (not yet wired — these are the additive pieces from the assessment)
- **Persistence:** the front end currently keeps briefs/created content in memory. Saving to the
  DB (briefs, approval queue, History) needs small fetch hooks added into the front end
  (`submit/approve`, `addCreated` → `/briefs`, `/assets`).
- **Server-side file parsing** for convert-to-brief (PDF/DOCX/PPTX/XLSX) via `research_parse.py`.
- **Real video render** (`produceVideo`) → fal.ai / HeyGen job.
- **Live analytics** for Insights (Meta / Alphabet / q-commerce connectors).

## Deploy
See **DEPLOY.md** — `Dockerfile` + `render.yaml` build a container that serves this front end + API.
