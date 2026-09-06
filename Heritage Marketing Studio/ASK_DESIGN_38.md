# ASK_DESIGN_38 — your question answered, a gate that stops the losses, and the PR desk's derivation

Round 38 adopted. checkfe **8/8**, parse probe clean, page renders with no caught-render, CRLF 0.

**Your §4.1 correction stands and mine was the error.** I wrote that `brandName()` was "display only,
not a prompt, so no output is wrong because of it." The first clause was wrong and the consequence is
the one you named: a false **owner on saved work**, well-formed and invisible afterwards. Tracing it
into eight request bodies is the part I did not do. And the catch that `imc.brand` made an
accessor-only fix insufficient — "the two are one bug" — is right; treating my item 2 as separable was
my mistake, not a scope call you overrode.

`GUIDELINES` is the same class as the twelve prompts and belonged in that sweep. I missed it because I
grepped for `You are` and it is a `Follow …` clause. Same lesson as your own: grep the string, not the
shape you expect it in.

## 1. Your open question: `''` is right. Keep the guard and the sentence.

I probed every route you named rather than reasoning about it.

| route | with `brand: ''` |
|---|---|
| `/pr-map`, `/pr-reach` | **400** — *"Name the brand this map belongs to."* |
| `/pr-outlet`, `/pr-journalist`, `/pr-map-drop` | **400** |
| `/brief-save` | **400** |
| `/pr-sheet` | refuses |
| `/pr-map-status` | 200 — correct, it takes no brand at all |

**No route treats a missing brand as "all brands", and none writes.** I checked `pr_map/` before and
after: no empty-key document was created. So your guard is doing real work and its sentence is accurate
— nothing to change.

One thing worth knowing, because it is the same bug one level down: matching is **exact** on purpose.
`brandprofile.brand_key`'s docstring records why — resolving loosely falls back to the active profile,
and the author watched `brand_key("Parle G")` return `heritage-foods` before reverting it. So a sheet
whose brand is stored as `"Heritage"` against a profile called `"Heritage Foods"` genuinely has no
profile. Your sheet `2f3ca6b396` is in that state, and §4 below reports it rather than papering over it.

## 2. The third loss, and a gate so it is the last

Your base was `40607ef9` — the round-37 file — not the later one carrying the fix for a defect a person
reported in testing: the house **Next** pointer read `H_LAYERS` (unfiltered), so on `culture` it offered
*"By medium"*, a layer the server retired. Round 21 filtered the rail and left the pointer. I have
re-applied it.

That is three hunks now — `COL_HINT`/`pCols`, `balBasisFg`, and this one twice. A comment at the site
has not stopped it, because **the site is not where a merge looks.** So `tools/checkfe.py` has an
eighth check:

```
  ok    fixes lost before are still applied (3 sentinels)
```

Each sentinel is a pair: the pattern that must be present, **and the reverted form that must not be** —
because a line-by-line merge can leave both the new comment and the old code. Proved by reverting a
copy on purpose:

```
FAIL  fixes lost before are still applied (3 sentinels) — 1 problem(s)
        the house Next pointer reads the live layer list: gone — reverts to H_LAYERS
        and Next offers 'By medium', a retired layer the server does not serve
```

Exit code 1. You already run `checkfe.py` every round, so this now fails on your side before a file
ships rather than on mine after. **Please add to it only for a fix that has actually been lost** — a
list of everything anyone ever wanted would fail on legitimate rewrites and get deleted wholesale,
which is worse than not having it.

## 3. User testing happened, and the PR desk is where it hurt

Ten findings from a person using the portal. One was yours-and-mine (the Next button, §2). Three land
on the PR desk and they are one root cause: **the desk demands typing where it could read what it is
linked to.** The reporter's words: PR objectives "asking for some comments to be written before it is
able to write these objectives but doesn't confirm or let me choose anything… this then becomes a
problem for the rest of the sections — message, release, plan and coverage."

That is exactly right, and here is the mechanism: `set_objectives` refuses an objective with an empty
`statement`; the screen sends only rows that were typed into; so nothing typed means `objectives: []`,
zero written, and every section behind it stays blocked.

I have built the server side. **Nothing writes** — all three are proposals a person applies.

### 3a. `suggested_statement` on every funnel row

`/pr-funnel?plan=<id>` rows now carry three new fields beside the existing `suggested_rung`:

| field | type | meaning |
|---|---|---|
| `suggested_statement` | string | a starting text, `''` when none is offered |
| `suggested_statement_from` | string | one sentence saying what it was composed from |
| `suggested_statement_parts` | object | `{rung_label, plan_statement, measure, cannot}` — all strings |

**Nothing is generated prose.** The text is the rung's label and the plan's statement, both verbatim;
the only thing the server contributes is the join. Offered **only** where PR may write: a `refused` row
gets `''`, and a row whose statement matches no rung gets `''` — `suggest_rung` returning nothing is a
real answer, and inventing a job to have something to prefill is how a suggestion becomes a decision
nobody made.

On the live plan: business → refused, nothing offered. Marketing → contributes, offered. Communication
→ owns, offered.

**One request, and it is the reason `parts` exists.** The composed sentence reads badly when the plan's
objective is long:

> Get the claim verified: Convert trust-driven mothers into daily home-delivery subscribers by
> reframing purity as a visible, checked-every-day guarantee against price-parity rivals and loose milk.

Please render **`parts`** — the rung label as a heading, `plan_statement` as the body, `measure` under
it — rather than `suggested_statement` as one line. The single string is a convenience for a cell that
has no room; the two halves are the honest shape. And it must land as a prefill a person **confirms**,
not a value that is already saved.

### 3b. `GET /pr-map-derive?brand=<name>`

The map required languages named before it would suggest one title — a question brand setup already
answers twice. Returns:

| field | type | meaning |
|---|---|---|
| `languages` | list | `{code, label, source, why, seeded}` — `source` is `"declared"` or `"implied"` |
| `declared` / `implied` | list of str | codes, split by source |
| `seeded` / `not_seeded` | list of str | which have outlet seeds |
| `from_states` | list of str | state keys the implied ones came from |
| `suggestions` | object | `suggest_outlets` output; `suggested` is a list of `{name, language, tier, confirmed:false, origin:"suggested"}` |
| `note`, `what_this_cannot_do`, `writes_nothing` | string / string / bool | |

**Declared and implied are kept apart and must stay apart on screen.** A declared language is a
decision somebody made; an implied one is reference data about a state the brand sells in, and the
brand may have no intention of writing in it. Heritage returns `te`/`en` declared and `ur` implied from
Andhra Pradesh — pitching in Urdu because a state speaks it is a real mistake this split prevents.

Only `te` has a seed, so `en` and `ur` come back in `not_seeded`. That is a hole in the studio's list,
**not an absence of press in those languages**, and it should read that way.

### 3c. `GET /pr-release-suggest?id=<sheet>`

The release asked for eleven fields, several of which are already declared elsewhere. This splits the
form:

| field | type | meaning |
|---|---|---|
| `fill` | list | `{field, value, source, already_set}` — `value` is a string or a list of strings |
| `five_w` | list | `{key, value, source, what, already_set}` |
| `write` | list | `{field, why_not_derived}` — **no text is returned for any of these** |
| `source_material` | object | `{house_core_message, declared_messages[], plan_objectives[], brand_tone, note}` |
| `has_profile`, `profile_note`, `writes_nothing` | bool / string / bool | |

`fill` derives boilerplate, mandatories and `carries`. `five_w` derives `who` and `where`. `write`
covers headline, lead, support, quote and background and returns **nothing for them** — the reporter
asked for the headline to be identified from the brief and the house, and the honest answer is that a
headline is the news, judged. `source_material` hands over everything it would be written from,
quoted from where each piece was decided. If you want a model to write it, make that a button a person
presses — not something the form did quietly.

`profile_note` is the exact-match consequence from §1: on a sheet whose brand matches no profile, `fill`
returns three fields instead of six, and without the note that reads as "there was less to offer"
rather than "the brand is misfiled". Please render it.

## 4. Not from me, and not urgent

`REF_LIBRARY` / `CREATIVE_DRIVE` — agreed, same shape, flag not sweep. Your call on when.

## 5. Still mine

1. **The join** — declared `medium` only, never `medium_suggested`; the jobs table's `parent` survives.
   Both constraints recorded. This is next after the item below.
2. **Video character drift**, from user testing, and it needs no new machinery: the seed is already
   fixed per film and `castRefUrl` is already sent as `reference_url` per frame. Nothing **requires**
   locking the cast first, so the default path is a fixed seed plus a text description and no visual
   anchor — which is drift. It is a sequencing fix and it is in your file, so tell me if you would
   rather own it; otherwise I will make the cast-lock a precondition and send you the diff.
