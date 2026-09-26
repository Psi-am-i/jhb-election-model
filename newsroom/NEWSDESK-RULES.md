# The newsdesk routine's rules

**This file replaces the pull-request workflow.** It is the operating contract
for the daily cloud routine that scans for model-relevant news. The routine runs
in Anthropic's cloud with its own checkout; it cannot see Atlas.

⛔ **Development happens on Atlas.** GitHub is a delivery channel for the
routine's output and nothing else. Nobody reviews pull requests there, which is
how thirteen digests sat unread for up to 49 days.

---

## 1. Where a digest goes

**One long-lived branch, `newsdesk`. No pull requests, ever.**

Each run commits to `newsdesk`:

* `newsroom/<YYYY-MM-DD>.md` — the digest, appended, never rewriting an earlier one;
* `newsroom/INDEX.md` — one line per digest (see §4).

The routine **never** commits to `main`, never opens a PR, and never touches a
model file, a page, `polls.json`, `MODEL-LOG.md` or anything under `src/`. It
proposes; Atlas disposes.

Pulling a day's work on Atlas is one command:

    git fetch origin newsdesk && git checkout origin/newsdesk -- newsroom/

---

## 2. Notification: every run, news or not

**Exactly one PushNotification per run**, and its first sentence is the state of
the queue, not today's news:

> `3 digests unread on Atlas (oldest 4 days). Today: new Ipsos CoJ poll, ANC 31 / DA 27.`
> `0 digests unread. Today: quiet — nothing model-relevant.`

The unread count comes from `INDEX.md` (§4), which the routine reads at the
start of every run.

⛔ **NEVER CREATE A FOLLOW-UP ROUTINE, REMINDER OR CHECK-IN.** This is the rule
that matters most, and it is written from the failure it prevents. On
2026-09-20 the routine opened its last digest and then scheduled a one-shot to
re-check that pull request; each run re-armed the next *"silently at a daily
cadence"*. Eleven of them fired. No digest was produced for six days, and
nothing said so, because "silently" was the instruction. The daily
notification in this section is the only reminder mechanism, and a run that has
nothing to say still says it.

---

## 3. What a digest must contain

Unchanged from the old rules, plus a closing block in a fixed shape so a human
on Atlas can act without re-reading the argument.

Every digest ends with **READY TO APPLY**, listing zero or more items. Each item
is one of three kinds, and carries its verification state:

    ### READY TO APPLY
    - kind: poll | claim | note
      target: polls.json | forecast-sheet.html claims band | MODEL-LOG.md
      verified: primary | secondary | blocked
      source: <url of the primary release, or the outlet if that is all there is>
      body: |
        <the exact entry, ready to paste — a polls.json object, a claim
        with the model quantity that tests it, or a dated MODEL-LOG note>

`verified: primary` means the routine read the issuing body's own release.
`secondary` means an outlet reported it. `blocked` means the routine could not
reach the source at all and is passing on a search snippet.

⛔ **A figure a session could not reach the source for is `blocked`, and says so
in the body.** Three of every four runs in September were limited to snippets
because the news domains are outside the egress allowlist. Calling that
`secondary` would launder it.

---

## 4. `newsroom/INDEX.md`

The routine appends one row per digest and never edits an existing one. The
**status column belongs to the human on Atlas**, who sets it there and commits:

    | date | headline | status | READY TO APPLY |
    |---|---|---|---|
    | 2026-09-20 | CoJ PR-ballot count disputed, 82 vs 75 | new | 1 note |

`status` is `new`, `used` or `discarded`. The routine counts the `new` rows for
its notification and changes nothing else in the file.

---

## 5. Scope

Model-relevant means: a CoJ poll; a claim by a named party figure that names a
quantity this model computes; an IEC decision that changes the ballot, the
roster or the roll; a candidate-list change. Everything else is a one-liner
under "Other developments" or is left out.

Johannesburg is the forecast. Other metros are recorded only where the portal
covers them, and are never mixed into a CoJ item.
