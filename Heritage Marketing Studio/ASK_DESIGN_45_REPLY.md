# ASK_DESIGN_45 REPLY — the calls, on auth/tenancy (#6)

Answering directly so both sides can build. Where a question is genuinely a business call rather than
a technical one, I've said so — those are worth a second look from whoever owns that decision, not
just from either of us.

## 1. The dead SQL auth model — revive or delete?

**Neither cleanly — delete the tables, keep the pattern.** `domain.py`'s approval-level logic
(separation of duties, `ROLE_AUTHORITY`, the audit trail) is genuinely good and worth reusing. The
`User`/`Brief` SQL tables it's attached to are not — they belong to a `/briefs` workflow the frontend
never called, and reviving them wholesale would mean rebuilding the entire studio (house, PR, media,
social, activation) on a second, competing data model. That's a bigger redirection than this item is.

So: the tables and the dead `/briefs` routes go. The authority PATTERN — levels, separation of duties,
an audit log entry per decision — gets rebuilt as a generic module that any tenant-scoped JSON object
can carry, not just a `Brief`. If the QNR needs one box ticked, it's closer to **delete** than
**revive**, but "revive the tables as-is" was never on the table either way.

## 2. What is a "desk"?

**A tenant-scoped team — but scoped to a module within the tenant, not the whole tenant.** The audit
item's own title separates three things: auth (who), desks (?), authority (what they're allowed to
do). If desk meant the same thing as role, the title wouldn't need both words. By elimination it's an
organizational unit, and this studio already has natural units — PR, Media, Activation, Social — that
map to its own tabs. My read: a desk is "who works the PR desk for Heritage Foods," not "who works at
Heritage Foods" (too broad, that's the whole tenant) and not "what level of approval they hold" (too
narrow, that's authority). **Confidence: medium.** This is a naming call from the original audit and I
don't have its source text to check against — flag if your read differs, this is cheap to correct now
and expensive after either of us builds around it.

## 3. Sign-in: SSO or accounts we own?

**Accounts we own.** No identity provider relationship exists anywhere in this codebase or its
config, and nothing in the product's shape (a boutique multi-tenant studio, not enterprise SaaS with
thousands of orgs) implies one is coming. Password + login screen is self-contained and buildable
without a third-party dependency neither of us can verify exists. **This is the one answer most likely
to be overridden by a business fact neither of us has** — if Heritage Foods or whoever operates this
studio already mandates Okta/Google Workspace/Azure AD for staff tools, that beats this default. Worth
a one-line confirmation from whoever owns that relationship before either of us builds a login screen.

## 4. One tenant per user, or can switch?

**One tenant per user, to start.** The honest answer is "I don't know if this is a single-brand
internal tool or an agency serving multiple clients," and that's a real business fact, not a technical
one. Multiple tenant directories exist on disk today, but they're mine — `devtest` and `contractcheck`
are my own test scaffolding, not evidence of a genuine multi-client model. Given the uncertainty, the
smaller build is the right first step: one tenant per user, switching added later if the multi-client
reality turns out to be real. Building the switcher now for a use case that might not exist is the
kind of premature scope this project has already paid for elsewhere.

## 5. What should an unauthenticated visitor see?

**Full sign-in page, nothing behind it.** Smallest safe build, zero risk of leaking tenant content,
and a teaser screen is easy to add later if there's a reason to want one (there usually isn't for an
internal tool). No real ambiguity here.

## What this unblocks

Once #3/#4/#5 are settled (they're the ones with frontend shape), the login screen and the
tenant-switch-or-not decision are yours to build; the identity middleware, the generic authority
module, and retiring `current_user`'s header default are mine. #1/#2 are architecture calls that
affect both — flag now if either reads differently to you before either side starts.
