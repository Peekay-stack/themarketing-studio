# ASK_DESIGN_21 — five edits on top of your round-20 return

Thank you for the jobs panel. **This round is small and additive: five surgical edits, no new panel.**

Phase 2 landed on the backend after `Design_Handover_20.zip` was built, so the base you worked from does
not contain these. They are already written and verified here — this document is the exact change set so
you can apply it to *your* revised file rather than merging two files.

`P2_frontend.patch` is in this zip. **It applies cleanly to the round-20 base** — I tested it, and the
result was byte-identical to the file running here (`sha256 b7d09985a916ee99…`). If your file still has
the surrounding lines untouched, `patch -p0 app.dc.html < P2_frontend.patch` will do all five. If it
does not apply, the five edits are written out below.

---

## What changed on the backend

**The messaging house is now 8 layers, not 9.** `Message by medium` is retired — it asked what each
medium makes *before there was an idea to express*, and the producers then read the platform's expression
instead, so the seven paragraphs a person chose there were overridden the moment a platform was adopted.
That question now lives in the jobs table you just built, asked once, after the idea.

**Nothing was deleted.** The stored content is untouched on disk and reachable three ways:

- `status()` returns it under a **new `retired_layers` key** — `[{id, label, went, why, options, chosen,
  n_options, n_chosen}]`. Kept out of `layers` so nothing offers it as a decision.
- `/jobs` folds each chosen line onto the medium it now belongs to. Owned and OOH are drawing on it live.
- The .docx prints it under a heading saying where the question went.

**The jobs row gained one field:** `rationale` — the channel reasoning that was in the old layer's note
(*"arterial roads near residential clusters, morning drive-time"*). Optional to show; if you do, it is
secondary to the expression, not equal to it.

---

## The five edits

### 1 · House cards must read the total from the server

Cards read their numerator from the server and their **denominator from this file**, so every card now
says *"8 of 9 layers decided"* over a finished house.

Find, in the `houseCards` map:

```js
      const done = h.chosen_layers != null ? h.chosen_layers : (h.progress || 0);
      const nextName = (this.H_LAYERS.find(([k]) => k === h.next_layer) || [])[1];
```

Insert a `total` after `done`:

```js
      const total = h.total_layers != null ? h.total_layers : this.H_LAYERS.length;
```

Then in the same block, replace all three uses:

```js
        progress: done + ' of ' + total + ' layers decided', dots: dots(done, total),
        ...
        next: done >= total ? 'All decided.' : (nextName ? 'Next: ' + nextName : 'Not started.') };
```

### 2 · The layer rail must render only layers the server still asks for

This is the one that matters most. The rail is built from the local `H_LAYERS`, so the retired layer
keeps its row — and clicking it calls a route that **rejects any layer the server does not recognise**.
A visible control that errors is worse than one that is gone.

In the house-detail section, after:

```js
    const house = s.house, status = s.houseStatus, cur = s.hLayer || 'core';
```

add:

```js
    const liveIds = (status && Array.isArray(status.layers) && status.layers.length)
      ? status.layers.map(l => l.layer || l.id || l.key) : null;
    const H_LIVE = liveIds ? this.H_LAYERS.filter(([k]) => liveIds.indexOf(k) >= 0) : this.H_LAYERS;
```

Then use `H_LIVE` in three places that currently use `this.H_LAYERS`:

```js
    const curDef = H_LIVE.find(([k]) => k === cur) || H_LIVE[0];
    const hLayers = H_LIVE.map(([k,name,parent], i) => {
```

and in the render bag:

```js
      hLayers, hRailNote: decided + ' of ' + H_LIVE.length + ' decided' + ( … unchanged … )
```

**Please do not remove the `medium` entry from `H_LAYERS`.** The filter is deliberately dynamic: it
handles the next retirement without another edit, and keeping the entry means the label is still
available for anything that looks one up by key.

### 3 and 4 · Two dropdown labels, same fix as the cards

`ideaHouseOpts`:

```js
        label: (h.brand || 'Untitled') + ' · ' + ((h.chosen_layers || 0) + ' of ' + (h.total_layers != null ? h.total_layers : this.H_LAYERS.length) + ' decided') })),
```

`houseOpts`:

```js
      houseOpts: houses.map(h => ({ id:h.id, label:(h.brand||'Untitled') + ' · ' + ((h.chosen_layers||0) + ' of ' + (h.total_layers != null ? h.total_layers : this.H_LAYERS.length)) })),
```

### 5 · Nothing to build for `retired_layers` — but do not crash on it

`status.layers` is now 8 long and there is a sibling key `retired_layers`. Anything iterating
`status.layers` is already correct. **Do not render `retired_layers` as layers.** Surfacing it read-only
somewhere — "no longer asked here, now in the jobs table" — would be welcome but is not required, and the
.docx already carries it.

---

## Still open from ASK_DESIGN_20, if not already done

Four items from last round. Ignore any you have already covered:

1. *"each format rendered at the ratio it prints at"* → the master renders at **3:4** and formats
   **re-flow**.
2. *"five ratios"* → there are **30** formats.
3. The toolkit card says the messaging house has **eight** layers. It now genuinely has eight — so this
   one has become correct by accident. Please check the wording still reads sensibly.
4. **`produceAdaptations` costs money.** It calls `/posm-image` once per selected format. The hero
   cut-out is **one asset for the whole kit** — six formats currently means six near-identical renders of
   the same subject at the same 3:4 ratio. Render once, then call `/posm-adapt` for the per-format
   sheets. That route makes no model call and is free.

---

## Before you send it back

```
python tools/checkfe.py app.dc.html
```

All seven must pass. The **seventh** (*template handlers reach the bag*) is the only one that has ever
failed here and the JS port omits it, so it will pass a file the real check fails.

Then please confirm, on a house with every layer decided:

- the card and the opened house agree — both should read **8 of 8**
- the rail has **no** `Message by medium` row
- the rail note reads *"8 of 8 decided — all decided."*
