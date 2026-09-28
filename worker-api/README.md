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
| `src/consent.js` | the consent screen's answer; the append-only log; contact confirmation |
| `../interactive/js/consent-terms.js` | the consent wording, the keys the page sends, the wording-version hash (one definition, page and Worker) |
| `../interactive/js/labels.js` | default labels for shared forecasts (one definition, page stub and Worker) |
| `src/forecasts.js` | save, edit, read, share page, card, report |
| `src/render.js` | `/f/<id>` HTML with Open Graph tags; card PNG via resvg-wasm |
| `src/seats.js` | the seam to the seat law (below) |
| `src/deletion.js` | forecast and account deletion |
| `src/lifecycle.js` | lock stamping, post-election message, reply, deletion run, Facebook deletion callback |
| `src/turnstile.js`, `src/blocklist.js`, `src/mail.js`, `src/crypto.js`, `src/http.js` | as named |
| `migrations/0001_init.sql` | D1 schema, including the consent-log triggers |
| `migrations/0002_message_confirmation_labels.sql` | per-account message stamps, the confirmation stamp, default labels |
| `seats-py/` | the Python Worker that runs `src/reader_seats.py` (stub) |
| `tools/sync_seats_py.mjs` | copies `src/seats.py` and `src/reader_seats.py` into `seats-py/`, byte for byte |

## Decisions taken here

| question | decision | why |
|---|---|---|
| One Worker or two (INTEGRATION.md §3d says extend `src/worker.js`) | **Separate Worker**, `joburg-forecasts`, as BACKEND.md §2 | owner's brief; keeps secrets and D1 out of the static site's deploy gate. §3d is superseded on this point |
| Magic-link email sign-in (BACKEND.md §3) | **Dropped** | not in the owner's provider list (DESIGN-decided §9) |
| What a shared forecast is labelled | **A label per forecast**, never a name: the reader's own text or X `@username` in the body's `display_name`; otherwise a random `<word>-<number>` default (`labels.js`, CSPRNG) in `forecasts.default_label`, assigned once at creation, unique among live labels (retried on collision). Clearing a typed label returns the default. An email-shaped label is refused | owner, 2026-09-29: no real names stored or shown; per forecast so one reader's forecasts are not linkable by label |
| The X username | offered as the default label; kept in a signed HttpOnly cookie (`handle`), never in D1 unless the reader keeps it as a label | owner, 2026-09-29 |
| What `users` holds | provider, provider account id, one CONFIRMED contact, and the message and confirmation stamps | owner's minimum; R5 findings 2 and 7 |
| Unverified or typed addresses | **Not stored.** One confirmation email per account (`confirm_sent_at`), the address inside the signed link; stored as the contact only when the link's POST is made. Facebook and Microsoft addresses take this route (neither asserts verification) | owner, 2026-09-29; R5 findings 2, 7 |
| An account that never confirms | holds no contact, gets no post-election message, and is deleted by the deletion run on `DELETION_AT`; the consent screen says so ("No confirmed email") | R5 finding 2 |
| Consent wording version | **The hash of the displayed text** (`consent-terms.js`), including the deletion date. The page sends the hash it rendered; the server recomputes and refuses a mismatch (409). Not a config value | R5 finding 6 |
| When the account row is created | **At consent**, not at sign-in. Between callback and consent the identity is a 30-minute signed cookie | a person who signs in and leaves holds nothing in the database |
| Consent log shape (§3d had `withdrawn_at`) | one row per decision per purpose, `granted` 0/1, `wording_version`; withdrawal is a new row | `withdrawn_at` is an UPDATE; the log is append-only, enforced by triggers |
| Withdrawing `store` or `age18` | deletes that account's forecasts, keeps the account and log | the lawful basis for holding them is gone |
| Seats | **Server trusts only the picks and recomputes** via the `SEATS` service binding to a Python Worker running `src/reader_seats.py`; a client `seats` key is refused | no JavaScript seat law (BACKEND §6); the page shows seats from the same Python file under Pyodide, the server's are stored |
| Seat service down | save answers **503**, nothing stored | a stored forecast without seats would need a second, later card |
| Card cache key | `cards/<id>/<rev>-<seats_code_ref>/<size>.png` | a fixed seat-code bug must not leave a stale PNG at an immutable URL |
| Post-election message | **per account**: `message_sent_at`, `message_status` (`sent` or `undeliverable`). Up to `MESSAGE_BATCH_SIZE` accounts per hourly run, `MAIL_CONCURRENCY` in flight; a stamped account is never mailed again. A permanent per-recipient failure (`E_RECIPIENT_SUPPRESSED`, or a hard-bounce event) is `undeliverable`; anything else, including a sender-side fault, is retried | R5 finding 1 |
| Post-election deletion | runs only when **no** account with a confirmed contact is unstamped; each refusal is logged at error level with `alert: "deletion_refused"`. Deletes in batches of `DELETION_BATCH_SIZE` | deleting people who were never asked is not "no reply". While mail is unconfigured, nothing is deleted |
| After "tell me about the next election" | forecasts deleted at `DELETION_AT`; sign-in id and contact kept | the message says so |
| Reply and confirmation links | GET shows a button; only POST acts. The token is in the URL **fragment** (`/api/reply/delete#t=…`, `/api/contact/confirm#t=…`), copied into the form by a script, so it never reaches a request log | mail scanners follow GET links; R5 finding 10 |
| Request logs | `observability.logs.invocation_logs: false`: invocation logs record the URL, and OAuth callbacks carry the code and state in it. Only this code's structured logs are kept; none carries a URL, token, address or forecast | R5 finding 10 |
| `noindex` on `/f/*` | **on** (meta and `X-Robots-Tag`) | README open decision 6 recommended it; reversible in `render.js` |
| Rate limits | per IP: the `ratelimits` bindings (saves, sign-in starts, confirmation requests); per account: a D1 counter of saves per day and a cap on live forecasts; all values in `wrangler.jsonc` | the binding's windows are 10 s or 60 s only, so BACKEND's "per hour" limits became per minute |
| Daily quota order | the per-minute limiter and Turnstile, then the body, then a quota **check**, then the seat call; the quota is **taken** only after the seat law answers (conditional, so racing saves cannot both take the last one) and refunded if the write then fails | owner, 2026-09-29: a save the seat law refuses (422) must not use up the quota |

## Seats: the contract with `src/reader_seats.py`

`src/seats.js` posts the four arguments of
`reader_seats.reader_seats(combined_shares, ward_winners, context,
total_votes)`, by name, to the SEATS service, and `seats-py/src/entry.py`
passes them through. `combined_shares` is the reader's `combined_share` (each
party's share of all votes, ward and list ballots together, DESIGN-decided §10)
divided by its own sum; `ward_winners` keys `ward_calls` by the schema's ward
ids; `context` and `total_votes` are the schema's `x-seat-context` and
`x-total-votes`, which `tools/make_schema.mjs` reads from the model artefact and
refuses to default. The answer is `{seats, ward, pr, council_total, majority,
excessive, code_ref}`; `seats.js` checks only arithmetic identities (ward counts
equal the picks, seats = ward + pr, totals add up, majority is half plus one,
roster parties only), never the law. A 422 from the service (the seat law
refused the picks, e.g. a ward won by a party given no vote) reaches the reader
as a 422 naming `combined_share`; any other failure is a 503 and nothing is
saved.

`tools/sync_seats_py.mjs` copies `reader_seats.py` and its import closure from
`src/` (the list is `FILES`; `tests/test_reader_seats.py` holds it equal to the
closure both ways). The copies are gitignored (all of `seats-py/src/` except
`entry.py`), so **a fresh clone must run `npm run sync:seats` before `npm test`**:
`--check` fails on a missing, partial or stale copy, or a stale `code_ref.py`.

## Tests

    npm run sync:seats   # once per clone, and after any change to the seat code
    npm test             # schema currency, seat-code copy check, then vitest

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
Email Service sending domain, its `send_email` binding `EMAIL` and the `MAIL_FROM`
var, a queue subscribed to the domain's delivery events (for hard bounces), and
the dates `POST_ELECTION_MESSAGE_AT` and `DELETION_AT`.

## Stubs

| stub | the real thing |
|---|---|
| `src/mail.js` sends nothing while unconfigured | written against the Email Service `send_email` binding (`EMAIL`) and `MAIL_FROM`; neither is set. Hard bounces reported after sending need a queue subscribed to the sending domain's events and a consumer (`index.js` exports `queue`, handled by `handleEmailEvents`); none is configured |
| `seats-py/src/entry.py` answers 501 | `src/reader_seats.py` and its import closure, copied by `tools/sync_seats_py.mjs` (the interface is agreed and tested from both sides) |
| `/auth/apple/notifications` answers 501 | JWT verification against Apple's JWKS, then deletion |
| `generated/*` from the prototype's placeholder fixtures | regenerate from the S2 export and the IEC's certified roster (`--model`, `--geometry`) |
| `src/blocklist.js` holds only impersonation patterns | the owner's content policy |
| post-election and confirmation message wording (`src/mail.js`) | owner and counsel |
| consent wording (`interactive/js/consent-terms.js`), including a placeholder "Where" line | owner and counsel; the "Where" line is R5 finding 3 |
| draft privacy notice (`interactive/privacy-placeholder.html`) | owner and counsel: responsible party, Information Officer, jurisdiction, the two dates |
