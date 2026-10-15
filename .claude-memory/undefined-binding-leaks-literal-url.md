---
name: undefined-binding-leaks-literal-url
description: "In app.dc.html, an UNDEFINED template binding in an img src renders the literal {{ x }} and the browser fetches it as a URL (404) — coerce image-url bindings to ''"
metadata:
  node_type: memory
  type: reference
  originSessionId: fcd137c0-c85a-447d-9d35-c10659cecac7
  modified: 2026-10-15T06:12:48.114Z
---

In `app.dc.html`'s Claude Design template engine, a `{{ binding }}` that resolves to **`undefined`** is left as its **literal text** in the DOM. For `<img src="{{ x }}">` that means the browser requests `/{{ x }}` and logs a 404 (seen live in Render request logs: `/%7B%7B%20ci.url%20%7D%7D` etc.). A binding that resolves to **`''` renders `src=""`** and makes no such request — so the fix is to **coerce every image-url a template binds to `''`, never `undefined`.**

An `sc-if` guard is NOT enough on its own: the leak fires when the value is undefined in the **hydrated** DOM (a row/asset that exists but has no `url` field), and worse when a **companion boolean guard disagrees** with the url (15 Oct bug: `charRows` had `hasRef: !!ref` true while `refUrl: ref ? ref.url : ''` was undefined because the ref object had no `.url`). Make the guard and the url key off the same thing (`ref && ref.url`).

Fixed 15 Oct (a9568c2): coerced `charRows.refUrl`/`hasRef`/`noRef`, `castItems.url`, `carouselCastCandidates.url`, `socialPackThumb`, `carouselPackThumb`. `carouselSlides.imageUrl` was already coerced to `''` in its builders (14684/14704/14737) and guarded, so it never actually leaked — its old log entry predated those coercions. See [[round31-queue]].

When debugging a `/{{ something }}` 404: find the bag method or `sc-for` row builder that produces `something`, and make sure it returns `''` not `undefined`.
