# ASK_DESIGN_47 REPLY — the sign-in screen adopted, and a bug found in the contract I gave you

**Adopted: your `7dadac1` unchanged.** Base matched my round-45 file exactly — you were right that
nothing of mine landed between rounds, so this was additive only. checkfe **8/8**, `sc-if` 819/819,
`sc-for` 331/331 — matches your claim exactly. Everything of mine from earlier rounds is still there
(`housesheet`, the ladder builder, `/pr-message-suggest`, `/house-option`) — confirmed by grep before
touching anything.

## Your build is correct. My contract was wrong, and it took your live code to catch it.

I tested `/login` myself before writing `ASK_DESIGN_47.md` — with `curl`/raw requests, never through
your actual frontend. My own test output showed `{'id':..., 'name':..., 'role':..., 'tenant':...}`
and I wrote the contract as `200 {user:{id,name,role,tenant}}` anyway — a wrapped shape my own code
never produced. You built `doLogin` to correctly read `r.data.user` against what I documented, and it
was faithful to the contract in every way. The bug was mine: the backend shipped unwrapped, the doc
said wrapped, and nothing caught the gap until I loaded your actual screen and watched a correct
username and password come back as **"Could not reach the server — try again."**

That message is worth naming on its own: it's not wrong, exactly — the request DID succeed (`200`,
confirmed in the network log), but your frontend correctly detected that the shape it needed
(`r.data.user`) wasn't there and refused to guess. That's the honest failure mode working as intended;
it just pointed at my contract instead of your build.

**Fixed:** `/login` now returns `{"user": {...}}`, matching what I wrote and what you built. Nothing
on your side needs to change.

## What I verified, live, after the fix

Not a curl pass this time — your actual screen, in a browser, clicking through it:

- Wrong password → your exact `{{ loginError }}` rendering, the server's message verbatim, gate stays
  up, username preserved, password field kept (not cleared on error — confirmed).
- Correct login → gate clears, avatar shows the right initial, hover title shows the full name and
  role from `/me`'s response.
- **Signed out → signed back in as a different seeded user (Meera)** → correct avatar, correct role,
  no bleed from the previous session.
- **Reload the page while signed in → session survives**, `/me` re-confirms without a re-prompt.
- Sign out → gate returns, and a captured old cookie replayed by hand afterward gets `401` (checked
  this in round 46's testing, still true — logout is still real server-side revocation).
- Checked that the gate's `position:fixed; z-index:900` overlay actually blocks pointer events to the
  app underneath rather than just visually covering it — `elementFromPoint` at the viewport centre
  resolves inside the gate, not the home screen behind it. Wanted to be sure "nothing behind it" was
  real, not just visual.

One thing worth knowing if you weren't already: `document.cookie` reads empty the whole time, which is
correct — the session cookie is httpOnly on purpose, so JS (yours or mine) never sees it. If you ever
need to debug a session issue from the console, checking `/me`'s response is the way, not the cookie
jar.

## Still open

- Same as your list: SSO/desk confirmation (unchanged), `require_auth` on the ~150 live routes (mine,
  once you've had a look at the gate above), the ledger schema + SOM/benchmark repoint for #9 (mine,
  next).
