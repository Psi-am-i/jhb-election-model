# Blind review brief — validate this session's work before it is deployed

You have the repository. You do not have the lead's reasoning, deliberately.

## What you are validating

Twenty-three commits, `edc7f50..HEAD` on branch `remediation`, none of them
deployed. The live site is the 26 September build. The owner wants them checked
before they ship.

    git log --oneline edc7f50..HEAD
    git diff edc7f50..HEAD

**The question is not "are these good ideas".** It is: **does each change do
what its commit message says, and does any of it make the published site wrong,
misleading, or broken?**

## The changes, grouped

**A correction to live figures.** Four figures on `/nobody-will-win` were
frozen as "published 31 August 2026" and sourced to a build that was never
deployed. They are re-sourced to `publications/joburg/ledger.jsonl` at the
8 August deploy, three arrows now point down instead of up, one sentence is
rewritten, five articles are re-dated, and a correction is filed on
`/corrections`. A test was added that requires a frozen figure to cite the
ledger and match it.

**The published track record changed.** `/about` now reports the model beating
its baselines by 34% on summed CRPS rather than 37%, and Johannesburg's seat
error as 96 rather than 62. An earlier blind review
(`audits/2026-09-27-backtest-difference/`) attributed this to commit `f33528f`
removing a temporal leak, and the hand-written caveat that described the leak
was rewritten. ⚠️ **The 11 August artefact this replaced was destroyed** by a
run of `build_validation.py`; `data/**` is gitignored and there was no copy.

**Two figures that disagreed.** A coalition's median was 118 on one page and
144 on another; both are now named and distinguished. A range printed over a
single simulation ("34 – 34 seats") now collapses to one figure, and the token
for its upper bound was retired through the ledger.

**Site behaviour.** The light/dark theme now follows the operating system. Two
articles moved from "How this is built" into the article list. The portal's
claim of sliders that do not exist was removed, as was the home page's
present-tense claim to run the model in the browser.

**New machinery.** `src/inputs_preflight.py` checks that a forecast of an unheld
election has its inputs. `src/backup_ignored.py` copies every gitignored file.
`build_site.py` now emits `site/regimes.json`. `build_validation.py` gained
`--from-json` and records its seed and git commit.

**Documents.** A pre-registration, several audit notes, a rewritten `TODO.md`,
and the judgement sheet gained an internal section and was briefly published
then unpublished.

## Where to look hardest

1. **`site/` against what the generators produce.** Nine pages ship. Does the
   tree rebuild them identically? `deploy_check.py` is supposed to refuse
   otherwise — confirm it would.
2. **The four re-sourced figures.** Are the new values what the ledger says was
   published on 8 August, and do the arrows now point the way the numbers moved?
3. **The `/about` figures.** Do the numbers on the page match
   `data/processed/validation_2021.json`? Does the rewritten caveat describe
   what the code now does?
4. **The retirement.** Was `claim.da_alone.wall_anc_high` retired correctly, and
   is the ledger still internally consistent?
5. **The new tests.** Do they fail when they should? A test that cannot fail is
   worse than no test. Construct a violation for at least the frozen-figure one.
6. **Anything that reads as an overclaim to a reader**, in the changed prose.

## Ground rules

Read-only. ⛔ **DO NOT RUN** `src/montecarlo.py`, `src/build_validation.py`
without `--from-json`, or anything with `--emit`: they write into
`data/processed/`, which is gitignored, and one of them already destroyed an
artefact this week. `src/build_site.py --out <a scratch path>` is safe and is
the right way to check the pages. `.venv/bin/python` for anything you run.

Say plainly if a change is correct. The useful output is a verdict per group
and a list of anything that must be fixed before this is deployed — not a
list of everything that could be improved.
