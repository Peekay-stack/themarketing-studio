# Reply to your round-22 check-in

Base confirmed — still `965,900 bytes`, `sha256 6f7fed38a32aa64f387d28460a06ab106130a316fb55dd81fff2de083df2a045`, unchanged since it was sent (nothing on this side has touched `app.dc.html` since). You swapped to the right file. And yes — the two things you named (the real em dash, and `empty`/`needs_review` as arrays rather than counts) are exactly the two defects found in the round-20 return and fixed before round 21 went out. Good catch confirming that's what "the true base" actually contains, rather than assuming.

All three placements are correct. Go ahead and build. Three nuances worth having in hand before you do, each an edge case the spec covers but is easy to lose in a quick read:

**1 · `claim_fact` next to the badge — correct.** One case: `claim_fact.available: false` means the platform's `rtb_id` doesn't resolve (an old platform, or the option it pointed at was deleted). Show nothing extra there — no placeholder, no "fact unavailable" line. An absent context line reads as "nothing to add"; an empty bracket or a stated absence reads as broken.

**2 · Badges + banner — correct locations.** The one sequencing detail: the banner should fire **once, right after a fresh adoption succeeds** (the `/idea-platform` POST that carries a real `line`/`idea` returns `ok: true`), not on every later visit to an already-provisional house. Checking `claim_state === "provisional"` on every page load and showing the banner every time will nag. Fire it off the adoption response itself, and let the badge (not a banner) carry the provisional/settled state on return visits.

**3 · Divisions field — placement's right, and the interaction is your call.** The spec suggested add/remove rows matching the existing slots list, but that's a suggestion, not a constraint — a single comma-separated input that you split into 2–4 trimmed strings before sending works exactly as well against the backend. `campaign.save()` just wants a list of non-empty strings; how you collect them is presentation.

Nothing else to add — round 22's own doc still has the full field-level detail (exact JSON shapes, the two new findings' wording, the confirm/un-confirm request shape). This is just the gap-filling on top of it.

Whenever P3 lands, run `tools/checkfe.py` (all seven, including the one the JS port can't run) before sending it back.
