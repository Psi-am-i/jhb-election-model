# How Johannesburg elections work, with the law cited (item 6)

Researched 2026-10-09 from primary sources only. The researcher's write was
refused, so the coordinator saved this, condensed from the report. Primary texts
are in `sources/` (seven PDFs: the Municipal Structures Act consolidated to
2006, the Act as gazetted, Amendment Act 3 of 2021, the Constitution, the IEC
Seat Calculation Detail for Laingsburg 2021, the 2024 Coalitions Bill, and the
NCOP Order Paper of 12 Aug 2026).

"Read" means the item text was read; "inferred" means it follows from text read
but is not stated there.

## 1. Two ballots, no district ballot
- Each metro voter has two votes: one for a ward candidate, one for a party
  (MSA Sch 1 item 9(1), read).
- The ward goes to the most votes; a tie is decided by lot (item 8(1),(2),
  read).
- A sole nominee is elected unopposed (item 8A, read).
- A metro has no district council (Const s155(1); MSA s2, s3, read). That
  Johannesburg is category A is inferred; its establishment notice was not read.

## 2. Council size
- The MEC sets the size by Provincial Gazette notice (s18(3)), by the Minister's
  formula with up to 10% deviation (s20(3),(4)(b), as amended by A3/2021).
  The metro ceiling is 270 (s20(1)(c)). All read.
- Half the councillors are ward councillors, rounded up (s22(2),(3)).
- 270, and so 135 + 135, for Johannesburg is inferred: the MEC notice was not
  read.

## 3. Seats (Schedule 1)
- **Quota** (item 12(1), read): A / (B − C) + 1, fractions disregarded.
  - A = valid votes for all parties, on the party ballot and for their ward
    candidates.
  - B = seats.
  - C = independent ward councillors.
  - Unopposed ward: the party's votes in that ward count twice (12(2)).
- **Entitlement** (13(1)): combined votes ÷ quota.
- **Surpluses** (13(2)(a)): leftover seats go by highest surplus.
- **Equal surpluses** (13(2)(b)): to the party with more valid votes, not by lot.
- **Ward wins** (13(3)): deducted; the list fills the rest, in order (13(5)).
- **Excessive seats** (item 16, subitems (3)–(8) added by A3/2021, in force
  1 Nov 2021, read):
  - A party whose ward seats are equal to or greater than its entitlement gets
    no list seats.
  - New quota (A − B) / (C − (D + E)) + 1: B = that party's votes, D = its seats,
    E = independents.
  - The others are re-divided; equal surpluses go to the higher vote; the
    council does not grow.
- **Before 2021** item 16 had only (1) and (2), which were silent on the
  overflow. That was the law for 2011 and 2016.
- **Laingsburg 2021** (IEC report, read): new quota 1,231; ANC 2, DA 3, KDF 1,
  PA 1. At the original quota the KDF would have had 2 (hand computation).
- **No list:** a party with ward candidates but no list has no term in the
  statute. The IEC subtracts its ward seats ("D", and "F" in the excessive
  block). See D1 and D2.

## 4. Delimitation
- An independent authority draws the wards (Const s157(4)(a)). The Demarcation
  Board delimits for each election after consulting the IEC (Sch 1 item 2).
- Voters per ward must be within 15% of the norm, plus community, access and
  boundary criteria (item 4).
- Gazette notice, then 14 days for objections (item 5).
- 2026: final wards handed to the IEC on 10 Dec 2025 (IEC news, read online).

## 5. The mayor
- Elected from the council within 14 days (s55(1)(a)), by secret ballot, one
  vote per councillor present (Sch 3 item 6(a),(b)).
- **The winner needs "a majority of the votes" in every round** (6(c)). The
  lowest candidate is eliminated until someone has one (item 7). A two-way tie
  goes to a further meeting, then lot (item 8).
- That "majority of the votes" means votes cast, so absentees and abstainers
  lower the bar, is inferred. Its anchor is Const s160(3)(c); no ruling was
  found.
- No coalition law is in force. The 2024 Bill, B 2-2025 and B 9-2025 (a
  threshold) are pending, with no enactment found on 2026-10-09.

## 6. Where our code and the statute differ

| # | point | verdict |
|---|---|---|
| D1 | parties with ward candidates but no list: the code removes their votes from A and their ward seats from the denominator | follows the IEC's published formula, not the statute's text |
| D2 | re-quota denominator C − (D + E + F) | follows IEC practice (the Laingsburg report prints it); F = 0 there, so the test cannot tell the two apart |
| D3 | equal surpluses: the statute gives them to the higher vote; the code ranks float remainders (`seats.py:122-134`; coordinator verified by reading), so rounding can decide before the vote count does. Its comment "Schedule 1 breaks exact ties by lot" is wrong | fix: rank on the integer surplus `votes − floor × quota` |
| D4 | unopposed wards' double count (items 12(2), 13(1)(b), 16(5)) | not handled anywhere; 2026 uncontested wards not checked |
| D5 | more than one excessive party, or a cascade | the statute is silent; the code's cascade is a reading |
| D6–D8 | trigger `>=`, excluded votes, fixed council, rounding | match |
| D9 | JUDGEMENT-CALLS §Q2 says Schedule 1 has no rule for ward ties (item 8(2): lot); row §M1 says surplus ties go by lot (13(2)(b): higher vote) | both misstate the statute |
| D10 | `test_overhang`'s Laingsburg case constructs votes; the IEC report publishes them all | the real votes reproduce the published council exactly (coordinator re-ran: ANC 2, DA 3, KDF 1, PA 1, council 7, excess DA 1) |

**Corrects the packet:** the mayor needs a majority of votes cast in every
round, not "no majority needed in the first round".

## 7. Reader-facing draft (about 280 words; statutory numbers only)

> **How Johannesburg's council is elected**
>
> Johannesburg is a metro, so it has no district council and no third ballot.
> Each voter casts two: one for a ward candidate and one for a party. The
> council has 270 seats, the most the Municipal Structures Act allows a metro.
> Half of them, 135, are wards. The candidate with the most votes in a ward
> wins it; no majority is needed.
>
> The two ballots are then added together. Each party's votes on both are
> divided by a quota: all party votes, divided by the seats left once
> independent ward winners are taken out, plus one. Seats still unfilled go to
> the largest remainders, and an exact tie goes to the party with more votes. A
> party's ward wins are subtracted from its total, and its list fills the rest.
>
> A party can win more wards than its total allows. It keeps every ward and
> gets no list seats. Since a 2021 amendment, its votes are then set aside and
> a new quota is struck for everyone else over the seats that remain. The
> council stays at 270, so the cost lands on the other parties' list seats. In
> Laingsburg in 2021 the Electoral Commission applied it, and the Karoo
> Democratic Force lost a seat. No court has ruled on the clause.
>
> Ward boundaries are drawn by the Municipal Demarcation Board, which handed the
> 2026 wards to the Commission in December 2025.
>
> Within 14 days of the result, the council elects an executive mayor by secret
> ballot. Each councillor present has one vote. A candidate needs a majority of
> the votes cast. If nobody has one, the last-placed candidate drops out and
> the council votes again. Councillors who abstain or stay away lower the bar,
> which is how a minority can install a mayor.

**Draft caveats:**
- "The KDF lost a seat" rests on a hand computation.
- "270" rests on the MEC notice, which was not read.
- "No court has ruled" was not verified against case law.
- The last two sentences rest on the inferred reading of Schedule 3 item 6.
