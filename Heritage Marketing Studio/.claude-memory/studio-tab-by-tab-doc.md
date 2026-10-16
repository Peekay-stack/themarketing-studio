---
name: studio-tab-by-tab-doc
description: "The Studio, Tab by Tab" build-review artifact — where it lives, what it is, and that it now carries engineering (frontend/backend/linkage) detail per tab, verified 4 Sep 2026
metadata:
  type: reference
---

Artifact: https://claude.ai/code/artifact/c26e0b2c-9d04-4162-8c4b-18bb606c306b — "The Studio, Tab by
Tab." A separate, older document from [[studio-work-inventory]] and the Portal Wiring Audit
(https://claude.ai/code/artifact/777fa9b9-004c-4ef0-8b1a-e6445336c586) — don't conflate the three.
This one is a business/product-level build review: every screen mapped as Inputs/Process/Outputs,
findings ranked, a productisation section (access model, compliance dates, integration order).

**Revision 3 (4 Sep 2026)** added an Engineering panel to every tab — the real frontend handler
(file:line), the real backend route + module (file:line), and the actual linkage/drift between them —
built from 7 parallel Explore agents re-reading the live code screen by screen, not from re-describing
revision 2's claims. Re-verifying surfaced that several revision-2 findings are now stale:

- **F3 (no channel carries a weight) — stale.** Plan channels now carry a real, enforced `share` field.
- **F4 (Media's Competitive/Social have no doors) — stale.** Both now have full frontend UI and are reachable.
- **F5 (PR never opened a real sheet) — stale for `pr/` and `pr_map/`** (7 real sheets, 1 media map on
  disk); `pr_framework/` is still genuinely empty, so crisis class-setting remains untried.
- **F1 (fabricated Home/Campaigns data) — fixed on Home**, still present as dead code on Campaigns but
  correctly gated so it no longer renders.

**New findings from this pass, not in the original document:**
- PR's crisis sign-off enforces QA-before-Legal/CEO but **not Legal-before-CEO** — both unlock at once.
  "Signed by" is unverified free-text (no session behind it — same unwired-auth gap F10 already named).
- Social Studio is the one producer that does NOT use `producers.stands_on()` (POSM and Activation both
  do) — it has its own separate, hand-maintained client-side description of what grounded a post, which
  isn't guaranteed to match what the server actually sent.
- Plan's "channel-wise messaging" reads from the **house's** medium layer (`plan.house_block()`), not
  the idea platform's per-medium expressions as the document's own revision-2 argument claimed.
- Sales enabler's channel/element list is defined independently on both sides (`SE_TABS` in
  app.dc.html vs. `sales.CHANNELS` in sales.py) and has already drifted — element counts aren't
  uniformly five per channel.

If asked to update this document again, re-verify rather than trust its own prior revision — that's
exactly the gap this revision closed.

**Revision 4 (4 Sep 2026)** added a hand-authored inline-SVG flow diagram above the Engineering panel
on all 12 tabs, per the user's explicit request for "a combination of visual flow diagram and written
text below it." Each diagram depicts the specific mechanism already verified in that tab's Engineering
prose (not a generic box-and-arrow restatement) — e.g. PR's diagram shows Legal/CEO sign-off unlocking
*simultaneously* rather than in the claimed order; Campaigns' shows the dead `ANALYSIS` literal now
correctly gated off plus the unwired `/actuals` ledger; Memory's shows scored promotion existing only
for prompt templates, not corrections, and History having no backend at all. Built with the
`artifact-diagramming` skill's conventions (currentColor base, one accent hue for the finding that
matters, `<figure>`+`<figcaption>`, per-SVG-unique marker ids).

**Now stale (fixed in [[studio-work-inventory]] rounds 90-91, doc itself not re-touched):** PR's
Legal-before-CEO gate is enforced (round 90); Memory's History is a real backend ledger (`made.py`),
not "no backend at all" (round 91). Re-verify before quoting either finding.
