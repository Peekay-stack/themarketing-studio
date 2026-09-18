---
name: imc-brief-data-ingestion-thread
description: "New initiative (17 Sep 2026), tracked in BRAND_GROUNDING_TESTING_LOG.md at the user's request even though it's not the Grounded/Independent toggle work — the IMC brief drops 95%+ of uploaded research data due to two hardcoded truncation caps, found via a real user A/B test with dummy data."
metadata:
  node_type: memory
  type: project
  originSessionId: d3a25b08-5f19-478b-bc7e-ff283771328e
  modified: 2026-09-18T04:48:02.445Z
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

**Phase 3 (2b House threading) DONE** — traced the real architecture first: every brief (any screen) goes
through `briefstore.canonicalise()` into one shared canon set via `ALIASES` (first-hit-wins), and
`strategy._brief_text()` reads a whitelist of that canon into "THE BRIEF" context every House layer's
prompt includes (core/emotional/functional, rtb_emotional/rtb_functional — the actual pillars/RTBs —
bridge/proof/culture). Same shape as the ROUND-83 audit that added needscopeAnalysis/smpDefence/
smpUnlocks after finding an identical no-canon-path gap. Fix: `briefstore.py` — `category_perspective`
added to `background`'s aliases (ordered before `sources_note`, so real category content wins over a
filename list), `consumer_insights` added to `consumerInsight`'s aliases, two new canon fields
`currentSituation`/`problemStatement` added. `strategy.py` — same two fields added to `_brief_text()`'s
whitelist (canon alone does nothing without this). Verified two ways: direct function test against real
Phase 2 draft data (no LLM call, pure string-building, all 4 fields correct incl. all 6 insight bullets
joined, no regression on pre-existing fields), and a live HTTP round-trip through the real `/house-new`
endpoint — inspected the saved house's `brief` dict on disk, all fields present with real content. No
server errors. Committed.

**Phase 4 (2c standalone synthesis deck) DONE — all four phases now complete.** User confirmed two design
choices first (this phase is genuinely new, not an extension of existing brief/house code): real `.pptx`
(python-pptx, already a dependency), backend+skill only today (verified directly, no frontend trigger yet
— the one known open item across the whole initiative). New `synthesis_skill/` (SKILL.md +
linkage-construction.md + deck-structure.md) — core discipline: find real patterns, never force one, say
plainly when nothing coheres, never let same-document claims masquerade as independent corroboration, no
brand recommendations (that's the brief's job). `synthesis.py`'s `build_linkages()` deliberately reuses
`research_parse.ingest_for_brief()`'s claims directly rather than re-parsing; `synthesis_render.py` builds
the actual pptx; new stateless route `POST /research-synthesis-deck`. Live-verified with all 10 real test
files: first run surfaced a real bug (`synthesize_research()`'s max_tokens=4000 too small at 10 files,
silently fell back to unmerged claims — uniform "Low confidence" was the tell), fixed by raising to 7000.
Re-run: confidence tiers genuinely differentiated, considered-not-used slide correctly flagged both known
artifacts plus an unprompted geographic-scoping call, and the deck's own honesty discipline showed up for
real — one slide named itself "not cross-source corroboration" rather than overclaiming, closing verdict
was "directionally aligned, quantitatively unverified." No server errors, route writes nothing to the
tenant store (stateless by design). Deck sent to the user directly. See
`BRAND_GROUNDING_TESTING_LOG.md`'s Phase 4 section for full detail.

**Frontend trigger built (17 Sep, later same day) — the initiative's one open item is now closed.** User
asked where the deck shows up, told honestly it was backend-only; asked to wire a button. Added to
`app.dc.html`'s comprehensive brand-brief builder screen (`screen:'imc'` — NOT the same "IMC Brief" label
as the separate guided/classic creative-brief format, a real navigation trap worth remembering): a
`generateSynthesisDeck()` method mirroring `generateImcDocx()`'s existing pattern exactly, a new "⊞
Research synthesis (.pptx)" button in the sticky footer, and a client-side guard toast when no files are
attached. `tools/checkfe.py` passed, LF-only line endings confirmed unchanged. Live-verified in the real
running browser (not just compile-checked): navigated to the actual screen, confirmed the button renders,
clicked with no files attached (correct guard toast fired), then simulated attaching a real file and
clicked again — a real `POST /research-synthesis-deck` fired, returned 200, and the UI showed "Downloaded
Heritage_Foods_Research_Synthesis.pptx," confirming the full chain end to end. Console errors checked —
only the same pre-existing, unrelated template-placeholder 404s already flagged.

**Real production bug found and fixed (17 Sep, later still) — split ingestion from drafting to fix a
genuine 524.** User tested the deployed site and hit a real Cloudflare 524 (proxy timeout, ~100s window)
drafting a brief with 5 decks attached — `ingest_for_brief()` ran Map sequentially, so 5 decks + Synthesize
+ the draft call itself easily exceeded it. First fix: parallelized Map via `ThreadPoolExecutor` (8
workers) — real 2-3x speedup (170s+ → 70-74s for the exact file mix that broke), but the full pipeline
still totalled ~119s, still over the line, since Draft's own call can't be parallelized away. User then
proposed running research synthesis as its own step before Draft, asked me to confirm the brief skill
doesn't need raw files once synthesis has run — traced every downstream consumer
(`brief_ai._payload_context`, `brandbrief.enrich_with_ai`, `synthesis.build_linkages`) and confirmed none
ever reads `file_results`, only `research["synth"]`. Built new `POST /research-ingest` (Map+Synthesize
only, JSON out); `/brand-brief-draft`/`/brand-brief`/`/research-synthesis-deck` now accept a pre-computed
`research` object and skip re-ingesting when given. `app.dc.html`'s `ensureResearchIngested()` caches the
result in `im.research`, invalidated on file add/remove; all three action buttons call it first. Caught and
fixed two real bugs while building this (an undefined `tmp` workdir on the new code path in
`/research-synthesis-deck`, and a missing image/document split in `/research-ingest`) before they shipped.
Live-verified end to end in the real browser: draft → ingest-then-draft; export and synthesis-deck reuse
the cache (no re-ingestion); adding a file and redrafting correctly re-ingests. No server errors. This is
real, verified progress for the case that broke — very large file counts (~20, the original design target)
untested at that scale and could still be marginal even for the ingestion step alone.

**Second bug found via deep-dive of a real generated brief.** User's real generated `.docx` (Heritage
Foods, real prompt/competitors) reviewed line-by-line via python-docx. Backgrounder/NeedScope/CB-CA/SMP
were genuinely excellent — well-differentiated, honestly caveated (the model correctly refused to invent
a 25-44-women cultural cut nothing in the data supported). But Executive Summary, Pricing/Distribution
snapshot, Opportunities & Threats, and Recommended Actions were all `brandbrief.to_skill_brief()`'s
hardcoded placeholder strings verbatim — confirmed by exact string match. Root cause:
`brandbrief.enrich_with_ai()`'s `except Exception: return None` swallowed failures with zero logging,
indistinguishable from the benign "no API key" case. Fixed: logs the exception now; `brief_render.
generate()` distinguishes genuine failure from no-key and appends an honest caveat to the document
naming which sections are structural defaults. Verified both paths (forced failure + benign no-key).
Committed and deployed.

**Chart-upload slot routing fix (17 Sep, later still).** User asked whether the split-ingestion fix
could accidentally sweep NeedScope wheel / CB-CA chart uploads into the research pipeline. Traced it and
found a real gap: the upload UI accepts `.pdf` for both chart slots but neither the frontend nor backend
image-extension lists included pdf, so a PDF chart silently got Map/Synthesized as a document instead of
read via vision. Confirmed design with the user before building: read-via-vision-and-redraw (not embed
the original file verbatim — that's separate, unrequested work), and route by UPLOAD SLOT rather than
file extension (the user dropping a file in the wheel box already says what it is). PPTX/DOCX charts
built from native shapes need real rendering (LibreOffice) to read fully — checked and it's technically
possible (the Render service is Docker-based) but the plan is `0.5c-512mb`, genuinely too tight to risk
safely (could OOM the whole container, not just fail one chart read) — raised this plainly, user chose to
ship image+PDF now and defer native-shape rendering until instance sizing is revisited, per their
explicit principle: "user control on this is absolutely critical" — never silently drop what was
uploaded, so an unreadable-as-chart file still reaches the brief as research content instead.

Built `research_parse.chart_image_from_upload()` (images pass through, PDFs rasterize via pypdfium2 —
already a dependency — page 1 → PNG), new `chart_wheel`/`chart_cbca` fields on `/brand-brief-draft`,
per-image labels in `brief_ai.py`'s vision prompt ("NeedScope wheel reference" / "CB/CA reference") for
the "unified" reading the user asked for, and frontend slot-based classification
(`isChartCapable`/`researchDocFiles`) shared by ingestion-caching and drafting, plus updated `IMC_SLOTS`
guidance text. Live-verified with a real distinctive test: a synthetic PDF reading "ZEBRAFLUX anchored in
DISCERNMENT," attached via the real browser — confirmed no `/research-ingest` call fired (correctly
chart-only) and the actual draft JSON contained the exact content, with the model explicitly reasoning
about it as a test artifact without letting it corrupt the real analysis. No server errors. Committed and
deployed. PPTX/DOCX-native-shape rendering remains open, deliberately deferred.

**Real user run reviewed (17 Sep, later still).** Synthesis deck confirmed genuinely excellent on a real
run with the original 524-triggering file mix — geometrically verified no layout overflow, found a real
non-obvious cross-source tension (qualitative treats "South India" as one market; hard data shows
Heritage's real footprint is only AP/Telangana), correctly flagged a single-source claim, honestly
flagged zero real data for the brief's own stated 25-44-women audience. A "test-deck.pptx could not be
parsed" message gave a false impression of total failure — matches no real file anywhere, source
unconfirmed, degraded exactly as designed (honest per-file note, not a crash) without affecting the other
6 real files. The brief docx's own Caveats section confirmed the earlier `enrich_with_ai()` visibility fix
is working (explicitly said several sections were structural defaults) — same root failure as before,
now disclosed instead of silent. While diagnosing it further: pulled real Render logs for the exact
request and found the diagnostic print never appeared anywhere — root cause, the Dockerfile never set
`PYTHONUNBUFFERED=1`, so Python block-buffers stdout under uvicorn/Docker by default, meaning every
print()-based log added today was potentially silently useless in production. Fixed (`ENV
PYTHONUNBUFFERED=1`). Also found and fixed a real instruction gap: the competitors field never told the
model to cite real figures verbatim (the backgrounder does) — natural model variance, not a malfunction,
but fixed for consistency. Both deployed — confirmed live via Render (finished 2026-09-17T12:35:28Z). User is picking testing back
up tomorrow with feedback; next real export failure (if it recurs) should finally surface its actual
exception in the logs, since the buffering gap that was hiding it is now fixed.


**Round: competitor "latest share/HH penetration" column + document footers (18 Sep).** User sent two more
real files ("much better now" / "almost there") plus two new asks, both gated behind "tell me before you
build anything": add Market share/HH panel to the Competitor Snapshot table, and a TMS-logo+URL footer on
every exported document. Traced the real code first: confirmed `brief_render.py` (pure Python), not
`build_brief_docx.js` (Node), is what actually renders the live brief -- the Node path is dead/superseded;
confirmed PR release has no `.docx`/`.pptx` export at all yet, so nothing to add a footer to there. User
chose (via a scoped question) to skip PR for this pass, and replaced the two-column ask with one merged
column: "latest market share/HH penetration (+/- vs last year same period)."

Built `research_parse._yoy_latest()` -- real, deterministic year-over-year (latest vs. the closest point
within 45 days of exactly one year earlier; contributes nothing rather than fake a YoY read off a nearer
point) -- and `latest_metrics_block()`, an UNCAPPED per-brand table read from the Map phase's raw data,
deliberately bypassing `synthesize_research()`'s lossy cross-file summarization so no competitor's number
gets silently dropped by a narrative-cap. Wired into `brief_ai._payload_context()` as its own block;
`_OUTPUT_CONTRACT`'s competitor object gained `latest_metric` (copy verbatim, or say "not in attached
data" -- never compute it). `brief_render.py`'s competitor table gained the column plus a real `w:cantSplit`
fix for a page-break bug the user's screenshot showed. **A real bug found before shipping**: the first
version printed raw fractions with a bare `%` appended (Heritage's real ~22% share showed as "0.2248%")
-- the source files store share as 0.22, not 22, despite the "...%" column name. Fixed with per-metric
scale detection in `_yoy_latest()` itself.

Footers: rasterized the existing product SVG mark to a static `frontend/assets/tms-footer-mark.png`
(via a browser-pane canvas conversion, since cairosvg is installed but its native cairo lib isn't present
on this Windows dev machine) and added it to `brief_render.py`, `docs.py`'s shared `_new_doc()` (covers
house/plan/idea platform/guided brief/production bible/call sheet/script in one change), and
`synthesis_render.py`'s slide builders. Live-verified end to end with a real minted test session and the
real Nielsen/household/qual-deck trio: 560 real YoY rows computed, real distinct per-competitor figures
in a live draft, the actual exported brief docx has the column + cantSplit + footer, the synthesis pptx
has the footer on all 7 slides, an existing house's docx confirmed the shared footer path too. No server
errors; test brief/session cleaned up. Committed and deployed. PR-release footer remains open (no export
exists yet) -- the user's own choice, not a gap.
