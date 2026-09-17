# Linkage Construction

A linkage is a chain of two or more synthesized claims that, read together, point to something neither
claim says on its own. The user's own worked example: *market share falling* + *awareness falling* +
*distribution holding up* + *competition rising on all measures* → the pattern is not "several bad
metrics," it is specifically that a demand-side problem (awareness) is the one to fix, because supply
(distribution) is fine and the pressure is external (competition), not internal. That reading — what the
combination rules in and rules out — is the linkage. Two isolated declining numbers are not a linkage by
themselves; the reasoning about what they rule in and out together is what makes it one.

## What makes a real chain

A candidate chain is worth building when the claims in it:

- **Share a subject.** The same brand, the same metric family, the same market/geography, or the same
  time window — something concrete ties them together, not just "both came from research files."
- **Move in a way that adds information together that neither claim gives alone.** One rising while
  another falls; one holding steady while others move (which is itself informative — it rules something
  out); a leading indicator and a lagging one in the same story.
- **Are independently sourced**, ideally from different files. A chain built entirely from claims that
  all trace back to one document is really just that document's finding restated in multiple pieces —
  say so if that's what you have, don't present it as cross-source triangulation.

## What is NOT a real chain

- **Coincidental co-occurrence.** Two findings from the same quarter's tracker are not linked just
  because they're both in that tracker — the tracker itself is one source, one voice.
- **Same finding, different words.** If "awareness is falling" and "top-of-mind recall dropped" trace to
  the same underlying number, that is one claim, not two links in a chain.
- **A chain that requires an uncited assumption to close.** If completing the story requires assuming
  something no source actually said ("this is probably because of the new competitor's ad spend" — with
  no source naming that), the chain is not finished. Either find the source that closes it or leave the
  gap named rather than filled.

## Naming the implication honestly

Once a real chain is built, name what it points to — the user's example does end in "need to dial up
awareness," and that is the right kind of statement to make. The discipline is in HOW it's stated:

- State it as what the evidence points to, in the evidence's own terms: "distribution holding while
  share and awareness both fall, with competition rising, points to a demand-side gap rather than a
  supply-side one." That is a reading of the pattern.
- Do not turn it into a plan: "…so the brand should launch a demand-generation campaign" is a strategic
  recommendation, which belongs in the brand brief, not this deck. The line to hold: this deck says what
  is happening and what kind of problem it looks like; it does not say what to do about it.
- Rank confidence honestly. A chain built from three independently-sourced, well-corroborated claims is
  a different confidence level from one resting on a single low-confidence claim — carry the claims'
  own confidence ratings (from `research_parse.synthesize_research()`) into the chain rather than
  flattening them into one uniform "finding."

## When no chain holds up

Try to build 2–4 candidate chains from the synthesized claims before concluding there isn't one. If,
after that honest attempt, nothing links:

- Say so directly on the headline slide — "no single cross-source pattern in this set" is a complete,
  correct answer, not a placeholder for more work.
- Give each source's most decision-relevant standalone finding its own line instead. The deck is still
  useful — it just reports independence instead of manufacturing connection.
- If two or three PARTIAL patterns exist but don't reconcile into one story (e.g., the household data
  and the Nielsen data tell a consistent supply-side story, but the qualitative research points somewhere
  unrelated), present them as separate, named reads rather than forcing them into one narrative arc.

## Worked example (illustrative)

Claims available (from a `synthesize_research()` output):
1. "Heritage's AP milk penetration and distribution both lead the category" — confidence: high,
   sources: household panel, Nielsen share/distribution.
2. "Heritage's first-choice/consideration rate trails its own awareness by a wide margin across all four
   quarterly trackers" — confidence: high, sources: 4 brand-health trackers.
3. "Heritage's equity is high on Trust/Warmth but low on Distinctiveness/Modern relevance" — confidence:
   high, sources: qualitative research, brand-health trackers.

Chain: (1) rules out a supply/access problem — the brand is already winning on reach. (2) says the gap
is specifically between awareness and choice, not between awareness and reach. (3) explains WHY: the
brand is trusted but not distinctive, so it is considered but not chosen first.

Reading: *"Heritage's growth constraint is not distribution or awareness — both are already strong. The
gap is between being known and being chosen, and the equity data says why: strong trust and warmth are
not converting to distinctiveness at the moment of choice."* Confidence: high (three independently
sourced, mutually reinforcing claims). No competing chain needed here — but note explicitly if the
underlying trackers repeat near-identical language quarter to quarter, since that affects whether this is
independent corroboration or the same thesis restated (see `synthesize_research()`'s own `pattern_note`
for this exact kind of caveat).
