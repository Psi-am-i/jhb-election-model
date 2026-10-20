# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to **Answered** with the date and the
answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG) is named.

Last updated: 2026-10-21.

---

## Open

### 1. Your party calls

**Context.** The party sheet (https://claude.ai/artifact/MvLaG1WzrzwVmq7driyMAb)
lists every party on Johannesburg's 2026 ballot with the model's expected share
and range. A party call is your judgement that the model has a party wrong
(too high, too low, too narrow). None is entered yet. Each call you make goes
into `judgements/joburg-2026.toml` with your reason, is listed in
JUDGEMENT-CALLS.md, and the forecast is run and reported both with and without
your calls.

**Your question (2026-10-21): how does ActionSA go from 18.1% to 12.5% if it is
sized on 2021?** The steps, from the model's trace of today's Johannesburg
2026 run (5,000 simulations, list vote):

| step | ActionSA | what happens |
|---|---|---|
| 2021 list vote | 18.1% | the starting record |
| carried to 2026 | 13.1% | multiplied by 0.72: how much of its share a party keeps from one local election to the next. ActionSA has stood in only one local election, so it takes the record's typical value for a party of its size (from 292 past party-metro cases) |
| by-elections | 14.7% | four contests imply 18.9%, capped at 16.3%, blended at ½ |
| level shrink | 14.5% | |
| the parties' shares made to add to 100% | 12.6% | every party's level is set on its own, and together they add to 114.6%, so each is divided by 1.146 |
| simulations | 12.7% average, 90% range 8.4%–17.9% | |

The step that does most of the work is the 0.72: 18.1% × 0.72 = 13.1%. It is
the record's typical value, applied because ActionSA has no
second local election of its own. Its 2024 national vote in Johannesburg,
5.4%, is not used: the model reads ActionSA's 2026 level from its local
record only. A party call would be the place to say ActionSA keeps more (or
less) of its 2021 vote than the average party.

**Gates.** The final rebuild of the forecast inputs.

### 10. Letting readers make the judgement calls

**Context.** You asked (2026-10-21) whether readers could make calls like
these on the site: "part of judgement calls we make and they can make." It is
possible. The interactive already re-seats a council from a reader's own
picks. A judgement-call control would let a reader change a party's starting
level (for example, how much of its 2021 vote it keeps) and see the forecast
redrawn. Two constraints apply: the same control has to be offered for every
party (your rule, no party singled out), and the redraw has to happen from the
published simulations in the browser, because the full model does not run
there.

**Options.** (a) Build it after go-live, as a new site feature with a brief
first (the usual process). (b) Build it before go-live, which delays go-live
by the brief, the build and the test site round.

**Recommendation.** (a).

### 9. Separate by-election weights for small and large parties

**Your answer (2026-10-21):** one weight, ½, for every party, provisional on
one measured cycle.

**New evidence since you answered: the checker found my size classes were
not the model's.** The model puts a party with no 2021 list vote in the class
of its 2024 national share; my analysis put every such party under 1%, and it
also counted parties the by-elections never reached. Re-done with the model's
classes, counting only parties the by-elections reach:

| class | best-fitting weight | range, leaving one metro out | party-metros |
|---|---|---|---|
| under 1% of the previous vote | 0.91 | 0.81 to 1.80 | 6 (ACDP in three metros, VF Plus, ATM, Justice and Employment) |
| 1% and over | 0.32 | 0.16 to 0.57 | 22 |

The two ranges do not overlap, and the rule written before the run said
separate weights are recommended when they do not. Run through the full
model (summed list-vote error over the eight metros, 2021; the weights were
fitted on the same metros, so this is in-sample):

| weights | summed list-vote error (points) |
|---|---|
| ½ for every party | 21.78 |
| 0.91 under 1%, 0.32 over | 21.42 |
| ½ under 1%, 0.32 over | 22.01 |

The last row shows that giving the larger parties ⅓ on its own scores worse
than ½. All of the split's gain comes from letting the six small-party cases
move almost the whole way to their by-election level.

**My recommendation is unchanged: ½ for every party.** The small-party class
rests on six cases, one of them a party (ACDP) counted three times, and the
gain is in-sample. The measurement and the rule disagree here, so it is your
call. Your answer above stands unless you change it.

**Gates.** The final rebuild, only if you choose separate weights.

### 7. The go-live yes

**Context.** Items 2, 3, 5, 6 and 9 are answered. Item 1 (party calls) is the
one left before the final rebuild. After the rebuild, with your yes:

- regenerate the frozen forecast and the site's simulation files;
- rebuild the test site from today's model (the one there now, UAT version
  d22294e0, carries the 16 October model);
- redeploy the seat-picture worker (`joburg-seats`) if its code changed, in
  the order `docs/DEPLOY-UAT.md` sets (site first, then the seat worker).

Your instruction: skip anything that need not run. Promoting the test site to
live stays yours.

### 11. Sign-in, and the three Cloudflare items listed for it

**Context.** These belong to the sign-in feature: readers signing in (Apple,
Facebook, X, Microsoft) so their predictions are saved and can go on a
leaderboard. It is built (`worker-api/`) but not switched on, and it has its
own security and privacy review gate (R5 in TODO.md §0). The three items:

- **Data location.** Where Cloudflare keeps the sign-in database (a "location
  hint" when it is created: Europe, Africa, and so on). It holds personal data
  (email addresses, and political predictions), so where it is stored matters
  under POPIA.
- **Provider app registrations.** Each sign-in button needs an app registered
  with that company under your account (Apple developer account, Facebook
  developer app, X developer app, Microsoft Entra). `worker-api/README.md` has
  the exact settings for each. Only you can create them.
- **Workers Paid.** Cloudflare's $5 a month plan. The free plan allows 100,000
  worker requests a day and very little processing time per request. Pages
  themselves are free and unlimited, but sealing a shared link and drawing its
  seat picture each count as worker requests, and results night could pass
  the limit. Above it, those requests fail. I have not checked which plan the
  account is on.

**Options.** Is sign-in part of this launch? If not, the first two wait. I
recommend Workers Paid either way, before results night.

### 6. The splinter split

**Your answer (2026-10-21):** go live with 35% as it is, and measure it after
going live. "It seems incorrect as it stands in a country so divided by
population group."

Kept open as a task: re-measure `SPLINTER_PARENT_WEIGHT` after go-live
(JUDGEMENT-CALLS §F6), with the population-group question in the brief.

---

## Answered

### 2. Two MK confirmations — answered 2026-10-21

**Question.** MK stood in the 2024 national election but never in a
Johannesburg local election. On 15 October you chose option A: place MK from
its own 2024 national results. (2a) Does that fitted placement win over your
earlier "about 90% ANC" note (JUDGEMENT-CALLS §SJ1)? (2b) Does a party count as
identified if the fit finds it in at least one voter group?

**Answer (owner).** 2a: the placement wins for MK. 2b: "Yes. I confirm that as
a test." Recorded in JUDGEMENT-CALLS §SJ1 at the final rebuild.

### 3. The by-election cap — answered 2026-10-21

**Question.** A party's by-election level is held inside its usual range
before it is blended in. Keep the cap, or let by-elections move every party by
the full weight?

**Answer (owner).** Keep the cap. Evidence (MODEL-LOG §1.326): removing it is
better in 3 of the 6 metros where by-elections reach a party and worse in the
other 3; the rule written before the run needed 4 of 6. The cap moves levels
both ways (it raised the ANC and DA in Cape Town as well as lowering others).
My statement that the uncapped fit is "worse overall" depended on the measure:
on the measure the pre-registration named, it is slightly better overall
(200 against 202 points²) and wins 2 of 6 metros. Corrected in MODEL-LOG
§1.327.

### 5. Polls — answered 2026-10-21

**Answer (owner).** Go live without polls in the forecast. Polls stay on the
interactive, for readers to use.

### 8. The two site settings — found done, 2026-10-21

`SEAL_KEY` is already set on the site worker (checked 2026-10-21: the secret
exists; its value was not read). The seat-picture worker `joburg-seats` was
last deployed 2026-10-14. Nothing is needed from you. If its code changes
before go-live, I redeploy it as part of item 7.

### 4. The by-election weight before go-live — answered 2026-10-20

**Question as asked.** Go live at ½ and test afterwards (a), or let the 2021
test change the weight before go-live (b).

**Answer (owner, 2026-10-20).** (b), and more: "the results should tell us and
make this a measured variable."

**Result (MODEL-LOG §1.326, 2026-10-21).** Measured over twelve weights from
0 to 1 against the 2021 result in the eight metros. Summed list-vote error
(points, eight metros): 0 → 23.90, ⅓ → 22.24, 0.4 → 21.94, **½ → 21.78**,
0.6 → 21.91, 1 → 24.68. Leaving each metro out in turn, the other seven pick
0.4 to 0.6. A second measure (least-squares fit, which weights the big misses
more) gives 0.33, with a range of 0.17 to 0.59 that contains ½. The gain comes
from the by-election swing; pulling the forecast back toward the last result
alone gains nothing. The measured weight equals the shipped one, so the model
does not change.
