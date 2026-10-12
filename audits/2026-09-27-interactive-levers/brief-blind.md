# Blind review brief — the reader-facing interactive, and the published forecast

You are reviewing for the owner of a public election forecast for the City of
Johannesburg, which votes on 4 November 2026. The site is live.

**You have the repository. You do not have the lead's reasoning, and that is
deliberate** — a review that is shown the argument reviews the argument.

## What is being asked

Two questions, in this order.

**1. Is the currently published forecast defensible?** It is live now at
joburg.whysoserious.city. Not "is it perfect" — is there anything in it that
should not be in public, or that a hostile reader with the repository could
fairly call misleading?

**2. What is missing from the plan below?** Not a list of its errors — an
answer to what a reader, a journalist or a rival modeller would ask that the
plan has no answer for.

⛔ **Finding faults is not the goal and is not what makes a useful review
here.** Previous reviews on this project were most valuable when they said what
the work was actually doing, including where it was right for reasons the lead
had not stated. If the plan is sound, say so and say what it costs.

## What is published now

* A forecast at 5,000 draws, seed 20261104, with per-party seat medians and
  bands, a who-can-govern coalition table, a ward map, and claims by named
  politicians tested against the model.
* Every figure a reader sees is a token carrying its own provenance, and a
  publication ledger records what each figure said when.
* `docs-public/` holds the methodology, the sources, the corrections and a
  review page.
* Polls were removed from the forecast on 12 September 2026 and are not an
  input today.

## What is planned

An interactive page where a reader changes assumptions and re-runs the real
model in the browser under Pyodide, then hand-draws a forecast of their own.

1. **A seat-law control.** The forecast under four laws: ours (surplus deducted
   from everyone), the old German rule (council grows), the modern German rule
   (everyone topped up to proportionality), and pure proportionality at a fixed
   270. All four are already computed and committed.
2. **Two model controls**: how much support moves between parties inside a
   population pool, and how much weight by-elections carry against history.
3. **A turnout control** — overall level plus a per-pool differential, entering
   after the IPF. Decided, not built.
4. **Hand-drawing.** A reader picks the winner in any of the 135 wards and sets
   the citywide PR vote, and the page then tells them how their map compares
   with the model's simulations.
5. **Sharing.** A reader's forecast travels in a URL; whether it may be stored
   is undecided.

Measured, and load-bearing for the plan:

* Ward outcomes are strongly correlated. The ANC's ward wins average 60.5 with
  an actual spread of ±22.3 across draws; if wards were independent the spread
  would be ±3.7, and the observed range is 0 to 104 wards.
* No single map is likely. The model's own most-likely map is drawn in 0 of
  5,000 simulations; the closest draw differs in 2 wards, the median draw in
  19, and two random draws differ from each other in a median of 32.
* Effect sizes for the candidate controls are in `MEASURED.md` beside this
  brief. Two candidates were dropped because they move under a tenth of a seat.

## Specific things worth an opinion

* The scoring of a reader's hand-drawn map. The plan is to report distance in
  wards against the simulations rather than a probability. Is that the right
  quantity, and what would you report?
* Running the model itself in the browser rather than a simplified copy, at 300
  draws against the published 5,000.
* Whether a control a reader moves should be allowed to change the headline
  forecast the site publishes, or only a copy of it.
* Anything about the published site you would take down.

## Ground rules

Read the repository. `HANDOVER.md` is where the branch stands, `MODEL-LOG.md`
is the dated record of findings, `JUDGEMENT-CALLS.md` is every choice a person
made that the data did not force. Quote what you rely on. Where you are
uncertain, say which measurement would settle it rather than guessing.
