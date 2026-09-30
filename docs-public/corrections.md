# Corrections

A **correction** means the page was wrong when it was published. That is different from an **update**, where the
model or the world moved and the earlier statement was true on its date;
updates appear beside the original as a dated "what the model says now" box.

Nothing is removed from this list.

## 30 September 2026 — a claim's title said something its test did not

<span data-asof="2026-09-30">**What was wrong.** One tested claim was titled *"A
government can be formed without the EFF or MK"* and given the verdict "a coin
flip". The test behind the verdict was narrower: whether a council without the
ANC, the EFF and MK reaches a majority. Almost every simulation has some
majority without the EFF and MK, so the title and the verdict disagreed.

**What changed.** The title now says what was tested: *"The DA can govern
without the ANC, the EFF or MK"*. The verdict and its figures are unchanged.
The quote it tests is now dated 13 September, the date of its cited report;
it was shown as 11 September.</span>

## 30 September 2026 — publication dates on the tested claims

<span data-asof="2026-09-30">**What was wrong.** Three tested claims were
labelled as published on 18 September, and one on 7 August. The deploy record
shows no publication on 18 September: those three first reached readers on 26
September, and the other on 8 August. It is the same class of error as the
27 September correction below.

**What changed.** Each claim's published date is now taken from the
publication ledger. The dates beside the claims on the home page are the dates
of the quotes, and now say so.</span>

## 30 September 2026 — "the most reliable majority" left out a word

<span data-asof="2026-09-30">**What was wrong.** The claim *"A government can be
formed without the EFF or MK"* said
that the DA and the ANC together are "the most reliable majority in the city
that does not involve the EFF or MK". The same box reported a more reliable one:
every party except the ANC, the EFF and MK together, which also excludes the EFF
and MK. What was meant, and what the numbers support, is that DA + ANC is the
most reliable **two-party** majority: on 27 September it reached a majority in
44% of simulations.

**What changed.** The sentence now says "the most reliable two-party majority
in the city". The figures in the claim are unchanged by this correction.</span>

## 27 September 2026 — three arrows on "Nobody will win Johannesburg" pointed the wrong way

<span data-asof="2026-09-27">**What was wrong.** Four figures on that piece were
labelled *as published on 31 August 2026*. They were not published on that date
or any other. They were read out of a build that was never deployed, and the
page readers actually had from 8 August until 26 September carried different
numbers.

**What the page said, and what it should have said.** The figures are shown
frozen, with an arrow where today's model disagrees. Three of those arrows
pointed upward against numbers that had in fact fallen:

| | the page said we published | we actually published | today |
|---|---|---|---|
| the ANC's stronghold wards | 55 | **74** | 61 |
| its proportional entitlement | 54 | **65** | 58 |
| how often the excessive-seats clause fires | 58% | **96%** | 65% |
| the DA as largest party | 71% | **62%** | 47% |

So a reader was told the ANC's ward wall had grown and the clause had become
more likely. Both had weakened, and the clause sharply — from almost every
simulation to about two in three. A sentence beside them read *"Still the ANC's
usual condition, and a stronger one"*, which was false in the same direction.

**How it happened.** The convention of freezing a piece's figures was adopted on
17 September, and it took the last build in the repository to be the last thing
published. That assumption went unchecked until 26 September, when archiving the
live pages showed that no commit here produces the bytes readers were being
served. That finding was written into the archive, the publication ledger and
the publishing rules — and not into these four figures, which had already been
frozen against the wrong source.

**What changed.** The four are re-sourced to the publication ledger, which
records what was served and when, and the arrows now compare against it. The
sentence is rewritten. Five articles dated 31 August are re-dated 8 August,
checked against the archived page rather than assumed. And the rule is now
explicit where the figures live: the source of a frozen figure is the ledger,
never a build.</span>

<span data-asof="2026-09-23">**Nothing was outstanding when this page was checked on 2026-09-23.** Checked against
the published page on 2026-09-23: the three entries this page carried in draft
all described figures that were never public. They came from a local build on
17 September that was never deployed — the "smaller parties" bar said 15 seats
on the published page, not 39; the published page has no two-ballot bars at
all; and its tiles and its article agree with each other at 62%. A correction
is for what a reader saw.</span>

<!-- The passage above is wrapped as a dated statement because that is what it
     is: a record of what the published page showed on 2026-09-23. Its figures
     are not model output and must not become tokens — a token would recompute
     them and the sentence would then describe today's page, not the one the
     correction is about. Without the wrapper all four blocked the build. -->

The defects those drafts described were real and are fixed — figures written by
scripts, medians summed as if they added up — and they are recorded in
`MODEL-LOG.md`, which is the technical record. They are not corrections,
because nothing wrong reached a reader.
