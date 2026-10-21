# Site round, 22 October 2026

Owner, 2026-10-22, verbatim:

> 14. Standardise them I do not care which - when listing 'other parties' do
> so alphabeticaly.
> 15. do 1,2 and 3

> what is interesting looking at the map, is that teh C's wards are almost all
> contested The DA's are largely Safe. So while the ANC is leaning to be the
> largest party, they have multiple races that are far tihgter than the DA.
> How would we phhrase that and include in our headline.

Items 14 and 15 are in OWNER-DECISIONS-ANSWERED.md. Written before the code;
not amended after.

## Items

1. **One rule for seat rows.** Every seats table (Our Forecast, the home page,
   Your Forecast section 1) gives a party its own row when its median is at
   least `MIN_SHOWN_SEATS` (2) seats in the published simulations; every other
   party is in "Others", its complement. One constant, in `src/reweight.py`
   (the page code already imports it); `scenarios.NAMED_PARTIES` and the two
   pages' copies of it are replaced by one function of the run. Rows stay in
   seat order (median, then mean). Wherever the site lists the other parties
   by name, the list is alphabetical (Your Forecast's vote panel already is).
   The two-ballot bars and the map's key are not seat tables and are left as
   they are. On the 21 October run this adds rows for BOSA and Freedom Front
   Plus (median 2 each).
2. **A tested claim: Helen Zille's coalition arithmetic** (News24, 9 October,
   her talk with the Centre for Development and Enterprise on 8 October). The
   quote: "if we get 40%, although we will be the biggest party by a long
   shot, we won't be big enough to get into government". The claim tested:
   the ANC, MK, the EFF, ActionSA and the PA together reach a majority (136
   of 270). Chance-rated on the same simulations as every claim
   (`scenarios.all_party_seats`); the page also says, from the run, how often
   the DA reaches 40% of the list vote (on 21 October: in none of the 5,000;
   its highest is 37.4%). Card format as the other five; verdict from
   `CHANCE_SCALE`. Slug `da-forty-percent-not-enough`.
3. **Two polls on Your Forecast's poll control**, reporting only (the forecast
   uses no polls): eNCA/MarkData Johannesburg (fieldwork 10 August to 14
   September 2026 per eNCA's methodology page, n = 1,011) and News24/SABI
   Johannesburg (25 August to 17 September 2026, n = 1,000), entered in
   `polls.json` with their sources, and each given a reader caveat in
   `content/joburg/poll-caveats.toml` (what it is and what limits it, as for
   the three there). Then `export_draws.py --index` only. If the model's
   rules refuse either poll for the page (`reweight.page_polls`), it is not
   forced in; that is reported.
4. **The 490,000 card's "since" line** gains one dated sentence: Zille
   repeated the claim on 8 October (News24, 9 October), "136 seats out of 270".
5. **The headline: how many close races each contender has.** A sentence
   after the largest-party line, the same for the two parties the headline
   names, every figure a placeholder filled by `render_home.py` from
   `ward_winner_probs.csv` and the map's own safe threshold
   (`render_map.SAFE`): for each, the wards it is favourite in and how many
   of those it wins in under that share of simulations. Wording, filled with
   the 21 October run: "The ANC is favourite in more wards, but more of them
   are close: it leads in 77, 32 of them under 90%; the DA leads in 45, 8
   under 90%." The phrase "more of them are close" is chosen by the figures
   (it is said only when it is true; otherwise the counts alone).

## Checks (QC.md §4b)

Diff reviewed by another agent before the build. Then the build and
`deploy_check`; the modules for the pages touched (home_page, forecast sheet,
your_forecast_page, claims, published_page, model_claims, reweight); the
whole suite once for the UAT version. Live with the owner's yes.

## Owner, later on 2026-10-22 (recorded here; the items above are unchanged)

> Levae the DA's latest. It's not very interesting. We can update teh first
> one if she's made the same claim. We need to look for other comments.

So item 2 (the Zille 40% card) is withdrawn from this round; item 4 (the
dated line on the 490,000 card) stays. Added at the owner's yes: the claims
page's standfirst says how claims are chosen and where to send one.
