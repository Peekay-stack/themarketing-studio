---
name: browser-verification-available
description: This project has a working browser pane — load the page and verify before claiming a screen works; endpoint tests alone were wrong three times.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 27396459-a562-47a1-a61d-312c29b2c1b0
  modified: 2026-08-28T14:09:21.286Z
---

Verify frontend claims by **loading the page**, not by testing endpoints.

**Why:** I told this user "ready for user testing" three times in a row and was wrong every time, always
the same way — I tested routes over HTTP, never rendered a screen. The logo bug survived three handovers
because of it. The actual cause was a click bubbling into a parent's close handler, which no static check
and no endpoint test could ever have seen.

**How to apply:** the `mcp__Claude_Browser__*` tools work here. Start a throwaway server on a spare port
(`.venv/Scripts/python.exe -m uvicorn main:app --port 8010` from `api/`) rather than touching the user's
own on 8000, `preview_start {url}`, then `javascript_tool` for inspection — `read_page` misses most
controls because they are `<span onClick>` rather than buttons, and screenshots fail when the pane is not
displayed. Keep JS results tiny; a broad DOM dump blows the token limit. Kill the server with `taskkill
//PID <pid> //F` when done.

Probing pattern that found the real bug: walk `parentElement` from the control, reading
`Object.keys(el).find(k => k.startsWith('__reactProps$'))` to find which ancestors carry an `onClick`.

If a check passes and the screen is still broken, fix the check — but load the page first, because the
check is usually not the thing that was missing.

**Round 49: a route that curl proves works is not proof anything calls it.** The user reported PR
messages never generating. I curl-tested `/pr-message-suggest` directly against all five real PR
sheets — real suggestions came back for four of them, 200 OK every time. The route was never the
problem. `loadPrMsgSuggest()` existed and worked; it was just never invoked on the path a real user
takes to reach the Messages tab — `prTabLoad(k)`, the dispatcher every other PR tab's loader is wired
through on tab-switch, simply had no `messages` entry. Curl tests the producer in isolation; it says
nothing about whether the consumer's trigger is wired to the interaction that actually fires in the
browser. Same session, same lesson twice: I also read "0 badges" after a ladder-builder click and
concluded it was broken, when the real issue was checking `main.innerText` in the same synchronous
tick as the click — before React's async commit landed. Reading DOM state immediately after simulating
a click, in the same script execution, sees the pre-click DOM; a second, separate `javascript_tool`
call afterward sees the true state.

Related: [[design-handovers-merge-never-replace]]
