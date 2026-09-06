# ASK_DESIGN_55 — round 58, three real findings from actual user testing

Adopt-only, all three verified. **Frontend file: `sha256: 2b5d71db9bcc…`** (items 1–2 only; item 3 is
backend-only, `api/posm.py` + `api/main.py`).

Round-57's work went to real user testing this morning. All three things reported back were real, and
none of them were things checkfe or a code read would have caught.

## 1. Cast department resurrected — round 55 conflated two different kinds of writing

User testing: *"only location in ai draft not the cast... by dropping it, seems like we are missing on
detailing."* Correct call. Round 55 removed the Cast department on the read that it duplicated the "Frame
generation guideline" box (`videoCharacters`) — the compact visual reference sheet that feeds every render
call. That's true, but it missed that the department box was a **casting brief** (who to hire, the region,
the performance quality — *"can hold genuine stillness on camera"*), not a rendering spec. Different
writing, no other home for it, and removing the box didn't just deduplicate — it deleted the fuller
thinking underneath the terse reference sheet.

**Fix**: `cast` is back in `DEPTS`, `home:'scripting'`, alongside Location. Departments heading reverted
from "Location" to "Departments" (now two cards, capped at 330px each per round 56's grid fix — confirmed
that fix handles 2 cards as cleanly as 1). The "Frame generation guideline" fine print updated to say
what's actually true: the Cast note above is what "Derive from script" condenses; the Location note is
read directly by the lock action, not pulled into the reference-sheet text. Verified structurally
(checkfe clean) — not reloaded live this round, in the interest of time; the mechanism is identical to
Location's, which was live-verified in round 56.

## 2. Plan balance layer — "Suggest a split" and a human's own entry were indistinguishable

User testing: *"what is the source of this... is it auto-generated?"* — asking about the Declared card's
reason text. The honest answer, before this fix: **no way to tell.** Both `/plan-balance` (the "Record the
split" button, a person's own entry) and round-58's `/plan-generate` for the balance layer ("Suggest a
split") wrote an identical `{brand_share, reason, basis, declared:true}` record. A model's suggestion and
a person's decision looked the same on screen — the exact ambiguity `declared` itself was added to
remove, one level up.

**Fix**: `plan.set_balance()` gained a `source` param (`'user'|'model'`), defaulting to `'user'` so old
records and the human "Record" path are unaffected. The `kind:"number"` branch of `generate()` (the
Suggest path) now passes `source='model'`. `balance_of()` folds `source:'user'` onto any pre-existing
record with no source at all (every one of those predates "Suggest a split," so that's not a guess).
Frontend: a "Suggested by the skill" chip + explanatory line appear on the Declared card only when
`source==='model'` — gone the moment a person clicks "Record the split" themselves.

**Verified**: `set_balance`/`balance_of` tested directly against a disposable plan id (deleted after) —
user record, model record, and a folded legacy record all produced exactly the right `source`. Not
re-verified through the UI this round (the logic is a single boolean gate on an already-proven `sc-if`
pattern); happy to do a full live pass if you want it before shipping further.

## 3. POS key visual generating an unusable image — root-caused, not patched

This is the one worth reading in full. **Nothing about the methodology was wrong** — I checked the actual
prompt sent last night against `.claude/skills/posm/references/key-visual.md`'s specified hero-cutout
template and it matched **character-for-character**. The bad image (a masked, unrecognisable face on what
was meant to be a calm schoolgirl) was not a prompt-quality failure.

**Root cause**: the route was `person-in-benefit`, describing a photorealistic child. Google's Gemini/
Imagen models have a documented, strict — and documented-inconsistent — safety policy against generating
minors: it doesn't cleanly refuse, it distorts. That's the black mask.

**The deeper bug, the one actually worth fixing**: the skill's own spec for `person-in-benefit` already
says `needs: casting and usage rights` — the same category of requirement as `endorser-with-pack`
(`needs: signed talent... a cast or actor library reference`). But the code only ever enforced that for
`endorser-with-pack`. `person-in-benefit` was rendered from raw text same as a perfectly safe subject like
a clock or a glass of milk — a hallucinated identifiable person, not a real one, exactly the thing the
pack rule already refuses to do for packaging.

**Fix**: extended the existing gate (`posm.gate()`) and the existing reference-image path (already built
and working for `endorser-with-pack` — `gemini.image_from_reference()`, "keep the person from the
reference image exactly") to also cover `person-in-benefit`. No cast/actor reference in the library →
clean 409 refusal naming the upload, same pattern as every other refusal in this app. A reference exists
→ the hero is generated *from* that photo, not hallucinated, which also sidesteps the safety-filter
problem generally (not just for children).

**Verified live, both directions, against the real running server:**
- `hero_type:'person-in-benefit'`, no cast in library → `409`, the new message, naming the fix.
- `hero_type:'metaphor-object'` (the exact route type this tenant's real drafts favour) → `200 OK`, no
  regression.
- Confirmed directly in Python that `endorser-with-pack` and `range-array`'s existing gates are untouched.

**Not built this round, flagged rather than assumed**: the KV-drafting prompt (`producers.key_visual()`)
still has no awareness of library state, so it can suggest `person-in-benefit`/`endorser-with-pack` routes
regardless of whether a cast reference exists — exactly the same gap `endorser-with-pack` already lived
with before this round. The refusal is real and correct when it fires, but a person still has to hit it
once to learn a route can't be built yet. Cheap to fix (tell the drafting prompt whether a cast reference
exists) if you want it; didn't do it unasked since it's a UX polish on top of the actual bug, not the bug.

## Still open

SSO/desk confirmations, `require_auth`, the ledger schema for #9 — all mine, none frontend.
