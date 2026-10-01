# Deploy through UAT

UAT is a Version URL of the live Worker `joburg-whysoserious`. `wrangler versions
upload` stores a new version without sending it any live traffic and prints a
`*.workers.dev` URL that serves only that version. After checking that URL,
`wrangler versions deploy <version-id>@100%` sends all live traffic to the same
version, so what goes live is the build that was checked. There is no separate
staging Worker and no second config file.

Every command runs from the repository root. The agent does not run wrangler; the
owner does.

## How each host behaves

| Host | Serves | `X-Robots-Tag` | Channel paths |
|---|---|---|---|
| `joburg.whysoserious.city` | Johannesburg, from the asset root | none | 302 to `/`, logged |
| `whysoserious.city`, `www.` | the portal | none | not handled; behave as any other path |
| `<city>.whysoserious.city` | `/<city>/`, portal if unbuilt | none | not handled |
| `<version-prefix>-joburg-whysoserious.<sub>.workers.dev` (Version URL, UAT) | Johannesburg, from the asset root | `noindex, nofollow` | 302 to `/`; the log line is written but Workers Logs does not show Version URL logs |
| `joburg-whysoserious.<sub>.workers.dev` (live workers.dev) | Johannesburg, from the asset root | `noindex, nofollow` | 302 to `/`, logged with this host |

Source: `src/worker.js`. Tests: `tests/test_worker_routing.py`.

## Channel short paths

Cloudflare Web Analytics does not record query strings, so `utm_` tags on links
cannot be counted there. Each channel gets its own short path instead. The Worker
answers it with a 302 to the home page and logs one object, whose keys Workers Logs
indexes as fields.

| Link to use | Channel in the log |
|---|---|
| `https://joburg.whysoserious.city/go` | `billboard` |
| `https://joburg.whysoserious.city/x` | `x` |
| `https://joburg.whysoserious.city/li` | `linkedin` |
| `https://joburg.whysoserious.city/fb` | `facebook` |
| `https://joburg.whysoserious.city/ig` | `instagram` |
| `https://joburg.whysoserious.city/g` (Google Ads final URL) | `google_ads` |

Matching ignores case and one trailing slash (`/GO`, `/go/`). A query string on the
short path, such as the `gclid` Google Ads appends, still matches and is dropped
from the redirect. Logged object:

```json
{"event":"arrival","channel":"billboard","host":"joburg.whysoserious.city"}
```

`host` separates real arrivals from hits on the live `workers.dev` host. Count
only `host = joburg.whysoserious.city`.

**Workers Logs keeps events for 3 days on Workers Free and 7 days on Workers Paid**
(developers.cloudflare.com/workers/observability/logs/workers-logs/, "Pricing").
Counts older than that are gone; export them at least that often.

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

Build `site/` and pass the number review as `HANDOVER.md` describes. Wrangler
uploads the working directory, so start from a clean tree:

```sh
git status --short          # expect no output
```

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
for p in go x li fb ig g GO go/; do
  printf '%-4s ' "$p"; curl -s -o /dev/null -w '%{http_code} %{redirect_url}\n' "$U/$p"
done
#   every line: 302 https://<version-prefix>-joburg-whysoserious.<sub>.workers.dev/
```

Then open `$U/?v=<anything>` in a browser and read the pages that changed. The
arrival log line cannot be checked here: Workers Logs does not show Version URL
requests.

If anything is wrong, stop. Nothing is live; fix, commit, go back to step 1.

### 3. Promote the checked version

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

## Counting arrivals

Dashboard → `joburg-whysoserious` → Observability → Query builder (or the
`query_worker_observability` tool):

- filter `event` = `arrival` and `host` = `joburg.whysoserious.city`
- group by `channel`, aggregate count
- time range: the campaign day or week, within the retention window above

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
