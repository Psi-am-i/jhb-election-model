# Deploy through UAT

UAT is a Version URL of the live Worker `joburg-whysoserious`. `wrangler versions
upload` stores a new version without sending it any live traffic and prints a
`*.workers.dev` URL that serves only that version. After checking that URL,
`wrangler versions deploy <version-id>@100%` sends all live traffic to the same
version, so what goes live is the build that was checked. There is no separate
staging Worker and no second config file.

Every command runs from the repository root. The agent may run steps 0 to 2
(build, `versions upload`, the Version URL checks) and deploy a UAT version of
a Worker so it can be tested (owner, 2026-10-12). Promotion to live is the
owner's alone: `wrangler versions deploy <id>@100%` for `joburg-whysoserious`
(step 3), and any deploy of `joburg-seats` that live traffic reaches (a live
`joburg-seats` is bound by the live site Worker; see "Releasing the closeness
badge"). The agent never runs those.

## How each host behaves

| Host | Serves | `X-Robots-Tag` | Channel paths |
|---|---|---|---|
| `joburg.whysoserious.city` | Johannesburg, from the asset root | none | 302 to `/`, logged |
| `whysoserious.city`, `www.` | the portal | none | 302 to the same path and query on `joburg.whysoserious.city`, not logged here |
| `<city>.whysoserious.city` | `/<city>/`, portal if unbuilt; `/support` and `/privacy` from the asset root | none | not handled |
| `<version-prefix>-joburg-whysoserious.<sub>.workers.dev` (Version URL, UAT) | Johannesburg, from the asset root | `noindex, nofollow` | 302 to `/`; the log line is written but Workers Logs does not show Version URL logs; the Analytics Engine point is written with this host |
| `joburg-whysoserious.<sub>.workers.dev` (live workers.dev) | Johannesburg, from the asset root | `noindex, nofollow` | 302 to `/`, logged with this host |

Source: `src/worker.js`. Tests: `tests/test_worker_routing.py`.

## Channel short paths

Cloudflare Web Analytics does not record query strings, so `utm_` tags on links
cannot be counted there. Each channel gets its own short path instead. The Worker
answers it with a 302 to the home page (a `p` twin: to `/your-forecast/`) and logs one object, whose keys Workers Logs
indexes as fields.

Each path below lands on the home page; its twin ending in `p` (`/gop`, `/xp`,
`/lip`, …, `/fmp`) lands on `/your-forecast/` and logs `<channel>_prediction`.
The list is `CHANNELS` in `src/worker.js`; this table follows it.

| Link to use | Channel in the log | Twin (to `/your-forecast/`) |
|---|---|---|
| `https://joburg.whysoserious.city/go` | `billboard` | `/gop` |
| `https://joburg.whysoserious.city/x` | `x` | `/xp` |
| `https://joburg.whysoserious.city/li` | `linkedin` | `/lip` |
| `https://joburg.whysoserious.city/fb` | `facebook` | `/fbp` |
| `https://joburg.whysoserious.city/ig` | `instagram` | `/igp` |
| `https://joburg.whysoserious.city/g` (Google Ads final URL) | `google_ads` | `/gp` |
| `https://joburg.whysoserious.city/e` | `email` | `/ep` |
| `https://joburg.whysoserious.city/r` | `reddit` | `/rp` |
| `https://joburg.whysoserious.city/yt` | `youtube` | `/ytp` |
| `https://joburg.whysoserious.city/fm` | `radio` | `/fmp` |

Matching ignores case and one trailing slash (`/GO`, `/go/`). A query string on the
short path, such as the `gclid` Google Ads appends, still matches and is dropped
from the redirect. Logged object:

```json
{"event":"arrival","channel":"billboard","host":"joburg.whysoserious.city"}
```

The same arrival is written as one Workers Analytics Engine data point
(binding `ARRIVALS`, dataset `joburg_arrivals`): `blob1` the channel, `blob2` the
host, `double1` = 1, index the channel. Nothing about the visitor is written.

`host` separates real arrivals from hits on the live `workers.dev` host and on
Version URLs. Count only `host = joburg.whysoserious.city`.

**The account stays on Workers Free until traffic warrants Workers Paid**
(owner, 2026-10-21, replacing the 2026-10-01 decision to move before results
night). On Workers Paid, Workers Logs keeps events for 7 days (3 on Workers Free;
developers.cloudflare.com/workers/observability/logs/workers-logs/, "Pricing").
Analytics Engine keeps them three months, so it holds the count; Workers Logs is
for checking a single arrival soon after it happens.

`[observability.logs] invocation_logs = false` in `wrangler.toml`: Workers Logs
keeps the arrival objects, errors and uncaught exceptions, and no per-request
record. `docs-public/privacy.md` says so; change the two together.

## One-time settings check

`wrangler.toml` sets `preview_urls = true` (Version URLs) and `[observability]
enabled = true` (Workers Logs). Cloudflare documents both as applied by `wrangler
deploy`. Whether `versions upload` or `versions deploy` also applies them is not
documented. Both are Worker settings, not code, so turning them on in the
dashboard does not change the version being tested.

1. If the first `versions upload` below prints no Version URL: Dashboard → Workers &
   Pages → `joburg-whysoserious` → Settings → Domains & Routes → Version URLs →
   Enable. Run the upload again.
2. After the first promotion: Dashboard → `joburg-whysoserious` → Settings →
   Observability. If Workers Logs is off, turn it on.

## Runbook

### 0. Build and commit

Before `build_site.py --publish`, replace the `OWNER:` line in
`docs-public/privacy.md` with the responsible party's legal name and physical
address. `--publish` refuses while that line is present. A build without
`--publish` is not stopped by it, so a UAT version can carry the placeholder;
live must not.

Build `site/` and pass the number review as `HANDOVER.md` describes. One
command builds every page, `/your-forecast/` included; its
draws are committed under `site/draws/` and upload with the rest
(`site/.assetsignore` lists only `__pycache__`, `*.pyc` and `.DS_Store`). A
re-export of the draws is a separate step (`src/export_draws.py`, then
`--index site/draws`), never part of a build. Wrangler uploads the working
directory, ignored files included, so start from a clean tree:

```sh
git status --short --ignored site/   # expect no output
```

Once the leaderboard is published, the one expected line is
`!! site/leaderboard/leaderboard.json`: it is gitignored on purpose and
`deploy_check` lets it ship (`deploy_check.SHIPPED_UNCOMMITTED`).

`deploy_check` also refuses any file under `site/` that git does not track.

A UAT build publishes into a scratch copy of `publications/`, never the real
ledger. The copy keeps the ledger's first 665 rows, which ends before the 30
September freeze edition (run `r-c68c627d287e`, 319 rows), and the build
re-publishes that edition with its reason. On the UAT site a figure the
freeze edition first published is dated to the build day: its tooltip reads
"Published 26 September 2026; now <build day>" where a build against the full
ledger reads "Unchanged since 30 September 2026" (157 tooltips on the
2026-10-03 build). Live is built against the real ledger and does not have
this.

A live release that moves the forecast runs `build_site.py --publish` on the
real ledger, then re-exports the draws (`export_draws.py`, each cell, then
`--index`), whose manifests name the new publication, then rebuilds with
`build_site.py --as-published`. A plain rebuild after a publication
classifies every figure against that publication and drops the arrows and
"now <date>" tooltips; `--as-published` classifies against the ledger as it
stood before it and appends nothing (2026-10-21: the Your Forecast page had
read the run from the pre-export manifest).

`[build]` in `wrangler.toml` runs `src/deploy_check.py --city joburg` before every
upload; a build whose numbers were not reviewed is refused there.

### 1. Upload a version (UAT)

```sh
env -u CLOUDFLARE_API_TOKEN npx wrangler versions upload --message "$(git log -1 --format='%h %s')"
```

Expected output includes these two lines (labels as printed by wrangler 4.x):

```
Worker Version ID: <version-id>
Version Preview URL: https://<version-prefix>-joburg-whysoserious.<sub>.workers.dev
```

Write both down. Live traffic is unchanged at this point.

### 2. Check the Version URL

```sh
U=https://<version-prefix>-joburg-whysoserious.<sub>.workers.dev
curl -sI "$U/" | grep -iE '^(HTTP|content-type|x-robots-tag)'
#   HTTP/2 200 · content-type: text/html · x-robots-tag: noindex, nofollow
curl -sI "$U/share.jpg"     | grep -iE '^(HTTP|content-type)'     # 200 · image/jpeg
curl -sI "$U/robots.txt"    | grep -iE '^(HTTP|content-type)'     # 200 · text/plain
curl -sI "$U/regimes.json"  | grep -iE '^(HTTP|content-type)'     # 200 · application/json
curl -sI "$U/your-forecast/"                 | grep -iE '^(HTTP|content-type)'   # 200 · text/html
curl -sI "$U/your-forecast/js/model.js"      | grep -iE '^(HTTP|content-type)'   # 200 · text/javascript
curl -sI "$U/your-forecast/py/manifest.json" | grep -iE '^(HTTP|content-type)'   # 200 · application/json
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$U/play/?t=5,0,0,0"   # 301 …/your-forecast/?t=5,0,0,0
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$U/make/?v=1"         # 301 …/your-forecast/?v=1#break
curl -sI "$U/draws/index.json"      | grep -iE '^(HTTP|content-type)'   # 200 · application/json
curl -sI "$U/draws/base.bin"        | grep -iE '^(HTTP|content-type)'   # 200 · application/octet-stream
for p in go x li fb ig g e r yt fm GO go/; do
  printf '%-5s ' "$p"; curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$U/$p"
done
#   every line: 302 https://<version-prefix>-joburg-whysoserious.<sub>.workers.dev/
for p in gop xp lip fbp igp gp ep rp ytp fmp GOP gop/; do
  printf '%-5s ' "$p"; curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$U/$p"
done
#   every line: 302 https://<version-prefix>-joburg-whysoserious.<sub>.workers.dev/your-forecast/
```

Then open `$U/?v=<anything>` in a browser and read the pages that changed. On
`$U/your-forecast/`, move a control, press "Share this forecast", and open the
copied link in a private window: it must show the same seat figures. Scroll to
"Break the model", give a ward to another party, press "Analyse my forecast",
then copy section 2's link and open it in a private window: the ward and the
analysis must come back. The
arrival log line cannot be checked here: Workers Logs does not show Version URL
requests. The loop above does write eight Analytics Engine points under the
Version URL host; the count excludes them by host.

If anything is wrong, stop. Nothing is live; fix, commit, go back to step 1.

### 3. Promote the checked version (owner only)

```sh
env -u CLOUDFLARE_API_TOKEN npx wrangler versions deploy <version-id>@100% --message "UAT passed"
env -u CLOUDFLARE_API_TOKEN npx wrangler deployments status
#   <version-id> at 100%
```

### 4. Check live

```sh
L=https://joburg.whysoserious.city
curl -sI "$L/?v=$(date +%s)" | grep -iE '^(HTTP|content-type|x-robots-tag)'
#   200 · text/html · no x-robots-tag line
curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$L/go"
#   302 https://joburg.whysoserious.city/
curl -sI https://whysoserious.city/ | grep -iE '^(HTTP|x-robots-tag)'
#   200 · no x-robots-tag line (the portal)
```

The `/go` request above writes one `billboard` arrival. Confirm it in Dashboard →
`joburg-whysoserious` → Observability → Events, filter `event` equals `arrival`.
It appears within a minute or two. That one test arrival is in the counts; subtract
it.

### 5. Roll back

```sh
env -u CLOUDFLARE_API_TOKEN npx wrangler versions list
env -u CLOUDFLARE_API_TOKEN npx wrangler versions deploy <previous-version-id>@100%
```

## Releasing entry version 2 (two ballots)

A reader's entry changed shape on 2026-10-08 (MODEL-LOG §1.292): whole votes
on the ward and list ballots, entry version 2, with a `version` column in
`joburg-entries`. Three things change together and their order matters.
This is the one place the order is written; `migrations/0002_entry_version.sql`,
`src/rank_entries.py` and `wrangler.toml`'s ENTRIES note point here.

1. **Apply migration 0002** (adds `version`, old rows read 1). The old site
   Worker's seven-column insert still works after it.

   ```sh
   env -u CLOUDFLARE_API_TOKEN npx wrangler d1 migrations apply joburg-entries --remote
   ```

2. **Deploy `joburg-seats`** with the two-ballot body, after
   `node worker-api/tools/sync_seats_py.mjs`:

   ```sh
   cd worker-api/seats-py && uvx --from workers-py pywrangler deploy
   ```

3. **Promote the site Worker** that sends the two-ballot body and binds
   `version` (sections 1 to 4 above).
4. **Clear the version 1 rows**, once the owner confirms (they are test
   entries):

   ```sh
   .venv/bin/python src/rank_entries.py --clear-version 1
   .venv/bin/python src/rank_entries.py --clear-version 1 --confirm <the count it printed>
   ```

**The accepted window between steps 2 and 3:** the old site Worker sends the
old body to the new seat Worker, which refuses it, so link previews fall back
to the generic image (`/og.png`). Seals and entry storage do not call the seat
Worker and are unaffected. Taking the steps in another order makes every
seal-time insert (after 3 without 1) or every preview (3 before 2) fail.

**Rollback.** Rolling the site Worker back to a version-1 build after step 4
brings both back: its links decode as version 1 again, and its seat calls send
the old body, which the new seat Worker refuses (previews fall back to the
generic image) until `joburg-seats` is rolled back too. Entries it stores are
version 1 by the column's default.

## Releasing the seeded lot (model correction batch, 2026-10-09)

The seat law draws an exact tie by a seeded lot keyed by the published run's
identity (JUDGEMENT-CALLS §Q2, §Q6). The identity travels in the schema's
`x-seat-context.lot`, which the site Worker sends to the seat Worker with every
entry, and the new `reader_seats` refuses a context without it. This is the one
place the order is written; `worker-api/README.md` and `src/reader_seats.py`'s
docstring point here.

1. **Promote the rebuilt site Worker first** (sections 0 to 4 above), with a
   `your-forecast/forecast.json` whose `x-seat-context` carries `lot`. Check:
   `jq '.schema["x-seat-context"].lot' site/your-forecast/forecast.json` prints
   `"<city>|<target>|<seed>"`, not `null`. The old seat Worker ignores the
   extra key, so nothing changes for readers yet.
2. **Then sync and deploy `joburg-seats`**:

   ```sh
   node worker-api/tools/sync_seats_py.mjs
   cd worker-api/seats-py && uvx --from workers-py pywrangler deploy
   ```

**The reverse order refuses every entry.** A new seat Worker behind an old
site Worker receives a context with no `lot`; `reader_seats` refuses it
("context has no 'lot'"), the site Worker answers 422, and nothing is saved.

**Rollback.** Roll back `joburg-seats` before the site Worker, for the same
reason.

## Releasing the reader badges (2026-10-10)

The card answer changed shape: `reweight.outcome_chance` returns `boldest`
(the call the badge judges) and the badge words are the owner's five
(JUDGEMENT-CALLS §N10). The site Worker's card route requires `boldest`
(`src/share-edge.js` `cardAnswer`) and draws the owner's badge from
`/stamps/`. So the seat Worker goes first:

1. **Deploy `joburg-seats`** with the new `reweight.py`, after
   `node worker-api/tools/sync_seats_py.mjs` (and `--check`):

   ```sh
   cd worker-api/seats-py && uvx --from workers-py pywrangler deploy
   ```

   The old site Worker keeps working against it: it ignores `boldest` and
   prints the new badge words in its pill.
2. **Upload, check and promote the site Worker** (sections 0 to 4 above).
   Check on the Version URL that a shared link's `/og/2/link.png` draws the
   owner's badge and the boldest call, and that `/og/1/link.png?<the same
   query>` answers 301 to it.

**The other order fails visibly but safely:** a new site Worker against the
old seat Worker gets an answer with no `boldest`, refuses it, and every link
preview falls back to the generic image (`/og.png`) until step 1 is done.

**Why the image address moved to `/og/2/`.** A sealed card's image is cached
for a year as immutable (`imageCache`). The address carries
`share-edge.js` `CARD_VERSION`, so the new card has new addresses and a new
edge cache key; `/og/1/…` answers 301 to `/og/2/…`. A crawler that kept the
old bytes under the old address keeps them until it re-fetches; nothing on
our side can reach that cache.

**Rollback.** Roll the site Worker back first, then `joburg-seats` if
wanted: the old site Worker reads the new answer (above). Rolling back only
`joburg-seats` puts link previews on the generic image.

## Releasing the card's one chance (2026-10-12)

The card prints the boldest call's own chance (JUDGEMENT-CALLS §N10, amended
2026-10-12); `reweight.py` changed (`boldest_call` takes the published
prediction, `outcome_chance` requires it). The seat Worker reads the
prediction from the site's `/your-forecast/forecast.json`, which must name
the same draws as `/draws/`. `/v1/card` now takes a `prediction_sha256` (a
hash of that prediction's seats) and answers it back, and the site Worker
refuses an answer that lacks it or whose call was not measured from the
prediction (`share-edge.js` `cardAnswer`).

**Either order is safe; neither draws a wrong card.** Deploy `joburg-seats`
first (steps below). A mismatched pair of Workers answers with a refusal,
never a card:
- *old site Worker, new seat Worker:* the new seat Worker refuses the old
  request (no `prediction_sha256`, 400); previews fall back to the generic
  image (`/og.png`, `no-store`) until the site Worker is promoted.
- *new site Worker, old seat Worker:* the old seat Worker refuses the new
  request body (400), or, if it answered, the answer has no `prediction` in
  its call; the edge refuses it. Previews fall back to `/og.png`, not cached.
- a `joburg-seats` isolate that holds an earlier `forecast.json` answers 409
  to a site Worker whose `forecast.json` carries another prediction; the
  isolate reloads on its next cold start.

A card's cached image is keyed by the draws' hash and by the prediction's
(`ps=`), so a new prediction on the same draws draws new images. Bump
`CARD_VERSION` whenever the card's wording or layout changes.

1. `node worker-api/tools/sync_seats_py.mjs` (and `--check`), then deploy
   `joburg-seats` as above.
2. Upload, check and promote the site Worker. On the Version URL, a shared
   link's `/og/3/link.png` draws "Your boldest call: ..." with "We give that
   ... chance.", and `/og/2/…` and `/og/1/…` answer 301 to it. The page's
   analysis (Analyse my forecast) still shows the council outcome's chance,
   labelled "Council outcome".

**Why the image address moved to `/og/3/`.** The card's wording changed and
a sealed card's image is cached for a year as immutable (see above).

**Rollback.** Roll the site Worker back first, then `joburg-seats`. Rolling
back only `joburg-seats` leaves the new site Worker asking with a body the old
seat Worker refuses (400): previews fall back to `/og.png` until both match.
Rolling back only the site Worker leaves the new seat Worker refusing its
older request the same way.

## Releasing the closeness badge (2026-10-13)

The badge measures how close a forecast is to the published prediction, in
the owner's fixed ten-point bands (JUDGEMENT-CALLS §N10, amended
2026-10-13). `reweight.py` changed (`outcome_badge` replaces
`outcome_chance`); the seat Worker reads the prediction's seats and list
votes from the site at `/your-forecast/forecast.json`. The
`/v1/card` request body is unchanged; its answer's `outcome` carries the
badge and `measure`, and no chance. The site Worker refuses an answer whose
`measure` is not `share-edge.js` `CLOSENESS_MEASURE` (`cardAnswer`).

**Either order is safe; neither draws a wrong card.**
- *old site Worker, new seat Worker:* the old edge requires `boldest` in the
  answer, finds none, and refuses it: previews fall back to `/og.png`
  (`no-store`) until the site Worker is promoted.
- *new site Worker, old seat Worker:* the old seat Worker answers a boldest
  call with no `measure`; the edge refuses it. Previews fall back to
  `/og.png`.

1. `node worker-api/tools/sync_seats_py.mjs` (and `--check`), then deploy
   `joburg-seats` as above.
2. Upload, check and promote the site Worker. On the Version URL, a shared
   link's `/og/6/link.png` draws the owner's badge and "We think this
   prediction is <phrase>, but time will tell.", no call and no chance;
   `/og/5/…` to `/og/1/…` answer 301 to it. "Analyse my prediction" shows
   the badge at twice its arrival-view size, "We think your prediction is
   <phrase>, but time will tell." and the sealed-and-ranked paragraph, and no
   council-outcome chance.

The card answer's `outcome` also carries `phrase` (amendment, 2026-10-13);
the edge refuses an answer without it, so a seat Worker from before the
amendment draws `/og.png` until `joburg-seats` is deployed.

**Why the image address moved to `/og/5/`, then `/og/6/`** (it was `/og/4/` before the
amendment; `/og/6/` follows the sealed wording and the card module's model
card, 2026-10-13). The card's wording changed and
a sealed card's image is cached for a year as immutable (see above).

**Rollback.** Roll the site Worker back first, then `joburg-seats`. Either
alone leaves a mismatched pair, which falls back to `/og.png` as above.

## Releasing our forecast's one card (2026-10-13)

`/forecast`'s share image is now the card the share sheet of `/your-forecast/`
draws (`play-card.js`, through `src/og-pages.mjs`): the whysoserious.city
logo, "forecast, <date>", no name. No seat Worker change, so no ordering
against `joburg-seats`.

- **Old image addresses.** The image's name is a hash of its content, so the
  address a chat app kept names no file after the deploy. `src/worker.js`
  answers `/og-page/forecast-<12 letters>.png` that the assets do not hold with
  301 to the image `/forecast` names in its `og:image`
  (`staleForecastImage`; `tests/test_worker_routing.py`).
- **Two ledger tokens retire.** The old card printed four coalitions; two of
  them (`coal.ANC+EFF+PA+ALJAMAAH.majority`,
  `coal.DA+ASA+PA+ACDP+IFP+VFPLUS.majority`) appeared on no page, only on the
  image, and are in the real ledger. `build_site.py` refuses until each is
  retired, which is the owner's step before `--publish`:
  `publication.retire('joburg', '<token>', reason=..., change_class='mechanism')`.
  A UAT build is made against a scratch copy of `publications/`
  (`--ledger-root`) with the two retired there; the real ledger is untouched.

## Entries at launch

Every seal the live Worker makes is stored as an entry in the D1 database
`joburg-entries`, including seals made while testing on the live host. Once
the checks above pass and before the site is announced, empty the table:

```sh
env -u CLOUDFLARE_API_TOKEN npx wrangler d1 execute joburg-entries --remote --command "DELETE FROM entries"
```

Preview versions refuse `/seal/1`, so a UAT check never makes an entry.

## Counting arrivals

### Analytics Engine (the count; three months)

The SQL API, Cloudflare
(developers.cloudflare.com/analytics/analytics-engine/sql-api/, read 2026-10-01):
endpoint `https://api.cloudflare.com/client/v4/accounts/<account_id>/analytics_engine/sql`,
a bearer token with *Account* | *Account Analytics* | *Read*, and
"Instead of `SELECT COUNT() FROM ...` use `SELECT SUM(_sample_interval) FROM ...`"
because high volumes are sampled.

The token and account id come from the environment, never typed into a command:
store the token in the Keychain and export it from an `.envrc` (policy:
`~/CLAUDE.md` rule 4 and `~/projects/SECRETS.md`). Names used below:
`CF_ANALYTICS_TOKEN`, `CF_ACCOUNT_ID`. The header is passed from a process
substitution so the token does not appear in the command line.

```sh
curl -s "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/analytics_engine/sql" \
  -H @<(printf 'Authorization: Bearer %s' "$CF_ANALYTICS_TOKEN") \
  --data "
    SELECT toStartOfDay(timestamp) AS day,
           blob1 AS channel,
           SUM(_sample_interval) AS arrivals
    FROM joburg_arrivals
    WHERE blob2 = 'joburg.whysoserious.city'
    GROUP BY day, channel
    ORDER BY day, channel
    FORMAT JSON"
```

Shared forecasts (`/s/`, src/share-edge.js) write the channel `share`, with the
share button used as `blob3` (`wa`, `x`, `copy`, `native`, or empty). By button:
the same query with `blob3 AS button` and `WHERE blob1 = 'share'`.

The dataset is created by its first write, so `SHOW TABLES` (same curl, that as
the `--data`) lists `joburg_arrivals` only after the first live arrival. Days are
UTC.

Retention and cost, Cloudflare, read 2026-10-01:

- developers.cloudflare.com/analytics/analytics-engine/limits/: "Data written to
  Workers Analytics Engine is stored for three months."
- developers.cloudflare.com/analytics/analytics-engine/pricing/: on Workers Paid,
  "10 million included per month (+$0.25 per additional million)" data points
  written and "1 million included per month (+$1.00 per additional million)" read
  queries; "Currently, you will not be billed for your use of Workers Analytics
  Engine."

**After results night, export once:** run the query above and commit its JSON
output to the private newsdesk repo. Points older than three months are deleted.

### Workers Logs (single arrivals; seven days)

Dashboard → `joburg-whysoserious` → Observability → Query builder (or the
`query_worker_observability` tool):

- filter `event` = `arrival` and `host` = `joburg.whysoserious.city`
- group by `channel`, aggregate count
- time range: within the last seven days

## When `wrangler deploy` is still the command

`versions deploy` changes which code serves traffic. It does not apply routes or
custom domains (`wrangler triggers deploy` does that). Use a plain
`env -u CLOUDFLARE_API_TOKEN npx wrangler deploy` when `routes` in `wrangler.toml`
change, for example a new city hostname. That path has no UAT step: it uploads and
sends live traffic to the new version in one command.

## Rejected approaches

| Approach | Why not |
|---|---|
| Separate staging Worker (`wrangler.staging.toml`, `uat-joburg.whysoserious.city`) | Tests a different Worker from the one that goes live; a second config file can drift from `wrangler.toml`. Removed 2026-10-01. |
| `[env.staging]` in `wrangler.toml` | Also a separate Worker. Not ruled out by inheritance: `routes`, `assets`, `build`, `workers_dev`, `preview_urls` and `observability` are inheritable keys; only `vars` and bindings are not (developers.cloudflare.com/workers/wrangler/configuration/). |
| `utm_` tags on campaign links | Cloudflare Web Analytics does not record query strings. |
