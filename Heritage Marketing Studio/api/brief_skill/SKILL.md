---
name: brand-brief
description: Produces a paginated Word brand strategy brief integrating competitor landscape, NeedScope emotional positioning, Current to Desired (CB/CA to DB/DA) framework, and Single Minded Proposition. Use when the user asks to build a brand brief, create a comprehensive brand brief, build a brand strategy doc, generate a brand positioning brief, do a NeedScope analysis, create a competitive brief with SMP, or uploads NeedScope chart images, market-share spreadsheets, household consumption data, brand strategy decks, competitor PowerPoint files, or qualitative research notes for brand analysis.
---

# Brand Brief

Generate a six-to-seven-page Word brand strategy brief that integrates four frameworks: competitive landscape, NeedScope emotional positioning, CB/CA → DB/DA shift, and Single Minded Proposition.

## What this skill does

Take whatever inputs the user has supplied — uploaded files, prior conversation context, or just a brand name — and produce a paginated `.docx` brief in the workspace folder with:

1. Executive summary.
2. Backgrounder — category perspective, current situation, consumer insights, problem statement. Orients a reader in evidence before any strategy appears; see `references/backgrounder-guidance.md`.
3. Competitor snapshot table.
4. Messaging comparison matrix.
5. NeedScope brand positioning section with an embedded wheel as `Figure 1` (built either from the user's uploaded NeedScope chart or constructed from communications cues).
6. CB/CA → DB/DA section with the embedded shift diagram as `Figure 2`.
7. Single Minded Proposition section with a green-bordered callout and a "why only this brand can say it" defence.
8. Pricing, distribution, and content snapshot.
9. Opportunities and threats table.
10. Recommended actions, every one of which ladders to the SMP and respects the NeedScope discipline.
11. Caveats that name exactly what to validate before externalising.

## When to invoke this skill

Invoke when the user wants any of the following:

- A full brand brief integrating NeedScope + CB/CA → DB/DA + SMP.
- A standalone NeedScope brand positioning analysis (still run the full skill, but lead with §4).
- A standalone SMP development exercise (still run the full skill — the SMP only earns its right to exist when the NeedScope and CB/CA → DB/DA reads support it).
- A competitive brief that ingests uploaded NeedScope research, market-share, or HH data.

Do not invoke when the user wants a plain content audit, a brand voice guideline doc, or a generic marketing performance report — those are different skills.

## High-level flow

Follow this order. Do not skip steps even if some inputs are missing — for missing inputs, run the fallback and flag the assumption in the brief's caveats.

1. **Triage what the user has provided.** Look at uploaded files, prior turns in the conversation, and the user's instruction. Use AskUserQuestion (or an elicitation form) only when a hard ambiguity remains after triage — for example, the brand is unnamed, or the user has uploaded two competing NeedScope charts and you don't know which is current.
2. **Parse inputs.** Extract data from every uploaded file the user provided. See `references/input-parsing.md` for the parsing patterns for each file type.
3. **Build the analytic core.** In this order: (a) the backgrounder — category perspective, current situation, consumer insights, problem statement, (b) competitor snapshot, (c) messaging matrix, (d) NeedScope positions for every relevant brand, (e) CB/CA → DB/DA for the focal brand, (f) SMP triangulation. The backgrounder goes first because CB/CA and the SMP should answer the problem statement it names, not the other way round. The SMP is the last analytic step because it must reconcile NeedScope + CB/CA → DB/DA + competitive whitespace.
4. **Generate the two figures.** NeedScope wheel and CB/CA → DB/DA diagram, as PNG files in the workspace. Use the SVG templates in `assets/` and convert with `cairosvg`. See `references/needscope-framework.md` for the wheel construction logic and `references/cb-ca-db-da-framework.md` for the shift diagram.
5. **Assemble the .docx.** Use the parameterised `assets/build_brief_docx.js` Node script with `docx-js`. The script handles page size (US Letter), styles (Arial body, sentence-case headings), tables (DXA widths), embedded figures, footers with page numbers, and the SMP callout block. See `references/docx-assembly.md` for the exact contract between the JSON brief object and the script.
6. **Validate and deliver.** Convert the docx to PDF (`soffice --convert-to pdf`) and inspect at least the first and last page as images to confirm the figures render and pagination is reasonable. Surface a `computer://` link to the `.docx` (and optionally the `.pdf`) in the chat.

## Input triage rules

Apply these in order:

- If the user uploaded a NeedScope chart image (PNG/JPG/PDF/PPTX), treat its brand positions as ground truth and build the brief's wheel to match them. Read the chart with vision tools where supported, or ask the user to confirm positions if the image is ambiguous.
- If the user uploaded market-share data (XLSX/CSV), use the numbers verbatim in the competitor snapshot, pricing, and distribution sections. Never override user-supplied numbers with web-research estimates.
- If the user uploaded HH (household) consumption / penetration data, use it in the distribution and opportunities sections to flag occasion-level patterns (e.g. heavy chai-time skew, low Gen-Z penetration).
- If the user uploaded brand strategy docs (PDF/DOCX), treat them as the authoritative source for the brand's current positioning, taglines, and tone — feed those into the messaging matrix and the CB/CA / DA cells.
- If the user uploaded competitor PPTX decks, parse them for taglines, audience claims, and feature emphasis to populate the messaging matrix.
- If the user uploaded qualitative research notes, mine them for verbatim consumer language to use in the CB/CA quote and DA aspirational quote.
- If multiple files conflict, default to: NeedScope chart > market-share data > brand docs > competitor decks > qualitative notes > web research. Note the conflict in caveats.
- Build the backgrounder from whatever of the above was supplied before touching any other section — its category perspective and current situation read the same market-share/HH data as the snapshot section; its consumer insights read the same qualitative notes as the CB/CA quotes. It is the one section that is allowed to say plainly that a part is not assessed when the matching input never arrived.

## Output contract

The brief must:

- Be exactly one `.docx` file delivered to the workspace folder.
- Be 6 to 8 pages on US Letter at default body 11pt (the backgrounder adds roughly a page).
- Embed both figures (NeedScope wheel + CB/CA → DB/DA) at high resolution.
- Have a footer carrying "Brief title · Page X of Y".
- Have a green-bordered SMP callout containing one sentence ending in a full stop.
- Have a "Caveats" section enumerating every assumption made because of missing inputs.

Do not produce: a PDF without the docx, a markdown-only output, or a deck. Those are different deliverables — refuse to substitute them silently.

## Framework discipline

These are non-negotiable.

### Backgrounder

- Four parts, in this order: **category perspective**, **current situation**, **consumer insights**,
  **problem statement**. Sits right after the Executive Summary — a third-party agency or non-marketing
  stakeholder needs to be oriented in the evidence before any framework mechanics start.
- Category perspective and current situation are read from structured data (market-share/HH files), not
  from the model's category memory, whenever that data was supplied — use the real figures verbatim, the
  same discipline as the pricing/distribution snapshot. Where no such data was supplied, say so rather
  than estimating.
- Consumer insights are synthesized from qualitative research where it was supplied — specific, citable
  findings, not a restatement of the whole deck. Where none was supplied, say so.
- The problem statement is the one paragraph the rest of the brief exists to answer: it names the actual
  business/marketing problem (not a symptom, not a metric target) in plain language. It must set up — not
  duplicate — the CB/CA → DB/DA section that follows several sections later: CB/CA works out what has to
  shift; the problem statement is why a shift is needed at all.

See `references/backgrounder-guidance.md` for how to write each part and a worked example.

### NeedScope wheel

- Six territories arranged clockwise from twelve o'clock: Power (Red), Freedom (Orange), Vitality (Yellow), Belonging (Green), Security (Blue), Discernment (Purple). This rotation is fixed across the plugin so the chart reads the same way every time.
- Each focal brand is positioned by reading the brand's communications cues (taglines, films, packaging) and assigning emotional territory plus pull direction. See `references/needscope-framework.md` for the assignment rules.
- The focal brand always gets a slightly larger pin and the word "(anchor)" below the label.
- A dashed strategic-bridge arrow connects the focal brand to its proposed adjacent territory — this visualises the brand's strategic move and must match the SMP narrative.

### CB/CA → DB/DA

- Two cards side-by-side. Left card grey-bordered, labelled "CURRENT". Right card green-bordered with a tinted background, labelled "DESIRED".
- Each card contains two sub-cards stacked: Behaviour above, Attitude below.
- Behaviour bullets describe observable purchase, usage, and occasion patterns. Attitude includes one verbatim consumer-voice quote and two declarative lines about how the brand is held.
- A green arrow runs between the cards labelled "THE SHIFT" with the one-line shift named below ("passive trust → active pride", or equivalent).
- A caption underneath the diagram restates the shift in one sentence — the message communication must layer the desired attitude on top of the current one, never replace it.

### Single Minded Proposition

- One sentence ending in a full stop, max 14 words. Tension-resolving, brand-true, competitor-defeating, and future-facing.
- Always followed by a "Why only [brand] can say it" defence that names each direct competitor and the word in the SMP they fail to earn.
- Always followed by a short "what this unlocks" list: brand line, mass line, activation idea, product idea — each tagged "illustrative — not final copy" so the brand team owns the final wording.

See `references/smp-guidance.md` for the SMP construction rules.

## Style discipline

- Sentence case everywhere — headings, table headers, figure captions. Never Title Case.
- Use the rupee sign `₹` (U+20B9) directly for Indian prices; the build script renders fonts that support it.
- Footer reads `{Brand} Brand Brief · Page X of Y`.
- Headings use a green H2 colour `#3F814C` to match the NeedScope green and the SMP callout border — visual continuity is intentional.
- Body 11pt Arial. Tables 10pt. Headings 12–14pt, weight 500.
- Never use emoji. Never use mid-sentence bold.

## When inputs are sparse

If the user has provided only a brand name and no files:

1. State up front that the brief will be built from web research and category memory.
2. Run targeted web research on the brand, top three competitors, recent campaigns, pricing, and any publicly disclosed market-share figures.
3. Build every section, but in the Caveats section explicitly list which numbers and which NeedScope positions are estimates that should be replaced with real data before externalising.

The brief still ships; the user knows what to validate. Never refuse to produce the brief.

## Implementation handoff

See `references/` for the operational details:

- `references/backgrounder-guidance.md` — how to write the category perspective, current situation, consumer insights, and problem statement, and how the problem statement sets up CB/CA.
- `references/needscope-framework.md` — how to assign brands to NeedScope territories from their communications, and how to construct the wheel.
- `references/cb-ca-db-da-framework.md` — how to populate the four quadrants and write the shift line.
- `references/smp-guidance.md` — how to triangulate the SMP and pass the four tests.
- `references/input-parsing.md` — how to read each uploaded file type and what data to extract.
- `references/docx-assembly.md` — the JSON contract for the build script and how to invoke it.

See `assets/` for templates and the runnable build script:

- `assets/needscope_template.svg` — the wheel template; the skill clones it and overwrites brand pin positions.
- `assets/cbca_dbda_template.svg` — the shift diagram template.
- `assets/build_brief_docx.js` — the parameterised Node script that ingests `brief.json` and writes the `.docx`.

## Final check before delivery

Before linking the user to the output file, confirm:

- The `.docx` exists and is non-trivial in size (> 100 KB once figures embed).
- Both figures render (open at least page 2 and page 3 of the rendered PDF as images and look at them).
- The backgrounder's problem statement is one paragraph and sets up the CB/CA shift, not a copy of it.
- The SMP is one sentence.
- Every competitor named in the brief has at least one row in the messaging matrix.
- The Caveats section lists every assumption made due to missing input.

Only then surface the file.
