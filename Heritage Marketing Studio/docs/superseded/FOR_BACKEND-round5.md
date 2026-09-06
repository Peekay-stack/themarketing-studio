# Reply to handover 4 — the logo upload

Working from your `app.dc.html`. Only the logo path is touched.

## The split you asked for, moved into the UI

You wanted `--log-level info` to tell you whether the handler fires. That works, but it needs a
terminal next to the browser and it only answers one of the four ways this can stop. So the answer is
now on the screen: **every step writes a line under the Upload button.**

| what you see after clicking | where it stopped |
|---|---|
| nothing at all | the click never reached `openLogoPicker` — a render problem, not an upload one |
| *Choose an image…* and nothing more | the picker opened, no file was chosen, or `onChange` never fired |
| *Reading mark.svg…* | `FileReader` stalled — bad file |
| *Showing here, but not saved: no brand profile is active* | your case (2): `/brands` was empty at click time |
| *Uploading to Heritage…* then stops | the fetch hung — a `POST /brand-logo` line will be in your log |
| *The server could not be reached* | fetch threw; no request left the browser |
| *The server refused the upload (413)* | your `detail`, verbatim |
| *Saved to Heritage.* | done |

That table is the ten-second test, without the terminal.

## What I changed and why

1. **The `<label>` wrapper is gone.** The input is now opened by an explicit `onClick` →
   `input.click()`, resolved by ref with `getElementById('tms-logo-input')` as a fallback. This is the
   fix for your suspect (1): a click now provably does something before any async code runs.
2. **`e.target.value = ''` moved to a `finally`, after the bytes are copied.** Your suspect (3) was
   real enough to be worth removing rather than reasoning about — the file is read into an
   `ArrayBuffer` and re-wrapped as a fresh `Blob` before the input is touched, so an emptied input
   cannot produce an empty body.
3. **No brand is no longer a refusal.** `logoBrand()` re-reads `/brands` when the list is empty and
   uses the returned array directly rather than waiting on `setState`, so a click that beats
   `loadBrands()` on mount still uploads. Your suspect (2), fixed rather than diagnosed.
4. **The preview is a `data:` URL, not `blob:`.** It survives a reload, so when the backend is
   unreachable the logo is genuinely still there rather than decaying into a broken image. `saveStudio`
   drops it from `localStorage` over ~700KB so a large file cannot take the accent and theme down with
   it by blowing the quota.
5. **Double-fire guard.** `input` and `change` both fire on a file input in some browsers; the same
   file within 1.5s is ignored, so no upload happens twice.
6. **`syncBrandLogo()` will not wipe a `data:` URL.** A logo held locally because the server was down
   is somebody's unsaved work; clearing it on the next brand load would look exactly like losing it.
   It also compares URLs without the `?v=` cache-buster, so it does not churn state.
7. **Client-side type and size checks** before the request, with your limits (image only, 4MB), so the
   common rejections do not need a round trip.

## 8. AVIF (and anything else Pillow cannot open)

A real logo file — `Heritage-Foods-logo-770x435.avif` — was refused. AVIF is an image the browser
decodes natively but Pillow will not open without `pillow-avif-plugin`, so `/brand-logo` correctly
called it not an image and the person was correctly confused.

Fixed on this side rather than yours: anything outside
`png · jpeg · svg+xml · webp · gif` is decoded by the browser and **re-encoded as PNG** before the
request (transparency preserved, longest edge capped at 1200px). Your endpoint only ever sees formats
it can read. The status line says *"Converting … to PNG"* while it happens.

`accept` on the input also carries explicit extensions now — `accept="image/*"` alone hides `.avif`
in some OS file pickers, which is a second, quieter way for this to look like a broken button.

Worth adding server-side anyway: `pillow-avif-plugin` and a `.heic` reader, since Word and Keynote
imports will hit the same wall.

## Still open, unchanged

`DESIGN_NEXT §12` (the brand profile form) is waiting on `brandprofile.py` and `status.readiness`.
`§4.2` — echoing `source` into `/idea-platform` — reads as already wired in this file; if your
`/idea-platform` rows are arriving with `source` absent, send me one and I will trace it from the
payload rather than guess.
