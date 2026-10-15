# Ward check: group arithmetic top-down vs counted results, Johannesburg (2026-10-15)

Read-only check; script /private/tmp/wardcheck/wardcheck.py on a snapshot of src at 17a59c1; outputs in this folder (npe2019_wards.csv, lge2021_PR_wards.csv, *_group_rates.csv). Two elections: 2019 national ballot, 2021 local PR ballot, both on the 2021 ward map (135 wards). 852 of 853 2019 VDs matched to 2021 wards by VD number (VD 32863002, 343 votes, dropped).

## Counted vs estimated
Counted: votes by party and registered voters per ward (IEC VD files). Census estimate: Census 2022 population by group (four groups). Estimated (repo method): registered voters and voters by group per ward (one citywide rate per group at each level, adults → registered → voted, each ward rescaled to its counted total); party support by group (fit on ward results × ward voter composition).

Estimated turnout by group: 2019 Black African 63.8%, Coloured 69.5%, Indian 64.6%, White 74.0%; 2021 36.4%, 54.1%, 40.5%, 52.4%.

The White group is not White voters only: the fit needs 1.74 registered "White" voters per census White adult (2021), impossible as a rate; about 43% of the White pool's estimated registrations are people the census does not count as White adults (DATA-QUALITY §11).

## Top-down vs counted
Citywide: identical by construction of the fit (before forcing, off by at most 0.07 pts 2019, 0.74 pts PA 2021).

Literal recipe (roll split by census POPULATION share):
| | 2019 | 2021 |
|---|---|---|
| total votes vs counted | −25,602 | −39,782 |
| ANC citywide share error | +6.6 pts | +6.1 pts |
| DA citywide share error | −8.1 pts | −8.4 pts |
Reason: White residents register at more than twice the Black African rate; population split puts 309k of the 2021 roll in the White group, the registration-fitted split 560k.

Ward by ward (repo method; MAE share points over 135 wards, 90th pct in brackets):
| | ANC | DA | EFF | ASA | IFP | wrong-party share | winners right |
|---|---|---|---|---|---|---|---|
| 2019 | 4.5 (8.4) | 3.1 (8.3) | 2.9 (5.8) | – | 1.9 (2.0) | 7.0 | 130/135 |
| 2021 | 4.7 (11.6) | 2.9 (7.7) | 2.6 (5.3) | 4.6 (9.8) | 2.9 (3.4) | 10.8 | 128/135 |
Largest misses, same wards both years: ward 65 (hostel; IFP 59.5% counted vs 3.6% top-down, 2021), ward 61 (Jeppe Hostel; IFP 33%), ward 131 and 127 (DA top-down far too high where census shows 7-10% White).

## Why wards miss when the city matches (2021 PR)
| method | ANC | DA | ASA | wrong-party share | winners |
|---|---|---|---|---|---|
| roll split by census population | 7.7 | 6.8 | 4.6 | 15.0 | 117 |
| repo registration split, one citywide rate set | 4.7 | 2.9 | 4.6 | 10.8 | 128 |
| rates refitted in 7 regions (in-sample) | 4.0 | 2.0 | 3.1 | 8.1 | 129 |
| rates refitted in 12 regions (in-sample) | 3.9 | 2.0 | 3.0 | 7.9 | 129 |
| rates from 20 nearest other wards (out of sample) | 4.9 | 2.6 | 4.5 | 10.1 | 127 |
| every group votes like its ward | 7.9 | 7.8 | 4.7 | 15.9 | 126 |
Causes, largest first: census vs roll; variation inside a group (hostel IFP: wrong-party share 23.9 in the 9 wards with IFP >10% vs 9.9 elsewhere; mostly ward-specific, not regional); group turnout by ward (not separable here); VD map (negligible).

## Six wards (top-down / counted votes)
Worked: ward 33, Soweto, 2021: registered BA 13,548 (est.), Col 70, Ind 24, Wh 65; BA voters 13,548 × 36.4% = 4,930; ANC 4,930 × 53.3% = 2,629 + 8 = 2,636; counted 3,370.
| ward | 2021 ANC | DA | ASA | EFF | 2019 ANC | DA | EFF |
|---|---|---|---|---|---|---|---|
| 33 Soweto (99.5% BA) | 2,636/3,370 | 134/177 | 913/1,512 | 793/886 | 6,236/7,491 | 462/594 | 1,775/1,969 |
| 83 Helderkruin (77% White) | 508/554 | 5,224/5,849 | 1,532/1,037 | 245/115 | 1,699/1,203 | 8,668/8,670 | 771/407 |
| 54 Mondeor (most mixed) | 1,500/1,656 | 3,719/3,974 | 1,735/2,443 | 417/524 | 4,067/4,476 | 7,258/7,243 | 1,304/1,624 |
| 18 Eldorado Park (92.5% Coloured) | 1,349/694 | 2,420/1,984 | 722/589 | 217/116 | 1,977/1,620 | 9,305/10,731 | 756/385 |
| 9 Lenasia (71% Indian) | 1,378/1,556 | 2,138/2,170 | 1,979/1,527 | 205/122 | 4,570/4,815 | 5,529/6,027 | 1,214/538 |
| 74 Bramley (best independent ward) | 696/934 | 4,910/4,985 | 1,557/1,714 | 287/295 | 2,086/2,682 | 7,871/7,816 | 844/842 |
Also: ward 18 PA top-down 3,898 vs 6,301 counted; ward 83 VF+ (2019) 372 vs 1,715. Place names inferred from voting-station names.

## National → local: which predicts 2021 wards better?
Scored on the 22 parties on both ballots, shares renormalised; both methods scaled to 2021 citywide shares.
| method | wrong-party share | ANC | DA | EFF | IFP | winners |
|---|---|---|---|---|---|---|
| A: 2019 group support × 2021 roll by group × 2019 group turnout | 12.4 | 6.0 | 5.7 | 3.2 | 3.6 | 127 |
| A2: same, 2021 group turnout | 12.5 | 6.1 | 5.8 | 3.3 | 3.6 | 126 |
| B: 2019 ward results × citywide ratio (the model's approach) | 9.1 | 3.9 | 4.8 | 2.5 | 0.7 | 130 |
| D: 2021 group support fitted on 2021 itself (in-sample) | 10.3 | 5.0 | 3.4 | 3.0 | 3.6 | 130 |
| uniform: every ward = city | 35.7 | 22.3 | 27.3 | 6.9 | 3.6 | 88 |
Limits: one city, one transition; group fits in-sample; neither method places a new party (20% of 2021 PR votes went to parties absent in 2019).
