---
name: imc-brief-data-ingestion-thread
description: "New initiative (17 Sep 2026), tracked in BRAND_GROUNDING_TESTING_LOG.md at the user's request even though it's not the Grounded/Independent toggle work — the IMC brief drops 95%+ of uploaded research data due to two hardcoded truncation caps, found via a real user A/B test with dummy data."
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-17T06:44:35.787Z
---

**File**: `Heritage Marketing Studio/BRAND_GROUNDING_TESTING_LOG.md`, section "New thread — IMC brief
data-ingestion & coverage quality (17 Sep)" — appended at the end, after the Round 15 brand-grounding
work. Deliberately kept in the same tracking doc at the user's explicit instruction, despite being a
different topic from the Grounded/Independent toggle — see [[brand-grounding-modes-project]] for that
separate thread.

**Origin**: the user (with Codex) built real dummy research data — a household-panel xlsx, a Nielsen
market-share/distribution xlsx, and a qualitative brand-equity pptx — and generated the same IMC brief
prompt with and without the data attached, to see how much the data actually changed the output. Asked
me to read both generated briefs plus all three source files and assess (as a senior marketing leader)
whether the data was "necessarily baked in," and how to improve it.

**What I found, root-caused in code**: `research_parse.py`'s `PER_FILE_CHARS = 8000` hard-truncates
every uploaded file to 8,000 characters before the model sees it; `brief_ai.py`'s `_payload_context()`
then caps the combined research blob at 16,000 characters total. Against the real files (145K/221K/12K
raw characters), this meant ~5.5%/~3.6%/~66% survived — and the surviving 66% of the deck stopped right
before its most decision-useful slides (the brand-equity scorecard onward). This explains a full set of
concrete defects verified against the real numbers: the competitive set didn't reconcile against the
uploaded file's own company list (dropped 3 real, sizeable competitors — Jersey/Vishakha/Vijaya, all
bigger than Amul); the focal brand's own ~22% AP share (a dominant #1) never appears; the qualitative
deck's specific scorecard/prism/recommended-proposition-territory never reached the brief; and a real
self-contradiction bug ("Sources: none attached" directly contradicted by "Per the uploaded market
data" two lines later).

**Correction logged**: I initially called the brief's inclusion of "Milky Mist" a hallucination — the
user corrected this. Milky Mist is a real category player the model reasonably knows from general
training knowledge; it just isn't in this specific synthetic dataset. The real defect is that the
brief's competitive set never reconciled against what the uploaded file's own README said was there —
not that it invented a fictional brand. Recorded so this mislabel doesn't recur.

**The user's three extension points** (their own framing, all agreed with as a senior-marketer read):
- **2a** — a new "Backgrounder" section after the Executive Summary: category perspective, current
  situation (share/penetration trends), consumer insights, problem statement. A real structural gap —
  the document currently jumps from Exec Summary straight into NeedScope mechanics with no section
  that orients a reader in evidence before strategy starts.
- **2b** — feed the qualitative research into CA-CB/Insights/Problem Statement, AND thread it forward
  into the Messaging House's pillars/RTBs later, not just the one document. Flagged as the harder half:
  right now every layer (Brief/House/Plan) independently re-reads raw files with no single "distilled
  insight" object carried forward the way a chosen core message already is.
- **2c** — a separate, standalone cross-source synthesis deck connecting patterns across data sources
  (e.g. "share falling + awareness falling + distribution holding + competition rising → dial up
  awareness"), with the user's own explicit caveat as the load-bearing design constraint: it must be
  honest when the data doesn't cohere into one clean story, offering competing reads rather than forcing
  a causal chain — the same "never invent, say what's missing" discipline
  [[brand-grounding-modes-project]] has enforced everywhere else, applied here to cross-source causal
  claims specifically (arguably the highest hallucination-risk feature in the whole studio).

**Proposed build sequence** (presented, not yet built): (1) fix the ingestion pipeline first — prereq
for everything else; (2) build 2a; (3) build 2b (extraction + the harder cross-layer threading); (4)
build 2c.

**Scope correction from the user on Phase 1**: design the ingestion fix for up to ~20 documents
attached to one brief, not just the 3 tested. This rules out "just raise the character caps" (20 files
at even a generous per-file cap would still blow well past any sane single-prompt budget, and raw-row
flattening at that scale reproduces the exact model-eyeballs-hundreds-of-rows imprecision already found
— e.g. the brief's Nandini range came out overstated vs. the real computed average). Needs a real
map-reduce shape instead: deterministic per-file aggregation for spreadsheets (real groupby/summary
stats via code, not the model guessing from flattened text — same technique I used to verify the
brief's own cited ranges), bounded per-file LLM summarization for decks/docs/PDFs (fixed output size
regardless of input length, prioritizing synthesis/recommendation content over intro slides), then a
reduce step combining the now-small per-file summaries into the brief-writing prompt. Total prompt size
this way stays roughly constant regardless of file count or file size, rather than growing linearly
with either — the actual requirement for a 20-file case.

**Status update (17 Sep, same day)**: Phase 1 (ingestion pipeline) BUILT and LIVE-VERIFIED end-to-end,
not committed to git yet. Full Map→Synthesize→Reduce pipeline in `research_parse.py`:
`analyze_spreadsheet` (real pandas/scipy groupby/trend/correlation, 5 live bugs found+fixed against the
real household-panel/Nielsen files, final numbers matched hand-computed values exactly), `analyze_document`
+ `summarize_document` (native pptx/docx/pdf structural extraction — pdfplumber font-size/position
heuristic for PDF since exports-of-decks have real selectable text but no native structure, scanned pages
flagged not OCR'd — then one bounded per-file LLM call extracting ≤25 citable findings, tested against
the real qual deck: all 16 slides correctly titled including the exact slide the old 8000-char cap
destroyed, with its real scorecard numbers correctly pulled), `synthesize_research` (one cross-file LLM
call merging corroborating claims with confidence tiers, flagging real disagreement, explicitly listing
"considered, not used" sources with reasons — tested at 9 real files, correctly merged 5 files into
shared claims and flagged 2 spreadsheet files as data-integrity artifacts). Both live AI-enrichment call
sites (`brief_ai.py` draft-time, `brandbrief.py` export-time `enrich_with_ai`) now read one shared
`research_parse.research_context_block()` instead of each doing independent raw-truncation (the same bug
existed at BOTH a 16k and a separate 14k cap — found only when tracing the actual live export path,
`brief_render.generate()` → `brandbrief.enrich_with_ai()`, not just the draft path). The `sources_note`
contradiction bug is fixed too — set deterministically from real filenames now, not left to the model.
End-to-end verified via a real authenticated POST to `/brand-brief-draft` with the original 3 dummy
files: competitive set now correctly includes Vijaya/Jersey (dropped before), SMP/CB-CA visibly grounded
in the qual deck's actual recommendation, sources_note lists all 3 files correctly. See
`BRAND_GROUNDING_TESTING_LOG.md`'s "Phase 1 built and live-verified (17 Sep)" section for full detail.
Phases 2–4 (2a Backgrounder section, 2b CA-CB/insight threading into House, 2c standalone synthesis deck)
still not started — same "confirm before big architecture" discipline as brand-grounding-modes' own
multi-phase build applies to those next.

**Status update (17 Sep, later same day)**: user asked for Phases 2-4, confirmed the brief SKILL.md
itself should be updated too (not just code — it's the file `brief_ai.py` loads into the drafting system
prompt). Agreed sequencing: commit Phase 1 first (done), then one phase at a time with live verification
between each, not batching 2-4 together.

**Phase 2 (2a Backgrounder) DONE**: new numbered section 2 in the brief, right after Executive Summary —
category perspective, current situation, consumer insights, problem statement. `brief_skill/SKILL.md`
updated (new section in the numbered list, a "Backgrounder" framework-discipline subsection, input-triage
rule, output-contract/final-check bullets) plus a new `brief_skill/references/backgrounder-guidance.md`
matching the existing reference-file voice (definition, sourcing table, worked example with the two
problem-statement failure modes named, how it hands off to CB/CA without duplicating it). Code: `brief_ai.py`
(`_OUTPUT_CONTRACT` + `_REFS` + bumped max_tokens), `brandbrief.py` (`_backgrounder_defaults()` honest
fallback pattern + `enrich_with_ai()` contract extended so export-time can also fill it), `brief_render.py`
(new "2. Backgrounder" section in `build_docx()`, sections 3-11 renumbered). Live-verified via both real
endpoints with the same 3 dummy files: `/brand-brief-draft`'s backgrounder is genuinely well-differentiated
(category vs. brand vs. consumer vs. diagnosis, real Nielsen/household figures cited, problem statement
visibly sets up the SMP that follows) and the actual exported `.docx` was inspected heading-by-heading —
clean 1-11 numbering, Backgrounder's real content (not placeholder text) in the right place. Committed.
Phases 3 (2b — House-layer threading) and 4 (2c — standalone synthesis deck) not started next.
