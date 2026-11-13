---
name: live-deploy-13-nov-and-moving-data
description: 13 Nov live deploy of film-engagement-2 (master bc9f95e), CRAFT_BRIEF on, Render ids, and how local tenant data (brand profiles, uploads) is moved to live
metadata:
  type: project
---

**Deploy facts.** Last live deploy before this was 28 Oct 07:24 UTC (master `b1519e6`). On 13 Nov the owner said "go ahead and deploy live... all paid for in render". I merged `origin/master` into `film-engagement-2` (two add/add-style conflicts, `api/filmcut.py` and `tools/test_stitch_freeze.py`: the branch already had the same freeze fix in a later form `a59aa4d` with an extra `size` parameter on `_join_filter`, so I kept the branch files; merged tree identical to the tested tip), pushed `HEAD:master` = `bc9f95e` (fast-forward). Render auto-deploys master: dep `dep-dbreuem1egvs73fo800g` live, then `CRAFT_BRIEF=1` set via `update_environment_variables` (merge mode, `replace:false`) which made `dep-dbrev8g874rs73fo2cf0` live. Checked by curl: `/health` 200, `/app` 200, `/craft-grammar` 401 (new route, login needed). Craft tick on live NOT seen by me (needs the owner's login).

**Render ids** (also in [[beta-deploy-plan]]): service `srv-dagfb76k1f9s73cmr8og` (`themarketing-studio`, repo Peekay-stack/themarketing-studio, rootDir `Heritage Marketing Studio`, autoDeploy on commit, branch master), workspace `tea-dageqc8u01pc73fi55c0`. Every Render MCP call needs `workspaceId`. The Render MCP exists under two server names; either works when given the workspace id.

**Tenant data is not deployed.** `api/tenants/` is in `.dockerignore`; live reads and writes the `/data` disk. So local brand profiles, library uploads, films and briefs never reach live by a push, even when a brand JSON is tracked in git. No Render backups exist (Phase 4 open), so never overwrite live data blind.

**How a brand profile was moved (13 Nov, Kumkum Beauty).** Owner created the brands by hand on live. I generated a one-paste browser-console snippet (scratchpad `make_paste.py` builds it from the local brand JSON, dropping id/created/updated/active/voice): it GETs `/brands`, stops unless exactly one brand has the name, prints a snapshot of the live brand, POSTs `/brand-save` with `id` set to the live id, re-reads, and prints whether the active brand changed. Use `/brand-save` (does not change the active brand), NOT `/brand-fields` (a new brand there becomes ACTIVE for the whole live tenant). `put()` upserts by id or by name, so saving without an id over an existing name overwrites it. Result: live brand `ee9ab0ff61`, 34 of 49 fields filled, matching local (15 empty locally too). Library uploads (6 Kumkum items) must be re-uploaded on live by hand; scope pack uploads to the brand so the pickers stay brand-scoped. Brand book use needs `BRAND_BOOK=1` (unset).

**Still true after the deploy:** the active brand on live is Kumkum Beauty (owner to switch back); the Kumkum film exists only on the local studio.
