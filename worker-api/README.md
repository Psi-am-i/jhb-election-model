# joburg-forecasts: accounts, storage and sharing for readers' forecasts

Secrets, memory and machine policy are global: see `~/CLAUDE.md` rule 4 and
`~/projects/SECRETS.md`. Do not restate them here.

**Status: built and tested locally; nothing provisioned or deployed.** No D1
database, R2 bucket, rate-limit namespace, Worker, secret or provider app exists.
The ids in `wrangler.jsonc` are placeholders.

The specification is `interactive/BACKEND.md`; the owner's decisions of
2026-09-28 are `audits/2026-09-27-interactive-levers/DESIGN-decided.md` §9 and
override it where they differ. Decisions taken here are listed below.

## Files

| path | what |
|---|---|
| `src/index.js` | router; the endpoint list is its header comment |
| `src/validate.js` | the forecast validator. Pure: the page can import it |
| `generated/forecast.schema.json` | the one forecast schema, generated from the model artefact; do not edit |
| `generated/geometry.json` | ward paths for the server's share card, generated |
| `tools/make_schema.mjs` | writes `generated/`; `--check` fails if it is stale |
| `src/providers.js` | Google, Apple, Facebook, X, Microsoft on `arctic` 3.7.0 |
| `src/auth.js` | OAuth start/callback, the pending identity, sessions |
| `src/consent.js` | the consent screen's answer; the append-only log |
| `src/forecasts.js` | save, edit, read, share page, card, report |
| `src/render.js` | `/f/<id>` HTML with Open Graph tags; card PNG via resvg-wasm |
| `src/seats.js` | the seam to the seat law (below) |
| `src/deletion.js` | forecast and account deletion |
| `src/lifecycle.js` | lock stamping, post-election message, reply, deletion run, Facebook deletion callback |
| `src/turnstile.js`, `src/blocklist.js`, `src/mail.js`, `src/crypto.js`, `src/http.js` | as named |
| `migrations/0001_init.sql` | D1 schema, including the consent-log triggers |
| `seats-py/` | the Python Worker that runs `src/reader_seats.py` (stub) |
| `tools/sync_seats_py.mjs` | copies `src/seats.py` and `src/reader_seats.py` into `seats-py/`, byte for byte |

## Decisions taken here

| question | decision | why |
|---|---|---|
| One Worker or two (INTEGRATION.md §3d says extend `src/worker.js`) | **Separate Worker**, `joburg-forecasts`, as BACKEND.md §2 | owner's brief; keeps secrets and D1 out of the static site's deploy gate. §3d is superseded on this point |
| Magic-link email sign-in (BACKEND.md §3) | **Dropped** | not in the owner's provider list (DESIGN-decided §9) |
| Where a display name lives | **In the forecast body**, nullable; never on `users` | owner: no name unless typed to show on a shared forecast |
| What `users` holds | provider, provider account id, one contact (email or phone), whether it is verified | owner's minimum |
| When the account row is created | **At consent**, not at sign-in. Between callback and consent the identity is a 30-minute signed cookie | a person who signs in and leaves holds nothing in the database |
| Consent log shape (§3d had `withdrawn_at`) | one row per decision per purpose, `granted` 0/1, `wording_version`; withdrawal is a new row | `withdrawn_at` is an UPDATE; the log is append-only, enforced by triggers |
| Withdrawing `store` or `age18` | deletes that account's forecasts, keeps the account and log | the lawful basis for holding them is gone |
| Seats | **Server trusts only the picks and recomputes** via the `SEATS` service binding to a Python Worker running `src/reader_seats.py`; a client `seats` key is refused | no JavaScript seat law (BACKEND §6); the page shows seats from the same Python file under Pyodide, the server's are stored |
| Seat service down | save answers **503**, nothing stored | a stored forecast without seats would need a second, later card |
| Card cache key | `cards/<id>/<rev>-<seats_code_ref>/<size>.png` | a fixed seat-code bug must not leave a stale PNG at an immutable URL |
| Post-election deletion | runs only after the message run has recorded **every** message as sent | deleting people who were never asked is not "no reply". While mail is a stub, nothing is deleted; logged hourly |
| After "tell me about the next election" | forecasts deleted at `DELETION_AT`; sign-in id and contact kept | the message says so |
| Reply and verification links | GET shows a button; only POST acts | mail scanners follow GET links |
| `noindex` on `/f/*` | **on** (meta and `X-Robots-Tag`) | README open decision 6 recommended it; reversible in `render.js` |
| Rate limits | per IP: the `ratelimits` bindings (saves, sign-in starts); per account: a D1 counter of saves per day and a cap on live forecasts; all values in `wrangler.jsonc` | the binding's windows are 10 s or 60 s only, so BACKEND's "per hour" limits became per minute |

## Seats: the contract with `src/reader_seats.py`

`src/seats.js` posts `{ward_calls, pr_share, council_seats}` to the SEATS
service and expects `{seats, ward, pr, council_total, code_ref}`. It checks only
arithmetic identities (ward counts equal the picks, seats = ward + pr, totals add
up, roster parties only), never the law. `seats-py/src/entry.py` **assumes** the
Python function is `reader_seats.reader_seats(ward_calls, pr_share,
council_seats) -> {"seats", "ward", "pr"}`. That name and shape must be agreed
with the author of `src/reader_seats.py`; until the file exists and is copied,
the Python Worker answers 501 and every save answers 503.

## Tests

    npm test          # schema currency, seat-code copy check, then vitest

Two vitest projects: `node` (`test/node/`, build checks) and `workers` (inside
workerd with local D1 and R2). The workers project replaces the SEATS binding
with `test/fake-seats.js`, **a test double that is not the seat law**, and uses a
random signing key per run. Each validator refusal is a constructed violation of
a valid forecast; the share page and card SVG are snapshot-tested
(`test/__snapshots__/`).

## Local development

    npm install
    npm run db:local        # local D1 under .wrangler/
    direnv allow            # .envrc reads secrets from the Keychain, by name
    npm run dev             # wrangler dev on 127.0.0.1:8802 (never 8765)

`env.dev` uses plain cookie names (`__Host-` cookies are refused over http) and
skips Turnstile. Secrets reach `wrangler dev` from the process environment
(`CLOUDFLARE_INCLUDE_PROCESS_ENV=true`), never a `.dev.vars` file. Keychain
service names are `JHB_FORECASTS_<NAME>`. Saving needs the SEATS Worker, so it
answers 503 locally until `seats-py` runs.

## Secrets (names only; set with `wrangler secret put <NAME>` on `joburg-forecasts`)

| name | from |
|---|---|
| `SESSION_SIGNING_KEY` | 32 random bytes, generated by the owner |
| `TURNSTILE_SECRET` | Turnstile widget for `joburg.whysoserious.city` (its site key is public and goes in the page) |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google |
| `APPLE_SERVICE_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY` | Apple (`APPLE_PRIVATE_KEY` is the whole `.p8` PEM text: `wrangler secret put APPLE_PRIVATE_KEY < AuthKey_XXXX.p8`) |
| `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET` | Meta |
| `X_CLIENT_ID`, `X_CLIENT_SECRET` | X (the OAuth 2.0 client id and secret, not the API key) |
| `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET` | Microsoft Entra |

## Provider registrations (owner)

Every provider needs a privacy-policy URL and most a terms URL; neither page
exists yet (`interactive/privacy-placeholder.html` is a placeholder). The
callback of every provider is `https://joburg.whysoserious.city/auth/<provider>/callback`.

| provider | where | register |
|---|---|---|
| Google | Google Cloud console, APIs & Services | OAuth consent screen (External; authorised domain `whysoserious.city`; privacy URL); OAuth client, type Web application; redirect URI `/auth/google/callback`. Scopes `openid email` only |
| Apple | developer.apple.com (paid Developer Program) | an App ID with Sign in with Apple; a **Services ID** (its identifier is `APPLE_SERVICE_ID`) configured with domain `joburg.whysoserious.city` and return URL `/auth/apple/callback`; a **Key** with Sign in with Apple (download the `.p8` once; Key ID and Team ID). To email private-relay addresses, register the sending domain under "Sign in with Apple for Email Communication". Do **not** register the server-to-server notification URL until `/auth/apple/notifications` is built (it answers 501) |
| Facebook | developers.facebook.com | app with the Facebook Login use case; Valid OAuth Redirect URI `/auth/facebook/callback`, strict mode on; Basic settings: privacy URL, **Data deletion callback URL `https://joburg.whysoserious.city/auth/facebook/data-deletion`**; `email` needs no app review; switch the app to Live |
| X | developer.x.com | project and app; User authentication: OAuth 2.0, confidential client (Web App), permission Read, **Request email from users on** (needs privacy and terms URLs); callback `/auth/x/callback`; website `https://joburg.whysoserious.city`. Check the access tier's quota for `GET /2/users/me` |
| Microsoft | entra.microsoft.com, App registrations | account types "any organisational directory and personal Microsoft accounts" (tenant `common`, the `MICROSOFT_TENANT` var); Web redirect URI `/auth/microsoft/callback`; a client secret (it expires: note the date for rotation); delegated permissions `openid email`; privacy and terms URLs; publisher verification, or the consent screen says "unverified" |
| Instagram | none | Meta closed personal-account sign-in (Basic Display API) in December 2024; Facebook covers Meta users |

## Cloudflare resources to create (owner)

D1 `joburg-forecasts` (location hint: open decision), R2 `forecast-cards`, two
rate-limit namespace ids, the `joburg-seats` Python Worker, the three-line
service-binding forward in `src/worker.js` for `/f/*`, `/api/*`, `/auth/*`, an
Email Service sending domain and binding, and the dates `POST_ELECTION_MESSAGE_AT`
and `DELETION_AT`.

## Stubs

| stub | the real thing |
|---|---|
| `src/mail.js` sends nothing | Cloudflare Email Service `send_email` binding; contact verification mail is not built either |
| `seats-py/src/entry.py` answers 501 | `src/reader_seats.py`, copied by `tools/sync_seats_py.mjs`, interface agreed |
| `/auth/apple/notifications` answers 501 | JWT verification against Apple's JWKS, then deletion |
| `generated/*` from the prototype's placeholder fixtures | regenerate from the S2 export and the IEC's certified roster (`--model`, `--geometry`) |
| `src/blocklist.js` holds only impersonation patterns | the owner's content policy |
| post-election message wording (`src/mail.js`) | owner and counsel |
