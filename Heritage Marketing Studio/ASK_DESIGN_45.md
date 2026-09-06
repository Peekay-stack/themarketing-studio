# ASK_DESIGN_45 — framing only: auth, desks and authority (audit #6)

As agreed — no paragraph, no spec. What's actually true in the code, and the questions I don't have
answers to. Send back questions before either of us builds anything.

## What already exists

**A real authorization model, fully built, and used by nothing.** `api/domain.py` has approval
levels, separation of duties (`Creator cannot approve their own item`), and an audit trail —
`ROLE_AUTHORITY`, `current_level`, `required_levels`, per-approval logging. It sits behind a `User`
table (`id`, `name`, `role`: Creator | ApproverL1 | L2 | L3) and a `Brief` table with its own
approve/submit/request-changes routes.

**Identity underneath it is a header, not a login.** `current_user()` reads `X-User-Id`, defaults to
`"puneet"` if the header is absent, and looks the id up with no password or token check at all —
commented `# lightweight dev auth` in the code, so this was never meant to ship as-is.

**The product you actually use doesn't touch either of those.** `/briefs`, `/users`, `/me`,
`request-changes` — zero references in `app.dc.html`. The whole SQL User/Brief/domain.py stack is
dead from the frontend's side. Everything the studio actually does — the house, PR, media, social,
activation, brand profile — runs through `tenancy.py`'s JSON file stores instead, and that system has
**no identity concept whatsoever**, not even the weak header one. `tenancy.tenant()` reads a single
process-wide environment variable. One tenant per running process; nothing in a request says who is
asking or which tenant they're asking for.

**Multiple tenant directories already exist on disk** — `default`, `devtest`, `contractcheck` — so
file-level scoping is real (F10's "scoping done" from the inventory). Which one answers a given
request is decided by how the process was started, not by anything the request carries.

**Net: two unconnected systems, and the one the product runs on has nothing.** This is the project's
own "two homes for one decision" pattern, at the level of who the user even is.

## What I don't know, and won't guess

- **Is the SQL system (`User`/`Brief`/`domain.py`) meant to be revived, or is it dead weight from an
  earlier direction?** Its approval-level logic is worth keeping if the direction was right; wrong if
  the file-based studio was always meant to replace it. I don't know which.
- **Is a "desk" a role (Creator/Approver, as the dead model has it), a person, or a tenant-scoped
  team?** The audit calls this item "auth, desks and authority" and I don't have the audit's own
  definition of desk in front of me to check against.
- **Single sign-on, or accounts we own?** Changes almost everything about what the frontend needs —
  a real login screen and password handling vs. redirecting to an identity provider.
- **Does a user belong to exactly one tenant, or can they switch?** If they can switch, the frontend
  needs a switcher and the backend needs the tenant to travel WITH the request rather than living in
  an env var. If not, simpler on both sides, and the current one-process-per-tenant shape might be
  close to fine as a stopgap.
- **What does an unauthenticated visitor see?** Right now: everything, as tenant `default`. A gate
  needs a "you're not signed in" screen designed somewhere, and I don't know if that's a modal, a
  full page, or a redirect.
- **Where does F10's other half land — the routes without `require_auth`?** Once identity exists,
  every route needs to check it, which is a backend-only change with zero frontend shape unless we
  want per-route error states to differ from what's there now (currently 404/400 for missing data,
  never 401/403 for missing permission, because permission checking doesn't exist).

## What I will NOT do without an answer first

Pick single-tenant-per-login vs. account-can-switch-tenants, decide whether the SQL approval model is
salvaged or deleted, or design a login screen. Each is a real decision with real cost either way, and
I'd rather ask than build the wrong one and have you revert it.
