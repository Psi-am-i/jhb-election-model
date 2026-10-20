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

**Options.** Mark the parties you disagree with on the sheet, or say "no
calls" and the forecast ships as the model has it.

**Gates.** The final rebuild of the forecast inputs.

### 2. Two MK confirmations (from your 15 October "option A" decision)

**Context.** MK stood in the 2024 national election but never in a Johannesburg
local election. On 15 October you chose option A: place MK voting district by
voting district from its own 2024 national results, instead of assuming its
voters look like the ANC's.

- **2a.** That replaces your earlier note that MK's voters are "about 90% ANC"
  (JUDGEMENT-CALLS §SJ1, `parent_weight = 0.9`). The note stays on the sheet
  and is used again only if the fit from MK's own results stops working.
  Confirm the fitted placement wins.
- **2b.** A party counts as "identified", and is placed from its own record,
  if the fit finds it in at least one voter group. Confirm that test.

**Gates.** The final rebuild.

### 3. The by-election cap

**Context.** A party's by-election level is held inside its usual range before
it is blended in. For a party with a 2024 national vote, that range comes from
how its local vote has related to its national vote in the past. So a large
by-election swing moves the party less than the weight says. In the 2021 test
the cap held back six parties in Cape Town and eight in eThekwini at weight ½.

**Options.** Keep the cap (the current setting), or let by-elections move every
party by the full weight.

**Measured (MODEL-LOG §1.326, 2021 backtest with the 2016–2021
by-elections).** Without the cap, the best-fitting weight is 0.34 and the fit
is worse overall: squared error 781 points² against 760 with the cap. Without
the cap the fit is better in 3 of the 6 metros where by-elections reach a
party (Johannesburg, eThekwini, Mangaung) and worse in the other 3. The rule
written before the run needed 4 of 6 to recommend removing the cap.

**Recommendation.** Keep the cap.

**Gates.** The final rebuild.

### 9. Separate by-election weights for small and large parties

**Context.** You asked whether the weight should differ by party size. The
model can take one weight for parties under 1% of the previous list vote and
another for the rest. Fitted on 2021 (MODEL-LOG §1.326): under 1%, 0.81
(range 0.50 to 1.90 leaving one metro out, 43 party-metros); 1% and over,
0.32 (range 0.16 to 0.58, 29 party-metros). Run with those two weights, the
summed list-vote error is 21.53 against ½'s 21.78, but the weights were fitted
on the same eight metros they are scored on, and the two ranges overlap
(0.50 to 0.58). Small parties carry little of the error either way: 25 parties
under 1% sum to 6.4 points against 54.2 for the 17 parties over 10% (at ½).

**Recommendation.** One weight, ½, for every party. The rule written before
the run allowed separate weights only if the two ranges did not overlap.

**Gates.** The final rebuild, only if you choose separate weights.

### 5. Polls

**Context.** No poll enters the forecast now (pulled out 2026-09-12). The rules
for using them, which house, how each is weighted, how a poll with no sample
size is priced, are not written. Putting polls in needs those rules, a
pre-registration and a backtest.

**Recommendation.** Go live without polls.

**Gates.** Nothing until you say otherwise.

### 6. The splinter split

**Context.** For a splinter party with no record of its own (no 2024 national
vote, no earlier local vote), the model assumes 35% of its voters look like the
parent party's and 65% like the city's (`SPLINTER_PARENT_WEIGHT`, JUDGEMENT-CALLS
§F6). It was measured over 22 past splinter cases (EFF from the ANC 0.89, GOOD
0.28, ActionSA about 0.02) and has not been re-measured since the archive grew.
Parties with a national record (MK, RISE, BOSA) no longer use it.

**Options.** Keep 35%, or hold it unchanged and re-measure after the election.
Either way the number for 2026 is 35%; the choice is whether to re-measure it
before go-live.

**Gates.** The final rebuild only if you want it re-measured first.

### 7. The go-live yes

**Context.** Once items 1, 2, 3, 5, 6 and 9 are settled and the final rebuild is done, I need
your yes to:

- regenerate the frozen forecast and the site's simulation files;
- rebuild the test site from today's model. The one there now (UAT version
  d22294e0, branch site-r11) carries the 16 October model.

Promoting the test site to live stays yours.

### 8. Two site settings (outstanding since 3 October)

**Context.** Both need your Cloudflare login.

- `wrangler secret put SEAL_KEY`. Without it, shared prediction links go out
  unsealed (anyone can edit the picks in the link).
- Deploy the `joburg-seats` worker. Without it, every shared link shows the
  default preview image instead of the reader's seat picture.

---

## Answered

### 4. The by-election weight before go-live — answered 2026-10-20

**Question as asked.** Go live at ½ and test afterwards (a), or let the 2021
test change the weight before go-live (b).

**Answer (owner, 2026-10-20).** (b), and more: "the results should tell us and
make this a measured variable." Whether ½, ⅓ or another value, the weight is
to be measured from the 2016–2021 by-elections against the 2021 result, per
party size if the evidence supports it, rather than declared.

**Result (MODEL-LOG §1.326, 2026-10-21).** Measured over twelve weights from
0 to 1 against the 2021 result in the eight metros. Summed list-vote error
(points, eight metros): 0 → 23.90, ⅓ → 22.24, 0.4 → 21.94, **½ → 21.78**,
0.6 → 21.91, 1 → 24.68. Leaving each metro out in turn, the other seven pick
0.4 to 0.6. ⅓ is 0.46 points worse than ½ on this measure. A second measure
(least-squares fit, which weights the big misses more) gives 0.33, with a
range of 0.17 to 0.59 that contains ½. The gain comes from the by-election
swing; pulling the forecast back toward the last result alone gains nothing.

The measured weight equals the shipped one, so the model does not change.
½ is now recorded as measured on one cycle rather than declared.

---

## From HANDOVER.md, 3 October, not re-checked since

These were listed for you on 3 October for the sign-in feature (R5 gate in
TODO.md §0). Their current status has not been verified.

- the data location for the sign-in data;
- the provider app registrations (`worker-api/README.md`);
- moving to Workers Paid before results night.
