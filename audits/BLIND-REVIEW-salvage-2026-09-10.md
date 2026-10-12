# Blind review brief — salvage, direction, and the assumption stack

Issued 2026-09-10 against branch `ultra-review`, HEAD `1d9a0e1`.
**Two independent reviewers, same brief, neither shown the other's work and
neither given the issuing agent's view.** Where they disagree, the disagreement
is the finding and goes to the owner unresolved (CLAUDE.md §4.4).

**Relaunch verbatim if the session is lost.** Do not paraphrase it — the
blindness is in the wording, and a brief rewritten by the agent under review is
not a blind brief.

---

Adopt the standpoint in `/Users/simondavis/.claude/skills/pollster/SKILL.md` —
read that file first and review as it directs. You are reviewer A [or B].
Another reviewer is working the same brief independently; you will not see their
work and they will not see yours.

REPOSITORY: `/Users/simondavis/projects/jhb-election-model` (branch
`ultra-review`, HEAD `1d9a0e1`). READ-ONLY. Do not edit any file, do not run
anything that writes to `data/`. You may run read-only commands and
`.venv/bin/python` scripts that only read.

WHAT THIS IS: a forecasting model for South African municipal elections. The
next election is 4 November 2026; nomination lists close 16 September 2026. It
backtests against 24 real city-year outcomes across 8 metros and 3 cycles (2011,
2016, 2021). There is a public site.

THE OWNER'S QUESTION, IN HIS OWN WORDS:

> "it once again sounds like there are problems everywhere and confidence in
> finding and fixing them only finds more problems. Can I get a blind review
> from an agent with pollster skill about how to salvage what we have and
> whether we are on the right track and untangling what has become spaghetti
> with assumptions at every level."

So three questions: (1) how do we salvage what we have? (2) are we on the right
track? (3) is this untangleable, or has it become spaghetti with assumptions at
every level?

The owner's stated worry is a specific one and you should engage it directly:
**every round of review finds more defects, and he can no longer tell whether
that means the foundation is rotten or the process is working.** Those two
states look identical from where he sits. Your job includes telling him which
one this is, with evidence.

WHERE THE EVIDENCE IS:

* `README.md` is the map. `CLAUDE.md` holds the operating rules. `HANDOVER.md`
  has a banner at the top with current state.
* `MODEL-LOG.md` is the record of record — ~23,500 lines, append-only, ~222
  numbered findings including negative results.
* `JUDGEMENT-CALLS.md` is the register of every number the data did not force.
  **Probably the single most important file for question 3.** Count them,
  classify them, judge how much of the forecast rests on them.
* `DATA-QUALITY.md`, `ITERATING.md` (what counts as "better"), `MACHINERY.md`,
  `SOURCES.md`, `audits/`, `prereg/`.
* The model is `src/montecarlo.py` (~5000 lines), `src/pools.py`,
  `src/compare_history.py` (the scoring harness), `src/fold.py`.
* `.venv/bin/python src/compare_history.py` runs the 24-city-year backtest in
  ~3 minutes against three naive baselines. It only READS; you may run it.
  `.venv/bin/python src/declares.py` prints an artefact-provenance table.
* `.venv/bin/python tests/run_all.py --list` lists 32 test modules; the suite
  reports 453 passed, 8 failed, 17 skipped. Subsets with `-k`.

⛔ CRITICAL INSTRUCTION ON HOW TO READ THE RECORD:
The write-ups in `MODEL-LOG.md` and the handover documents were written by the
same agent that did the work, and that agent has a documented history of
confident wrong conclusions — including a headline score comparison that was
wrong because it compared two different statistics, and three tracking documents
that listed already-shipped work as outstanding. **Do not take any conclusion in
those documents at face value. Re-derive the decisive numbers yourself from the
code and the artefacts.** Where you cannot verify a claim, say so explicitly
rather than repeating it. Equally: do not assume the record is wrong because you
were warned. Check.

WHAT COMES BACK — blunt, ranked by expected value per unit of work, separating
"this is wrong" from "this is undefended":

1. **THE VERDICT ON DIRECTION.** Does this end in a defensible public forecast
   by 4 November? Strongest single piece of evidence for, and against.
2. **THE DEFECT-RATE DIAGNOSIS.** Is the stream of found-and-fixed defects
   evidence of (a) a rotten foundation, (b) a maturing process finding real
   things, or (c) a review process generating findings faster than value?
   Distinguish with evidence, not vibes. Measure it if you can find a way —
   whether recent findings are getting more or less severe, whether they cluster
   in one layer.
3. **THE ASSUMPTION STACK.** How many judgement calls does the published
   forecast actually rest on? Which would change the headline if wrong? Which
   are measured, which argued, which typed? Is the stack **layered** (errors
   compound) or **flat**? This is the spaghetti question; it deserves the most
   work.
4. **WHAT TO SALVAGE, WHAT TO CUT.** Minimum viable core for an 8-week ship;
   what to switch off or move behind a caveat. Be specific about mechanisms.
5. **WHAT NOBODY SHOULD BELIEVE YET.** Numbers or claims in the record or on the
   site you would not defend in front of a hostile expert.

Take the time you need — this is a review, not a scan. Cite `file:line` for
everything material. If a question cannot be answered from what is in the
repository, that is itself a finding and one the owner needs.
