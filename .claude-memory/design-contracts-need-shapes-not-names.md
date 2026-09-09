---
name: design-contracts-need-shapes-not-names
description: "Payload contracts in ASK_DESIGN_*.md must state each field's TYPE; naming fields alone produced two live rendering bugs Design could not have avoided."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 8ceac62b-7222-47d3-9a92-41e0ce0e0317
  modified: 2026-08-28T12:40:17.108Z
---

When documenting a backend payload for Claude Design, write the shape of every field, not just its
name. Listing `missing[]`, `asks`, `avoid` as bare names in ASK_DESIGN_33 caused two live defects:
`missing` holds full **sentences** (Design read `x.label || x.what || x.id`, rendering `"Not
entered: , "`), and `asks`/`avoid` are **one paragraph each, not lists** (`prSeq` returns `[]` for a
string, so both halves of every prompt guide were invisible on all six producers).

**Why:** Design's code was faithful to the contract in both cases. Plural names plus this app's
list-heavy conventions make "array of objects with a text field" the correct inference — so a
name-only contract actively misleads. Neither bug produced a console error or failed checkfe; both
needed the page open with real data.

**Round 44 added two more of exactly this, cost four rounds later.** I named `palette`, `fonts` and
`dos` to Design without their types. They then wrote `Array.isArray(b.colours)` — but `colours` is a
**dict** on the server (`b.setdefault("colours", {})`), so the only brand with colours on file rendered
as having no palette. And `bfBrand: d.brand || …` — `/brand-fields` returns `brand` as the whole
**record**, not a name string, and an object is truthy, so the fallback chain was dead and the landing
headline read "What the studio is told about [object Object]". Same root cause both times: a plural or
singular name invites the obvious shape, and the obvious shape was wrong.

**Round 47: stating the shape isn't enough if the stated shape is wrong.** I wrote `ASK_DESIGN_47.md`'s
login contract as `POST /login` → `200 {user:{id,name,role,tenant}}`. I had already tested `/login`
with raw curl/urllib before writing that — my own terminal output showed `{'id':..., 'name':...,
'role':..., 'tenant':...}`, unwrapped — and I documented the wrapped shape anyway, from what I'd
intended to build rather than what I'd just watched come back. Design built `doLogin` correctly
against the doc (`r.data.user`); the login worked at the network level (`200`) and still failed on
screen with "Could not reach the server," because the one field the frontend needed wasn't there. This
is the same failure class as the other instances above, but the earlier ones were "described a field
without its shape, Design inferred wrong"; this one is "described a shape, tested a different one,
never noticed the two didn't match." A curl pass proves a route responds; it does not prove the
response matches the sentence written about it three paragraphs later.

**How to apply:** In every handover payload block, annotate types — `missing[] (strings, full
sentences)`, `asks (one paragraph, not a list)`, `colours (dict: role -> name, no hex)`,
`brand (the whole record; its name is brand.name)`. Before sending, call each function, PRINT the
real payload, and diff that printed output against the sentence being written about it — not "I tested
this earlier," re-paste the actual line. Also state whether the route returns `available: false` or
converts it to HTTP 4xx `{detail}` — the two trade routes convert, which made a whole availability
branch unreachable. Relates to [[browser-verification-available]] (a curl-clean route is not a
verified contract once the other side has built a real screen against it — that needs a browser pass
against their actual code, not another curl) and [[design-handovers-merge-never-replace]].
