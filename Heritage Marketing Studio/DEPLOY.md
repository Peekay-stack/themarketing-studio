# Getting the Heritage Marketing Studio online

The backend serves your real front end, so once it's running there's **one URL** — open it and
the whole app is there (Home, Briefs, Social/Video Studio, Campaigns, Insights, the Brand Brief
Builder at `/brand-brief-builder`, and API docs at `/docs`).

The app runs with **zero keys** (mock copy + placeholder creatives). Add keys to switch on the
real thing: `ANTHROPIC_API_KEY` (copy + brand-brief enrichment), `FAL_KEY` (image/cinematic
video), `HEYGEN_API_KEY` (avatar video).

---

## Option A — Run locally (2 minutes, no link)
```
cd api
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd brief_assets && npm install && cd ..               # only needed for brand-brief .docx
export ANTHROPIC_API_KEY=sk-ant-...                   # optional; Windows: set ANTHROPIC_API_KEY=...
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000

## Option B — A shareable public link in ~5 minutes (local + tunnel)
Run Option A, then in a second terminal expose it with a free tunnel:
```
# Cloudflare (no signup):
cloudflared tunnel --url http://localhost:8000
# …or ngrok (free account):
ngrok http 8000
```
Either prints a public https URL you can share. Note: it's live only while your machine and the
tunnel are running — good for demos, not for 24/7.

## Option C — A permanent public link (Docker → Render/Railway/Fly)
The repo includes a **Dockerfile** (installs Python, Node, and the cairo libs the brand brief
needs) and a **render.yaml** blueprint.

**Render (easiest):**
1. Push this folder to a GitHub repo.
2. render.com → New + → **Blueprint** → pick the repo (it reads `render.yaml`).
3. Add your API keys in the dashboard (all optional) → Deploy.
4. You get a permanent URL like `https://heritage-marketing-studio.onrender.com`.

**Railway / Fly.io:** both auto-detect the Dockerfile.
```
# Railway:  railway init && railway up
# Fly.io:   fly launch   (accept the Dockerfile)   then   fly deploy
```
Set the same env vars in their dashboards/CLI.

**Run the container anywhere:**
```
docker build -t heritage-studio .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=sk-ant-... heritage-studio
```

---

### Notes
- **Database:** defaults to local SQLite. For a shared/persistent deployment set `DATABASE_URL`
  to a Postgres URL and add `psycopg[binary]` to requirements.
- **Data persistence on Render free tier:** the filesystem is ephemeral; use Postgres for durable
  data (briefs/posts) in production.
- **First brand-brief render** needs the Node deps (the Dockerfile handles this automatically).
