---
name: beta-deploy-plan
description: "Deploying the studio as a beta at themarketing-studio.com — Render + Cloudflare, the state-on-disk constraints, and the Phase-1 prep done 9 Sep"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-09T15:34:08.431Z
---

Goal: a gated beta at **themarketing-studio.com**. Domain is at **GoDaddy** (registrar), DNS/proxy/SSL
via **Cloudflare** (user's account, both already logged in). Host: **Render** (Dockerfile +
`render.yaml` already in the repo, at `Heritage Marketing Studio/`, NOT the repo root).

## The hard constraint

Stateful monolith: FastAPI + SQLite (`heritage.db`) + brand/house/plan JSON on disk + generated
media on disk, one company per process (`STUDIO_TENANT` resolves once per process). So: **one
container, one uvicorn worker, one persistent volume, HTTPS.** No serverless, no autoscaling.

## Phase 1 — repo prep, DONE 9 Sep (uncommitted)

- **`STUDIO_DATA_DIR` env var** (new). `tenancy.DATA_DIR`/`TENANTS` and `database._default_db_url()`
  both honour it — set it to a mounted volume path and all writable state (tenant docs + generated
  assets + `heritage.db`) lives there, so a redeploy doesn't wipe it. Unset → unchanged (local/tests).
  Verified both ways. The legacy read-only `api/renders|media|edits` dirs are deliberately NOT moved.
- **`SEED_PASSWORD_<UID>`** env vars (new, `database.py`). `SEED_PASSWORD_PUNEET` etc. override the
  `<id>-dev` dev passwords; an account with an env password is re-hashed on every boot (rotate =
  redeploy). Verified: `puneet` logs in with the env value, not `puneet-dev`.
- **`/docs` `/redoc` `/openapi.json` removed from `_PUBLIC_PATHS`** (`main.py`) — API browser + schema
  now behind login on a deployed instance.
- **`.dockerignore` rewritten** — was leaking `api/.env` (real keys!) into image layers and baking in
  ~730MB of dev test data. Now excludes `**/.env*`, `api/tenants|media|renders|edits|library|learning`,
  `*.db`, handover files, `.git`, `.claude`.
- **`render.yaml` rewritten** — added the `disk:` block (mountPath `/data`, 10GB), `STUDIO_DATA_DIR=/data`,
  the 2 missing keys (`GOOGLE_API_KEY`, `NVIDIA_API_KEY`), 4 `SEED_PASSWORD_*` placeholders,
  `healthCheckPath: /health`. `GEN_MODEL` set to `claude-opus-4-8` (the code's own default).
  Cookies are Secure automatically unless `STUDIO_INSECURE_COOKIES=1` — never set that in prod.

## Phase 2 — DONE 9 Sep. LIVE at https://themarketing-studio.onrender.com

- GitHub: **`Peekay-stack/themarketing-studio`** (`master`). Deployed commit **`4a238e7`**.
- Render service `themarketing-studio`: **Starter** ($7/mo), **Singapore**, Docker, Root Directory
  `Heritage Marketing Studio`, health check `/health`. Web Shell + Disk tabs available.
- Persistent disk **`studio-data`, 10GB, mount `/data`** — attached and WORKING (`/data/heritage.db`
  + `/data/tenants/default/...` confirmed via Web Shell, survives redeploy).
- Login works with `SEED_PASSWORD_PUNEET` (set as env var). `/health` shows anthropic/fal/google/
  nvidia = true (heygen/sarvam false — same as local, not needed). `GEN_MODEL=claude-opus-4-8`.
- Generation verified end to end on the deployed box: brief → messaging house (8/8 layers) → idea
  platform, all producing real strategic content.

### Two bugs hit and fixed during Phase 2 (both committed + pushed)

1. **`.dockerignore` ate `research_parse.py`** — the `**/research_*/` glob (meant for dated scratch
   folders) also matched the module, so `/brand-brief-draft` 500'd with `ModuleNotFoundError` on the
   container (lazy import, so the app still booted). Fixed in `4a238e7`: narrowed to
   `**/research_[0-9]*/` + explicit `!` re-includes for `research_parse.py`/`library.py`/
   `learning.py`/`media.py`.
2. **`STUDIO_DATA_DIR` not set** — the service was created MANUALLY so `render.yaml`'s envVars were
   never applied; the user added the API keys + `SEED_PASSWORD_PUNEET` by hand but missed
   `STUDIO_DATA_DIR`. Result: all data wrote to the ephemeral `/app/api/tenants`, `/data` sat empty.
   Fix was one env var in Render → Environment: `STUDIO_DATA_DIR=/data` → redeploy. **Lesson: when a
   Render service is made manually, every `render.yaml` env var must be re-entered by hand.**

## Phase 3 — NEXT (tomorrow, 10 Sep). Domain: themarketing-studio.com

Not started. First step: is `themarketing-studio.com` already in the user's Cloudflare account?
(account id `c3cb7d8bdadbdc5c48edde69b7dead3b`). Then:
- Cloudflare **Add a site** (if needed) → 2 nameservers → set them at **GoDaddy** (registrar).
- Render → service → Settings → **Custom Domains** → add `themarketing-studio.com` +
  `www.themarketing-studio.com`. Render gives the DNS target.
- Cloudflare DNS: `CNAME @` and `CNAME www` → `themarketing-studio.onrender.com`, **Proxied**.
  (Cert issuance may need the record briefly DNS-only then re-proxied.)
- Cloudflare SSL/TLS → **Full (Strict)**; **Always Use HTTPS** on.
- Verify: `https://themarketing-studio.com/app` → login; cookie is `Secure`.

## Phase 4 — Ops (after the domain)

- Daily backup of `/data` to R2/S3 (Render Starter disks aren't auto-backed-up).
- Monthly spend cap on the Anthropic/Fal accounts (app has no per-user quota).
- Cloudflare rate-limit on `/complete`, `/scene-still`, `/posm-image`.
- If brand-brief/POSM renders OOM on 512MB → bump Render plan to the $25/2GB tier (disk + data survive).

## Render MCP — offered, NOT set up

User tried `claude mcp add render ...` in a plain PowerShell window → `claude` not on PATH. Next
time: write the Render MCP server straight into the MCP config (`.mcp.json` at repo root or
`~/.claude.json` `mcpServers`) — `{command:"npx", args:["-y","@render/mcp-server"], env:{RENDER_API_KEY:"..."}}`
— and have the user paste a Render API key (Account Settings → API Keys). Would let a session read
Render logs / deploy status / env directly instead of screenshot ping-pong.

## Known beta-grade rough edges (documented, not blockers)

`/complete` has no retry/backoff and no global exception handler → provider outage = raw 500. Single
worker → one slow generation briefly blocks others. `api/tenants/` is committed to git (~478MB) —
optional cleanup: `git rm -r --cached` + gitignore, since `STUDIO_DATA_DIR` makes the checked-out
copy dead weight.

See [[account-migration-plan]] for the git/backup discipline and [[studio-work-inventory]] for the
architecture review this plan draws on.
