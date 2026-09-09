---
name: studio-save-audit-doc
description: "What's Saved, Where" — the persistence/save-location audit artifact, its URL, and headline findings, 4 Sep 2026
metadata:
  type: reference
---

Artifact: https://claude.ai/code/artifact/b2dead30-c51d-440b-8b56-ab5371c3a8e1 — "What's Saved, Where."
A third, separate document from [[studio-tab-by-tab-doc]] and the Portal Wiring Audit
(https://claude.ai/code/artifact/777fa9b9-004c-4ef0-8b1a-e6445336c586) — don't conflate the three. This
one answers a different question than either: for every distinct thing a person creates or the AI
generates, across all 13 tabs, is it saved at all, and exactly where on disk.

Built from 9 parallel Explore agents (one per area), synthesized 4 Sep 2026. Not a wiring audit (doesn't
ask whether saved data is later read) and not a security audit — purely "does this survive a reload, and
where does the file/document actually live."

**Headline findings, in priority order for future fix work:**

1. **POSM/Onground generate real files and lose track of every one.** Every hero cutout, backdrop,
   studio shot, assembled poster, artwork/print export lands on disk tenant-scoped, but with no manifest
   entry — `execution["artefacts"]` was clearly built to index these and is never once written to. Only
   POSM cast drafts have a real adopt-to-permanent-record path.
2. **Video Studio has almost no document layer.** Script, department cards, character sheet, and
   scene→frame mapping are React state only — reload loses them outright. The designed fix
   (`cut.py`'s versioned manifest) is fully built and correctly wired, but orphaned by the same
   `POST /cut` wiring gap the Portal Wiring Audit already named.
3. **Social Studio saves nothing it produces** — captions, hashtags, visuals, refine edits, schedule flag
   are all client-only, zero backend route. The one real save path under the "social" umbrella (the
   geography/budget campaign: frame/benchmark/cells) is filed under the **Media** tab, not Social Studio.
4. **Sales enabler's channel economics never leave the browser** — bigger than the previously-documented
   gap. `/sales-channel` is fully built server-side and never called; even the one field that DOES save
   (brief text via `/sales-element`) writes to a sheet the frontend never loads back (`GET /trade` is
   never called).
5. **New tenant-scoping gap, same shape as `library.py`'s (fixed round 90): `learning.py` still
   hardcodes its own directory** — every tenant shares one corrections log, promoted-templates store, and
   approve/reject history. Not yet fixed.
6. Everything else (Strategy/House, Plan, PR, core Brief/Brand-profile flows) is in genuinely good shape
   — real, tenant-scoped, mostly-atomic writes, sign-off/status tracked deliberately.

If asked to fix any of this, re-verify against current code first — same discipline as the other two
audit documents.

**Revision 2 (4 Sep 2026)**, after [[studio-work-inventory]] round 91's build landed — re-checked every
row this update touches directly against the live code (`tenancy.KINDS`, every `_record_made()` call
site, the rebuilt `/library-adopt`, `briefstore.origin()`) rather than trusting the round-91 build notes
verbatim. What changed in the document:
- Finding #1 (POSM/Onground orphaned renders) — **fixed**: `made.py`, a new per-tenant ledger, is now
  written by all 15 generation routes via a shared `_record_made()` helper. Explicitly kept distinct
  from `execution["artefacts"]`, which is a separate field and is STILL empty — the new ledger indexes
  by tenant/kind, not by execution.
- Finding #2 (Ground Truth doesn't distinguish upload vs. adopted) — **fixed**: physical bucket split
  (`uploaded/` vs `tms-approved/`) plus a provenance badge computed from `source`, not the item's name.
  13 real library rows migrated live, verified byte-for-byte.
- Finding #3 (Video Studio has almost no document layer) — **partially addressed**: asset tracking via
  `made.py` now covers cast references, storyboard stills, produced films and re-scores. The actual
  document-layer gap (script, department cards, scene→frame mapping) is UNCHANGED — not touched this
  round, still real.
- Finding #4 (Sales enabler) and #5 (`learning.py` tenant-scoping) — unchanged, still open, confirmed
  still true against current code (`tenancy.KINDS` still lacks `"learning"`).
- New nuance added: Social's shared use of `/scene-still` means its post images now get a `made.py`
  ledger row too, even though the post itself (caption, hashtags, schedule flag) still has no backend
  route at all.
