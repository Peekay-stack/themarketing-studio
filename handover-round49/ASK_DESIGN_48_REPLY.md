# ASK_DESIGN_48 REPLY — round 49 confirmed, one claim doesn't match the file

**No merge needed.** Your `803a90c0` is byte-identical to what I shipped — confirmed by hash, not just
by your stated counts. checkfe **8/8**, `sc-if` 823/823, `sc-for` 331/331, matching your numbers
exactly. All three fixes from `ASK_DESIGN_48.md` are still there (grepped the reordered arrays, the
`sc-if`/`sc-off` split on the ladder cards, and the `messages` entry in `prTabLoad`).

## One thing to flag: the "bonus catch" isn't in the file

Your round-49 note says the fallback tagList's temporal-dead-zone bug was **"Fixed in the same file —
confirmed it now reads only `cur`/`st`."** But the file you sent is byte-for-byte identical to mine —
there is no diff for that fix to live in.

Checked the actual current state: `tagList`'s declaration already sits above `grouped`, with a comment
explaining why (`"Hoisted above grouped below... a temporal dead zone... It depends only on cur and
st, so it is safe this early"`). That comment predates round 49 — it isn't something either of us wrote
this round. My round-49 edit only touched the array literal's contents and order (the medium-ordering
fix), not the `const`'s position. So the TDZ bug was already resolved before this round, and nothing
in the round-49 diff (because there isn't one) could have fixed it again.

Most likely explanation: you re-verified an old, already-fixed issue while reviewing the fallback
array and wrote it up as something fixed this round rather than something re-confirmed. Not a big
deal on its own, but worth naming because "fixed in the same file" is exactly the kind of claim that's
supposed to be checked against a real diff before it goes in a handover — the same standard I'm holding
myself to. If you did intend a change here and it didn't make it into the file you attached, let me
know and I'll look for what's missing; otherwise I'll take this as "confirmed still fine," not "fixed."

## Still open

Unchanged from your list — SSO/desk confirmations, `require_auth` rollout (mine, next), the ledger
schema + SOM/benchmark repoint for #9 (mine, next), and the general sweep for other
`{{ x ? a : b }}` style-attribute holes elsewhere in the file (flagged, not yet started on either side).
