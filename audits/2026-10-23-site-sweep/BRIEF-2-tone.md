# Brief 2: tone sweep of the live site

Owner, 2026-10-24: "and do a tone sweep please." Evidence:
`audits/2026-10-23-site-sweep/tone.md` (read-only audit, 23 October) and
FINDINGS.md §4. Runs after the freeze-release content fixes, on the same
release; a writer makes the edits, I review the diff, then `/code-review`,
UAT, the owner's yes.

## The rules applied

1. **STYLE.md rules 0–11**: dry, every sentence informs, no lilt, no
   telling the reader what matters; corrections say what was wrong and what
   is right, nothing else. **The test for "informs":** delete the sentence or
   heading; if the reader has lost no fact, it goes. Example that fails: a
   bold lead "ActionSA's level is This Model's own." (everything on the site
   is This Model's).
6. **No new words.** The writer removes and replaces wording only as this
   brief lists. Any sentence the sweep would add that the brief does not name
   is listed for the owner, not written.
2. **"This Model"** in reader text wherever the site means its own model,
   never "the model", "our model", "the simulations' engine". Internal terms
   (pools, draws, seed, overhang, θ, modal, the file or script names) never
   appear; say what they do.
3. **Forecast, prediction, result** (STYLE.md rule 11): This Model makes a
   forecast; a reader makes a prediction; an election produces a result.
4. **All parties or none.** No control, range or treatment applies to one
   party.
5. **Written pieces are frozen.** Articles (6 and 8 August) and other dated
   pieces are not rewritten; their teasers reprinted on live pages are live
   text and are swept.

## Work

**A. "the model" and internal terms on live pages** (about 60): index,
sources, your-forecast (and its JS strings), support, privacy, methodology,
forecast, two meta descriptions, the page header ("what the model says now").
Hard leaks removed: the forecast footer naming `src/render_sheet.py`, "seed
20261104", "(simulation 633)" and its tooltip, "the DUDULA 7.9%", bar
data-tips spelling internal codes ("Bosa", "Vfplus", "Rise") instead of
party names.

**B. Forecast / prediction / result** (about 19): the home page's "Your
Forecast" block says "prediction" where the reader's own call is meant; the
interactive is named one way throughout (see decision 1); "a changed
forecast", "the most typical result" and similar fixed to the right term.

**C. Lilt and telling the reader what matters** (about 12): e.g. "and it has a
quirk", "but not just any values", "But historical…". Removed or replaced by
the fact.

**D. Tooltips:** "21 October 2026." on claims.html (18) gets the standard form
"<value> since <date>."; the six one-line tooltips on laingsburg and
nobody-will-win ("Is now 68.") get the standard two lines with SOURCE.

**E. Corrections entries saying more than two parts** (4): cut to "what was
wrong / what is right". The entries' headings and dates do not change.

**F. Repository records:** STYLE.md updated to the rules above (rule 3's
"What changed" becomes "What is right"; rule 11's page name; rule 1's example;
rule 6 made consistent with "This Model"). A test scans live body prose,
data-tips, meta descriptions and aria labels for "the model" and the internal
terms, with a planted-violation case (CLAUDE.md §4: it must show it looked,
can see, and scanned the right set).

## Decisions for the owner (default in brackets if not answered)

1. **The interactive's name:** "Your prediction" everywhere (the URL
   `/your-forecast/` stays) — or "Your forecast". [Your prediction: a reader's
   call is a prediction under rule 11.]
2. **The home lede's "That is surprisingly likely this year"** came in as your
   own wording (64ef092). Keep it, or cut it under the lilt rule? [Keep: your
   words.]
3. **Dated claim cards (7 Aug, 26 Sep, 7 Oct):** frozen like articles, or
   swept? They carry "turnout fantasy", "special universe", "Not close.",
   "Helen" ×2. [Frozen: they are dated pieces.]
4. **The forecast page's coalition box** fixes "the DA without the ANC, EFF or
   MK" and calls it "its one realistic option" — one party's view singled out.
   It comes from your definition for the Mashaba claim (REALISTIC_PARTNERS,
   7 October). Keep it on the claim card only and take it off the forecast
   page, or keep both? [Claim card only.]

## Limits

Branch `site-sweep-1`; no forecast number changes; tokens stay tokens. No
corrections entry: nothing published was wrong. Targeted site tests, then the
whole suite once for the UAT version.
