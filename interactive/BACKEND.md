# Readers' forecasts: backend specification

**Status: specification only.** Nothing here is built, provisioned or deployed.
No Cloudflare resource exists for it. The prototype pages call
`js/api-stub.js`, which imitates the API below in the browser's localStorage.

Secrets, memory and machine policy are global: see `~/CLAUDE.md` rule 4 and
`~/projects/SECRETS.md`. This file names the secrets this service needs and
how they reach the Worker; it does not restate the policy.

## 1. What this reverses

PUBLISHING-BACKLOG §10 decided that a reader's forecast would live only in its
URL, so that "a stored forecast is a reader's political statement held on our
infrastructure" never arose. The owner has now decided to store forecasts
against a sign-in, so that winners can be contacted and readers can opt in to
updates (§9b's leaderboard question is answered the same way). **This service
reverses §10's URL-only rule.** The consequences are the rest of this file: a
lawful basis for special personal information, a retention period, a deletion
path, and validation of untrusted input.

## 2. Shape

```
joburg.whysoserious.city ── src/worker.js (static site, deploy-gated)
        │  /f/*  /api/*  /auth/*   forwarded over a service binding
        ▼
joburg-forecasts Worker ── D1 `forecasts` ── R2 `forecast-cards` (rendered PNGs)
        │                    Rate Limiting binding, Turnstile, Email Service
        ▼
OAuth providers (Google, Apple, Facebook, X); magic-link email
```

A separate Worker behind a service binding keeps the database, the secrets and
the sign-in code out of the static site's Worker and its `deploy_check.py`
gate, and lets either be deployed without the other. The site Worker's change
is three `if (path.startsWith(...)) return env.FORECASTS.fetch(request)` lines.

## 3. Sign-in

**Providers:** Google, Apple, Facebook and X over OAuth 2.0 authorisation code
with PKCE, plus an emailed magic link. Scopes are the minimum that yields a
stable account id, a name and an email: `openid email profile` (Google),
`name email` (Apple), `email public_profile` (Facebook), `users.read` (X).

| provider | what to expect |
|---|---|
| Google | OIDC id_token; verify signature against Google's JWKS, `aud`, `iss`, `nonce`. |
| Apple | `response_mode=form_post` (a POST to the callback). Name arrives **only on the first sign-in**; email may be a private relay address. Client secret is a JWT signed with the Apple key, minted per request. |
| Facebook | Email may be absent if the user signed up by phone. |
| X | Email is not reliably returned. The consent screen asks for one when absent (the prototype does this). |
| Magic link | 32-byte random token, stored hashed, single use, 15-minute expiry, sent with Cloudflare Email Service. Rate-limited per address and per IP. |

**Flow.** `GET /auth/:provider/start` writes `state`, `nonce` and the PKCE
verifier to a short-lived signed cookie and redirects. The callback checks
`state`, exchanges the code, verifies the token, and upserts the user by
`(provider, provider_sub)`. It sets a session cookie (`__Host-session`,
`HttpOnly; Secure; SameSite=Lax; Path=/`, 30 days) whose value is a random id
looked up in D1, so a session can be revoked. First sign-in goes to the consent
screen; no forecast is stored until consent is recorded.

**Accounts are not merged across providers** by email. Merging on an unverified
email is an account-takeover route; a reader who signs in two ways has two
accounts.

## 4. Storage (D1)

Kept: a display name, an email, the provider and its account id, the forecasts,
and the consent record. Nothing else: no profile photo, no friends list, no
location, no IP address beyond the rate limiter's transient counters.

```sql
CREATE TABLE users (
  id            TEXT PRIMARY KEY,            -- random, not the provider id
  provider      TEXT NOT NULL,               -- google|apple|facebook|x|email
  provider_sub  TEXT NOT NULL,
  email         TEXT,                        -- NULL until supplied
  email_verified INTEGER NOT NULL DEFAULT 0,
  display_name  TEXT NOT NULL DEFAULT '',
  show_name     INTEGER NOT NULL,            -- chosen on the consent screen, no default
  created_at    TEXT NOT NULL,
  UNIQUE (provider, provider_sub)
);
CREATE TABLE consents (                      -- append-only: the evidence of consent
  id            INTEGER PRIMARY KEY,
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  notice_version TEXT NOT NULL,              -- the privacy notice text shown
  store         INTEGER NOT NULL,            -- special PI consent (required)
  age18         INTEGER NOT NULL,
  contact_if_win INTEGER NOT NULL,           -- separate, optional
  updates       INTEGER NOT NULL,            -- separate, optional
  at            TEXT NOT NULL
);
CREATE TABLE forecasts (
  id            TEXT PRIMARY KEY,            -- 10 chars base62 from crypto.getRandomValues (~59 bits)
  user_id       TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rev           INTEGER NOT NULL DEFAULT 1,  -- bumps on edit; keys the card cache
  body          TEXT NOT NULL,               -- validated JSON, §6
  model_ref     TEXT NOT NULL,               -- artefact key of the published run it was made against
  created_at    TEXT NOT NULL,
  updated_at    TEXT NOT NULL,
  locked_at     TEXT                         -- set at the cutoff, §8
);
CREATE TABLE sessions (id TEXT PRIMARY KEY, user_id TEXT NOT NULL
  REFERENCES users(id) ON DELETE CASCADE, expires_at TEXT NOT NULL);
CREATE TABLE deleted_forecasts (id TEXT PRIMARY KEY, at TEXT NOT NULL);  -- so /f/<id> can answer 410
```

`PRAGMA foreign_keys = ON` so deleting a user deletes everything of theirs.
D1 has no South African location; the privacy notice discloses the transfer
(POPIA s72) and the database is created with the location hint nearest the
readers the owner chooses (an open decision).

## 5. The share URL and its image

**URL:** `https://joburg.whysoserious.city/f/<id>`. The id is random, so
forecasts cannot be enumerated.

**`GET /f/<id>`** returns server-rendered HTML: the page in `f/index.html` with
the map as inline SVG, the seats, the coalition, the date, the calls to action,
and the share links as plain `<a href>` intents. Link-preview crawlers
(WhatsApp, Facebook, X, LinkedIn, Slack) do not run JavaScript, so the Open
Graph tags must be in this response; the comment at the top of `f/index.html`
lists them. The page's script only enhances it (the native share sheet, image
download). Unknown id: 404. Deleted: 410 with a page that says so.

**`GET /f/<id>/card.png?v=<rev>`** (and `card-story.png`) is the og:image.
It is rendered from the same `buildCardSVG` the page uses (one builder, not
two), rasterised in the Worker with `resvg-wasm` and one embedded open-licence
font, so crawlers get a stable image whatever font a reader's phone has. The
first request renders and writes the PNG to R2 under `cards/<id>/<rev>/<size>.png`;
later requests stream it from R2. `Cache-Control: public, max-age=31536000,
immutable` is safe because `rev` is in the URL; editing bumps `rev`, and the
og:image URL changes with it. Rendering cost is paid once per revision.

**Display names are untrusted text on an image published from our domain.**
Validated at save (§6), escaped at render, capped at 40 characters, and any
forecast can be reported from its page. A reader can share as "A reader".

## 6. Validation: a forecast is untrusted input

`POST /api/forecasts` and `PUT /api/forecasts/:id` accept JSON and reject,
with a 400 naming the field, anything that fails these checks:

* body at most 16 KB (135 calls plus a full-roster `pr_share` with long party codes approaches 8 KB); `Content-Type: application/json`; same-origin `Origin`
  header (CSRF), plus the `SameSite=Lax` session cookie;
* `ward_calls`: an array of exactly 135 entries, each a party code in the
  certified roster **for this city and election** (read from the published
  artefact, not from the request), in ward order;
* `pr_share`: an object whose keys are exactly the roster, values finite,
  0 ≤ v ≤ 100, summing to 100 ± 0.5;
* `coalition`: 1 or more distinct roster codes; `mayor` null or a member of
  `coalition`;
* `model_ref`: must equal a published run's artefact key; the server records
  it, so "distance from ours" is always against a named, dated run;
* `display_name`: NFKC-normalised, control and bidirectional-override
  characters stripped, whitespace collapsed, 1–40 characters, checked against
  a short blocklist; no URLs.

Seats are **not** accepted from the client, so a shared card cannot show seat
totals that do not follow from the calls. The server computes them with the
model's own `seats.allocate`, which is Python: either the forecasts Worker is
a Python Worker (Cloudflare runs those on Pyodide, the same runtime the page
uses) importing `src/seats.py`, or a small Python Worker behind a second
service binding does only that. A JavaScript copy of the seat law is not an
option (PUBLISHING-BACKLOG §9). Which of the two is an open decision; both
wait on the model-side question in README "Integration" of how ward calls and
list shares become the combined votes `seats.allocate` takes.

## 7. Rate limiting and abuse

* **Turnstile** on save and on magic-link requests (`siteverify` server-side,
  secret `TURNSTILE_SECRET`).
* **Workers Rate Limiting binding**: per IP, 10 magic-link requests an hour and
  30 saves an hour; per user, 30 saves a day.
* **Per-user cap** of 20 live forecasts (owner to confirm).
* **Card rendering** only for an existing id and current `rev`; any other `v`
  redirects to the current one, so the renderer cannot be driven by arbitrary
  input.
* **Report**: `POST /api/forecasts/:id/report` records a report; the owner
  can hide a forecast (`410`) pending review.

## 8. Deletion, retention, and the election-day lock

* `DELETE /api/forecasts/:id` (owner of the forecast only): deletes the row,
  deletes its R2 cards, purges the cached URLs, records the id in
  `deleted_forecasts`, and `/f/<id>` answers 410 from then on.
* `DELETE /api/me`: deletes the user row; the cascade removes sessions,
  consents and forecasts; R2 cards are deleted by prefix. Email list membership
  (if updates were ticked) is removed in the same request.
* Unsubscribe links in every email work without signing in (signed token).
* **Retention** (owner to decide; proposed): forecasts and contact details are
  deleted on 30 June 2027, after scoring and any prize, by a scheduled Worker
  (Cron Trigger). Update-list membership lasts until unsubscribe. The consent
  log is kept as long as the data it covers.
* **Lock.** At the cutoff (proposed: 07:00 SAST on 4 November 2026, when polls
  open) every forecast gets `locked_at`; edits are refused and scoring uses the
  locked body. DESIGN-decided §5: the scoring rule and code are frozen before
  that date, and the same scorer runs on every reader's forecast and on the
  model's.

## 9. Secrets

Set with `wrangler secret put <NAME>` against the `joburg-forecasts` Worker.
Never in `wrangler.toml`, never in a file:

| name | what |
|---|---|
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google OAuth client |
| `APPLE_SERVICE_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` | Sign in with Apple |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | Facebook Login |
| `X_CLIENT_ID`, `X_CLIENT_SECRET` | X OAuth 2.0 |
| `SESSION_SIGNING_KEY` | HMAC key for the short-lived OAuth state cookie and unsubscribe tokens |
| `TURNSTILE_SECRET` | Turnstile siteverify |

Client ids are not secret but are kept with their secrets so a rotation
changes both in one place. Local development reads them from the Keychain via
direnv, per `~/projects/SECRETS.md`; `wrangler dev` must receive them from the
process environment, not from a `.dev.vars` file. Confirm the installed
wrangler supports that before relying on it; if it does not, local development
runs against the stub.

## 10. Before this goes live (not code)

* A privacy notice, the Information Officer's registration with the
  Information Regulator, and a PAIA manual (§ README "Legal").
* An operator agreement covering Cloudflare as the processor (POPIA s21) and
  a breach-notification procedure (s22).
* Competition rules, if there are prizes.
* Provider app registrations: each requires a privacy-policy URL and, for
  Apple and Facebook, a data-deletion URL; both are the pages above.
