---
name: design-asks-need-exact-files-and-instructions
description: "When asking Claude Design to do something, name the exact file(s) and give precise, itemized instructions — vague asks like 'worth a sweep' or 'worth a look' confuse them."
metadata:
  node_type: memory
  type: feedback
  originSessionId: 5e956381-ce19-4f83-93e1-71a73ced8b2b
  modified: 2026-08-31T04:41:32.287Z
---

The user's explicit correction: "if you want something done by them - then give clear instructions and
files to be used. they get confused."

**Why:** The pattern that triggered this was round 49's handover, where I'd flagged "a general sweep of
remaining `{{ x ? a : b }}` style-attribute holes" as something worth doing without ever actually
finding them myself — an open-ended, unscoped ask. Design's round 50 handover corrected an unrelated
claim ("bonus catch" fix that wasn't actually a diff), and the pattern of vague, unscoped asks sitting
on the "still open" list for round after round (SSO/desk confirmations, the sweep) is what the user is
naming here.

**How to apply:**
- Before asking Design to find or fix something, find it myself first if it's mechanically searchable
  (grep, a route test, a live click-through). Hand them the exact count, the exact file, the exact
  lines — or better, fix it myself and hand them a diff to review, the way the three prior
  attribute-hole fixes and this sweep were done.
- An ASK_DESIGN doc's action items should read like a checklist with file names and line-shaped
  specifics, not "worth a look" or "flagged for later." If I don't have the specifics yet, that means
  the investigation isn't finished — don't ship the ask until it is.
- Genuinely open questions (business decisions like SSO vs. accounts, desk definition) are the
  exception — those really do need to go back as questions. But even then, frame them as a small,
  numbered list with the exact options, not a paragraph (see [[design-contracts-need-shapes-not-names]]
  for the parallel rule about payload shapes).
- If an ask has been sitting on "still open" for more than one or two rounds without action, that's a
  signal the ask itself was too vague to act on — rewrite it concretely rather than repeating it.

Related: [[design-contracts-need-shapes-not-names]], [[design-handovers-merge-never-replace]].
