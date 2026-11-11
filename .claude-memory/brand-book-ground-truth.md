---
name: brand-book-ground-truth
description: "11 Nov: brand book / identity manual upload read into the prompts as ground truth. BUILT on branch brand-book-ground-truth (worktree C:/Users/punie/hms-brandbook, head ea4a877), localhost only, NOT merged, off unless BRAND_BOOK=1. Where it lives, the three gates, how to run the test studio, what is proven and what is not (no real brand book read yet), open owner decisions, Nat Habit book parked."
metadata:
  node_type: memory
  type: project
  originSessionId: 188571ea-55a9-4350-b9a0-481c7a9d13b2
  modified: 2026-11-11T06:26:08.275Z
---

Owner ask (11 Nov): let the brand book and identity manual be uploaded as ground truth (Memory, and from the "What the studio is told" page), so producers, briefs and the messaging house have a reference. **Localhost only for now.** "Keep it optional." Nat Habit brand-book writing (nathabit.in; the owner declined the first WebFetch) is **parked** until this is built; that book could become the first real test document.

**What exists before this:** Library kind `brandbook` (upload + sign-off in Memory) was never read by anything. All generators get brand context through `brandprofile.voice_block()` (~15 callers), so one injection point serves all.

**Built (branch `brand-book-ground-truth` from master `b1519e6`, commits `bb60655` backend, `ea4a877` page; worktree `C:\Users\punie\hms-brandbook`, NOT merged, not pushed to deploy):**
- `api/brandbook.py`: reads a SIGNED-OFF library file (PDF/Word/PPT, reuses `research_parse` extractors, pages up to 150, 60k chars per read) into a digest with fixed sections (positioning, voice, messaging, claims, dos, donts, identity) and a page ref per point via `jsonout.ask_json`. Digest = DRAFT until a person edits and approves; stored on the brand profile JSON under `brand_book`, never in the Library. Hex colours not in the book's own text are dropped; unread page refs cleared; scanned PDFs refused in words.
- Three gates before one word reaches a prompt, else `voice_block` is byte-identical: env `BRAND_BOOK=1`, the brand's own "use" tick (default off, = "optional"), an approved digest whose file is still in the Library and still signed off. Strategy scope never gets the visual section. Block sits before "Only these are the brand's"; text says the profile stands where they differ (my reading of "keep it optional", owner can flip it).
- Routes: GET `/brand-book`, POST `/brand-book-read|save|use|drop`; `/brand-fields` carries `brand_book`. Hourly brake `BRAND_BOOK_CALLS_PER_HOUR` (10). Page: collapsed card under Brand core (upload, sign off, Read it, per-point edit, Approve, on/off, "exactly what would be added"); one flat row list (`bagBrandBook`, handlers `bb*`).
- Tests: `tools/test_brand_book.py` 44 cases (model stubbed, scratch data dir); selfcheck 1438 calls 0 problems; checkfe ok; smoke passed. Page driven in a browser against a scratch studio with the model stubbed: sign off, read, edit, approve, switch on, panel carried the block; upload from the card; corrupt PDF refused.

**Run the test studio:** scratchpad `run_bb_owner.py` (worktree code, owner's own local data from the OPUS api folder as `STUDIO_DATA_DIR`, real key loaded into the process only, `BRAND_BOOK=1`) on http://localhost:8001/app. UI-check variant `run_bb_stub.py` (scratch data, stubbed model, test session cookie) on 8001.

**NOT proven:** the digest quality on a REAL brand book (working agreement: prove the risky generation step on the owner's real example first; the first real read is a small paid model call, ask before it); the "switched off" amber note in a browser; a real scanned/outlined PDF; whether the book actually improves ideas/briefs (needs an A/B like the craft layer).

**Open:** merge decision and live rollout (off on live unless `BRAND_BOOK=1` is set there); producers' gate gets dos/donts only via the same block (not a separate gate); later could split `identity` manual from `brandbook` kind; Telugu/Hindi books untested.
