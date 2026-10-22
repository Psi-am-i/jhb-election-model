# Integration architecture: model, draws, page, accounts, sharing (2026-09-28)

How the pieces being built in parallel fit together:

* the freeze steps F1–F11 (`TODO.md` §0);
* the re-weighting engine (`PLAN.md` beside this file);
* the reader's own forecast and sharing (`interactive/`, prototype under
  construction);
* accounts and storage (not built).

Every interface below has one definition, and every step names what exists when
it is done.

## 1. The shape

```
 ATLAS (Python, gitignored data)                CLOUDFLARE (one Worker)
 ────────────────────────────────                ─────────────────────────────────
 run_model ──(frozen at F11)──┐                  static assets  site/
                              │                    ├ pages (built by build_site.py)
 export_draws.py ─────────────┼─► site/draws/      ├ draws/base.bin + grid/*.bin
 lever_grid.py  ──────────────┘   (+ manifest)     └ py/  reweight.py, seats.py …
                                                           (copied, never retyped)
 build_site.py ── copies src/*.py the page needs ─► site/py/
 deploy_check.py ── gate ───────────────────────► wrangler deploy

                                                 src/worker.js
 BROWSER                                           ├ host routing (today)
 ───────                                           ├ /api/auth/*    OAuth, session
 static first paint (published tokens)             ├ /api/forecast  save / read / delete
 Pyodide (background) runs reweight.py,            ├ /f/<id>        HTML with og: tags
   seats.allocate on the reader's picks            └ /og/<id>.png   rendered from stored data
                                                 D1: users, consents, forecasts
                                                 secrets: wrangler secret put
```

## 2. What depends on the freeze, and what does not

Only one class of saved thing is invalidated by a model change.

| reader artefact | depends on | invalidated by a model change? |
|---|---|---|
| **Own forecast**: 135 ward winners, a PR vector, a coalition | `seats.allocate`, the statutory seat law | **No.** The seat law is statute, not model |
| **Played-with-the-model state**: lever positions | the published draws and the grid | **Yes.** Same levers, different model, different answer |
| **Score of an own forecast** against the model's draws (percentile) | the draws | **Yes** |
| **Score after 4 November** against the result | the result and the frozen scoring rule | No, if the rule is frozen before polling day |

**Consequence.** "Make your own forecast", saving and sharing can launch before
the model is frozen, because a reader's own forecast does not use the model's
draws. What must wait for the freeze is "play with the model" and any
comparison of a reader's map with the model.

Every saved record carries `model_version`, the code hash of the published run,
so a comparison made against a superseded model can say so rather than
silently rescore.

## 3. Components, their one definition, and their contracts

### 3a. Model side (Atlas)

* **F1.** `run_model` records each draw's pool turnouts (agent running now).
  Not a draw change: `tests/test_draw_record.py`.
* **`src/export_draws.py`** (after the freeze). Calls `run_model` directly,
  never `main`. Writes `site/draws/base.bin`: per draw, seats for every
  seat-winning party plus OTHER under the four seat laws, ward winners, PR
  shares and pool turnouts. Also writes `manifest.json`: `artefact_key` (code
  hash, seed, draws, config), column names, party codes and dtypes.
  * **Done when** its seat columns byte-equal `seat_draws.csv` and the
    `regime_*` CSVs, and `declares.py` audits it as a `run`.
* **`src/lever_grid.py`.** The `dirichlet_scale` × `w_bye` cells, same format.
  * **Done when** the default cell byte-equals `base.bin`.

### 3b. Code shared with the browser

* **`src/reweight.py`** is new and pure Python + numpy:
  * turnout tilts: a joint target for all four pools;
  * the poll likelihood: trust 0 means uniform weights;
  * the effective-draw count, and a refusal floor below which a control greys
    out;
  * weighted quantiles and probabilities.
* **`seats.allocate`** turns a reader's picks into seats.
* **The browser runs these files, never a translation.** `build_site.py`
  copies them into `site/py/`. A test asserts each served file is byte-identical
  to `src/` and that the list of copied modules equals what the page imports,
  in both directions (`CLAUDE.md` §4 rule 0).
* **Done when** `tests/test_reweight.py` passes three checks:
  * uniform weights reproduce the published figures exactly;
  * Black African +5pp lands within 2 standard errors of a paired re-run;
  * the same fixture gives the same output under Pyodide as natively. The
    Route B harness pattern, `audits/2026-09-28-route-b/identity.mjs`, is
    reused.

### 3c. The page

* **One page, three routes:**
  * `/play`: the model's controls;
  * `/make`: the reader's own forecast;
  * `/f/<id>`: a shared forecast.
* **Built by `build_site.py`** from `interactive/`, so the number gate and
  `deploy_check` see it like every other page.
* **First paint is static.** Published tokens, no Pyodide. Pyodide loads behind
  it and the controls unlock when it is ready. The untouched `/play` page *is*
  the published forecast.
* **The number gate.** Figures the page computes live are not typed figures.
  The gate has to recognise the page's computed regions, the way it recognises
  `data-mode="generated"` tokens today, or the deploy will refuse the page.
  * **Done when** `build_site.py --out <scratch>` stamps `blocking=0` with the
    interactive pages included.

### 3d. Accounts, storage and sharing (the Worker)

Extend `src/worker.js` rather than add a second Worker: one deploy, one gate.

* **Auth.** OAuth code flow per provider plus an email magic link. The
  session is a signed HttpOnly cookie. Client secrets go in
  `wrangler secret put`, never in `wrangler.toml` (`~/CLAUDE.md` rule 4).
* **Storage, D1:**
  * `users`: id, provider, provider_id, email, display_name, created;
  * `consents`: user, purpose, wording_version, granted_at, withdrawn_at;
  * `forecasts`: id, user, payload, model_version, created, deleted_at.
* **One schema for a forecast.** `forecast.schema.json`, generated at build
  time from the roster and the ward list, and used by both the page and the
  Worker. A forecast is untrusted input. Reject:
  * ward calls outside the 135 wards or the roster;
  * a PR vector that is not a distribution;
  * a coalition that is not a subset of the parties.

  Also rate-limit per user and per IP.
* **Share URL and preview.** `/f/<id>` serves HTML with `og:title`,
  `og:image` and `twitter:card` set on the server; social crawlers do not run
  JavaScript. `/og/<id>.png` is rendered **on the server from the stored,
  validated forecast** with an SVG-to-PNG library in the Worker, and cached in
  R2 or KV. **Never accept an uploaded image**: a reader-supplied PNG could
  contain anything, published under our name.
* **Deletion.** `DELETE /api/me` removes the user, their forecasts and their
  preview images. Withdrawing consent is honoured on the next request.

### 3e. Scoring (must be frozen before 4 November)

* **`src/score_forecasts.py`**, one function scoring the model's forecast and
  every reader's by the owner's three measures (`DESIGN-decided.md` §5):
  * absolute seat error per party;
  * ward winners called;
  * the ward-versus-PR split.
* **Needs** the result-ingest path and the party-name mapping: the IEC spells
  four Johannesburg parties differently from our baseline files.
* **Done when** it is committed, tested on the 2021 result as if it were 2026,
  and its code hash is recorded before 4 November.

## 4. Privacy (POPIA): must be decided before sign-in goes live

* A named person's election forecast may be special personal information
  ("political persuasion"). The consent screen asks separately, both boxes
  unticked, for "contact me if my forecast wins" and "send me updates", and
  states the purpose, the retention period and how to delete.
* **For the owner, not for an agent:**
  * a privacy notice;
  * the retention period;
  * the prize rules;
  * whether the responsible party must register an Information Officer;
  * whether storing forecasts against identities is acceptable at all.

  The last reverses PUBLISHING-BACKLOG §10's decision not to store readers'
  forecasts, and is recorded as the owner's decision of 2026-09-28.

## 5. Lanes, in parallel, and the critical path

| lane | work | blocked by | can start |
|---|---|---|---|
| **M** model | F1–F11 | owner's F3–F6 decision | now (F1, F2 running) |
| **E** engine | `export_draws`, `lever_grid`, `reweight.py`, `site/py/` copy and test | nothing: build against today's model, re-run after the freeze | now |
| **P** page | `interactive/` prototype, then into `build_site.py` | the prototype (running now) | now |
| **S** server | Worker API, D1, OAuth, og rendering | provider choice and secrets; the POPIA decisions | after the owner's decisions |
| **R** scoring | `score_forecasts.py`, result ingest, name mapping | nothing | now; deadline 4 November |

**Critical path to "make your own and share" live:** P → S → deploy. It needs
no model freeze. **To "play with the model" live:** M (freeze) → E (re-run on
the frozen model) → P → deploy.

**Collision rules while lanes run in parallel** (`CLAUDE.md` §3):
* only lane M edits `src/montecarlo.py` or `src/pools.py`;
* lane E adds new modules and never edits `montecarlo.py`;
* nobody measures while M re-emits;
* one full suite run per commit, on a settled tree.

## 6. Decisions only the owner can make

1. **The model fixes.** F3–F6 in full (freeze about 7 October), or F3 + F5
   only (1 October).
2. **Accounts.** Which sign-in providers.
3. **Privacy and prizes.** Retention period, prize rules, the privacy notice,
   and the POPIA position.
4. **Launch order.** Whether "make your own and share" launches before the
   freeze, as §2 allows, or together with "play with the model".
