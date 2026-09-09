---
name: get-page-text-blind-to-overlays
description: "get_page_text extracts all DOM text regardless of z-index/visual stacking — cannot be used to verify a modal, auth gate, or paywall overlay is actually blocking content"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 2992e305-436f-4002-a763-1671cfdf2a8a
  modified: 2026-09-07T05:33:47.917Z
---

`get_page_text` reads text nodes from the whole DOM and has no concept of visual stacking — a
full-screen `position:fixed` overlay sitting on top of the real content (a login gate, a modal, a
paywall) is invisible to it. It will report the content *underneath* the overlay as if it were showing,
which reads exactly like "the gate isn't blocking anything" even when the gate is working perfectly.

**Why:** hit this live testing Heritage Marketing Studio's real login enforcement (round 92, 7 Sep) —
after a genuine sign-out, `get_page_text` still showed the full Home screen, which first read as a real
bug in the frontend's `authOut` gate. Checking properly (`getComputedStyle` on the "Sign in" heading's
ancestor chain) showed a correct `position:fixed; inset:0; z-index:900` full-viewport overlay — the gate
was fine the whole time; the verification method was blind to it.

**How to apply:** whenever verifying anything that gates content behind a fixed-position overlay (auth
screens, modals, paywalls, cookie banners) — don't conclude from `get_page_text` alone that it isn't
working. Confirm via `getComputedStyle` (position/zIndex/display) on the gating element, `read_page`'s
accessibility-tree semantics, or an actual screenshot. `get_page_text` is the right tool for confirming
*what data is present*, not for confirming *what's actually visible or interactive*.
