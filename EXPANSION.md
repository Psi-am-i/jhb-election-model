# Expansion plan — one engine, many cities

**Status:** approved 2026-08-07, execution starting. This is the living
document for phase 2; update it as steps land rather than letting it rot.
Phase 1 (the Johannesburg model and its site) is complete and published.

## Context

`whysoserious.city` becomes a portal to per-city election models
(`joburg.`, `tshwane.`, …). Phase 1 produced an excellent site that is
**single-city by construction**, and a codebase exploration found the deeper
problem underneath: model results are *typed into prose by hand*, so they go
stale silently. Three are wrong on the live site today:

| Live text | Model actually says |
|---|---|
| standfirst: "the DA finishing first **54%** of the time" | **62%** |
| "roughly 73 wards on a **65-seat** entitlement, in **six of every seven** simulations" (×3 places) | ~74 wards, entitlement ~59, **96%** |
| portal dateline: "overhang moves the majority bar to **~141**" | dead expand-rule copy — council fixed at 270, majority 136 |
| `review.md`: "Largest party in **63%**" | 62% — and it contradicts the sheet's 54% |

The same quantities are restated by hand across files (587,000 ×3, "129 of
135" ×3, "73 wards / 65 entitlement" ×3, "865 VDs" ×6, "5,000 simulations"
×5). Naively auto-updating all of them would create a *worse* failure:
numbers inside dated arguments would silently change and turn correct
articles into nonsense ("short by 39 seats" is only true while the median is
97). Hence the foundation of this plan:

> **Every reused stat is tagged `free` or `fixed`, and always carries its
> source and the timestamp of insertion.** `free` recomputes every build.
> `fixed` is pinned to the moment it was written — and the build reports
> when the live model has drifted away from it, so a human can re-pin or
> rewrite the argument.

**Decisions taken with the user (2026-08-07):** one repo / one Worker /
`cities/*.toml`; one newsdesk routine per city; **Tshwane is the pilot**;
place-derived palette per city (Joburg amber stays, Tshwane jacaranda),
approved individually; drift **warns and reports, never blocks**; pinned
figures read plainly but expose their provenance on hover; the registry is
per-city YAML covering **numbers and strings**.

Data acquisition is already complete for all eight metros (SOURCES.md,
"All-metro sweep") — this is engineering and editorial work only.

## Step 0 — The stat registry (foundation; ships on Joburg alone)

**`content/<city>/stats.yaml`** — one entry per reusable token:

```yaml
p_da_largest:                 # free: always what the model says now
  mode: free
  source: model:structural."P(DA is the largest single party)"
  format: pct0
  inserted: 2026-08-07

claim_zille_da_median:        # fixed: pinned inside a dated argument
  mode: fixed
  value: 97
  source: model:scenario(turnout_tilt_da=1).DA.median
  captured: 2026-08-07T01:20Z
  run: "seed=20261104 draws=1500"
  tolerance: 2
  used_in: "claims/zille-490k — the 'short by 39 seats' argument"

headline_overhang_party:      # strings too
  mode: fixed
  value: "the ANC"
  source: model:p_excessive_by_party.argmax
  captured: 2026-08-06
  tolerance: exact
  used_in: "headline + standfirst"

laingsburg_da_wards:          # external fact, never drifts
  mode: fixed
  value: 3
  source: "external:IEC Laingsburg 2021 Seat Calculation Detail"
  captured: 2026-08-05
```

**Renderer** — a `{{token}}` substitution pass in `src/render_sheet.py`
(which already owns the `__GEN_*__`/`__BALLOTS_*__`/`__REGIMES_*__`
markers), extended to `render_map.py`, `build_site.py` and the interactive
template. Rules:

- `free` → live value each build. `fixed` → pinned value, always.
- An **unresolved token fails the build** — no silent blanks.
- Every rendered token emits `<span class="stat" data-src data-when
  data-mode [data-live]>`, so pinned figures read plainly but reveal
  "pinned 7 Aug 2026 · model now says 103 · 1,500-simulation run" on
  hover/tap. One small shared JS + CSS block, reused site-wide.
- **Drift report** on every build: token, pinned vs live, delta vs
  tolerance, and the article that depends on it. Warns, never blocks;
  `--strict-drift` available for CI. The daily newsdesk agent runs the same
  report and opens a PR when an argument's premise has moved.

**Migration**: convert the ~40 restatements the inventory found, defaulting
to `free` for "what the model says" statements and `fixed` for anything
inside a dated argument (the whole claims block: 39 seats, 985k/1.29m/644k,
524k/41%, 97 of 136, 62 wards, ~47 seats, 3-in-100). Fix the four stale
values above in the same pass.

## Step 1 — City configuration (the spine)

`cities/<code>.toml` + `src/cityconfig.py`; every script takes `--city`,
default `joburg`, so current commands keep working.

- **identity** — code, slug, display name, IEC province code (traps: `WP`,
  `KN`, `NMA`), ward-ID prefix (Joburg `798`, Tshwane `799` —
  `byelections.py:54`), subdomain, palette tokens.
- **structure, derived not typed** — council size, majority, ward and VD
  counts, registration, and that city's official quota/A/seats per election
  for `validate_seats.py`. New `src/derive_city.py` emits these from the
  city's own IEC files. (Council size isn't constant even within a city:
  Joburg was 260 in 2011.)
- **party universe** — replaces the **four parallel copies** of
  chips/names/order (`export_interactive.py`, `render_sheet.py`,
  `render_map.py`, template JS).
- **judgements** — blocs, `PLAN_BOUNDS`, `theta_mode`, `individual_theta`,
  bloc-shift ranges, alphas, contestation uplifts, entrant slot, `w_bye`.
  Each carries a `note` recording its evidence; `derive_city.py` *proposes*
  values from that city's NPE→LGE history for a human to accept or override.
  These are the highest-risk items — applied blind to another city they
  produce plausible, wrong output rather than crashing.
- **`[newsdesk]`** — search terms, local outlets, party figures.

Plus a single path helper replacing the ~14 hard-coded `_JHB_` filename
literals, and `data/processed/<city>/…` outputs.

## Step 2 — Kill the duplicate-constant drift

The template hand-mirrors `montecarlo.DEFAULTS` in three places (JS
constants, 19 slider `min`/`max`/`value` triples, `DEFAULT_CFG`) and
`leverage.py` keeps a fourth (`THETA_CENTRAL`). They have **already
drifted**: `POLLING_SPAN` is 4 in the JS and 8.0 in Python. Make
`build_interactive.py` generate the JS constants and slider attributes from
the city config, as it already injects `DATA`/`REF`. Prerequisite for
multi-city; a live-bug fix for Joburg.

## Step 3 — Content split

- `content/<city>/*.md` for copy that must vary (headline, standfirst, the
  city's "surprise" story, landscape); shared copy (how-to-read,
  why-simulations, methodology) stays central and tokenised.
- `content/<city>/claims.yaml` — the claims section becomes data (quote,
  speaker, party, outlet, url, date, the model quantity that tests it,
  verdict, body), each verdict's figures registered as pinned stats with
  their run. The newsdesk can then propose a claim as a data diff.
- Map chrome to config: `render_map.py`'s `DISTRICTS` labels, `COS`
  (derivable from centroid), `ANG` (aesthetic).

## Step 4 — Portal + deployment

- `src/build_portal.py` → `site/index.html` at `whysoserious.city`: a card
  per city (live / in preparation) showing its current headline number.
- One Worker, hostname → `site/<slug>/` (static assets can't do host-based
  rewrites, so a small Worker script with an assets binding); routes per
  subdomain; `joburg.whysoserious.city` unchanged. Nav links are already
  relative, so subdirectories work as-is.
- Per-city `og:url`/canonical — also fixes the X-card mismatch.
- `python src/build_all.py --city tshwane` = ingest → model → renders →
  site, one command.

### Staging (decided 2026-08-07)

A **separate staging site, not merely a `[env.staging]`**. With a portal plus
per-city subdomains served by one Worker doing hostname routing, an
environment would need a parallel set of hostnames
(`joburg-staging.`, `tshwane-staging.`…) to exercise that routing at all; one
separate staging Worker serving the same `site/` build tests the routing in
one place, and gives the strict-token build and the drift report somewhere
real to fail before the public sees anything.

*Trap to remember*: wrangler environment config is **not** fully inherited —
top-level `[assets]`, `routes` and `vars` must be restated under the env
block. That is the same class of quiet failure as the routes-above-`[table]`
bug already in this repo's git history. Cloudflare *versions/preview URLs*
are useful for eyeballing but awkward on a custom-domain Worker.

Staging sends `X-Robots-Tag: noindex` via the existing `_headers` file. The
current `/dev/` convention on the live Worker is zero-config and useful but
publicly reachable and crawlable — it gets a `robots.txt` disallow now, and
is retired or protected once staging exists.

**Domains**: `whysoserious.city` (portal) and `whysoserious.club` are ours on
this Cloudflare account. `whysoserious.org` sits on GoDaddy nameservers and
is **not** ours to use — do not wire anything to it.

## The three standing policies (decided 2026-08-07)

**1. Findings are re-run per city, never transferred.** "Turnout is
second-order — persuasion, not mobilisation" and "blocs don't leak (587,000
votes went to the couch)" are *measured Johannesburg results*. Each city
publishes only what was measured there, which costs a real analysis pass per
city (the leverage test, the bloc-leakage measurement) and is the only
version that cannot be wrong. If Tshwane's answer differs from Joburg's,
that difference is itself the story. Components transfer; conclusions do not.

**2. The launch gate is hard.** A city page goes public only when all three
hold:

* `validate_seats.py` reproduces that city's published 2011, 2016 and 2021
  councils exactly — quota, vote totals, every party;
* every judgement in its config has been reviewed and carries a `note`, with
  **no inherited Johannesburg placeholders left**;
* `content/<city>/landscape.md` is written.

Claims tested and city-specific presets may follow after launch; those three
may not.

**3. Core sections at launch; the rest earn their place.** Every city ships
with the map, the arithmetic strip, the headline numbers, where the parties
land, who can govern, plus the shared seat-law explainer and how-to-read /
about. The story sections — a "surprise", claims tested, a reservoir-style
finding — appear only when that city actually has one worth telling. No
filler written to fill a slot.

### What is shared vs per-city

| Shared, rendered once | Per city |
|---|---|
| Seat law, excessive-seats clause, Laingsburg precedent | Headline and standfirst |
| The four-regime German comparison | The city's "surprise", if it has one |
| Why simulations, how to read this page | Party universe, blocs, chips |
| Blind-test methodology, model limits | Coalition landscape and named rows |
| The stat-provenance mechanism itself | Claims tested, scenario presets |
| | Map chrome, palette, landscape.md |
| | Every measured finding (see policy 1) |

## Step 3b — Universal vs city-specific, and the city's own narrative

Two editorial questions the code cannot answer, both needed before a city
launches.

**What transfers?** An explicit audit splits the site into *universal*
components (the seat law and the excessive-seats clause, the German
comparison, why-simulations, how-to-read, the blind-test methodology — these
render once and are shared) and *city-specific* ones (headline, the city's
"surprise", party universe and blocs, coalition landscape, claims, map
chrome, palette). The trap to avoid is **transferring findings, not just
copy**: "persuasion, not mobilisation" is a *measured Johannesburg result*.
It must be re-run for each city, never asserted.

**What does the city believe?** `content/<city>/landscape.md`, from a
research pass: who governs and how, live coalition tensions, mayoral
candidates, and the dominant public narrative — then which parts of it are
testable against the model. This drives three things: the claims section,
the newsdesk search terms, and *which scenario presets the interactive
offers*. Joburg's "Every DA voter turns out" has no Tshwane analogue; the
Tshwane equivalents are likelier "the ActionSA coalition holds" versus
"Brink takes it back".

**Social listening** — worth having, but the access is genuinely
constrained, so it gets a feasibility spike rather than a promise. X's API
has been paid-only since 2023 and even the Basic tier is rate-limited;
Instagram's Graph API only reaches accounts you own; Nitter mirrors are
largely dead; scraping either breaches terms and gets blocked. Cheapest
options to test first: `site:x.com` WebSearch queries from the newsdesk
agent (catches indexed, high-engagement posts); SA outlets' own reporting
*of* viral political posts; Reddit's free JSON API (r/southafrica,
r/Johannesburg — genuinely open and genuinely political); the YouTube Data
API's free tier for political-channel comments. Only if those prove thin,
and only if the site ever finds funding, consider paying X.

## Step 5 — Per-city newsdesk

Clone `joburg-daily-newsdesk` (trig_01HaFqN6HCtCDRycukFxsJJ2) per city via
`RemoteTrigger`, staggered 15 minutes, prompt generated from the config's
`[newsdesk]` block, output `newsroom/<city>/YYYY-MM-DD.md`. Digest schema
unchanged (poll drafts, claim candidates without verdicts, MODEL-LOG notes,
PR-gated) **plus the drift report** — so a moved premise becomes a morning
PR rather than a silent inaccuracy.

## Pilot: Tshwane

Config + derive + jacaranda palette + landscape research + first run + human
review of every judgement + newsdesk routine. Known shape from its own 2021
files: **107 wards, 778 VDs**; ANC 34.8% / DA 31.8% / EFF 10.4% / ActionSA
9.3% / **VF+ 7.8%** — a materially different party universe (VF+ first-class,
PA marginal), and a live ActionSA-led ANC+EFF coalition under public strain,
which is the story.

## Verification

- **Joburg-invariance gate (the important one)**: after every refactor step,
  rebuild Joburg and assert model outputs unchanged — `forecast_summary.json`
  identical, DA 79 / ANC 74, P(ANC+DA) 87.6%, P(excessive) 96.3% — and that
  page diffs contain only intended changes. The engine may be generalised;
  the forecast may not move.
- **Token gate**: build fails on any unresolved `{{token}}`; drift report
  printed and reviewed; grep built HTML for bare digits that should be
  tokens.
- **Per-city correctness**: derived council/ward counts must match that
  city's IEC Seat Calculation Detail, and `validate_seats.py` must reproduce
  its published 2011/2016/2021 councils exactly — the test that validated
  Joburg.
- **Structure gate**: tag-balance + duplicate-id validator over every built
  page; `node --check` on extracted JS (both already in use).
- **Deploy gate**: portal and both subdomains resolve; per-city og tags
  correct; cache-busted probes for each city's headline numbers.

## Progress

| Step | State |
|---|---|
| 0 · Stat registry (free/fixed + drift report) | **done** — 39 tokens, drift + unresolved gates tested |
| 1 · City config spine + `derive_city.py` | **done** — Joburg config generated from the constants; byte-identical run |
| 2 · Generated JS constants / sliders | **done** — engine-diffed across four scenarios |
| 3 · Content split + claims as data | **done** — map chrome to config, claims.toml; per-city copy fragments still to come with the first non-Joburg page |
| 4 · Portal + Worker routing | **done** — portal live at the apex, hostname routing, per-city canonical URLs, `build_all.py`; staging still outstanding |
| 5 · Per-city newsdesk | not started |
| Pilot · Tshwane | config + map block done; **pipeline paths now city-agnostic**, so the blocker is the judgement review and the launch gate |

**Standing rule, held at every step so far:** Johannesburg's forecast has not
moved — byte-identical `forecast_summary.json`, byte-identical map, and the
browser engine returns identical results across four scenarios.

**Platform gotchas found while wiring the Worker**, both worth remembering:
with an assets binding the platform serves a matching asset *before* the
Worker runs, so hostname routing needs `run_worker_first = true`; and
fetching `/portal.html` triggers the extension-stripping 307, which moves
the visitor off the apex URL — request the clean path. Each new city needs
its own `custom_domain` route entry and DNS record; a wildcard route would
not get a certificate.

**What now stands between the framework and a Tshwane page** is no longer
code: it is the judgement review (`cities/tshwane.toml` still carries
Johannesburg placeholders), `validate_seats` proving the 214-seat council,
and `landscape.md` — the three conditions of the launch gate.

Recorded in `MODEL-LOG.md` §1.24. Data acquisition for all eight metros is
already complete — see `SOURCES.md`, "All-metro sweep".
