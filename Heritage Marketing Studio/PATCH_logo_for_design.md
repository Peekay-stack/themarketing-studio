# Patch — the two logo deltas, exactly. Re-apply these to your handover 6.

Yes, please re-apply rather than take my file. It is your layout, and I can verify the result in a
browser when it comes back — I could not do that until yesterday, which is why this bug survived three
rounds. A mistake here is now cheap to catch.

Four edits. All in `app.dc.html`. Nothing else changes.

Reference: my merged file is **813,130 bytes, 10,165 lines**,
`sha256 4122ef9a2d09f8d1c09c2804e9fabfa815b5f864625d58072ca963b2762040df`. Yours will not match byte for
byte and does not need to — the self-check at the bottom is the thing that matters.

---

## Edit 1 · Add the `stopBubble` method

**Find** (in the class, next to the other settings handlers):

```js
  openSettings = () => this.setState({ settingsOpen:true });
  closeSettings = () => this.setState({ settingsOpen:false });
```

**Add directly after it:**

```js
  // Every drawer and modal in this file is built as a full-screen backdrop carrying the close handler,
  // with the panel as its CHILD. That means a click on anything inside the panel bubbles up to the
  // backdrop and closes the thing you were using. Put this on the panel and the backdrop keeps its job
  // while the panel keeps its clicks.
  //
  // Most controls survived it by accident - an accent swatch still saved the accent on its way out, so
  // the drawer shutting looked like a quirk. The logo upload could not: it needs its <input> to still be
  // in the document when the file picker resolves, and the panel unmounting took the input with it. So
  // "Upload a logo does nothing" was never about uploading. Measured in a live page, both ways.
  stopBubble = (e) => { if (e && e.stopPropagation) e.stopPropagation(); };
```

## Edit 2 · Expose it in the bag

**Find:**

```js
      settingsOpen: s.settingsOpen, openSettings:this.openSettings, closeSettings:this.closeSettings,
```

**Add a line directly after it:**

```js
      stopBubble:this.stopBubble,
```

## Edit 3 · Put it on the four panels that hold controls

Each of these is the **inner** `<div>` — the immediate child of a `position:fixed; inset:0` backdrop that
carries a close handler. In every case, insert `onClick="{{ stopBubble }}"` before `style=`.

| # | the panel | its style string starts |
|---|---|---|
| 1 | **Studio settings drawer** — the reported defect | `width:420px; max-width:92vw; height:100%; background:#F7F5F1; border-left:1px solid #DDD9D1; overflow-y:auto; padding:28px 28px 40px;` |
| 2 | the prompt drawer | `width:660px; max-width:94vw; height:100%; background:#F7F5F1; border-left:1px solid #DDD9D1; overflow-y:auto; padding:26px 28px 40px;` |
| 3 | the brief picker | `background:#F7F5F1; border-radius:24px; padding:32px; max-width:640px; width:100%; box-shadow:0 40px 90px -30px rgba(8,43,21,0.6);` |
| 4 | the launcher | `background:#F7F5F1; border-radius:24px; padding:34px; max-width:760px; width:100%; box-shadow:0 40px 90px -30px rgba(8,43,21,0.6);` |

So #1 becomes:

```html
<div onClick="{{ stopBubble }}" style="width:420px; max-width:92vw; height:100%; background:#F7F5F1; border-left:1px solid #DDD9D1; overflow-y:auto; padding:28px 28px 40px;">
```

Each style string is unique in the file — if a replace matches zero or more than one, stop rather than
guess.

**Deliberately NOT patched:** the lightbox and the brand menu. Click-anywhere-to-close is right for a
lightbox, and a menu should close when you pick from it. If you restructure the backdrop to be a
**sibling** of the panel instead of its parent — which is the better fix and yours to make — drop
`stopBubble` entirely; it exists only to patch the nesting.

## Edit 4 · `openLogoPicker` — click before you say

**Find, inside `openLogoPicker`:**

```js
    this.logoSay('Choose an image…', 'wait');
    // Cleared before opening, so picking the same file twice still fires a change event.
    try { el.value = ''; } catch (e) {}
    try { el.click(); } catch (e) {
      this.logoSay('This browser blocked the file picker. Add the logo to the library and pick it above instead.', 'bad');
    }
  };
```

**Replace with:**

```js
    // Cleared before opening, so picking the same file twice still fires a change event.
    try { el.value = ''; } catch (e) {}
    // CLICK FIRST, THEN SAY. This ordering is the whole fix and it is not cosmetic.
    //
    // logoSay() is a setState. It flips `hasLogoNote` from false to true, which makes the <sc-if> below
    // this control render for the first time and can have the reconciler replace the subtree holding the
    // input. `el` was resolved before that, so it is then a DETACHED node - and .click() on a detached
    // file input does nothing at all, throws nothing, and logs nothing. The status line still said
    // "Choose an image...", so the screen reported that it had opened a picker that never opened.
    //
    // It also protects the user-activation gesture: a file picker only opens inside a real user
    // activation, and putting a render between the click and the .click() is the kind of thing that
    // costs it. Nothing needs to happen between them, so nothing does.
    var opened = false;
    try { el.click(); opened = true; } catch (e) {}
    if (!opened) {
      // Second attempt against a freshly resolved node, in case the one we held was already stale.
      try {
        var el2 = (typeof document !== 'undefined') ? document.getElementById('tms-logo-input') : null;
        if (el2) { el2.click(); opened = true; }
      } catch (e2) {}
    }
    this.logoSay(opened ? 'Choose an image…'
      : 'This browser blocked the file picker. Add the logo to the library and pick it above instead.',
      opened ? 'wait' : 'bad');
  };
```

Note the status line is now set from **whether the click actually landed**, rather than asserted before
the attempt. That is what made the old version lie: it said "Choose an image…" whether or not a picker
had opened.

---

## Self-check before you send

```bash
python tools/checkfe.py
```

Expect `sc-if 290/290`, `div 1318/1318`, `class members unique (466 declared)`. The member count going to
466 is `stopBubble`; if it stays at 465 the method did not land.

Then, in a browser with the page open on Studio settings, paste this in the console. It stubs the picker
so nothing actually opens:

```js
(async () => {
  const wait = ms => new Promise(r=>setTimeout(r,ms));
  const inp = document.getElementById('tms-logo-input');
  if (!inp) return 'settings not open';
  let clicked = 0; const orig = inp.click.bind(inp); inp.click = () => { clicked++; };
  [...document.querySelectorAll('span')].find(e=>e.textContent.trim().includes('Upload a logo')).click();
  await wait(400);
  inp.click = orig;
  const t = document.body.innerText;
  return {
    handlerFired:     clicked,                                    // want 1
    panelStillOpen:   t.includes('Studio settings'),              // want true  <- the fix
    inputStillInDom:  !!document.getElementById('tms-logo-input'),// want true  <- the fix
    statusLine:       (t.match(/Choose an image[^\n]*/)||['(none)'])[0]
  };
})()
```

**Before the patch** this returns `panelStillOpen: false`, `inputStillInDom: false`, `statusLine: (none)`.
**After**, all four should be `1 / true / true / "Choose an image…"`.

If you have a server, the end-to-end version — this uploads a real 1×1 PNG and expects
*"Saved to <brand>."*, then use **Remove** to clear it:

```js
(async () => {
  const inp = document.getElementById('tms-logo-input');
  const b64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==';
  const bin = atob(b64), arr = new Uint8Array(bin.length);
  for (let i=0;i<bin.length;i++) arr[i] = bin.charCodeAt(i);
  const dt = new DataTransfer(); dt.items.add(new File([arr],'probe.png',{type:'image/png'}));
  inp.files = dt.files;
  inp.dispatchEvent(new Event('change',{bubbles:true}));
  await new Promise(r=>setTimeout(r,3500));
  return document.body.innerText.match(/Saved to[^\n]*|not saved[^\n]*|refused[^\n]*|could not[^\n]*/)?.[0];
})()
```

If either check disagrees with the above, send me the output rather than the file and I will trace it.
