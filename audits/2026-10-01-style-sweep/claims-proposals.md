# Proposed STYLE.md rewrites of the claims' published write-ups — for the owner

Source: `content/joburg/claims.toml`, fields `intro` and `steps`. These are
published, dated write-ups, so none of this is applied. Each block is
before/after. Every `{{token}}` and `[[token]]` in each "after" is the same
multiset as its "before"; none is added, removed or moved between steps.
Verdicts, labels and figures are unchanged. Register: surnames, no verdict
adjectives (STYLE §7), no rhetorical questions.

Already applied (not the dated write-up): the two `since` boxes (DA 490,000;
ANC alone). See `CHANGES.md`.

Done since, as corrections with /corrections entries (`85254b1`): claim 4's
heading, coin-flip clause and verdict (below), and the 587,000 standfirst of
"When the ANC falls, nobody catches the votes" (`articles.toml`, CHANGES.md
M4).

If approved: paste each "after" over its field, run
`.venv/bin/python src/render_sheet.py --city joburg`, and decide whether the
change needs a dated note (the convention for a published piece).

---

## Claim 1 — DA, Zille, "490,000 registered DA voters" (published 8 August 2026)

Each of this claim's `intro` and `steps` is wrapped in
`<span data-asof="2026-08-07">…</span>`; the wrapper stays. The steps below
show the text inside it.

### intro

Before:

> `<span data-asof="2026-08-07">`When we put the claim through the full model on 7 August 2026 it fell short by {{claim_short_by}} seats at the median. The figures below are from that run. The model has changed since, and the turnout setting they were measured under no longer exists, so read them as history rather than as today's forecast. The claim also falls at its use of arithmetic.`</span>`

After:

> `<span data-asof="2026-08-07">`Run through the full model on 7 August 2026, the claim fell short by {{claim_short_by}} seats at the median. The figures below are from that run. The model has changed since and the turnout setting they were measured under no longer exists, so they are history, not today's forecast. The claim's arithmetic also fails.`</span>`

### steps[0]

Before:

> **It is half of the wrong number.** 490,000 is almost exactly half of the ~{{claim_poll_base}} votes expected in Johannesburg if turnout stays at its record low. At first glance it looks plausible, until you realise that if there are more voters, you need half of a bigger number. If all DA members did what Helen wanted, the total number of voters would be ~{{claim_poll_surged}}, and half of that is {{claim_half_surged}} — not 490,000.

After:

> **It is half of the wrong number.** 490,000 is almost exactly half of the ~{{claim_poll_base}} votes expected in Johannesburg if turnout stays at its record low. More voters means half of a bigger number. If every registered DA voter voted, as Zille asks, the total would be ~{{claim_poll_surged}}, and half of that is {{claim_half_surged}}, not 490,000.

### steps[1]

Before:

> **They can't reach the higher number.** Push every DA and ActionSA supporter to the highest turnout their areas have ever recorded — {{claim_hi_turnout}}%, a turnout fantasy at a local election — and the DA does clear the wrong original target, polling ~{{claim_da_votes_surge}}. But that is still well short of {{claim_half_surged}}.

After:

> **The higher number is out of reach.** With every DA and ActionSA supporter turning out at the highest rate their areas have recorded ({{claim_hi_turnout}}%), the DA polls ~{{claim_da_votes_surge}}. That clears the original target and is short of {{claim_half_surged}}.

Note: "a turnout fantasy at a local election" is cut (STYLE §7). If the point
that no local election has reached that rate is wanted, it needs its source
before it is stated as a fact.

### steps[2]

Before:

> **Even {{claim_da_share_surged}}% of the vote doesn't buy {{claim_da_share_surged}}% of the seats.** {{claim_da_share_surged}}% would be {{claim_prop_seats}} seats of {{council_size}}. But the excessive-seats law still fires in nine simulations out of ten, handing the ANC every stronghold ward it holds — about {{claim_anc_wards_surged}} wards on an entitlement of about {{claim_anc_entitlement_surged}}. The surplus is deducted from everyone else's column, the biggest slice from the biggest party. So the DA's median actually lands on {{claim_da_median}} of the {{majority}} needed.

After:

> **{{claim_da_share_surged}}% of the vote does not buy {{claim_da_share_surged}}% of the seats.** {{claim_da_share_surged}}% would be {{claim_prop_seats}} seats of {{council_size}}. The excessive-seats clause still fires in nine simulations out of ten, and the ANC keeps every stronghold ward, about {{claim_anc_wards_surged}} on an entitlement of about {{claim_anc_entitlement_surged}}. The surplus is deducted from the other parties, the largest share from the largest party. The DA's median is {{claim_da_median}} seats, against the {{majority}} needed.

### steps[3]

Before:

> **Could she still be right?** We looked for a reading that works. Her exact words — “We need 490,000 registered DA voters to go vote DA, if they do that we win an outright majority” — never say what total she is measuring against. Against 2021's poll of ~{{claim_poll_2021}} ballots, 490,000 would be {{claim_490k_of_2021}}%. So the claim is true in exactly one world: the DA doubles its vote while every other party combined sheds about {{claim_others_shed}} votes, keeping the voter numbers frozen at the record low. If that happened, is Helen right? Nothing in twenty years of turnout records produces that world — but even assuming it exists, while the ANC holds its ~{{claim_anc_wards_surged}}-ward wall the excessive-seats law means the DA needs about {{claim_vote_share_needed}}% of the vote to reach {{majority}}. So even in a special universe with never-before-seen events, it is false. The few simulations where the DA does govern alone are the ones where its surge breaks the wall itself, flipping stronghold wards — in those draws the ANC falls to ~{{claim_anc_collapse_seats}} seats. To do that, the DA needs to do more than turn out its existing supporters. It needs new ones.

After:

> **A reading under which it holds.** Zille's words, “We need 490,000 registered DA voters to go vote DA, if they do that we win an outright majority”, do not say what total she measures against. Against 2021's poll of ~{{claim_poll_2021}} ballots, 490,000 would be {{claim_490k_of_2021}}%. That requires the DA to double its vote while all other parties together shed about {{claim_others_shed}} votes, leaving turnout at the record low. Twenty years of turnout records contain no such election. Even then, while the ANC holds its ~{{claim_anc_wards_surged}}-ward wall, the excessive-seats clause means the DA needs about {{claim_vote_share_needed}}% of the vote to reach {{majority}}. The few simulations in which the DA governs alone are those where its surge flips stronghold wards; in them the ANC falls to ~{{claim_anc_collapse_seats}} seats. That takes new DA voters, not only higher turnout among existing ones.

---

## Claim 2 — ANC, Masemola, "absolute authority" (published 26 September 2026)

### intro

Before:

> This is an appeal, not a forecast, so the thing to test is whether the mandate being asked for is available at all. Absolute authority means governing without needing anyone else: {{majority}} of the {{council_size}} seats. In the {{n_draws}} simulations behind today's forecast, the ANC does it in [[anc_alone_count]] of them.

After:

> This is an appeal, not a forecast, so the test is whether the mandate asked for is available. Absolute authority means governing alone: {{majority}} of the {{council_size}} seats. In the {{n_draws}} simulations behind today's forecast, the ANC reaches it in [[anc_alone_count]].

### steps[0]

Before:

> **Not close.** The ANC's median is [[anc_median]] seats, against the {{majority}} it would need. Its single best result anywhere in the {{n_draws}} simulations is [[anc_best]], and that draw is the outer edge of the range, not a likely outcome.

After:

> **The median is short of a majority.** The ANC's median is [[anc_median]] seats, against the {{majority}} it would need. Its best result in the {{n_draws}} simulations is [[anc_best]], at the outer edge of the range.

### steps[1]

Before:

> **Being first is a different question, and that one is open.** The ANC is the largest party in [[anc_largest_share]] of simulations against the DA's [[da_largest_share]]. First place is a genuine contest. Sole control is not: no party reaches {{majority}} alone in more than a handful of draws.

After:

> **Coming first is a separate question.** The ANC is the largest party in [[anc_largest_share]] of simulations, the DA in [[da_largest_share]]. No party reaches {{majority}} alone in more than a handful of simulations.

### steps[2]

Before:

> **The ANC does have routes — they are all coalitions.** With the EFF and MK, its closest partners on this ballot, the three together reach {{majority}} in [[anc_left_share]] of simulations, on a median of [[anc_left_median]] seats. Going the other way — an ANC-led council built with ActionSA, the PA and the smaller parties instead — reaches it in [[anc_side_share]]. These routes and others are open to the ANC. Absolute authority is not.

After:

> **The ANC's routes to a majority are coalitions.** With the EFF and MK, the three reach {{majority}} in [[anc_left_share]] of simulations, on a median of [[anc_left_median]] seats. An ANC-led council with ActionSA, the PA and the smaller parties reaches it in [[anc_side_share]].

Note: "its closest partners on this ballot" is cut as a characterisation the
page does not source (STYLE §7).

---

## Claim 3 — MK, Baloyi, "the biggest party in the city" (published 26 September 2026)

### intro

Before:

> Unlike most campaign talk this is a precise, checkable prediction: more seats than anyone else. MK is the largest party in [[mk_largest_share]] of the {{n_draws}} simulations.

After:

> This is a checkable prediction: more seats than any other party. MK is the largest party in [[mk_largest_share]] of the {{n_draws}} simulations.

### steps[0]

Before:

> **The gap is large, not marginal.** MK's median is [[mk_median]] seats of {{council_size}}. Even at the top of its range — [[mk_p95]] seats, a result it beats in only one simulation in twenty — it is short of the ANC's typical [[anc_median]] and the DA's [[da_median]].

After:

> **MK's range against the ANC and the DA.** MK's median is [[mk_median]] seats of {{council_size}}. At the top of its range, [[mk_p95]] seats (exceeded in one simulation in twenty), it is below the ANC's median of [[anc_median]] and the DA's of [[da_median]].

### steps[1]

Before:

> **First place is a two-horse race in this forecast.** The ANC is largest in [[anc_largest_share]] of simulations and the DA in [[da_largest_share]]. Everything else, MK included, shares what is left.

After:

> **First place is between the ANC and the DA.** The ANC is largest in [[anc_largest_share]] of simulations and the DA in [[da_largest_share]]. The other parties, MK included, share the rest.

### steps[2]

Before:

> **The complaint about polls does not reach this forecast.** Our model uses no poll at all. It is built from the record — how this city has actually voted, and the trajectories we can measure in that record. So the claim that pollsters undercount MK, whether or not it is right, leaves these numbers where they are. To be largest, MK would have to be under-represented in past ballot boxes, not in a survey — a different and much harder argument.

After:

> **The forecast uses no poll.** It is built from how this city has voted and the trends measurable in that record. Whether or not pollsters undercount MK, these figures do not depend on polls. For MK to be largest here, its support would have to be missing from past results, not from surveys.

---

## Claim 4 — DA, Zille, coalition red lines (published 26 September 2026)

### intro

Before:

> A red line is a choice, not a claim about the world, so there is nothing here to call true or false. What can be tested is what it costs. Ruling out the EFF and MK leaves the DA two high-probability ways to a majority: everyone else in the council except the ANC, which clears {{majority}} in [[no_red_share]] of simulations, or a deal with the ANC itself, which clears it in [[grand_share]]. The narrower option — ActionSA and the PA alone — is the [[three_share]] case discussed just below.

After:

> A red line is a choice, not a claim about the world, so there is nothing to call true or false. What can be tested is its cost. Ruling out the EFF and MK leaves the DA two routes that often reach a majority: every other party except the ANC, which clears {{majority}} in [[no_red_share]] of simulations, or a deal with the ANC, which clears it in [[grand_share]]. The narrower option, ActionSA and the PA alone, is the [[three_share]] case below.

### steps[0]

Before:

> **Without the ANC, the red line holds about half the time.** A council built from every party except the ANC, the EFF and MK reaches {{majority}} in [[no_red_share]] of the {{n_draws}} simulations. That is the whole of the rest of the council acting as one — the most generous possible reading of the DA's options, and it still comes down to a coin flip.

After:

> **Without the ANC, the red line leaves a majority in [[no_red_share]] of the {{n_draws}} simulations.** That counts every party except the ANC, the EFF and MK together reaching {{majority}}, which assumes the whole rest of the council acts as one: the most generous reading of the DA's options.

Done (2026-10-02): the heading, the coin-flip clause and the verdict were
corrected in `85254b1`, with a /corrections entry (59% on 26 and 27
September; verdict now "MORE LIKELY THAN NOT"). The live heading is "Without
the ANC, the red line leaves a majority in [[no_red_share]] of simulations."
The rest of this "after" (the body sentence) remains a proposal.

### steps[1]

Before:

> **The plausible version of that coalition is much weaker.** The DA with ActionSA and the Patriotic Alliance — the partners most often named — reaches {{majority}} in [[three_share]] of simulations. Two medians describe them and they answer different questions: across all [[n_draws]] simulations the three hold [[three_median]] seats, and in the [[three_share]] where they do reach a majority they hold [[three_median_when_wins]]. The who-can-govern table reports the second, because it is asking what governing looks like when it happens. Getting from the first to a majority means adding parties that will each hold a handful of seats, and keeping all of them.

After:

> **The DA with ActionSA and the PA.** The three, the partners most often named, reach {{majority}} in [[three_share]] of simulations. Two medians describe them. Across all [[n_draws]] simulations they hold [[three_median]] seats; in the [[three_share]] where they reach a majority they hold [[three_median_when_wins]]. The who-can-govern table reports the second. From the first, a majority needs several more parties of a few seats each, all of them kept.

### steps[2]

Before:

> **The alternative the red line leaves is a deal with the ANC.** The DA and the ANC together clear {{majority}} in [[grand_share]] of simulations. Neither party has said it wants that. It is, on this arithmetic, the most reliable two-party majority in the city. `<span data-asof="2026-09-30"><em>`Correction, 30 September 2026: this sentence called it "the most reliable majority in the city that does not involve the EFF or MK", which the combination above contradicts. `<a href="/corrections">`Corrections`</a>.</em></span>`

After:

> **The other route is a deal with the ANC.** The DA and the ANC together clear {{majority}} in [[grand_share]] of simulations. Neither party has said it wants that. It is, on this arithmetic, the most reliable two-party majority in the city. `<span data-asof="2026-09-30"><em>`Correction, 30 September 2026: this sentence called it "the most reliable majority in the city that does not involve the EFF or MK", which the combination above contradicts. `<a href="/corrections">`Corrections`</a>.</em></span>`

Note: "on this arithmetic" stays; without it the sentence is a stronger
claim. The inline correction keeps its reason, because the /corrections entry
gives a different and less specific one ("Many governing majorities occur in
most simulations").

### steps[3]

Before:

> **The same test applied to the other side.** An ANC-led council excluding the DA, the EFF and MK reaches {{majority}} in [[anc_side_share]] of simulations — almost exactly the same odds as the DA's route. On coalition arithmetic alone, neither leader is better placed than the other.

After:

> **The same test for the ANC.** An ANC-led council without the DA, the EFF and MK reaches {{majority}} in [[anc_side_share]] of simulations, close to the DA's figure.

Note: "close to the DA's figure" restates "almost exactly the same odds"; it
is a claim about two live tokens (on 1 October, the two printed figures were
within three points of each other) and needs rewording if they separate.

---

# STYLE rule 10 (2026-10-02): chance in the claim, simulations in the explanation

Owner, 2026-10-02: "The use of simulations is explanatory and should not be in
headlines." The two `since` boxes are applied (see `CHANGES.md`, rule 10). The
items below are in the dated `intro` and `steps`, so they are proposals. Each
"after" is written against the published text; where an earlier proposal above
rewrites the same field, apply this change to that "after" instead. Tokens are
unchanged except where a note says so. A sentence never opens on a token,
because a chance token can display as "under 0.1%" or "over 99%".

| # | claim · field | before | after | note |
|---|---|---|---|---|
| R1 | DA 490,000 · steps[2] (inside `data-asof="2026-08-07"`) | "But the excessive-seats law still fires in nine simulations out of ten" | "But the excessive-seats law still had a nine-in-ten chance of firing" | dated history; body, not heading |
| R2 | ANC alone · intro | "In the {{n_draws}} simulations behind today's forecast, the ANC does it in [[anc_alone_count]] of them." | "Today's forecast gives it [[anc_alone_share]] chance ([[anc_alone_count]] of the {{n_draws}} simulations)." | adds `[[anc_alone_share]]`, already printed in this claim's since box |
| R3 | ANC alone · steps[1] body | "The ANC alone has the most seats in [[anc_largest_share]] of simulations, the DA alone in [[da_largest_share]], and two or more parties tie for the most seats in [[largest_tied_share]]." | "Most seats alone: [[anc_largest_share]] chance it's the ANC, [[da_largest_share]] chance it's the DA. Two or more parties tie for the most seats: [[largest_tied_share]] chance." | heading unchanged |
| R4 | ANC alone · steps[2] body | "the three together reach {{majority}} in [[anc_left_share]] of simulations, on a median of [[anc_left_median]] seats. … reaches it in [[anc_side_share]]." | "the three together reach {{majority}}: [[anc_left_share]] chance, on a median of [[anc_left_median]] seats. … reaches it: [[anc_side_share]] chance." | |
| R5 | MK · intro | "MK is the largest party in [[mk_largest_share]] of the {{n_draws}} simulations." | "MK has the most seats alone: [[mk_largest_share]] chance." | `{{n_draws}}` leaves the sentence; the how-to-read box says what a chance is |
| R6 | MK · steps[1] body | "The ANC alone has the most seats in [[anc_largest_share]] of simulations and the DA alone in [[da_largest_share]]. Two or more parties tie for the most seats in [[largest_tied_share]]." | as R3 | heading unchanged |
| R7 | red line · intro | "which clears {{majority}} in [[no_red_share]] of simulations, or a deal with the ANC itself, which clears it in [[grand_share]]." | "which clears {{majority}}: [[no_red_share]] chance; or a deal with the ANC itself: [[grand_share]] chance." | |
| R8 | red line · steps[0] **heading** | "**Without the ANC, the red line leaves a majority in [[no_red_share]] of simulations.**" | "**Without the ANC, the red line leaves a majority: [[no_red_share]] chance.**" | ⚠️ the /corrections entry "Without the ANC, the red line holds about half the time" says "The heading now reads 'Without the ANC, the red line leaves a majority in 59% of simulations.'" Changing the heading leaves that entry quoting a wording the page no longer prints, and rule 5 of the brief says presentation changes get no entry. Not applied: the owner decides between leaving the corrected heading as it is and changing it with the entry left as a record of the correction's own wording |
| R9 | red line · steps[1] body | "reaches {{majority}} in [[three_share]] of simulations" | "reaches {{majority}}: [[three_share]] chance" | the later "in the [[three_share]] where they do reach a majority" is explanatory and stays |
| R10 | red line · steps[2] body | "clear {{majority}} in [[grand_share]] of simulations" | "clear {{majority}}: [[grand_share]] chance" | the inline 30 September correction is untouched |
| R11 | red line · steps[3] body | "reaches {{majority}} in [[anc_side_share]] of simulations" | "reaches {{majority}}: [[anc_side_share]] chance" | |

Left as they are (explanatory, not a claim of chance): "Its single best result
anywhere in the {{n_draws}} simulations" (ANC steps[0]); "a result it beats in
only one simulation in twenty" (MK steps[0]); "Across all [[n_draws]]
simulations they hold" (red line steps[1]); "The few simulations where the DA
does govern alone" (DA 490,000 steps[3]).
