-- R5 findings 1, 2 and 7 (2026-09-29).
--
-- The post-election message is recorded PER ACCOUNT, so a run that is cut off
-- or fails for one address resumes where it stopped and never re-sends to an
-- account already stamped (finding 1):
--   message_sent_at  when the one post-election message was handed to the
--                    mail service, or found undeliverable
--   message_status   'sent', or 'undeliverable' (a permanent per-recipient
--                    failure: a hard bounce or a suppressed recipient). Both
--                    count as "the message went out" for the deletion gate;
--                    a transient failure leaves both columns NULL.
--
-- A contact is stored only once it is confirmed (findings 2 and 7). An address
-- the provider did not verify, or one the reader typed, is not stored: it is
-- carried inside the signed confirmation link, and becomes users.contact only
-- when that link is used. confirm_sent_at records that the one confirmation
-- email for this account has been sent, so no second one goes out.
ALTER TABLE users ADD COLUMN message_sent_at TEXT;
ALTER TABLE users ADD COLUMN message_status TEXT CHECK (message_status IN ('sent','undeliverable'));
ALTER TABLE users ADD COLUMN confirm_sent_at TEXT;

-- Owner, 2026-09-29: no real name is collected or shown. A forecast the reader
-- has not labelled shows a random "<word>-<number>" label (interactive/js/
-- labels.js), assigned once per forecast at creation and kept here, apart from
-- the body, so a reader who clears their own label gets it back. Unique among
-- live forecasts (the insert also refuses a label another forecast typed).
ALTER TABLE forecasts ADD COLUMN default_label TEXT;
CREATE UNIQUE INDEX forecasts_default_label ON forecasts (default_label);
