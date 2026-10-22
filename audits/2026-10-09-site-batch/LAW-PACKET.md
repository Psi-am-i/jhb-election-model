# Item 6 packet: how Johannesburg elections work, with the law cited

One agent. Read-only. Write only to `audits/2026-10-09-site-batch/law/`. Do not
sub-delegate. You may use web search and fetch, but only for primary sources:
- the Government Gazette;
- gov.za or justice.gov.za acts;
- the Electoral Commission (elections.org.za);
- the Municipal Demarcation Board.

Use secondary sources only to find a primary one.

Read first:
- `CLAUDE.md`, `STYLE.md`;
- `SOURCES.md`;
- `JUDGEMENT-CALLS.md` (seat-law entries);
- `MACHINERY.md` (seat law);
- `tests/test_overhang.py` (the Laingsburg 2021 pin);
- `src/seats.py`, `montecarlo.allocate_with_overhang`;
- the site's existing explanation (`site/methodology.html`, `site/index.html`,
  `site/laingsburg-2021.html`).

Produce `law/SUMMARY.md` covering:
1. **What a Johannesburg voter casts:** the ward ballot and the PR (list) ballot,
   and why a metro has no district ballot.
2. **Council size and the ward share:** half wards, half PR.
3. **How seats are allocated:**
   - the quota;
   - combined ward and PR votes;
   - ward seats subtracted;
   - largest remainder;
   - excessive seats ("overhang") and what happens to everyone else;
   - independents and parties with no list (the C and D terms).
4. **Delimitation:** who draws wards, and when.
5. **Who becomes mayor:** council election of the executive mayor; no majority
   needed in the first round; coalitions.

For every legal statement, give the statute, section and item (for example
"Local Government: Municipal Structures Act 117 of 1998, Schedule 1, item N"),
a link to the primary text, and whether you **read the item text** or **inferred
it**. Mark every place where the model's code (`seats.py`) and the statute
differ, or where you could not confirm the code follows the statute.

Then a 200–300 word reader-facing draft in the site's voice (STYLE.md: dry,
every sentence informs). It may type no model figures; a statutory number such
as a seat count may be typed if the statute fixes it.

Return the summary as your final message.
