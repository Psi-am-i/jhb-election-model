# S0 review packet: guards, verification and provenance for the prediction brief

Issued verbatim to two independent reviewers, 2026-10-08.

## Ground rules

- **Read-only.** Edit nothing in the repository. Do not run `src/montecarlo.py`,
  `src/compare_history.py`, `src/build_site.py`, `src/pools.py --emit`, or
  anything that writes into `data/`, `site/`, `content/` or `publications/`.
  Scratch files only in the directory you are given. Use `.venv/bin/python`.
- **Do not sub-delegate.**
- Read first: `CLAUDE.md` (§2, §3, §4 "A test that asserts ABSENCE", §5
  `declares.py`), `QC.md`, `STYLE.md` rule 11, then
  `audits/2026-10-07-prediction-restructure/BRIEF.md` (revision 3), which is
  what you are reviewing.
- For every claim say whether you **verified** it (file:line, or a command you
  ran) or are **arguing** it.

## The owner's request (verbatim)

"please task some agents to review guards and verification that it's outputs are
generated, that they are used as inputs where required and that everything has a
provenenace and we know when somethings doesn't happen and when it does."

## Your task

For every artefact and quantity the brief creates, changes or retires, including:
- rule A's prediction;
- each simulation's ward and list votes in `site/draws/`;
- the new reader entry version;
- our sealed prediction;
- the hand-off from the levers;
- the redirect;
- the removal of the single-simulation bar;
- the retirement of `start_rule.py`'s rule;

answer the questions assigned to you below. Ground each answer in the repository
as it stands: name the existing producer, the consumers, and the guard or test
that exists today, or say that none does.

The answer is a list of **guards to add to the brief**. Each must state:
- what it asserts;
- the population it scans, stated and checked in both directions where the
  claim is bidirectional;
- the constructed violation it must catch and stop catching when reverted;
- which file or test it lives in.

## Questions

**Reviewer 1: generated, consumed, provenance.**
1. Is every output the brief creates actually produced by a named producer, and
   is every place that must consume it named? Where could a consumer silently
   read an old or absent input and fall back to a default instead (CLAUDE.md
   §4b's `levels._citywide` returning `{}` is the precedent)?
2. Does each new or changed artefact declare what produced it, so that
   `src/declares.py --verify` and `tests/test_intermediates_are_current.py` can
   see it go stale? Which artefacts would carry no key?
3. Our prediction must be identical in four places: the build, the opening state
   of `/your-prediction/`, our card and the sealed entry. What makes divergence
   impossible or detected, and what is missing?
4. Where does "one definition" of rule A fail today, and what test enforces that
   every caller uses the one function?

**Reviewer 2: knowing when something happens and when it does not.**
1. For each new mechanism, what is the silent failure? Examples: the hand-off
   falls back to the old start; the redirect sends a link to the wrong page; the
   seal is skipped; a simulation's ward votes are missing and treated as zero.
   What guard or counter makes each failure visible, with a positive control?
2. Which existing guards, traces (`--run-dir` stages) or counters does the brief
   make blind or stale? This model has shipped an observer that could not see
   (QC.md §3).
3. Our prediction is sealed per published version, and the last one before the
   lock is scored. How do we know a version was sealed, and how do we know when
   a publish happened without one?
4. The brief's open question: a reader sets both the ward winners and the
   ward-ballot vote, so the two can disagree. In a real election the ward votes
   decide the winners. Should the service refuse, warn or allow an entry where
   they are implausible together? Propose a test of "implausible" that is
   derived from data, not typed.

Return: the guard list, then short answers to your questions.
