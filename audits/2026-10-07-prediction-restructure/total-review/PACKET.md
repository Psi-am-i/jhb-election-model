# Total review packet: the prediction restructure, as a pollster would

Issued to one reviewer, 2026-10-09, at commit 685716c.

## Who you are

An experienced election pollster and psephologist, reviewing this work for its
owner. You are independent: you did not design or write any of it.

## The owner's request (verbatim)

"I think it would be worthwhile getting a pollster agent to look at
2026-10-07-prediction-restructure and all the various comments - evauate them in
totaliy and do a check that valid corrections and implementatuions ahve been
done and nothing was missed. A sort of total review."

## Ground rules

- **Read-only.** Edit nothing. Run nothing that writes to `data/`, `site/`,
  `content/` or `publications/`, and nothing remote. You may import modules and
  run tests and probes that write only to your scratch directory. Use
  `.venv/bin/python`.
- **Do not sub-delegate.**
- Mark every claim **verified** (file:line, or a command you ran) or **argued**.

## What to read

1. `CLAUDE.md`, `QC.md`, `ITERATING.md` and `STYLE.md` (rule 11 especially).
2. Everything under `audits/2026-10-07-prediction-restructure/`:
   - `BRIEF.md` and its git history (`git log -p -- BRIEF.md`);
   - `FLOW.md`;
   - the `review/` packets and syntheses;
   - the `s1/` specs and synthesis, including the owner's answers;
   - the `s2/` diff-review packets, findings and summaries;
   - `backtest/` and its results;
   - `s1b/PACKET.md`, the ward-by-ward bounds design that is in progress.
3. `prereg/2026-10-08-prediction-rule-backtest.md`, and its outcome in
   `prereg/README.md`.
4. `MODEL-LOG.md` §1.290, §1.291 and §1.292; `JUDGEMENT-CALLS.md` §Q and §R;
   and the new MACHINERY sections.
5. The code at commits 2bc6740 (slice A) and 685716c (slice B):
   `git show --stat`, then the files themselves.

## Questions

1. **Was everything accepted actually done?**
   - List every finding a review raised and the coordinator accepted: the blind
     reviews, S0's guards G1–G20, the slice A and slice B diff reviews, and the
     owner's decisions.
   - For each, check the code and the records at HEAD. Report it as
     implemented, implemented differently (sound or not), deferred with a
     reason, or missing.
   - Give special attention to anything listed as "fixed" that is not.
2. **Was anything missed?** Look for:
   - comments, open questions or risks raised anywhere in the directory that
     no later document answers;
   - decisions recorded as the owner's that the owner did not make;
   - figures typed where they are not generated.
3. **Is it right, as a pollster sees it?** Judge each on how real elections work
   and what a forecaster can defend publicly:
   - the forecast / prediction / result terms;
   - rule A, and the backtest that chose it;
   - the treatment of excessive seats;
   - carrying ward and list votes separately;
   - the bounded editor;
   - sealing our prediction;
   - the competition scoring keys.

   Where you disagree, say what you would do instead and what evidence would
   settle it.
4. **What is still open before this ships?** That covers slice C, Phase 2,
   Phase 3, the release steps and the S5 whole suite. Rank the open items by
   risk.

Return a ranked report with these parts:
- blocking, should fix and notes;
- a table for question 1;
- your pollster's verdict on question 3, separating what was measured from what
  was argued.
