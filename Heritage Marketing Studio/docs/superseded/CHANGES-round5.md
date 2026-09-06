# CHANGES — handover 5

Base: your `Design_Handover_4/app.dc.html`, unmodified except for what is listed here.
**Scope: the client-logo path only.** Nothing else in the file was touched — no renames, no
reformatting, no reordering, no changes to any other screen, method or bag key.

---

## Template — one block, in Studio settings under "Brand logo"

**Removed** (the `<label>`-wrapped picker):

```html
<label style="display:inline-flex; … margin-bottom:26px;">
  ⬆ Upload a logo
  <input type="file" accept="image/*" onChange="{{ uploadClientLogo }}" style="display:none;" />
</label>
```

**Replaced with:**

```html
<div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
  <span onClick="{{ openLogoPicker }}" style="…same button styling…">⬆ Upload a logo</span>
  <input id="tms-logo-input" type="file"
         accept="image/*,.png,.jpg,.jpeg,.svg,.webp,.avif,.gif,.bmp"
         ref="{{ logoInputRef }}" onChange="{{ uploadClientLogo }}"
         style="position:absolute; width:1px; height:1px; opacity:0; pointer-events:none;" />
</div>
<sc-if value="{{ hasLogoNote }}" hint-placeholder-val="{{ false }}">
  <div style="font-size:12.5px; line-height:1.55; margin-top:9px; color:{{ logoNoteColor }};">{{ logoNoteText }}</div>
</sc-if>
<div style="height:26px;"></div>
```

Three reasons for each part:

- **`<label>` → explicit `onClick`.** A wrapping label opens the picker in the browser's own code, so
  the first observable thing a click does is a native dialog — and when the dialog does not appear
  there is nothing to look at. `openLogoPicker` writes a status line *before* it calls `.click()`.
- **`display:none` → offscreen.** A `display:none` input is `.click()`-able in every browser I know
  of, but it is the one property that would make it not be, and it costs nothing to avoid.
- **`accept` carries extensions.** `accept="image/*"` alone hides `.avif` in some OS pickers.

`checkfe` note: `sc-if` +1/+1, `div` +3/+3, all balanced.

---

## State — one key

```js
brands: [],
logoNote: null,   // { text, tone: 'wait'|'ok'|'warn'|'bad'|'info' }   ← added
```

## Bag — five keys, added directly after the existing `clientInitial, clearClientLogo, uploadClientLogo` line

```js
openLogoPicker:this.openLogoPicker, logoInputRef:this.logoInputRef,
hasLogoNote: !!(s.logoNote && s.logoNote.text),
logoNoteText: (s.logoNote && s.logoNote.text) || '',
logoNoteColor: this.LOGO_NOTE_COLOR[(s.logoNote && s.logoNote.tone) || 'info'] || '#6B7280',
```

No `bag*()` method was added, so the bag-composition check is unaffected.

---

## Logic — 4 methods changed, 8 added

### Changed

| method | change |
|---|---|
| `saveStudio(next)` | a `data:` `clientLogo` over 700,000 chars is nulled **before** the `localStorage.setItem`. A 4MB logo would otherwise blow the quota and take the accent and theme down with it — the whole studio record, lost to one large file. |
| `clearClientLogo` | adds one `logoSay(…)`. Behaviour otherwise identical, `/brand-logo-clear` unchanged. |
| `syncBrandLogo()` | two guards: (a) returns early rather than clearing a `data:` URL when the brand has no server logo — that URL is somebody's upload made while the backend was down, and wiping it looks exactly like losing their file; (b) compares URLs with the `?v=` cache-buster stripped, so a synced logo does not churn state on every call. |
| `uploadClientLogo` | rewritten — see below. |

### Added

| member | what it is |
|---|---|
| `LOGO_NOTE_COLOR` | `{ wait/info:#6B7280, ok:#1E7E34, warn:#C8860F, bad:#C0392B }` — existing tokens, no new colours. |
| `logoInputRef` | `React.createRef()`. |
| `logoSay(text, tone)` | the one writer of `state.logoNote`. |
| `openLogoPicker` | ref → `getElementById('tms-logo-input')` fallback → `el.value=''` → `el.click()`, each failure with its own message. |
| `logoHandleFile(f)` | the pipeline: validate → read → preview → resolve brand → normalise → POST → report. |
| `logoBrand()` | returns the active brand, re-reading `/brands` when the list is empty and using the **returned array** rather than waiting on `setState`. |
| `logoDataUrl(f)` | `FileReader` → data URL, promise that resolves `null` rather than rejecting. |
| `logoToPng(dataUrl)` | `Image` → `canvas` → PNG blob, longest edge capped at 1200px, transparency preserved. |

All eight names are unique in the class; `checkfe`'s member census stays clean.

---

## What `uploadClientLogo` now does, and which of your three suspects each part answers

```
click
  └─ openLogoPicker      writes "Choose an image…"        ← suspect (1) becomes observable
       └─ change event
            └─ uploadClientLogo
                 ├─ no file        → "No file chosen"
                 ├─ dedupe guard   (input + change both fire in some browsers; same
                 │                  name|size|lastModified inside 1.5s is one upload)
                 ├─ _logoBusy      (a second click during an upload is ignored)
                 └─ logoHandleFile
                      ├─ not an image / over 4MB → named, with the actual size
                      ├─ logoDataUrl → setStudio      shows immediately, survives reload
                      ├─ logoBrand()                  ← suspect (2) fixed, not diagnosed
                      ├─ normalise → PNG if needed    ← the AVIF failure
                      ├─ arrayBuffer → fresh Blob     ← suspect (3) removed
                      ├─ POST /brand-logo
                      └─ report: reached? ok? detail? saved?
   finally: el.value = ''                             ← moved here, after the bytes are copied
```

### Suspect (1) — does the handler fire?

You could not tell, and neither could a screenshot. Now every step writes a line under the button, so
the failure point is a sentence on the screen rather than a server log read next to a browser:

| line shown | where it stopped |
|---|---|
| *(nothing at all)* | the click never reached `openLogoPicker` — a render problem, not an upload one |
| *Choose an image…* and no more | picker opened; no file chosen, or `onChange` never fired |
| *Reading mark.svg…* | `FileReader` stalled |
| *Showing here, but not saved: no brand profile is active…* | your (2) — and it now only appears if a re-read of `/brands` also came back empty |
| *Converting … to PNG…* | format normalisation |
| *Uploading to Heritage…* and no more | the fetch hung — a `POST /brand-logo` line will be in your log |
| *The server could not be reached* | fetch threw; no request left the browser |
| *The server refused the upload (413)* | your `detail`, verbatim |
| *Saved to Heritage.* | done |

### Suspect (2) — `activeBrand()` null

A click can beat `loadBrands()` on mount. `logoBrand()` re-reads `/brands` and reads the brand off the
**returned** array, so there is no `setState` race. The refusal message only survives as the case where
there genuinely is no brand.

### Suspect (3) — `e.target.value = ''` before the await

Removed rather than reasoned about. The file is read to an `ArrayBuffer` and re-wrapped as a fresh
`Blob` before anything touches the input, and the input is cleared in a `finally` after that. An
emptied input can no longer produce an empty body under any timing.

---

## `blob:` → `data:`

Your instinct to drop the blob URL was right; the replacement matters as much. A `data:` URL survives a
reload and localStorage, so when the server is unreachable the logo is **genuinely still there** rather
than a string that decays into a broken image. That is what makes "showing here, but not saved" an
honest sentence instead of a promise the next page load breaks.

`componentDidMount`'s `blob:` strip is unchanged and still correct — old records need it.

---

## AVIF — the one thing that is arguably yours

A real file, `Heritage-Foods-logo-770x435.avif`, was refused. AVIF is an image every current browser
decodes and Pillow will not open without `pillow-avif-plugin`, so `/brand-logo` correctly said "not an
image" about a file that plainly is one.

Handled here: anything outside `png · jpeg · svg+xml · webp · gif` is decoded by the browser and
re-encoded as PNG before the request. Your endpoint only ever sees formats it can read, and the
filename is rewritten to `.png` to match.

**Worth doing server-side anyway:** `pillow-avif-plugin`, and a `.heic` reader. Phone screenshots and
Keynote exports will hit the same wall on `/library-add`, which has no conversion in front of it.

---

## Verified in a browser, which is the part you could not do

Loaded, opened Studio settings, dispatched a real `change` with a real `File` on `#tms-logo-input`:

- the handler runs; the data URL lands in `state.studio.clientLogo` and in `localStorage`
- the status line renders with the right token colour (`#C8860F` on the no-brand warning)
- the header and sidebar marks both update
- no console errors on load or through the flow

Not verified: the actual `POST /brand-logo` round trip — there is no backend on this side. That half is
yours, and it is the half you already proved.

---

## Not touched

`DESIGN_NEXT §12` (the brand profile form — waiting on `brandprofile.py` and `status.readiness`), the
live-action shots screen, the four `house-docx`/`plan-docx` buttons, and everything in DESIGN.md §8.
