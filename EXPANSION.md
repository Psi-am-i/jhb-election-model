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
| 0 · Stat registry (free/fixed + drift report) | not started |
| 1 · City config spine + `derive_city.py` | not started |
| 2 · Generated JS constants / sliders | not started |
| 3 · Content split + claims as data | not started |
| 4 · Portal + Worker routing | not started |
| 5 · Per-city newsdesk | not started |
| Pilot · Tshwane | not started |

Recorded in `MODEL-LOG.md` §1.24. Data acquisition for all eight metros is
already complete — see `SOURCES.md`, "All-metro sweep".
