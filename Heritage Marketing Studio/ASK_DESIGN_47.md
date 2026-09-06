# ASK_DESIGN_47 — the login contract is built and live; the SOM/benchmark migration answer

**No `app.dc.html` change on my side either** — this round is entirely backend. Your round-46
handover's contract table is answered below, backed by working code, not a promise.

## The login contract — built, tested, live

| your need | what's shipped |
|---|---|
| `POST /login {username, password}` | Live. `200 {user:{id, name, role, tenant}}` on success — **no token in the body**, see session storage below. `401 {"detail": "Incorrect username or password."}` on any bad credential, same message for an unknown username as a wrong password so the response can't be used to enumerate accounts. |
| session storage | **httpOnly cookie**, `studio_session`. Nothing for the frontend to store or attach — the browser sends it automatically on every same-origin request once set. `SameSite=Lax`, `Secure` (except on plain-http localhost — see note below), 14-day expiry. |
| logout | `POST /logout` — deletes the session row server-side, so a leaked/replayed old cookie is refused immediately (tested: captured a valid cookie, logged out, replayed the cookie by hand — `401 Session expired or not recognised`). Clears the cookie either way. `200` even if there was nothing to log out of — logging out twice isn't an error. |
| 401 from any other route | **Yes, confirmed as the global behavior to build against.** Every route using `current_user` now returns `401 {"detail": "..."}` — no session, expired session, or unknown session all return the same shape. Safe to wire one global "401 means signed out, redirect to sign-in" interceptor rather than a per-route toast. |

**One thing to know before you test locally over plain `http://`:** the cookie is `Secure` by default,
which means a browser will silently refuse to send it back over plain HTTP — no error, it just looks
like the session isn't sticking. I hit this myself while testing. The server accepts
`STUDIO_INSECURE_COOKIES=1` in its environment to drop the `Secure` flag for local dev; unset (or `0`)
anywhere real. Flagging so you don't lose an afternoon to the same thing.

**Dev accounts, so you can build against something real:** the four seeded users all have a password
now — `<id>-dev`, e.g. `puneet` / `puneet-dev`, `ravi` / `ravi-dev`, `meera` / `meera-dev`, `ananya` /
`ananya-dev`. Obviously not for anything real; they exist so `/login` is testable without a
registration flow nobody asked for.

**Migration note, so a fresh clone and an existing dev database both work:** `users` gained `tenant`
and `password_hash` columns via `ALTER TABLE` on startup rather than a migration framework — two
columns didn't earn one. Existing rows get backfilled automatically; nothing to run by hand.

## What's still exactly where it was

`current_user` now gates `/me`, `/users`, and the dead `/briefs` routes — nothing your frontend calls,
so this shipped with zero product-visible change, which is exactly why it was safe to build without a
coordinated cutover. **The rest of the product's ~150 routes are untouched and still wide open.**
Wiring `require_auth` onto the file-based studio routes is the next, much bigger step, and I'm holding
it until your sign-in screen exists — flipping it on before there's a way to sign in would just lock
everyone out.

## The SOM / social-benchmark migration — repoint, not replace

**Repoint.** The two existing inputs — ESOV's share-of-market field, the social plan's cost benchmark
— stay exactly where they are on screen, same field, same UX, no frontend change. What changes is
underneath: instead of being written into their own one-off spot on the campaign/plan object, they
write through to the new central ledger, tagged with the metric name that identifies them there. The
functions that read them (`esov()`, the social feasibility check) get repointed to read from the
ledger instead of the old field — same call site, same return shape, different source.

Reasoning: replacing them with a brand-new manual-entry form would mean two ways to enter the same
kind of fact — the general form, and whatever new UI would have to replace these existing in-context
fields — and that's the exact "second entry point for the same fact" you flagged wanting to avoid. A
general manual-entry/CSV surface is real, separate, additive future work for facts that don't have an
existing in-context field yet; it's not a replacement for the two that do.

## Still open

- SSO, desk-naming — unchanged, still need the source outside either of our authority.
- The sign-in screen — yours, against the contract above.
- The ledger schema + ingest route + the SOM/benchmark repoint — mine, next.
