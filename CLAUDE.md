# Project notes for Claude Code sessions

## Daily newsdesk routine (`joburg-daily-newsdesk`, cron `30 4 * * *`)

This repo is scanned daily by a scheduled routine (past output in
`newsroom/*.md`) that opens a PR when it finds anything model-relevant. It
never applies changes directly — a human reviews everything via the PR.

**Known gap, fixed by this note:** once a newsdesk PR was opened, the routine
only messaged its owner again if something on the PR *changed* (a CI
failure, a review comment). An untouched PR — nobody looked at it, nothing
changed — went completely silent. One sat open and unreviewed for 5 days
with zero reminder before this was caught.

**Every run of the daily newsdesk routine, quiet news day or not, MUST:**

1. List open pull requests whose branch starts with `newsdesk/` (state=open),
   noting each PR's number, title, and age in days since creation.
2. Send exactly one PushNotification for the run, leading with that backlog
   status as the first sentence — e.g. "2 newsdesk PRs still awaiting
   review: #1 (5 days old), #3 (1 day old)." or "No open newsdesk PRs — all
   caught up." — followed by today's result (new PR opened + link, or
   "Quiet day — nothing model-relevant.").

This backlog line goes out **every day** regardless of whether today's news
scan found anything, until the backlog is empty. That's the whole fix: an
open PR must never again go unmentioned just because nothing changed on it.
