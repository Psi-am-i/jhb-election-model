# Non-DA claim candidates, Johannesburg 2026

Searched 22 October 2026. Window: August to 22 October 2026. Sources read in full
in Chrome (News24 with the owner's sign-in; Daily Maverick) or by direct fetch
(eNCA, TimesLive). Wording below is checked against the page unless marked.
Checked against `content/joburg/claims.toml` (six cards: da-outright-majority,
anc-absolute-authority, mk-biggest-party, da-coalition-red-lines,
da-forty-percent-not-enough, actionsa-soweto) and the newsdesk digests in
`~/projects/atlas-jhb-model-newsdesk/newsroom/` to 2026-10-21.

Council arithmetic used below: 270 seats, 136 for a majority. Any model figure
comes from a run; none is quoted here.

## Ranked candidates

### 1. MK: a 2-3% party is a wasted vote (new quantity, arithmetic test)

- **Speaker:** Bongani Baloyi, MK mayoral candidate for Johannesburg
- **Quote (verbatim):** "They must not waste their vote on a party that will take 2% or 3%; they must be strategic"
- **Source:** Daily Maverick, Lunga Simelane, 6 October 2026,
  https://www.dailymaverick.co.za/article/2026-10-06-mk-can-win-joburg-outright-says-mayoral-candidate-bongani-baloyi/
- **Test:** the seats a party wins at 2% and at 3% of the Johannesburg vote, from
  the forecast's seat allocation (including overhang deductions); equivalently,
  per simulation, the number of parties between 2% and 3% and the seats they hold,
  and how often those seats decide whether a coalition reaches 136.
- **Read:** checkable, and probably wrong under PR. At one seat per roughly 1/270
  of the vote, 2% is about five seats before any overhang deduction. In a hung
  council where majorities are decided by a few seats, the test is whether those
  seats are pivotal, and the coalition counts in claims.toml already compute that
  kind of quantity. Applies to every small party equally, which fits the
  no-party-singled-out rule.
- **Risk:** it is advice to voters, not a forecast, so the card has to frame it as
  "would such a vote be wasted" rather than true/false. Arithmetic settles it
  (like da-outright-majority) rather than a chance.

### 2. MK: ANC losses are MK's gains (new quantity, mechanism test)

- **Speaker:** Bongani Baloyi, MK
- **Quote (verbatim):** "One thing people don't appreciate about our strength is that we are the ones who eat into the ANC's base. So if the ANC goes down with whatever percentage, it's going to be a direct consequence or attributed to uMkhonto Wesizwe's growth"
- **Source:** same Daily Maverick article, 6 October 2026.
- **Test:** across simulations, the ANC's vote-share change from 2021 against MK's
  share, citywide and by ward: whether ANC loss tracks MK gain, measured as the
  fraction of the ANC's lost share that MK's share accounts for.
- **Read:** a precise, falsifiable claim about who takes the ANC's vote. Polls on
  file show the DA and ActionSA also moving, so MK being the whole of the ANC's
  loss could be wrong.
- **Risk:** the model may not represent vote flows between parties; if it draws
  shares per party with no transfer structure, it can report co-movement but not
  attribution. Check `MACHINERY.md` before accepting. A card written on
  correlation would claim a mechanism the model does not have (owner rule
  2026-10-16, "model before site text").

### 3. MK: "MK can win Joburg outright" (headline is reported speech; fails the bar)

- **Speaker:** Bongani Baloyi, MK
- **Status:** the Daily Maverick headline and body say Baloyi "wants voters to
  believe the party can win an outright majority" and that MK is "aiming for an
  outright majority". These are the reporter's words. No sentence in quotation
  marks says it. The full article was read in Chrome to check.
- **Nearest verbatim:** TimesLive, 21 September 2026 (podcast write-up), on
  becoming mayor: "It's going to happen," and "I know it's going to happen."
  https://www.timeslive.co.za/politics/2026-09-21-podcast-bongani-baloyi-bets-on-mk-party-to-beat-the-anc-in-johannesburg/
  The same piece's claim that MK will lead the city is also paraphrase.
- **Test if usable:** P(MK reaches 136 seats alone). Becoming mayor needs a
  coalition, which the model does not see.
- **Note:** the newsdesk already drafted this as a new card
  (`newsroom/drafts/2026-10-09-mk-outright-majority.md`), quoting the reported
  speech. On the exact-quote bar it should not go up as worded. The podcast audio
  may hold a verbatim line; it was not checked.

### 4. IFP: hung councils will go to GNU partners, led by a majority party

- **Speaker:** Velenkosini Hlabisa, IFP leader and Cogta minister
- **Quote (verbatim):** "I am sure there will be better stability (after the local elections), simply because most of the municipalities are going to be led by a coalition of partners in the GNU"
  Also, same interview: "There is a very clear understanding now that if you want a stable municipality, get a majority party to lead."
- **Source:** News24, Sithandiwe Velaphi, 7 October 2026,
  https://www.news24.com/southafrica/news/no-more-small-parties-leading-councils-says-hlabisa-as-gnu-partners-eye-hung-metros-20261007-0804
  (He also refers to Johannesburg by name: the lesson of smaller parties leading
  the council.)
- **Test:** P(the GNU member parties on the Johannesburg ballot together reach
  136). The member list must be fixed from the GNU's signatories (ANC, DA, IFP,
  PA, FF+, GOOD, PAC, UDM, Al Jama-ah, Rise Mzansi; confirm). A second quantity,
  P(the largest party is in the GNU bloc), tests "get a majority party to lead"
  (read as the plurality party).
- **Read:** the claim is national; Johannesburg is one instance of it. The bloc
  contains the ANC and the DA, whose two-party chance (`grand_share`) is already
  on the da-coalition-red-lines card, so the result is likely near certain and
  adds little. The interesting part is willingness, which the model cannot see.
  Lowest interest of the usable four.

### 5. ANC: Morero asks to govern alone (duplicate quantity; update to an existing card)

- **Speaker:** Dada Morero, ANC, executive mayor of Johannesburg
- **Quote (verbatim):** "Allow us to lead on our own, for the next five years"
  Also: "Give us a full mandate so that we can deliver without having to go through tedious processes of negotiations"
- **Source:** eNCA, 24 August 2026,
  https://www.enca.com/news-top-stories/give-us-full-mandate-moreros-pitch-joburg-mayor-position
- **Test:** P(ANC reaches 136 alone), the quantity the anc-absolute-authority
  card (Masemola) already tests.
- **Use:** not a new card. A dated `since` line on anc-absolute-authority naming
  a second speaker, the sitting mayor, as the newsdesk proposed for Hill-Lewis
  against Zille's card.

## No usable claim found

| party | what was found | why it fails |
|---|---|---|
| EFF | Tlaleng Mofokeng, mayoral candidate, Ellis Park manifesto (News24, 12 Sep): News24 writes that she "called on voters to deliver a 50-plus-one majority for the EFF" | Paraphrase. Her own words in the piece are rhetoric with no quantity. |
| EFF | Mofokeng, News24 Real Politiki, 9 Sep: Zille is "no competitor" | Two-word quote; the context is in the video, not the text. If the video says the EFF will beat the DA, P(EFF seats > DA seats) would test it. Not checked. |
| EFF | Malema: campaign close at Orlando Stadium, 31 October (X) | An event, not a claim. Worth a check after 31 October. |
| ActionSA | Mashaba, Daily Maverick 16 Oct; News24 "The Queue" 21 Oct | Pledges (500 metro police a year, mayoral committee chosen). No quantified claim about the result. Coalition stance paraphrased only. |
| ActionSA | Mashaba "without Soweto" | Already on the site (actionsa-soweto). |
| PA | Kenny Kunene, mayoral candidate (Daily Maverick 20 Sep): "When I become mayor, I will implement municipal debt relief" | A promise conditional on office, not a claim about the result. A search summary said he called polls at about 2% "an insult"; no source with that quote was found (Moneyweb was down, Briefly and Daily Maverick do not have it). |
| ANC | Mbalula: "the ANC can get 50%" (Joburg ETC) | National, and dated about December 2025, outside the window. |
| ANC | Mbalula, Daily Maverick 15 Oct: "nothing that binds us forever with the DA" | About the national GNU, not about Johannesburg. |
| ANC | Ramaphosa on outright wins in all municipalities | Only found in a search summary with no source; the quantity duplicates anc-absolute-authority. |
| Rise Mzansi, IFP (Mabaso), FF+, ACDP, Al Jama-ah, BOSA | Candidate announcements and pledges | No quantified claim found. |

## Side findings for the newsdesk (no change made)

1. **The "ActionSA-commissioned poll" in the 2026-10-21 digest is from 2021.**
   The digest logged ActionSA 31.7 / ANC 30.5 / DA 24 / EFF 7.3 as a new poll.
   The actionsa.org.za post "Polling Puts ActionSA Ahead in Joburg" is dated
   30 September 2021 (https://www.actionsa.org.za/polling-puts-actionsa-ahead-in-joburg/),
   and its comparisons are against 2016 results. It is the same poll as the
   register's existing `actionsa-internal-2021` entry, not a new reading. That
   item in the digest's READY TO APPLY block should be discarded.
2. **Daily Maverick, 6 Oct, publishes a News24/SABI Johannesburg breakdown:**
   DA 29.2, ANC 22.6, MK 12, ActionSA 7. The 2026-10-05 and 2026-10-21 digests
   rejected these figures as having no source. Daily Maverick is a secondary
   source for them, not the release itself.
3. Baloyi in the same article: MK is campaigning "across all 15 wards every
   single day". Johannesburg has far more wards than that; probably a
   transcription error or a sub-region. Not a result claim.
