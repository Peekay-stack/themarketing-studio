---
name: beta-deploy-plan
description: "Deploying the studio as a beta at themarketing-studio.com — Render + Cloudflare, the state-on-disk constraints, and the Phase-1 prep done 9 Sep"
metadata: 
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-10T06:27:52.519Z
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

## Phase 3 — IN PROGRESS (started 10 Sep). Domain: themarketing-studio.com

The user owns `themarketing-studio.{com,online,store,in,xyz}` at GoDaddy — **only `.com` is in play**.

**Done 10 Sep:**
- Cloudflare: site `themarketing-studio.com` added, **Free** plan. Imported-DNS review screen — **deleted
  the 2 parked GoDaddy A records** (`15.197.148.33`, `3.33.130.190`); kept the `www` CNAME, the
  `_domainconnect` CNAME, and the `_dmarc` TXT.
- Cloudflare-assigned nameservers: **`carl.ns.cloudflare.com`** + **`jacqueline.ns.cloudflare.com`**.
- GoDaddy: nameservers were **already** set to those two (pre-done in an earlier session); **DNSSEC is
  OFF** (button reads "Turn On DNSSEC" — leave it). Nothing to change at GoDaddy.
- Clicked "I updated my nameservers" → Cloudflare now says *"checking the nameservers… wait a few
  hours"*. **Waiting for zone to go Active** (email will confirm).
- Render: **both custom domains added** to the `themarketing-studio` service (apex + `www`), showing
  unverified. Render CNAME target = **`themarketing-studio.onrender.com`**; Render A-record fallback IP
  = **`216.24.57.1`**.

**DONE 10 Sep — site is LIVE at https://themarketing-studio.com** (and `/app`):
- CF DNS: `CNAME @` + `CNAME www` → `themarketing-studio.onrender.com`. Added grey-cloud, Render
  verified + issued Let's Encrypt certs for both, then flipped both to **Proxied / orange**.
- `_dmarc` TXT kept; `_domainconnect` CNAME left in place (harmless GoDaddy helper).
- Render Custom Domains: both **Verified + Certificate Issued**; `www` auto-301s to apex.
- CF SSL/TLS: Universal SSL **Active** (covers apex + `*.`, expires 9 Dec, auto-managed);
  **Always Use HTTPS ON**, Automatic HTTPS Rewrites ON, TLS 1.3 ON. Encryption mode should be
  pinned to **Full (Strict)** on SSL/TLS→Overview (behaviourally already strict — clean 200s,
  no redirect loops; user to eyeball the Overview page).
- Verified end-to-end: `http→https` 301, `www→apex` 301, `https://themarketing-studio.com/app`
  → 200 login screen in a real browser, valid cert.
- Still optional (not blockers): Min TLS → 1.2, enable HSTS once http is never coming back.
  `COOKIE_SECURE` is already on by default (no `STUDIO_INSECURE_COOKIES`).

## Phase 4 — Ops (after the domain)

- Daily backup of `/data` to R2/S3 (Render Starter disks aren't auto-backed-up).
- Monthly spend cap on the Anthropic/Fal accounts (app has no per-user quota).
- Cloudflare rate-limit on `/complete`, `/scene-still`, `/posm-image`.
- If brand-brief/POSM renders OOM on 512MB → bump Render plan to the $25/2GB tier (disk + data survive).

## Render MCP — SET UP & WORKING (10 Sep)

Uses the **hosted** endpoint (no Node/npx — `npx` isn't installed on this machine). Config lives in
**`.mcp.json` at the OPUS repo root** (`C:\Users\punie\Heritage-Marketing-Studio-OPUS\.mcp.json`),
**git-ignored** (`.gitignore` line `.mcp.json`) because it holds a live Render API key:

```json
{ "mcpServers": { "render": {
  "type": "http", "url": "https://mcp.render.com/mcp",
  "headers": { "Authorization": "Bearer rnd_<key>" } } } }
```

API key = Render → Account Settings → API Keys (current one named `claude_code_mcp1`; the first key
leaked in a chat screenshot and was rotated out). MCP config only loads at Claude Code **startup** —
edit the key → restart → `/mcp` shows `render` connected. Workspace: **`Peekay-Workspace`**
(`tea-dageqc8u01pc73fi55c0`). Service: **`themarketing-studio`** (`srv-dagfb76k1f9s73cmr8og`).
Every Render MCP call needs `workspaceId` passed explicitly.

Gives a session: `list_services` / `get_service` / `list_deploys` / `get_deploy` / `list_logs`
(build+app+request) / `get_metrics` / `update_environment_variables` / `trigger_deploy` /
`query_render_postgres` — no more screenshot ping-pong. **Auto-deploy is ON** (branch `master`,
trigger `commit`); commits outside `Heritage Marketing Studio/` (e.g. `.claude-memory/`) don't
rebuild.

## Known beta-grade rough edges (documented, not blockers)

`/complete` has no retry/backoff and no global exception handler → provider outage = raw 500. Single
worker → one slow generation briefly blocks others. `api/tenants/` is committed to git (~478MB) —
optional cleanup: `git rm -r --cached` + gitignore, since `STUDIO_DATA_DIR` makes the checked-out
copy dead weight.

See [[account-migration-plan]] for the git/backup discipline and [[studio-work-inventory]] for the
architecture review this plan draws on.
