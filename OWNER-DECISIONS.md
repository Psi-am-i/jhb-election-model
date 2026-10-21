# Decisions waiting on the owner

The one place where every open question for the owner lives. Each item carries
its full context, so it can be answered without the chat transcript. A chat
message that needs a decision links here and names the item by its heading.
When an item is answered, it moves to `OWNER-DECISIONS-ANSWERED.md` with the
date and the answer, and the record it changed (JUDGEMENT-CALLS, MODEL-LOG)
is named.

Last updated: 2026-10-21.

---

## Open

Answered items: `OWNER-DECISIONS-ANSWERED.md`.

### 14. Which parties get their own seat row on Our Forecast and the home page

**Context.** The two forecast pages pick their rows by different rules, and on
the 21 October forecast they disagree. Your Forecast gives a party its own row
when its median is at least 2 seats (your rule, 2 October:
`interactive/pyboot/page.py` `MIN_SHOWN_SEATS`). Our Forecast and the home
page's seat table use a fixed list of nine named parties
(`scenarios.NAMED_PARTIES`: DA, ANC, EFF, ActionSA, MK, PA, IFP, Rise Mzansi,
Al Jama-ah). BOSA and Freedom Front Plus now have a median of 2 seats each
(5,000 simulations), so Your Forecast shows them and Our Forecast puts them in
"Others". The untouched Your Forecast page is meant to be the published
forecast exactly; `test_the_page_engine_at_uniform_weights_is_the_forecast_pages_rows`
is red on this.

**Options.** (a) Our Forecast and the home page use the same rule as Your
Forecast: every party at a median of 2 seats or more gets a row, the rest are
"Others". BOSA and Freedom Front Plus gain rows; the named list goes. (b) Your
Forecast uses the named list. (c) Leave them different.

**Recommendation.** (a). One rule for every party, and a party enters or
leaves the table by its own figure, not by a list someone typed.

**Gates.** A change to two live pages: a brief, then UAT, then live with your
yes. One test stays red until then.

### 15. News for the site

**Context.** The newsdesk digests since 12 October were checked at their
sources (the routine cannot reach news sites; this check read them directly,
News24 through your subscription). Polls are not in the forecast; a poll
appears on the site only as reporting.

1. **Helen Zille's coalition arithmetic** (News24, 9 October, from her talk
   with the Centre for Development and Enterprise on 8 October): "if we get
   40%, although we will be the biggest party by a long shot, we won't be big
   enough to get into government", because the ANC, MK, the EFF, ActionSA
   and the PA together "might get over 50% before we can". A tested claim:
   when the DA is near 40%, how often does a bloc of those five parties reach
   136 of 270 seats? Needs a model query; no verdict yet. It would be the
   third DA claim of six (now DA 2, ANC 1, MK 1, ActionSA 1).
2. **Two polls not yet on the site**, both verified at source:
   eNCA/MarkData (DA 35.0, ANC 21.8, MK 12.5, EFF 11.9, ActionSA 10.3, PA 3.7
   of vote intention; 1,011 Johannesburg registered voters intending to vote;
   fieldwork 10 August to 14 September per eNCA's methodology page, though
   two other dates are also published; margin ±3.08 points) and
   News24/SABI (DA 29, ANC 23, MK 12, EFF 11, ActionSA 7 of registered
   voters; 1,000 voters; 25 August to 17 September; margin 3.3 points). They
   would go on Your Forecast's poll control as reporting, each with its
   caveat line.
3. **A dated "Since then" line on the 490,000 claim card:** Zille repeated
   the claim on 8 October ("136 seats out of 270").
4. **Not usable:** the digest's "new" ActionSA poll (ActionSA 31.7%) is the
   2021 poll, published 30 September 2021, already on file; MK's "can win
   Joburg outright" is reported only in paraphrase; the DA's Electoral Court
   case is reserved with no date; no new Johannesburg by-election.

**Recommendation.** 1, 2 and 3, in one site round with a brief. On 1, decide
with item 17's claims-balance question, since it adds a third DA claim.

**Gates.** Nothing in the forecast.

### 16. Tshwane: three decisions before a forecast

**Context.** Tshwane's inputs, checked read-only today: the 2026 ward map,
past results, census and national baselines are on disk. The IEC ward roll was
read from its page on 21 October (snapshot of 29 September: 107 wards,
1,684,463 registered; `archive/iec-registration-2026-09-29/`). Missing: the certified party roster and party lists (in the IEC's certified
Gauteng candidates PDF of 16 September, on disk; a first parse finds 79
parties, 70 with a party list), by-election adjustments (never built for
Tshwane), and a page builder (none exists; new code). Three things need you:

1. **The roster.** Marking Tshwane's roster complete deletes every party not
   on it. Johannesburg's yes was for its list only. Yes for Tshwane's
   certified list, once parsed and checked?
2. **Tshwane's judgement values.** `cities/tshwane.toml` carries values copied
   from Johannesburg and says nothing may be published until they are
   reviewed. Editing that file re-keys every city's pool specs, Johannesburg's
   live one included, so it needs a full re-emit window, and Johannesburg's
   forecast would be rebuilt with it (its numbers should not move; the
   re-emit checks that). Review now and accept the window, or publish Tshwane
   first with the copied values stated as copied?
3. **Two briefs to approve when written:** the voting-district-to-ward
   assignment for Tshwane (a code change so the assignment is per city) and
   the Tshwane headline page (ward map and seats, its own address).

**Recommendation.** 1 yes. 2: review now and take the window, because a
published forecast built on another city's judgement values would claim
calibration it does not have. 3: approve when written.

**Gates.** The Tshwane forecast.

### 17. Marketing plan

**Context.** The plan is
`~/projects/atlas-jhb-model-newsdesk/marketing/PLAN-2026-10-21.md`: 14 days to
4 November, free channels first, the prediction game as the main hook, a
day-by-day calendar, and measurement from the site's own arrival counts. It
waits on nine decisions in its §9: budget; which channels; whether you front
it in person; whether the 14 October Mail and X drafts were sent; an email
short link; what "every party" means for the party note; the claims balance;
confirming the live entries table was emptied of test predictions; the
billboard slot.

**Recommendation.** Read §9 and answer there or here. Two are urgent: empty
the entries table before the first post, and store the Cloudflare analytics
token so the daily counts start (the free plan keeps logs for 3 days).

**Gates.** The first post (planned 22 October).
