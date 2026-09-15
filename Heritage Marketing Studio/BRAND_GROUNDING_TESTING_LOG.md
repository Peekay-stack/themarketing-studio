# Brand grounding modes — user testing log

Running log of user-testing feedback on the Grounded/Independent toggle (BRAND_GROUNDING_MODES_PLAN.md)
and what was done about each round. One entry per round of feedback, in order. Updated after every
round — do not renumber or rewrite past entries, only append.

---

## Round 1

**Feedback (verbatim, with screenshots PIC 1–4):**

> PIC 1,2,3 - The toggle button doesnt seem to be working - both in the header chip and the studio
> settings, when grounded is on - shows heritage; when general is on shows heritage as well. I went
> back to the IMC brief after drafting one with Grounded on and it showed the same text written in
> the prompt, brand and category fields (see PIC 4)

Screenshots showed: the header brand chip ("Heritage Foods") unchanged across both toggle states; the
Studio Settings brand-switcher dropdown (Heritage Foods/Kumkum/Loomwell/Parle G/Sthir) also unchanged;
and the IMC Brief screen's "Describe the brief" / Brand / Category fields still carrying the same
"heritage" / "Heritage" / "Dairy" content after switching to General.

**Root causes found:**
1. The header brand *chip* and the Studio Settings brand *switcher* are a different control (which
   brand is active) from the Grounded/General toggle (whether this piece of work uses that brand) —
   not a bug, but confusing to see side by side with no visual distinction.
2. A real, separate bug: the IMC Brief's own "Draft/Redraft with AI" button calls `/brand-brief-draft`
   → `brief_ai.py`, a completely different code path from the guided Brief Builder's drafting flow.
   It had never been wired to the Grounded/General toggle at all, so flipping the toggle changed
   nothing for this screen — the Brand/Category fields kept sending their typed content regardless,
   and `brief_ai.py`'s own prompt told the model to *"(infer from the ask)"* whenever the Brand field
   was empty, which is the exact behavior that had already been flagged earlier in the project as the
   root cause of a brief inventing "India's favorite Biscuit" as a brand name it was never given.

**Fixed:**
- `draftBrief()` now sends `brand_mode` to `/brand-brief-draft`, and forces `brand:''` in General mode
  regardless of what the field shows.
- `brief_ai.py`'s prompt no longer falls back to "(infer from the ask)" for the brand name in General
  mode — it now explicitly tells the model not to invent or infer one. Verified live: a real draft
  call with brand/category blank came back `"[BRAND NAME REQUIRED — none supplied; this is a
  category-level glucose biscuit template]"` instead of confidently inventing a name.
- Switching to General now clears the IMC screen's own Brand/Category fields (confirmed via direct
  DOM check) — the prompt textarea is deliberately left alone, since it's the person's own analysis
  request, not a brand fact.
- Server-side enforcement added too (`/brand-brief-draft` forces `brand:''` when `brand_mode=general`),
  not just trusted from the client.
- Renamed the toggle's off-state label from "General" to "Independent" everywhere (button text only;
  the internal state value stayed `general`), per a mid-turn request in this same round.

---

## Round 2

**Feedback (verbatim, with screenshots PIC 1–3):**

> PIC 1 - these 2 toggle switches don't sync. PIC 2 - add an "independent" profile in this also which
> moves when the toggle switch is changed to independent. PIC 3 - after toggling from grounded to
> independent - the brand and category went black but the prompt continued to be the same as before

PIC 1 showed the header's toggle pill and the IMC screen's own local toggle pill, visible on the same
screen, showing different states. PIC 2 showed the Studio Settings brand-switcher dropdown, asking for
an "Independent" entry to appear in that same list, with the active marker moving to it when selected.
PIC 3 confirmed Round 1's fix (Brand/Category cleared) while noting the prompt field stayed as-is.

**Decision needed and asked directly** (via a clarifying question, since a wrong guess meant rebuilding
across 4 tabs): should the header pill and each tab's own pill be (a) collapsed into one master
toggle, (b) kept separate but only one shown at a time, or (c) kept separate with better labelling —
and should picking a real brand from the dropdown auto-switch back to Grounded?

**User's answers:** One master toggle only. Yes, picking a real brand auto-switches back to Grounded.

**Fixed:**
- Collapsed four separate toggle states (`briefBrandMode`, `houseBrandMode`, `planBrandMode`,
  `producerBrandMode`) into **one** — `producerBrandMode` — read and written everywhere (Brief,
  Strategy/House, Plan, every Producer).
- Removed all 6 per-tab pill UI blocks (Brief Builder, IMC screen, House create-form, House opened
  screen, Plan create-form, Plan opened screen) — the header pill is now the only one anywhere.
- Removed the now-dead `setBriefBrandMode`/`setHouseBrandMode`/`setPlanBrandMode` functions and their
  bag values; folded their side effects (IMC field clearing, syncing an opened house/plan's own stored
  mode) into the one remaining setter.
- Added "Independent work" as a real, selectable row in the header's brand-switcher dropdown, styled
  and behaving exactly like a brand row (shows "Active"/"Switch", moves when the mode changes). Does
  not call `/brand-active` — the real active brand underneath is untouched.
- Fixed `switchBrand`'s edge case: clicking a brand that's already active server-side (the normal case
  when Independent is on with some brand still active underneath) used to no-op entirely; now it
  correctly snaps the mode back to Grounded even though the active brand itself doesn't change.
- The header chip itself now shows "Independent — no brand attached" (distinct styling) instead of
  continuing to show the previously-active brand's name while Independent is selected.
- Verified live end to end: toggled via the dropdown, confirmed the chip/pill/dropdown all agree at
  every step, confirmed only one pill exists anywhere in the UI (checked on the IMC screen
  specifically, the origin of Round 1's report).

**Still open from PIC 3**: the prompt field is left untouched on purpose when switching to
Independent — flagged to the user as a deliberate choice, not confirmed as final. Revisit if they say
otherwise.

---

## Round 3

**Feedback (verbatim, with screenshots PIC 1–2):**

> PIC 1 independent this is fine and this happens inthe studio setting also - great. PIC 2 Grounded -
> should the brand name and category not appear here automatically ? - or it is a company field at
> header chip level and brand name still needs to be entered? How are we treating this (header panel,
> studio settings and brand profile and the toggle switch for 1. one company-Multi brands 2. 1
> company 1 brand . For the previous changes, i hope the backend are also suitably wired?

PIC 1 confirmed Round 2's fix working correctly, including in Studio Settings. PIC 2 showed the IMC
Brief screen in Grounded mode with Brand/Category fields sitting empty despite Heritage Foods being
the active brand — a real gap, not a misunderstanding: nothing had ever auto-filled these fields from
the active profile, in either mode, since the screen was first built.

**Fixed:**
- Opening the IMC screen while Grounded now pre-fills Brand/Category from the active brand's own
  `name`/`category` — only when both fields are still blank, so an in-progress draft or a deliberate
  override is never overwritten by revisiting the screen.
- Switching back to Grounded from Independent does the same fill (symmetric to Round 1/2's "clear on
  the way into Independent").
- Switching to a *different* active brand via the header/Studio Settings now overwrites Brand/Category
  to match the new brand — deliberately overwrites rather than only-fill-when-blank, since choosing a
  different brand is exactly the "no, a different one now" case (matches `switchBrand`'s own existing
  aggressive-reset pattern for every other piece of stale per-brand state).
- Verified live: fresh IMC screen showed "Heritage Foods" / "Dairy — milk, curd, and value-added
  dairy" pre-filled with zero typing; switching the active brand to Parle G updated both fields to
  "Parle G" / "Biscuits — glucose, mass-market (₹5 price point)" immediately.

**Answered, not a code change** — the mental model for header chip / Studio Settings / brand profile /
toggle, and confirmation that the backend for Rounds 1–2 is genuinely wired (not just UI): see the
reply in-conversation. Summary: the header chip + Studio Settings' switcher are ONE concept (which
brand profile is active — works the same whether a tenant holds one brand or several); the toggle is
a second, independent concept (does this piece of work use that active profile, or none at all); the
brand *profile* screen is where the underlying facts live and get edited. Nothing about this changes
between a single-brand and a multi-brand tenant — a single-brand tenant just never has a reason to use
the "Switch" links, since there's only ever one row plus "Independent work."

---

## Round 4

**Feedback (verbatim, across two messages, the second after a session pause):**

> 1. When I changed from grounded to independent, on the IMC brief screen, the brand field went
> blank, but the prompt continued to be the same as before and the button below still said
> "Re-draft with AI" and not "Draft with AI"
> 2. After the brief "independent" was still on but when i moved to the next tab - strategy - it
> toggled back to grounded. i swtiched it back to "independent" - however, when I entered brand
> details - pulled a brief then moved to core message, then again it toggled back to grounded...
> How do you suggest we handle this?

**Root causes found (two separate bugs):**

1. **Bug 1 — stale draft state on toggle.** Switching modes cleared the IMC screen's Brand/Category
   fields (Round 3's fix) but never touched `im.draft`/`im.status`/`im.message`. So a screen that had
   already been drafted kept showing "↻ Redraft with AI" and the old drafted content underneath, even
   though the fields above now read as if nothing had been entered — internally inconsistent, and
   exactly what was reported.
2. **Bug 2 — `pickBrief` silently flipping the toggle.** The user's own described sequence ("pulled a
   brief then moved to core message, then again it toggled back to grounded") is **one** root cause,
   not two: Round 2's toggle-sync had been added to all five branches of `pickBrief` (Brief/House/
   Idea/Plan/else), reading the picked brief's own `brand_mode` and pushing it onto the master toggle.
   Nearly every brief on file predates this feature and defaults to `grounded`, so pulling almost any
   real brief while Independent silently snapped the toggle back — which is also why it looked like it
   "happened again" on the next tab: the house had already been created in grounded mode because the
   toggle had already flipped before creation ran, not a second bug on the Strategy tab itself.

The distinction that resolved it: `enterHouse`/`enterPlan` (opening a house/plan that **already
exists**, with its own recorded `brand_mode`) legitimately sync the toggle to reflect that document's
own decided truth. `pickBrief` (pulling a brief's *text* into a house/plan/producer piece that does
**not exist yet**) has nothing whose truth needs reflecting — there is no document yet, only the
person's own current, deliberate toggle choice, which pulling in reference text should not override.

**Fixed:**
- `setProducerBrandMode` now also clears `im.draft:null, im.status:'idle', im.message:''` on every
  mode change (either direction), not just Brand/Category. No data loss: `/brand-brief-draft` already
  auto-saves every draft to the brief library server-side on generation, and `draftBrief()` never sends
  a `brief_id` in its payload, so clearing `im.draft` client-side can't cause an upsert collision.
- Removed the `producerBrandMode: mode` sync from all 5 branches of `pickBrief` (Brief/House/Idea/
  Plan/else) — picking a brief now only pulls its text in, never touches the toggle. Confirmed via grep
  that `enterHouse`'s/`enterPlan`'s own sync (correct, since those open an already-decided document)
  was left untouched, and that no other `.brandMode`/`snap.brandMode` references were left dangling.
- Validated: `tools/checkfe.py` all 8 checks passed; LF/NULL-byte scan clean (CRLF:0, lone CR:0,
  NULL:0).
- **Live-verified end to end (15 Sep) in the running app**, not just by reading the code:
  - Started a fresh IMC brief in Grounded (fields auto-filled "Heritage Foods" / "Dairy — milk, curd,
    and value-added dairy" per Round 3), used "Or fill it in manually" to populate a draft — button
    correctly read "↻ Redraft with AI". Switched Grounded → Independent: button reverted to "✦ Draft
    brief with AI" and both fields cleared to `""`, confirmed via direct DOM read of the button text
    and the `#imc-b`/`#imc-c` input values.
  - Saved that Grounded-mode draft to the brief library (a real test document, `Heritage Foods — IMC
    brief`, id `6e667d80e2`, deleted again after the test). Opened Strategy, switched to Independent,
    clicked "Start a house" → "Pull from a brief" and picked that grounded Heritage Foods brief.
    Confirmed via DOM read: the header still showed **Independent** active (chip reads "—", not a
    brand name) and the house panel showed "Heritage Foods — IMC brief · pulled from the brief
    library" — the brief's text came in as intended, without touching the toggle.

**Not yet re-confirmed with the user**: removing the `pickBrief` sync entirely (rather than some other
resolution, e.g. asking before overriding) was a judgment call made from the `enterHouse`/`enterPlan`
vs. `pickBrief` distinction above, not a design question put back to the user the way Round 2's
4-vs-1-toggle question was. Flagged here in case they'd rather it worked differently.

---

## Round 5

**Not a bug report** — the user asked directly for an audit: "find out similar error in other tabs as
well — producers - social, video, POSM, on ground and PR" (report first), then, after the report,
"Fix all of them the same way, one pass and also check the other tabs, though not fully developped yet
but... i would like this to be the default on all tabs, sub tabs and layers."

**What the audit found:** Round 4's fix only ever cleared the IMC screen's own `im.draft`/`status`.
Every other generation surface keeps its own "already drafted" state with its own Redraft/Regenerate
label driven purely by whether that state is non-empty — none of it knew the mode underneath had just
changed. Confirmed present in: Social (`posts`), Carousel (`carousel.routes`/`concept`/`slides`),
Video (`videoConcept`, `fullScript`, every department's `shoot[id]` card, `sceneFrames`, the cast
reference frame), POSM (`pm.options`/`scamps`/`images`/every rendered piece), Onground (`og.ideas`),
PR (the release sub-tool's `release`/`rel`/`relStatus`), and two upstream surfaces not in the original
five: the Idea Platform (`idea.line`/`options`) and the guided Brief Builder used by Media/Digital/
Packaging/PD/PR-format (`state.brief`, via the same `hasContent()`-driven label pattern). The other
bug class from Round 4 (a picker silently flipping the toggle) did **not** recur anywhere else — the
only writers of `producerBrandMode` are the toggle's own setter, `switchBrand`, `enterHouse`/
`enterPlan`, and the already-fixed `pickBrief`.

**Fixed:** `setProducerBrandMode` now clears the AI-generated output on every one of those surfaces,
in the same single pass, on every toggle flip. The rule applied everywhere: the **output** goes,
whatever the person actually **typed** (a prompt, a note, an asset pick) stays.

**A real regression caught by live-testing the fix itself, not by the user:** the first pass reset
`posm`/`og`/`idea` to `null` outright, reasoning that their own accessors already fall back to an
empty shape. Live-tested against Onground: typed a prompt into the activation-idea box, generated real
ideas, switched to Independent — the button correctly reverted to "Generate ideas for me", but the
typed prompt was gone too, because it lives in that same `og` object and a blind reset doesn't know
the difference between a person's words and the model's. This is the exact class of bug this round
exists to fix, just self-inflicted. Rebuilt `idea`/`posm`/`og` as field-by-field clears instead (same
discipline already used for `pr`), re-tested the same way: typed prompt survived, generated ideas and
the button label both correctly reset.

**Deliberately not touched, flagged rather than silently skipped:**
- `state.campaign` — the Idea Platform's own ladder/roles/posts/video handoff hub. Server-persisted
  with its own id and lifecycle, same shape as House/Plan, not an in-progress client draft — needs
  their open-time-sync-plus-backend-route treatment, not a blind client reset.
- House/Plan's per-layer generated-but-uncommitted suggestion rows (`pGenerateLayer`/
  `hGenerateLayer`'s output, merged in via `applyHouse`/`applyPlan`). House/Plan already get
  `/house-brand-mode`/`/plan-brand-mode` server correction on toggle flip (Round 4); whether that also
  invalidates stale unchosen layer suggestions is a backend question, not verified either way.
- Brand-character drafting — checked and confirmed unaffected: `draftCharacter` always requires an
  active brand and never reads `producerBrandMode` at all, so Independent mode doesn't apply to it.
- PR's other rooms (media map, crisis log, coverage record) — left alone on purpose; those are running
  records, not disposable AI drafts the way the release sub-tool's output is.

**Validated:** `tools/checkfe.py` all 8 checks passed (both before and after the regression fix); LF/
NULL-byte scan clean. **Live-verified** two producers end to end with real generation calls: Social
(generated real posts in Grounded, switched to Independent — button reverted "Regenerate" → "Generate
posts", posts cleared) and Onground (generated real ideas in Grounded with a typed prompt, switched to
Independent — button reverted, ideas cleared, **and the typed prompt survived**, confirming the
regression fix). Video, POSM, PR-release, Carousel, Idea Platform and the guided Brief Builder were
fixed with the same reviewed, field-by-field pattern and passed static checks, but were not each
individually live-tested with a real generation call in this round — flagged so it's clear what's
proven versus reasoned.
