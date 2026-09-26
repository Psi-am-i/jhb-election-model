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

## 3b. The point of the routine is a DRAFT ARCHIVE, not a reading list

⛔ **A digest nobody turns into anything is the failure mode this whole file
exists to end.** Fifteen were written and none reached the site.

When an item clears the bar in §5 **and** names a quantity this model computes,
the routine writes a **draft article** to `newsroom/drafts/<date>-<slug>.md`, in
the shape the site already takes:

    ---
    title: <the headline, as it would appear on the home page>
    standfirst: |
      <two or three sentences, the shape of an articles.toml standfirst>
    href: <the anchor it would live at, if it belongs inside an existing piece>
    quantity: <the model quantity that decides it, named exactly — e.g.
              P(MK is the largest single party)>
    verified: primary | secondary | blocked
    sources:
      - <url>
    ---

    <the body: what was claimed, by whom, on the record, and what the model
    would have to say for the claim to be true. NO MODEL FIGURES — the routine
    has no forecast and must not invent one. Leave `{{token}}` placeholders
    where a number goes.>

⛔ **The routine never states a model number.** It has no `data/`, no run and no
forecast; anything numeric it wrote about the model would be fabricated. It
names the quantity and leaves the token. Atlas fills it by running the model.

Publishing one on Atlas is then: read it, run the quantity, replace the tokens,
move it into `content/joburg/articles.toml` plus the piece it belongs to, build,
deploy.

---

## 3c. Paywalls: the routine cannot read them, Atlas can

The owner holds a **Daily Maverick** subscription (working) and **News24**
(broken as of 2026-09-26, with support). A cloud session has neither, and three
of every four September runs were reduced to search snippets.

So the split is:

* the routine reads what is open, and marks anything it could not reach
  `verified: blocked`, naming the URL it wanted;
* **a `blocked` item is a queued instruction to Atlas**, where the owner's
  browser is logged in. It is read there, and its `verified:` is upgraded by
  whoever read it.

⛔ **Never upgrade `blocked` to `secondary` because a second outlet repeated the
same snippet.** Two outlets copying one wire is one source.

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
