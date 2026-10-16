---
name: synthetic-dicts-write-real-tenant-files
description: "Passing a made-up dict to ideas.save()/campaign.save() persists a real file into api/tenants/ — snapshot before ANY test, not just ones that look like writes."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 90a7bc18-857f-4d9f-8f33-64caa3c80f5f
  modified: 2026-08-17T17:35:17.100Z
---

In this project the store modules (`ideas`, `strategy`, `campaign`) write straight to `api/tenants/`
using whatever `id` is on the dict handed to them. So a quick unit-style check like
`campaign.save({'id':'t','platforms':[…]}, {...})` silently created a real
`api/tenants/default/platforms/t.json`, which then showed up as `count: 1` on a live `GET /campaign`.

**Why:** these functions take a plain dict rather than a handle to a loaded record, so there is nothing
to distinguish a fixture from a real document. `_path(pid)` just joins the id onto the tenant dir.

**How to apply:** snapshot `api/tenants/` **before the first test of the session**, not before the test
that obviously writes — and take the snapshot before any `*.save()` call, including ones with fabricated
ids. Redirecting `strategy.HOUSE_DIR` / `ideas.PLATFORM_DIR` at a temp copy does work and is the right
pattern (see the round-18 ladder test), but it has to be done for *every* module touched, `campaign`
included. Grep the tenant tree for the fixture's marker before declaring a test clean — a diff against a
snapshot taken too late shows nothing, because both sides already contain the residue.

Related: [[browser-verification-available]], [[design-handovers-merge-never-replace]].
