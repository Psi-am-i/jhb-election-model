# Reply to Stats SA — Magakwe Jan Kgope, 26 August 2026

Also sitting in Gmail as a threaded draft (`r8169553557879738468`), thread
"Census 2022: home language by ward (metros), and follow-up on a Small Area
Layer request of 5 August".

- **To:** MagakweK@statssa.gov.za
- **Cc:** Info@statssa.gov.za, TracyD@statssa.gov.za
- **Subject:** Re: Census 2022: home language by ward (metros), and follow-up on a Small Area Layer request of 5 August

---

Dear Magakwe,

Thank you for the language file and the two links, and for coming back on both requests.

We have gone through the workbook properly, and I want to start with what it does well, because it is genuinely useful. Summed to national level it reproduces the published Census 2022 home-language shares almost exactly — isiZulu 24.52% against 24.4% published, isiXhosa 16.42% against 16.3%, Afrikaans 10.68% against 10.6%, and so on, with no language out by more than 0.12 of a percentage point. That is a clean, trustworthy extract and we are grateful for it.

Two things in it we would flag back to you, and then the substantive question.

A. AN ORPHANED ROW

Row 7 of the sheet — the first data row, immediately above "Western Cape" — is "Emakhazeni Local Municipality" (47,243 persons), sitting at the province indentation level rather than inside Mpumalanga. It does not appear anywhere else in the sheet. The Mpumalanga province total (4,963,185) does include it, but the sum of the municipalities listed under Mpumalanga comes to 4,915,944 — short by 47,241, which is Emakhazeni.

The provincial figures are therefore correct; it is the placement that has gone wrong. But anyone reading the hierarchy by indentation, as one naturally would, will silently get a phantom tenth "province" and an under-counted Mpumalanga. It may be worth checking whether the extract routine does this generally.

B. NO TOTAL, AND NO RESIDUAL CATEGORY

The sheet carries 16 language columns and no total column, and no "Other"/unspecified category. Nationally the 16 columns sum to 59,608,380 against an implied population aged 1 and older of roughly 59.94 million, so about 0.55% of persons are in languages not listed. That is small, but it means shares computed from the sheet alone are all very slightly overstated, and a user has no denominator inside the file to normalise against.

Could a future extract include a total column and an "Other" or "Unspecified" residual? It would make the file self-contained.

While on classification: the sheet gives sign language as 9,309 persons nationally, against roughly 235,000 in Census 2011. We assume this reflects a change in how the question or the coding treats sign language rather than an actual collapse, but as we may need to describe it in print, could you confirm what changed?

C. THE SUBSTANTIVE QUESTION — STILL WARD LEVEL

I should be straightforward rather than keep asking the same thing in different words: the municipal table cannot do the work we need. The model compares one ward against another *within* a metro — the City of Johannesburg alone has 135. A single set of figures for Johannesburg as a whole (isiZulu 29.0%, English 14.1%, Sesotho 11.8%, and so on) describes the city's composition but not how it varies across it, and it is the variation the model uses.

So, more precisely than before:

1. Census 2011 language by ward, in SuperWEB2. We understand that in SuperWEB2 (superweb.statssa.gov.za/webapi) the Census 2011 Community Profiles database offers "South Africa by Electoral Ward" as a geography, with Language among the indicator groups — so language by ward does exist for 2011. Is there a Census 2022 database there carrying the same electoral-ward geography? The release you linked (https://www.statssa.gov.za/?p=18967) states that the ward-level product is accessible through SuperWEB and SuperCROSS, which is what prompts the question. And if ward genuinely is not available for 2022, may we use and cite the 2011 ward-level language table, clearly labelled as 2011?

2. The finest 2022 geography at which language IS available. If ward is out for 2022, what is the lowest level published — small area layer, sub-place, or main place? We would gladly take any of those and apportion to wards ourselves, given a correspondence (small area or sub-place to 2020/2026 ward). Is such a correspondence obtainable from the Geography division?

3. The ward product's variable list. Is the Ward-level Small Area Population Estimates product limited to population group, age and sex by design — because the ward figures are modelled estimates rather than direct counts, and only those variables could be estimated reliably? And does the phase 2 schedule at https://www.statssa.gov.za/?p=17568 envisage further variables at ward level later?

D. THE SMALL AREA LAYER REQUEST — STILL OPEN

On 20 August you advised that the SAL data we asked for (income, dwelling type, employment) "is not available". I would be grateful for a little more detail, because at present we do not know how to proceed:

 - Which part is unavailable — the small area geography itself, those particular variables, or the combination?
 - Is the reason confidentiality or suppression at small-area level, that it has not yet been released, or that it is not produced at all?
 - If it is a confidentiality matter, is there a formal route — a data-user agreement, an application to the Research Data Centre, a fee schedule, or anonymised microdata carrying a small-area code? We are willing to sign conditions of use, accept suppression rules, and submit outputs for review before publication.

E. THE RIGHT DESK

If any of the above properly sits with Census Dissemination, the Geography division or Methodology rather than User Information Services, please point us there and we will take it up directly.

For context: this is an open, non-commercial research model of the 2026 municipal elections. The code, the sources and the errors are all published, Stats SA is credited and linked throughout, and we would far rather publish a stated limitation than an inference we cannot support — which is why the questions are this precise.

Thank you again for your time and patience with this.

Kind regards
Simon Davis

simon@scarabtech.com · joburg.whysoserious.city
