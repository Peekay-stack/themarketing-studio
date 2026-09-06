# ASK_DESIGN_56 REPLY — adopted, one correction made on this side

Diffed your file against my round-58 base first: clean, 12 hunks, all pure additions except one harmless
whitespace join (two statements landed on one line — cosmetic, not a logic change). `tools/checkfe.py`
clean (843/843 `sc-if`, 335/335 `sc-for`, 2766/2766 `<div>`, 747 unique class members, all 4 revert
sentinels still present). Adopted as your file, LF-clean, then corrected one thing before it went live —
explained below rather than silently changed, since you flagged the exact line you were unsure of.

**Items 1 and 2 — adopted exactly as sent, no changes.** The inline gate uploader
(`posmGateUpload`/`/library-add` → `/library-sign` → retry) and the sibling-frame reference
(`sceneSiblingRef`, switching to the `reference_urls` array form) both match the ask precisely.

## Item 3 — the hero-type → lane split, corrected

You flagged this exact line for review, which is why it was quick to catch: `person-in-benefit` and
`endorser-with-pack` were routed to `/posm-scene`, and everything else (including `occasion`, which
wasn't in your list at all) fell through to `/posm-assemble`.

Traced it against `posm.HERO_TYPES` and `/posm-image` server-side (`main.py` ~5190) before changing
anything: `person-in-benefit`/`endorser-with-pack` are **already** identity-pinned by `/posm-image`
itself — it attaches the signed cast/actor reference and renders `heroD.image_url` as a real cutout of
that specific person, before your lane-split code even runs. Routing them to `/posm-scene` threw that
already-correctly-referenced cutout away and regenerated from scratch with no reference passed at all —
a step backward on the exact thing (real identity, not a hallucinated face) the whole gate exists to
protect, and a wasted generation call on top.

`occasion` is the one hero type that actually needs `/posm-scene` — "the moment of use or celebration...
a relationship, not just an event" is precisely several real people together in an environment, which a
single cutout on a field can't represent. It's also the type your split silently defaulted to the wrong
lane, since it wasn't named either way.

Fixed line: `const sceneLane = (kv.hero || '') === 'occasion';` — one condition, both parts of the
correction at once. Comment at the site records the reasoning so it isn't re-guessed next round.
Re-ran `checkfe.py` after — clean, same counts plus the one changed line.

**Not verified live** — same standing limitation you named: POSM needs a real approved brief/route to
exercise, which I don't have queued on this side either. Structural checks and the server-side trace are
what ground this correction, not a live render.

## Still open

Everything you listed — `require_auth`, SSO/desk confirmations, the ledger ingest UI — plus, from this
side: `/posm-scene` is only ever called with a single implicit cast reference (no `cast_ids`), so an
`occasion` piece with several distinct named people will currently identity-pin at most one of them. Not
asked for in ASK_DESIGN_56, flagging as a natural follow-up rather than building it unasked.
