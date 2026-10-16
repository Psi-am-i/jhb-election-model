# Pre-registration: the newcomer width split by where a party's centre comes from (2026-10-16)

Written before any run of the change. Evidence that prompted it: scratch study
`scratchpad/mk-tail/` (read-only), owner's question "how does MK get 6% largest
party over ANC".

## The change
`party_width` adds a newcomer term delta for a party with no result at the previous
local election in the city. delta is fitted on all new party-cycles together.
The change fits one delta per anchor class, by the same estimator
(`width_record.joint_nll`), on each class's own rows:
- **anchored**: new to local, centre taken from its own national result in this city;
- **unanchored**: new with no national result to start from.
Arm S (symmetric per class). Arm K (two-sided per class: separate up/down widths)
is run as a comparison only; it is a draw-law change and ships only if it scores
better on the real record AND passes review.

## Predictions (against the world and the mechanism)
G1. Established parties' widths are unchanged (delta does not apply to them).
P1. Fitted delta(anchored) < delta(unanchored); the record's anchored cases
    (COPE 2011, EFF 2016, ID 2006, GOOD 2021, UDM 2000) show no ratio above 1.65
    of the national share at >= 0.5% national share.
P2. Arm S: Johannesburg 2026 P(MK largest party) falls from 5.6% to between 1.5%
    and 4.5%; MK mean list share moves by under 1 point (the mean is pinned).
P3. Backtest (8 metros, 2011/2016/2021): wrong-party seats change by under 3
    in total per year; the biggest movers are city-years with a sizeable
    anchored newcomer (COPE 2011, EFF 2016). The held-out log score of
    anchored newcomers' list shares improves; unanchored newcomers' does not
    get worse by more than its sampling error.
P4. ActionSA 2021 Johannesburg (unanchored, the record's largest upside) keeps
    a predicted band that covers its real 16.0%.

## What would falsify the change
Arm S scoring worse on the record for anchored newcomers than the shipped single delta.
