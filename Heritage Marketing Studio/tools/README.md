# tools/ — the two build tools for `app.dc.html`

`api/frontend/app.dc.html` is one 8,353-line Design Component. Claude Design works in it whole, and that
does not change — the single file *is* their tool. These two tools make it reviewable and checkable
without taking that away.

There is no Node in this environment, so both are Python and neither can execute JavaScript. What they
can do is guarantee two specific things, and each guarantee is backed by a test.

```bash
python tools/checkfe.py          # before every commit that touches the file
python tools/partials.py status   # what the parts are and how big
python tools/partials.py verify   # round-trip check, changes nothing
python tools/test_tools.py        # prove the tools themselves still work
```

## checkfe.py — the check that was missing

Once I flattened newline escapes in this file and broke eight string literals. The tag-balance and
binding checks I was running all passed, because neither of them looked at JavaScript. Design found it.

`checkfe` is the missing check. It is not a parser; it is a scanner that understands enough lexical
structure to be certain about:

- **Unterminated string literals** — a `'` or `"` string cannot cross a line break, which is exactly
  what mangled escapes produce. This is the one that matters.
- **Bracket balance**, ignoring anything quoted, commented, templated or in a regex. A naive brace count
  here is meaningless: the markup is full of `{{ }}` and the logic is full of `${}`.
- `sc-if` / `sc-for` / `<div>` pairing.
- Duplicate class members — the later one silently wins.
- `bagX()` methods spread into the bag but never defined, or defined and never spread.

Exit 0 means every check passed. It does **not** prove the file runs. Nothing here can.

## partials.py — split for the repo, join for the app

Splits the file on the comment banners **it already has**:

```
markup :  ^  <!-- ===== NAME ===== -->      (exactly two spaces of indent)
logic  :  ^  // ===== NAME =====            (inside the data-dc-script block only)
```

No sentinels are inserted and nothing is modified, so there is no marker for anyone to delete by
accident. Deeper-indented banners stay put — `    <!-- ==== STEP: SCRIPTING ==== -->` inside the video
screen is a sub-section, not a file.

Today that yields **59 parts**, largest 1,059 lines. `parts/` is gitignored: `app.dc.html` remains the
single source of truth and the parts are a review aid, regenerated on demand.

The round trip is **byte-identical**, and `test_tools.py` proves it on the real file every run. A build
step that *nearly* reproduces a 661KB file is worse than none, because the damage lands later and looks
like somebody else's bug. `join` refuses outright if a part is missing or has been emptied.

## What is deliberately not done: splitting `renderVals`

`renderVals()` is 1,059 lines and returns ~650 keys — by far the largest part. It looks like the obvious
next target. It is not, and the reason is measurable:

> 142 locals are set up before the `return {`, and **112 of them are referenced inside it**.
> `s` alone appears 263 times.

Move a slice of that literal into a new `bagX(s)` method and every one of those references breaks — at
**runtime**, not at parse time. No check in this directory would catch it, because the syntax stays
perfectly valid. `checkfe` would go green on a broken file, which is precisely the failure these tools
exist to prevent.

Design can do this safely because they can run the component and see the screen. The recipe:

1. Take one area's keys out of the return into `bagArea(s)`.
2. Move the locals that only that area uses into the new method with them.
3. For locals shared with other areas — `s`, `im`, `lrn`, `cp`, `dc`, `prod`, `th` — pass what is needed
   as arguments, or promote the derivation to its own small method called from both.
4. Spread it back in: `...this.bagArea(s)`.
5. `python tools/checkfe.py`, then load the screen.

Design has already done this four times (`bagStrategy`, `bagPlan`, `bagExec`, `bagSales`), so the pattern
is proven — and because new areas now go straight into their own method, the growth problem is already
solved for new work. Retro-splitting the existing 650 keys is tidiness, not capacity.

## The one real fragility this surfaced

Line 33 of `app.dc.html` loads SheetJS from a CDN:

```html
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
```

Every other asset is local. This one means spreadsheet export silently stops working offline, and the
portal is run from a `.bat` on a laptop. Worth vendoring into `api/frontend/` — not urgent, but it will
be confusing the first time it happens.

## selfcheck.py + smoke.py -- the backend checks that were missing (19 Sep)

Added after the deployed `main.py` called `producers.stands_on(..., brand_mode=...)` while the deployed
`producers.py` was older and had no such parameter. Nothing above can see that: `checkfe` reads only the
front end and `contract.py` reads response shapes; Python itself only notices a wrong keyword when the
line runs, so a real user got HTTP 500s for a day.

```bash
python tools/smoke.py               # BEFORE every push: exports the COMMITTED tree, boots it, checks it
python api/selfcheck.py             # just the call-signature audit, on the working tree
curl https://themarketing-studio.com/selfcheck    # AFTER every deploy -- login-free, returns ok + commit
curl https://themarketing-studio.com/selfcheck/deep   # AFTER every deploy -- the server checks its OWN signed-in routes on real data
```

- `api/selfcheck.py` reads every call from one project module into another and checks it against the real
  signature of the function it calls (unexpected keyword, too many positional args, module that will not
  import) and a required argument a call never supplies (only where the call has no `*args`/`**kwargs`).
  It does not check argument values or types, and a pass does NOT mean the app works.
- `tools/smoke.py` runs that audit plus a boot test against `git archive HEAD` in a scratch folder with an
  empty data directory (the live shape), and hits the read routes and the routes that broke before with a
  signed-in test session. No AI provider is called. Exit 0 = safe to push. It never touches real data.
- `GET /selfcheck` is public on purpose and returns only pass/fail, counts and the deploy's commit; the
  per-call detail goes to the server log.
- `GET /selfcheck/deep` makes the running server call its own signed-in routes (lists, open-a-house/plan,
  the docx exports, and the routes that broke on 18-19 Sep) against its own real data and report a status
  per route -- no login, no credential, nothing written, no AI call. Requests are in-process and carry a
  random key that exists only in the server's memory (`selfcheck.internal_key_ok`, checked by the login
  middleware), so an outside caller cannot use it. It also proves the door is shut: the same route with no
  key and with a wrong key must answer 401. Output is route templates + status codes only, never data.
  Rate-limited to one real run a minute (a repeat returns the last result, `cached: true`). It cannot see
  routes that need a named user (`Depends(current_user)`), writes, real model output, or the browser.

## test_pack_choice.py -- the pack-photo decision in /scene-still (19 Sep)

```bash
python tools/test_pack_choice.py     # exit 0 = every choice attaches (or withholds) the pack correctly
```

Calls the real `/scene-still` route in-process with the image providers stubbed (no key, no cost, no writes,
scratch data dir) and checks the whole matrix: Automatic / Never / a picked pack / "design one", in both
Grounded and Independent. On the code before 19 Sep it fails exactly the two cases where a picked pack was
ignored; it proves the DECISION about references, not what an image model then draws.

21 Sep: also pins the pack-in-scene wording (`pack_role`: side / hero / in_use / cta / corner / none, photo vs illustrated
styles, the wording when a cast frame or a previous render is also attached) and the session-only reference photo
(`pack_reference`: attached as the pack, refused if not an image data URI or over 8 MB, and never stored -- checked
with the real ledger write on). `packscene.py` holds the wording; it was proven on 10 real generations first.

## test_carousel_concept.py -- the Carousel writer'''s shows_pack flag (Deploy 2, 22 Sep)

```bash
python tools/test_carousel_concept.py  # exit 0 = the shows_pack contract behaves
```

Stubs `producers._ask` with canned JSON -- no key, no cost. Checks that the model'''s own shows_pack
answer is trusted when given (even against pack-sounding or pack-free wording), that a slide the model
left the field off (or one added by hand with addSlide, which never goes through this prompt) falls back
to `posm.looks_like_pack()` on its own visual note, and that the prompt tells the model the closing
slide is handled for it. It does not decide which slide is the CTA -- that is computed from slide
POSITION in the frontend (`resolveSlidePackRole`), never a stored tag, so reordering or deleting slides
can never leave a stale label behind.

## test_identity_lock.py -- the reuse-the-exact-people wording (22 Sep)

```bash
python tools/test_identity_lock.py  # exit 0 = age is conditional, everything else still locks
```

Face, hair, skin tone and body type still lock unconditionally against a cast/plate reference; age now
follows the shot's own words the same way clothing already did (a real before/after Carousel held a
recurring man's face but never let him age, until this). Checks the wording is present, not what a real
model draws with it.

## test_library_naming.py -- library item names and AVIF references (21 Sep)

```bash
python tools/test_library_naming.py  # exit 0 = names, rename and the AVIF conversion all behave
```

Runs the real `/library-add`, `/library-rename` and `/library` routes in-process against a scratch data
directory (no key, no cost). Checks that a name given on upload is used, that a rename changes the name and
nothing else (file, sign-off, note), that blank/unknown/over-long names are handled, and that an AVIF
reference is sent to the image services as PNG while JPG/PNG/WebP go through byte-for-byte unchanged.
