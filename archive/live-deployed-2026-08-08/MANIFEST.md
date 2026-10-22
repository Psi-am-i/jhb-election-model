# The pages that were live when the ledger was backfilled

Fetched 2026-09-26 from the running site. `wrangler deployments list` puts the
last deployment of this Worker at **2026-08-08T17:29:45Z**, and that is the
`published_at` on every backfilled row.

⚠️ **No commit in this repository produces these bytes.** All 77 commits that
touch `site/index.html` were hashed against the live file and none matches, so
the build that is serving readers was never committed. That is the reason these
four files exist: they are the only copy.

⚠️ **`data-when` is per token, not per page**, and it is the model's input
cut-off rather than a publication date: 22 of the 27 tokens say 2026-08-07,
three say 2026-08-04, one 2026-08-05, one 2026-08-06. Each row carries its own.

`publication.backfill()` refuses a row whose page it cannot re-hash, so these
bytes are committed rather than kept in a scratchpad.

⛔ Do not reformat, re-save, re-fetch or rename these files. The sha256 below is
the row identity (`r-preledger-<first 12 hex>`) and the path is stored in every
row's provenance.

| page | URL | bytes | sha256 |
|---|---|---|---|
| `index.html` | https://joburg.whysoserious.city/ | 149,773 | `fb020f7081faac5967ff42ede75b34b8258e605f411a82cf74f8763da2fdd6f4` |
| `methodology.html` | https://joburg.whysoserious.city/methodology | 23,876 | `0600c22919ce7281f97627df2fdba0e8c3e6c624f23a073b3d8cd6dcb8086135` |
| `review.html` | https://joburg.whysoserious.city/review | 14,020 | `8e85b1dbcdb57751a77aa421ac4a5ddf2337463add87e8e205388ec245d52ba3` |
| `sources.html` | https://joburg.whysoserious.city/sources | 14,004 | `f769d2d2e77503b778e08e737678b844b9bc0bc6ac19e16f8d9c7c960e8d606b` |

Four pages, because that is the whole live site: `/forecast`, `/about`,
`/corrections` and `/nobody-will-win` return 404 there. They are new in the
build that has not yet shipped. `review.html` and `sources.html` carry no
tokens at all; the 27 rows come from `index.html` (25) and `methodology.html` (2).
