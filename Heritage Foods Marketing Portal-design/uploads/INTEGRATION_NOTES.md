# Brief Builder — front-end ↔ backend contract

Use this so the design work in Claude Design stays wire-compatible with the backend.
When you send the revised front end back, I re-connect it to these endpoints — no backend rewrite needed.

## The screen
`brief-builder-screen.html` is the Builder screen as a **self-contained file** (schema inlined,
no backend). It renders and is clickable on its own, so Claude Design can import and restyle it.
`Builder_react_source.tsx` is the same screen as the live React component (for reference).

## Keep these stable while restyling (this is what lets me re-wire it)
1. **Format ids** — `brand, comms, imc, media, digital, pack, product, pr`.
2. **Field keys** — each field's key (e.g. `background`, `proposition`, `mandatories`). Restyle the
   labels/layout freely, but keep the key on each input (in the HTML it's the `id="fx_<key>"`;
   in React it's the map key). Keys per format are inlined in the file and served at `GET /brief-schema`.
3. **The section rule** — Communications & IMC use the *builder* section set; Media/Digital/Packaging/
   Product/PR use the *front-end* section set; Brand routes to the skill. (All encoded in `/brief-schema`.)

## Endpoints the builder talks to (already live in the backend)
- `GET /brief-schema` → formats + sections + fields + `source` (builder|frontend|skill).
- `GET /catalog` → `campaign_objectives` for the dropdown.
- `POST /complete` `{messages:[{role,content}]}` → AI co-writer draft (returns `{completion}`).
- `POST /briefs` (BriefIn) → creates the brief (Save).
- `POST /briefs/{id}/submit` → sends it into the L1–L3 approval queue.
- Brand format only: `POST /brand-brief` (multipart) → returns the Word brief.

## Field key → Brief column mapping (used on Save)
background→background_context, businessObjective→business_objective, commObjective→communication_objective,
audience→target_consumer, insight→consumer_insight, competition→competitive_context,
proposition→single_minded_proposition, rtbs→reasons_to_believe, tone→tone_personality,
mandatories→mandatories_brand_codes, deliverables→deliverables_channels, budget→budget,
timeline→timeline_milestones, kpis→success_metrics_kpis.
Any other key (bigIdea, channelRoles, mediaHabits, funnel, etc.) is preserved into background_context
as labelled lines — no data lost.

## Hand-back
Send me the exported front end (HTML or React). I will: mount it as the primary app, wire the
buttons/inputs to the endpoints above using the format ids + field keys, keep the approval engine,
generation, avatar/cinematic video, and the brand-brief skill intact, and hand you a runnable build.
