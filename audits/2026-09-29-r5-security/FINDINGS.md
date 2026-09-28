# R5 findings: summary filed by the lead (2026-09-29)

The full report is the reviewer's hand-back message; this file records its
findings so they survive the session. Brief: `brief.md` (committed at
`6c96285`).

**Checked by the lead in the code:**
* finding 1: `worker-api/src/lifecycle.js:79` marks the post-election job done
  only when `failed === 0`;
* finding 6: `worker-api/src/consent.js:30` rejects keys the consent page
  sends (`show_name`, `display_name`, `email`).

BLOCK = blocks launch, FIX = fix before launch, LATER = after launch.

| # | severity | finding |
|---|---|---|
| 1 | FIX | Post-election mail re-sends hourly on any failure; deletion then never runs; one sequential cron will not scale |
| 2 | FIX | Unverified or absent contacts are never messaged, then deleted; the confirmation link is not built; tests seed only verified users |
| 3 | **BLOCK** | Special personal information may be transferred abroad: no D1 jurisdiction chosen, disclosure vague, POPIA s57(1)(d)/s72. Counsel to answer. Processors (providers, Turnstile, Workers Logs) undisclosed |
| 4 | **BLOCK** | No privacy notice; retention "[owner to decide]"; `POST_ELECTION_MESSAGE_AT` and `DELETION_AT` empty, so retention is unlimited |
| 5 | FIX | Consent wording contradicts the code: the post-election message goes regardless of ticks; "anyone with the link" and the analysis purpose are not stated; "email needed to delete" is untrue |
| 6 | FIX | Consent screen and server disagree: every consent currently returns 400; the UI offers magic-link (dropped) and omits Microsoft |
| 7 | FIX | A typed, unverified address could send mail to a third party; double opt-in needed |
| 8 | FIX | Deletion leaves copies in D1 Time Travel, Workers Logs, and browser and platform caches (immutable PNGs); disclose the windows |
| 9 | LATER | An R2 card can be orphaned by a render racing a delete |
| 10 | FIX | Reply tokens and OAuth codes land in Workers Logs URLs |
| 11 | LATER | Facebook protected by `state` only; add PKCE by hand |
| 12 | LATER | Unbounded chunked bodies on public form endpoints |
| 13 | LATER | No CSP, `frame-ancestors` or `nosniff` on HTML pages |
| 14 | LATER | Forecast cap race; quota burned on refusal (owner decided it should not be); reports not Turnstile-guarded; card renders not rate-limited; rate-limit key relies on `cf-connecting-ip` surviving the forward |
| 15 | LATER | Expired sessions never purged |
| 16 | FIX | `.gitignore` covers only 3 of 8 copied Python files; `sync_seats_py --check` passes on a partial copy |
| 17 | sound | Lock time and the append-only consent log are correct; the consent log is destroyed with the account (counsel to confirm) |

**Sound:**
* sessions and cookies; CSRF by `Origin`; return paths; ownership;
* the validator (rebuilds from the schema, 16 KB cap, `__proto__` blocked);
* signed tokens; the Facebook deletion HMAC; the Apple stub returning 501;
* the Python Worker has no routes;
* no secret values in any file;
* data minimisation.

**Not assessed:**
* the Python Worker actually running;
* real provider responses;
* Workers Logs fields and Time Travel retention;
* the site-Worker forward (not written);
* the email service;
* production rate limits;
* any legal conclusion.
