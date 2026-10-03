-- joburg-entries: one row per sealed forecast (owner, 2026-10-03). The site's
-- Worker inserts it when it seals a link (src/share-edge.js storeEntry);
-- src/rank_entries.py ranks every row on results night.
--
-- Exactly what is stored, and nothing else: no IP address, user agent, cookie
-- or account (docs-public/privacy.md, "Forecasts entered"). The columns are
-- share-edge.js ENTRY_COLUMNS; tests/test_entries.py holds the two together.
--
-- Applied by the owner (wrangler.toml, the ENTRIES note):
--   npx wrangler d1 migrations apply joburg-entries --remote
CREATE TABLE entries (
  seal_id     TEXT PRIMARY KEY,      -- the signature half of the link's `s`
  sealed_at   INTEGER NOT NULL,      -- the seal's time, seconds since 1970 UTC
  label       TEXT NOT NULL,         -- the name the reader typed, or ''
  model_ref   TEXT NOT NULL,         -- forecast.json model_ref at sealing
  context_ref TEXT NOT NULL,         -- the link's `c`
  state       TEXT NOT NULL,         -- the link's `f`, as sealed
  forecast    TEXT NOT NULL          -- `f` decoded: the JSON score_forecasts scores
);
