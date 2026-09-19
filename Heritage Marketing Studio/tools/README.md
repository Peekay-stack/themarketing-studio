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
```

- `api/selfcheck.py` reads every call from one project module into another and checks it against the real
  signature of the function it calls (unexpected keyword, too many positional args, module that will not
  import). It does not check argument values or missing required args, and a pass does NOT mean the app works.
- `tools/smoke.py` runs that audit plus a boot test against `git archive HEAD` in a scratch folder with an
  empty data directory (the live shape), and hits the read routes and the routes that broke before with a
  signed-in test session. No AI provider is called. Exit 0 = safe to push. It never touches real data.
- `GET /selfcheck` is public on purpose and returns only pass/fail, counts and the deploy's commit; the
  per-call detail goes to the server log.
