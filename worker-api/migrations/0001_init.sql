-- joburg-forecasts: accounts, consent log, readers' forecasts.
--
-- What is kept about a person (DESIGN-decided §9, owner 2026-09-28): the
-- provider, the provider's account id, and ONE contact route. No name, photo,
-- friend list, location or IP address. A display name exists only inside a
-- forecast's body, and only when the reader typed one to show on that forecast.
--
-- D1 enforces foreign keys, so deleting a user cascades to sessions, forecasts,
-- reports and quota rows. Consents deliberately have NO foreign key: see below.

CREATE TABLE users (
  id               TEXT PRIMARY KEY,          -- random; never the provider's id
  provider         TEXT NOT NULL CHECK (provider IN ('google','apple','facebook','x','microsoft')),
  provider_sub     TEXT NOT NULL,             -- the provider's stable account id
  contact_kind     TEXT CHECK (contact_kind IN ('email','phone')),
  contact          TEXT,                      -- NULL until one is known
  contact_verified INTEGER NOT NULL DEFAULT 0 CHECK (contact_verified IN (0,1)),
  created_at       TEXT NOT NULL,
  UNIQUE (provider, provider_sub),
  CHECK ((contact IS NULL) = (contact_kind IS NULL))
);

-- The consent log. APPEND-ONLY: one row per decision, per purpose. A
-- withdrawal is a new row with granted = 0; the current state of a purpose is
-- its latest row. wording_version names the consent text the reader was shown.
--
-- No foreign key to users: a cascade would have to pass the no-delete trigger.
-- Instead the trigger refuses to delete a consent row while its user exists,
-- and account deletion deletes the user first, then its consent rows, in one
-- batch (src/deletion.js). The log lives exactly as long as the account.
CREATE TABLE consents (
  id               INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id          TEXT NOT NULL,
  purpose          TEXT NOT NULL CHECK (purpose IN
                     ('store','age18','contact_if_win','updates','next_election')),
  granted          INTEGER NOT NULL CHECK (granted IN (0,1)),
  wording_version  TEXT NOT NULL,
  at               TEXT NOT NULL
);
CREATE INDEX consents_user ON consents (user_id, purpose, id);

CREATE TRIGGER consents_no_update BEFORE UPDATE ON consents
BEGIN
  SELECT RAISE(ABORT, 'consents are append-only');
END;

CREATE TRIGGER consents_no_delete BEFORE DELETE ON consents
WHEN EXISTS (SELECT 1 FROM users WHERE id = OLD.user_id)
BEGIN
  SELECT RAISE(ABORT, 'consents are append-only while the account exists');
END;

CREATE TABLE sessions (
  id_hash     TEXT PRIMARY KEY,               -- sha256 of the cookie value
  user_id     TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at  TEXT NOT NULL
);
CREATE INDEX sessions_user ON sessions (user_id);

CREATE TABLE forecasts (
  id              TEXT PRIMARY KEY,           -- 10 chars base62, crypto random
  user_id         TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  rev             INTEGER NOT NULL DEFAULT 1, -- bumps on edit; keys the card
  body            TEXT NOT NULL,              -- validated JSON (src/validate.js)
  model_ref       TEXT NOT NULL,
  seats           TEXT NOT NULL,              -- JSON from the SEATS service, never from the client
  seats_code_ref  TEXT NOT NULL,              -- which seat code produced `seats`
  hidden          INTEGER NOT NULL DEFAULT 0, -- set by the owner after a report
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL,
  locked_at       TEXT
);
CREATE INDEX forecasts_user ON forecasts (user_id);

-- So /f/<id> can answer 410. Holds the id only: nothing about the person.
CREATE TABLE deleted_forecasts (id TEXT PRIMARY KEY, at TEXT NOT NULL);

-- Reports hold no reporter identity.
CREATE TABLE reports (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  forecast_id TEXT NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
  reason      TEXT NOT NULL,
  at          TEXT NOT NULL
);

-- Per-user daily save count (the Rate Limiting binding's windows are 10 s or 60 s).
CREATE TABLE save_quota (
  user_id  TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  day      TEXT NOT NULL,
  n        INTEGER NOT NULL,
  PRIMARY KEY (user_id, day)
);

-- One-shot scheduled jobs (the post-election message, the deletion run).
CREATE TABLE jobs (name TEXT PRIMARY KEY, done_at TEXT NOT NULL, detail TEXT);
