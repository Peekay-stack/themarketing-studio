---
name: drive-the-real-page-with-stubs
description: How to test a signed-in screen in the browser pane without signing in or spending credits -- find the app instance, stub fetch, real clicks and keys
metadata:
  type: reference
---

The browser pane cannot sign in (never enter credentials) and the login overlay covers the app, so a signed-in screen looks
untestable. It is testable, and it caught real bugs on 21 Sep (Rename ignored Enter; the pack line layout). Recipe:

1. Navigate to http://localhost:8000/app (the shell is public). Wait ~3 s.
2. Find the app component: walk the React fiber from `#dc-root` (`__reactContainer$...`), probing `memoizedState`,
   `memoizedProps` and `stateNode` for an object with `setState` and `state.libNote`. Keep it on `window.__inst`.
   Screens are ids like `library` (Memory) and `exec` with `xTab:'social'`.
3. Save `window.__realFetch`, then replace `window.fetch` with a stub that records every call and returns fake JSON
   (`/library*`, `/library-rename`, `/scene-still`...). Nothing real is touched; the server still answers 401 to anything else.
4. Hide the sign-in overlay in THIS pane only (the fixed-position element containing "Sign in"). Set state with
   `__inst.setState({screen:..., <fake data>})`.
5. Use real events where behaviour matters: `computer` clicks/typing/`Enter`. The click coordinate frame is scaled (800 wide
   vs a 1024 page = 0.78125), so multiply page x/y by 0.78125. `Return` was not delivered as Enter; use `Enter`.
6. Read `__inst.state`, the stub's call log and the DOM. Screenshots come back blank when the pane is hidden -- measure with
   `getBoundingClientRect` instead.
7. Clean up: restore `window.fetch` and un-hide the overlay.

**Why:** the server log showed no rename request, which located the bug in the page; driving the page then reproduced it
(Enter did nothing). **How to apply:** for any "this control does nothing" report, do this before theorising. Related:
[[browser-verification-available]], [[reload-the-page-after-every-frontend-edit]].
