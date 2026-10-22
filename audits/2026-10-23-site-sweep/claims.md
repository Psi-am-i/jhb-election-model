# Claims pages — reviewer report, 2026-10-23 (read-only agent)

1. da-outright-majority step 4: "every other party combined sheds about 190,000 votes" — with the poll frozen, others shed what the DA gains (~241k -> 490k, ~250k). 190k inconsistent. stats.toml claim_others_shed. FALSE. Dated span 2026-08-07, still printed.
2. da-coalition-red-lines label "without the ANC, the EFF and MK": Zille ruled out MK and EFF only (Daily Maverick 13 Sep 2026). Share image puts NEAR CERTAIN after her quote although intro says nothing to call true or false. MISLEADING.
3. red-lines step 1 "except the ANC ... 93%": the 93% excludes ANC, EFF and MK (render_sheet.py:785). MISLEADING.
4. Red-lines vs Soweto pages count the "everyone else" DA bloc on opposite standards (claims.toml:109-112 vs 140). MISLEADING / even-handedness.
5. Soweto step 3 "0.2% ... jumps to 80%": ~10 of 5,000 simulations; too few for a chance. MISLEADING.
6. Soweto since box "the roll adds a ward to Soweto: 41": no ward added; ward 29 crossed the site's 50% cut after crosswalk change 982cc97 (MODEL-LOG ~30328). MISLEADING.
7. Soweto attribution "Inside Metros": link is Inside Politics (insidepolitic.co.za), interview with Inside Metros. Minor.
8. claims.html standfirst "same 5,000 simulations as the forecast": 490k claim tested on the 7 August run. MISLEADING.
9. 490k since box "Zille repeated the claim, '136 seats out of 270'": that is the majority target, not the 490k arithmetic. Unverified (paywall).
10. "If all DA members did what Helen wanted" / "is Helen right?" / "turnout fantasy" / "special universe": she said registered voters; only speaker on first-name terms; tone singles out one party. EVEN-HANDEDNESS.
11. anc-absolute-authority "EFF and MK, its closest partners": site's own characterisation; "ANC-led" not tested for leadership while DA coalitions are (render_sheet.py:786 vs 357-359). EVEN-HANDEDNESS.
12. 490k step 3 "the excessive-seats law still fires in nine simulations out of ten, handing the ANC every stronghold ward": typed figure; the law hands nobody wards — the party keeps wards it wins, remaining seats of the fixed 270 go to others. WORDING/MISLEADING.
13. "draws", "setting" in reader text (claims.toml:34,35,40,62,63). WORDING RULE.
14. Poll caveat srf-2026q1-coj "same ... sample design": register attests only same house and turnout model; pollster named two ways. Minor.

Checked true: council 270 / majority 136 in all 5,000 draws; p_alone <0.1% (2 of 5,000, MK); DA+ANC most reliable pair 56.5%; "no poll at all" (poll_paths off); 490k/917k=53%; all five quotations verbatim and correctly attributed (Zille BD 1 Mar, Masemola Joburg ETC 13 Aug, Baloyi TimesLive 9 Sep, Zille DM 13 Sep, Mashaba 9 Sep); 2021 nine-party coalition; verdict words match chance scale; poll caveats match register; claims pages never say the council grows.
Not verified: Zille 8 Oct News24 quote; August-run fixed tokens (retired turnout setting); SRF wave design; Inside Metros piece.
