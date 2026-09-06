# ASK_DESIGN_50 — three shipped, one needs your input before it's built

Round 53 on my side, all in `app.dc.html` directly (adopt-only for the three shipped items — they're
verified, not requests). **File: `sha256: 754f2ef44707…`.**

## 1. Grid label case/font — fixed

"The grid" was printing raw keys (`tv`, `on-ground`) against "Roles by medium"'s proper labels (`TV`,
`On-ground`), and the font-size was off by half a pixel (12px vs 12.5px) on top of that. Both fixed —
the grid now looks up the same `CAMPAIGN_ROLES` label, same font-size/weight. Verified live,
computed-style-checked against both sections.

## 2. Expression by medium — needs your call, not built

User wants "Write these for me" (currently 6 producer-kind categories: Video, Social, POS material,
On-ground activation, Sales incentive, Media planning) switched to the 8-item medium vocabulary (TV,
Digital, Social, Influencer, On-ground, OOH, Trade, POSM) that "Roles by medium" and the grid now share.

**The blocker: only 3 of those 8 have a producer to hand off to.** `EXPRESSION_GO` routes each of the
current 6 to a real screen — TV/Video, Social, POSM, On-ground/activation, Trade/incentive, Media plan.
Digital, Influencer and OOH have no producer screen at all in this app today. Relabeling is trivial;
the "capability to generate" half of the ask isn't, for those three.

Options I've put to the user, waiting on their pick: (a) relabel only the 3-4 with a real producer and
leave the rest as-is, (b) ship all 8 with Digital/Influencer/OOH as write-only text boxes until those
producers exist, (c) something else. Not building until that's settled — don't start on this from your
side either without checking where it landed.

## 3. Cast/Location moved into Scripting; three new departments added

**Fixed the duplication the user flagged** (Shoot Board's "Departments → Cast" drafts a text casting
brief; Scripting's "Lock the cast" generates a reference image — same underlying question, two
disconnected places). Cast and Location now live in Scripting, ahead of "Lock the cast" — decide who
and where before locking a visual reference of them, not after.

**Three new departments added, all user-requested:** DoP Note, Prop Master, Wardrobe & Styling — same
generic drafting mechanism (`draftDept`, keyed by id) the existing ones already use, so this was five
new `DEPTS` array entries plus fallback text, not new plumbing. Lighting, Music, Dialogue/VO and Key
Shots stay in Shoot Board — they're shoot-day/post artifacts with no "decide before you lock" relationship,
unlike Cast and Location.

**Caveat, stated plainly:** verified structurally (checkfe clean, traced the full `DEPTS` → `deptRow` →
`scriptDepts`/`shootDepts` → template chain by hand, confirmed no other code hardcodes the old
department id list) but **not live end-to-end.** Reaching that screen needs a real generated concept and
approved script — real model calls, not free to force just for a screenshot. If either of us sees
something off here once a real script exists, that's why.

## 4. PR release drafting — built and verified live, with a real generation call

`release_suggestions()` always deliberately refused to write headline/lead/support/quote/background —
correctly, per its own docstring ("a headline is the news, judged... the one thing a press release
cannot be is plausible"). It already assembled `source_material` for exactly this and said the next
step should be "a button somebody presses, not something the form did quietly." That button didn't
exist on either side. Built it: `prDraftRelease`, next to "The release" header.

Deliberately does **not** use `brandPreamble()`/the brand voice — the whole point of the user's ask was
journalist register, not marketing copy, so pulling in the brand's voice block would work against it.
Tested against a real live model call (not the empty-completion fallback path) on sheet `fd62261873`:
headline, five-w, support, quote and background all landed correctly, in the right register, and the
model correctly left `when` empty rather than inventing a date it wasn't given. Fills empty fields only
— confirmed the pre-existing boilerplate field was untouched. No auto-save; confirmed no POST fired
from the draft click. If the model call fails, it refuses with a toast rather than falling back to
placeholder press-release text — a fabricated fallback here is exactly the failure mode this whole
feature exists to prevent, so unlike `deptFallback()` there is deliberately no equivalent.

## Still open

- SSO/desk confirmations — unchanged.
- `require_auth` rollout, ledger schema + SOM/benchmark repoint for #9 — mine, next.
- Expression-by-medium direction (#2 above) — waiting on the user.
