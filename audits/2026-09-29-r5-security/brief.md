# R5 blind review brief: accounts, consent, storage and sharing (2026-09-29)

You are reviewing the backend that will let members of the public sign in, save
an election forecast and share it, for joburg.whysoserious.city (the City of
Johannesburg election, 4 November 2026). **You do not have the lead's
reasoning.**

Read only: do not edit any file, do not run `wrangler deploy`, do not create any
Cloudflare resource, do not set secrets, and do not delegate. You may run
`npm test` in `worker-api/`, and `wrangler dev` on port 8802 only (never 8765),
stopping it afterwards.

## What exists

* `worker-api/`: a Cloudflare Worker for OAuth sign-in (Google, Apple,
  Facebook, X and Microsoft, via `arctic`), consent, D1 storage, the share
  pages `/f/<id>`, share images rendered on the server, deletion, a post-election
  message and a lock at polling time. Read its `README.md` first.
* `worker-api/seats-py/`: a Python Worker that recomputes seats with the
  project's own `src/reader_seats.py` and `src/seats.py`.
* `interactive/`: the pages that call it (prototype, placeholder data).
* The owner's decisions: `audits/2026-09-27-interactive-levers/DESIGN-decided.md`
  §9 and §10, and `interactive/BACKEND.md`.

## The owner's requirements

* Keep only a provider handle or id and one contact route, and nothing else.
* Sign-in is needed to save and share, not to create.
* Consent is explicit, with separate unticked opt-ins.
* After the election, each account gets one message asking to delete or to be
  told about the next election; no reply means deletion.
* A saved forecast may reveal political views. That is special personal
  information under South Africa's POPIA.

## What is asked

1. **Security.** Session handling and cookies; the OAuth state, nonce and PKCE
   flow for each provider (including which providers do not use PKCE, and
   whether `state` alone is sufficient there); CSRF on state-changing
   endpoints; input validation, since a forecast is untrusted input; injection
   into server-rendered HTML and the SVG/PNG card; rate limits and quota
   bypass; the service binding to the Python Worker; secret handling (names
   only; check that no value is in any file); caching of deleted content.
2. **Privacy and POPIA.** Is data collection minimal? Does the consent flow
   meet explicit, specific, informed and voluntary consent? Can consent be
   withdrawn? Is deletion complete, including R2 images, caches, logs and
   backups? What does each provider actually return, and is anything kept that
   should not be? Are the data residency and the cross-border transfer
   disclosed? What does the post-election message flow do to people with an
   unverified contact?
3. **Correctness of the contract.** The seat request to the Python Worker
   against the real `src/reader_seats.py` signature; the lock time; the
   append-only consent log.
4. **Anything a hostile tester would try first.**

## Output

Numbered findings, each with its severity (block launch / fix before launch /
later), the file and line, whether you verified it by running or by reading,
and the fix, in under 1,500 words. State plainly what you could not assess.
You are not a lawyer, so mark POPIA points as a practitioner's view, not legal
advice.
