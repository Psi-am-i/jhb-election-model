# Corrections

A **correction** means a page was wrong when it was published. An **update**
means the model or the world moved; it appears beside the original as a dated
"what the model says now" box.

Nothing is removed from this list.

## 30 September 2026 — a claim's title said something its test did not

<span data-asof="2026-09-30">**What was wrong.** A tested claim was titled *"A
government can be formed without the EFF or MK"*, with the verdict "a coin
flip". The verdict tested something narrower: whether a council without the
ANC, the EFF and MK reaches a majority. Almost every simulation has a majority
without the EFF and MK.

**What changed.** The title now reads *"The DA can govern without the ANC, the
EFF or MK"*. The quote is dated 13 September, the date of the report it cites;
it was shown as 11 September.</span>

## 30 September 2026 — publication dates on the tested claims

<span data-asof="2026-09-30">**What was wrong.** Three tested claims were
labelled as published on 18 September, and one on 7 August. Nothing was
published on 18 September. The three first reached readers on 26 September,
and the fourth on 8 August.

**What changed.** Each claim's published date is now taken from the
publication ledger. The date beside each claim on the home page is the date of
the quote, and is labelled as such.</span>

## 30 September 2026 — "the most reliable majority"

<span data-asof="2026-09-30">**What was wrong.** We said the DA and the ANC are
'the most reliable majority in the city that does not involve the EFF or MK'.
Many governing majorities occur in most simulations; DA + ANC is only the most
common *two-party* one.

**What changed.** The sentence now says 'the most reliable two-party majority
in the city'.</span>

## 27 September 2026 — three arrows on "Nobody will win Johannesburg" pointed the wrong way

<span data-asof="2026-09-27">**What was wrong.** Four figures on that piece were
labelled *as published on 31 August 2026*. Nothing was published on that date.
The figures came from a build that was never deployed; from 8 August until 26
September readers had different numbers. Each frozen figure carries an arrow
where today's model disagrees, and three of those arrows pointed up against
numbers that had fallen:

| | the page said we published | we actually published | on 27 September |
|---|---|---|---|
| the ANC's stronghold wards | 55 | **74** | 61 |
| its proportional entitlement | 54 | **65** | 58 |
| how often the excessive-seats clause fires | 58% | **96%** | 65% |
| the DA as largest party | 71% | **62%** | 47% |

A sentence beside them read *"Still the ANC's usual condition, and a stronger
one"*. The figures had been frozen against the last build in the repository,
on the assumption that it was the last thing published.

**What changed.** The four figures are taken from the publication ledger,
which records what was served and when, and the arrows compare against it. The
sentence is rewritten. Five articles dated 31 August are re-dated 8 August,
checked against the archived page. The source of a frozen figure is the
ledger, never a build.</span>

<span data-asof="2026-09-23">**Checked against the published page on
2026-09-23: nothing outstanding.** Three draft entries on this page described a
local build of 17 September that was never deployed.</span>

<!-- The passage above is wrapped as a dated statement because that is what it
     is: a record of what the published page showed on 2026-09-23. Until
     2026-10-01 it also quoted that page's figures (typed, not tokens: a token
     would recompute them and describe today's page instead); they were cut as
     describing drafts no reader saw. -->

The defects those drafts described (figures written by scripts, medians summed
as if they added up) are fixed and recorded in `MODEL-LOG.md`.
