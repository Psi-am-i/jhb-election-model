# Model correction batch, items 7 and 9: investigation packet

Issued to two investigators, read-only, in parallel. Each takes one item.

## Ground rules
- Edit nothing in the repository. Write only to
  `audits/2026-10-09-model-fixes/<item>/` and to the scratch directory you are
  given.
- Do not run `montecarlo.py` as a script, `compare_history`, `build_site` or an
  emit. In-process runs are allowed, with output to scratch only.
- Use `.venv/bin/python`. Do not sub-delegate.
- Read `CLAUDE.md` §1 and §4, `MACHINERY.md`, `JUDGEMENT-CALLS.md`,
  `DATA-QUALITY.md`, `audits/2026-10-09-model-questions/FINDINGS.md` and
  `integrity/FINDINGS.md`.
- Mark every claim **verified** or **argued**.
- **Report early:** put a first finding in your final message even if later
  questions are partial. If the harness refuses a report file, return the full
  findings as text.

## Item 7: the PA's centre against the Coloured pool
1. Trace the PA's centre to its sources:
   - the 2021 result;
   - the 2024 national file;
   - by-elections (w_bye);
   - the level shrink;
   - the θ band;
   - the renormalisation.

   Give each step's value.
2. Trace the Coloured pool's size (registration × turnout) and the PA's pool
   vector (99.4% Coloured). Is any of the three wrong against real results?
   - the PA's real vote by area in 2021 and 2024;
   - its real share of Coloured-majority VDs;
   - the 2026 roll by group.
3. In real elections, what share of the PA's votes came from outside
   Coloured-majority areas? Does the vector allow that?
4. Specify a guard that sees a party taking more of a group than any real
   result shows. State its population, its threshold derived from data, and the
   constructed violation it must catch (the ×12 centre that every current
   counter missed). Do not edit code.
5. Say what each candidate correction would do to the PA's and the DA's seats.
   The owner decides.

## Item 9: the 46 parties with no level shock
1. **Who they are:** list all 46, each with its centre, its 2021 result if any,
   its 2024 national result if any, why it is seeded, and its drawn median and
   5–95% seats.
2. **The record:** for real parties of comparable size (bins by share), across
   the panel, how much has a party's citywide share moved between consecutive
   elections? Give the distribution of log ratios and of absolute changes.
   Treat arrivals and departures separately.
3. **The draws:** for the 46, the variation of their drawn citywide shares,
   from the within-pool split and everything else, in the same units and bins.
4. **The verdict, by size bin:**
   - does the existing variation match the record (Occam: add nothing)?
   - is it too narrow?
   - is it too wide?

   Use a stated test.
5. **"The variation should actually happen."** List every place where the code or
   the records claim a variation source for these parties that does not run
   (the arrival band, §1.198), and the exact correction to the record or to the
   code so the stated mechanism is the running one.

Return: findings ranked, with figures labelled by what they are and over which
population.
