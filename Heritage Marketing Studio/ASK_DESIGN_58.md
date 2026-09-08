# ASK_DESIGN_58 — Welcome page (replaces the plain sign-in card at themarketing-studio.com)

**Base file**: `api/frontend/app.dc.html`, sha256 `798cc61e9536ad2c…`, 23,277 lines. Diff against
whatever you last synced (ASK_DESIGN_57) before touching anything, same discipline as always.

## The ask

Today, the moment anyone opens the studio — signed in or not — they see the `authOut` block below:
a plain navy field with a small centered card, "Sign in", one line of subtext, two fields, a button.
Functionally correct (it's a real, server-enforced login gate as of this week, not a decorative one),
but it says nothing about what's on the other side of it. We want the **same single screen** —
still one composition, no scrolling, still gated, still the first thing anyone sees at
`themarketing-studio.com` — reworked into a real welcome moment: a short intro to what the studio is,
a handful of feature highlights, and the sign-in form, together, minimalist rather than a multi-section
marketing site.

This is **not** the fuller scrolling landing page with a header/nav/footer we explored earlier this
week (`api/static/landing.html`, still on disk as reference material below if any phrasing is useful) —
that page is parked. What we actually want live at the root domain is this one gate screen, elevated.

## Current state — the exact block this replaces

```html
<!-- ===================== AUTH GATE ===================== -->
<!-- Full sign-in page, nothing behind it — the smaller, safer build the framing settled on. Checking
     and unreachable are kept visually distinct from a confirmed sign-out: a network blip must never
     read as a bad password, and a session is never presumed valid while it is still being asked about. -->
<sc-if value="{{ authChecking }}" hint-placeholder-val="{{ true }}">
  <div style="position:fixed; inset:0; z-index:900; background:#F7F5F1; display:flex; align-items:center; justify-content:center;">
    <div style="font-size:13.5px; color:#6B7280;">Checking your session…</div>
  </div>
</sc-if>
<sc-if value="{{ authUnreachable }}" hint-placeholder-val="{{ false }}">
  <div style="position:fixed; inset:0; z-index:900; background:#F7F5F1; display:flex; align-items:center; justify-content:center; padding:24px;">
    <div style="max-width:340px; text-align:center;">
      <div style="font-family:'Epilogue',sans-serif; font-size:16px; font-weight:700; color:#17325E; margin-bottom:8px;">Can't reach the studio server</div>
      <div style="font-size:13px; line-height:1.6; color:#6B7280; margin-bottom:18px;">Your session couldn't be checked — this isn't a sign-out. Try again once the server answers.</div>
      <button onClick="{{ retryAuth }}" style="background:#17325E; color:#F7F5F1; border:none; border-radius:10px; padding:10px 20px; font-weight:700; font-size:13px; cursor:pointer;">Try again</button>
    </div>
  </div>
</sc-if>
<sc-if value="{{ authOut }}" hint-placeholder-val="{{ false }}">
  <div style="position:fixed; inset:0; z-index:900; background:#17325E; display:flex; align-items:center; justify-content:center; padding:24px;">
    <div style="background:#F7F5F1; border-radius:20px; padding:40px 36px; width:380px; max-width:100%; box-sizing:border-box;">
      <div style="margin-bottom:24px;">{{ studioMark }}</div>
      <div style="font-family:'Epilogue',sans-serif; font-size:20px; font-weight:700; color:#17325E; margin-bottom:6px;">Sign in</div>
      <div style="font-size:13px; color:#6B7280; margin-bottom:24px;">Access is by account only.</div>
      <label style="display:block; font-size:11.5px; font-weight:700; color:#17325E; margin-bottom:6px;">Username</label>
      <input value="{{ loginUsername }}" onChange="{{ onLoginUsername }}" onKeyDown="{{ onLoginKeyDown }}" style="width:100%; box-sizing:border-box; border:1px solid #DDD9D1; border-radius:10px; padding:10px 12px; font-size:14px; margin-bottom:14px;" />
      <label style="display:block; font-size:11.5px; font-weight:700; color:#17325E; margin-bottom:6px;">Password</label>
      <input type="password" value="{{ loginPassword }}" onChange="{{ onLoginPassword }}" onKeyDown="{{ onLoginKeyDown }}" style="width:100%; box-sizing:border-box; border:1px solid #DDD9D1; border-radius:10px; padding:10px 12px; font-size:14px; margin-bottom:8px;" />
      <sc-if value="{{ hasLoginError }}" hint-placeholder-val="{{ false }}">
        <div style="font-size:12.5px; line-height:1.5; color:#C0392B; margin-bottom:8px;">{{ loginError }}</div>
      </sc-if>
      <button onClick="{{ doLogin }}" disabled="{{ loginBusy }}" style="width:100%; box-sizing:border-box; background:#17325E; color:#F7F5F1; border:none; border-radius:10px; padding:12px; font-weight:700; font-size:14px; cursor:pointer; margin-top:8px;">{{ loginButtonLabel }}</button>
    </div>
  </div>
</sc-if>
```
(`app.dc.html:87-121`.) `authChecking`/`authUnreachable` are session-state screens, not the welcome
moment — leave their current minimal treatment alone; they're deliberately plain so a network blip
never gets dressed up to look like something worse. Only `authOut` is in scope.

## Design brief

**Layout idea, not a mandate** — a two-zone single screen reads well here and needs no scroll: one
side (or the top, on narrow widths) carries the intro + feature highlights; the other carries the
sign-in card, close to its current shape and copy so the working login flow doesn't need re-testing.
Keep it to one screen, one breath — this is a gate people pass through daily, not a page they browse.

**Brand constraints** (from the book, already enforced elsewhere in this file — see the CSS comment
at the top of `<style>`): navy (`#17325E`) carries the identity; Signal Orange (`#F0561E`) is rationed
to exactly one live element at a time and never used for running copy; status colours
(green `#259821` / amber `#E8A93C` / red `#C0392B`) are interface signals only, not decoration. Font is
Epilogue throughout, already linked in `<helmet>`. The mark itself (`{{ studioMark }}`, resolving to
`assets/logo-stacked-notagline.svg` or its reverse) is the T‑diamond‑S glyph — it can detach from the
lockup and stand alone (see the `__bundler_thumbnail` template at the top of the file for that
treatment), so a bigger standalone glyph moment is fair game if the layout wants one.

**Minimalist, not empty** — the brief below gives four or five real things to say; say them plainly,
no stock icon grid, no filler stat counters. If a feature needs an icon, pull from the same restrained
mark language already in the file rather than a generic icon set.

## Content brief

**Intro** (one or two sentences, sets what this is before anyone signs in):
> Heritage Marketing Studio is where a brand's strategy becomes its creative — one decided idea,
> carried without drift from a brief through to social posts, POS material, onground activations and
> film.

**What it does, in the fewest honest words** (pick and trim freely — these are facts to draw from,
not a fixed list to fit verbatim):
- **One spine, five stages.** Brief → messaging house → idea platform → IMC plan → execution. Every
  later stage is grounded in what the earlier one actually decided, not a fresh guess.
- **Four producers, one idea each.** Social, POS material, onground activation and video all read the
  same platform and plan — never three channels quietly saying different things.
- **A real approval chain.** Named approvers per brand, a plan that locks while a decision is pending,
  a full audit trail — not an honour system.
- **A ground-truth library.** Signed-off pack shots, logos and cast references, one home each. Nothing
  the studio generates is treated as fact until a person approves it.
- **Built for more than one brand.** Multi-tenant, multi-brand from the ground up — a company running
  several brands works from the same studio, each kept to its own facts.

**Sign-in copy** — keep close to what's live (`"Sign in"` / `"Access is by account only."`); tighten
only if the new layout genuinely needs different pacing. This is an internal, invitation-only tool —
avoid anything that reads like a public-signup CTA ("Get started", "Try it free"); the honest line is
closer to *"Already have an account? Sign in below"* than a sales pitch.

## What's out of scope this round

- `authChecking` / `authUnreachable` — untouched, see above.
- The fuller multi-section landing page (`api/static/landing.html`) — parked, not what's being asked
  for here; reference only if a phrase from it is useful.
- No new backend routes or state needed — `authOut`'s existing fields (`studioMark`, `loginUsername`,
  `loginPassword`, `hasLoginError`, `loginError`, `doLogin`, `onLoginUsername`, `onLoginPassword`,
  `onLoginKeyDown`, `loginBusy`, `loginButtonLabel`) already cover the working login form; carry them
  through unchanged into whatever markup replaces this block.
