# Blind review brief: the freeze batch, and five open decisions (2026-09-29)

You are a senior election forecaster and survey methodologist reviewing for the
owner of a public forecast of the City of Johannesburg election on 4 November
2026. Load and follow the `pollster` skill before you start.

**You have the repository. You do not have the lead's reasoning or
recommendations, and that is deliberate.** Read only: do not edit any file, do
not run `src/montecarlo.py` or `pools.py --emit`, do not write under `data/`,
and do not delegate to other agents. You may call `run_model` directly for a
check (see `audits/2026-09-28-route-b/routeb_proto.py`). `src/pools.py` has
uncommitted changes in the working tree, and they are part of what you are
reviewing.

## The situation

The model is about to be frozen. After launch, readers' saved forecasts depend
on it. The plan is `TODO.md` §0; the owner's decisions are in
`audits/2026-09-27-interactive-levers/DESIGN-decided.md` §7–§9. Work done since
2026-09-28, each with its record:

1. **The interactive's inputs.** `src/citywide_table.py` (MODEL-LOG
   §1.265–§1.267, `audits/2026-09-28-route-b/`).
2. **Architecture.** The page re-weights the 5,000 published draws.
   `audits/2026-09-28-interactive-architecture/` (PLAN.md, INTEGRATION.md), and
   the built engine `src/export_draws.py` and `src/reweight.py` (§1.271,
   `prereg/2026-09-28-reweight-against-paired-rerun.md`).
3. **Per-draw pool turnouts recorded.** `tests/test_draw_record.py`.
4. **Pool-seed sensitivity.** §1.268, `audits/2026-09-28-seed-survival/`. It
   led to C3's composition side and C4 being deferred.
5. **F3, the conservation repair.** Uncommitted `src/pools.py`; §1.269,
   JUDGEMENT-CALLS §L14, `audits/2026-09-29-f3-conservation/`.
6. **A reader's forecast turned into seats by statute.** `src/reader_seats.py`,
   §1.270, JUDGEMENT-CALLS §M1.
7. **Mergers.** Not built; the specification is
   `audits/2026-09-29-mergers/SPEC.md`, and the prereg is
   `prereg/2026-09-27-independents-and-mergers.md`.

## Part A: review the work

Is each of 1–6 methodologically sound for a forecast that will be frozen and
published? Look especially at:
* re-weighting published draws as a stand-in for re-running the model: what it
  can and cannot honestly represent;
* F3's choice to hold a pool at the city's own rate rather than partially pool
  it, and what that does to the other pools it re-fits;
* the decision to defer C3/C4 on outcome grounds;
* anything in the batch a hostile expert with the repository could fairly call
  misleading.

## Part B: your opinion on five open decisions

Each is stated neutrally. Give your recommendation and why, and say what
evidence would change it.

1. **Merger retention.** What share of a merged-away partner's baseline should
   move to the partner on the ballot? The spec proposes a declared, unmeasured
   judgement with a range. Is that the right treatment, and what value or range?
2. **Whether a merger may create a record the successor lacks.** RISE has a
   2024 national record but no 2021 local one. Should GOOD's 2021 local vote
   give RISE a local record (the spec says this would pull RISE *down* through
   the blend), or should the transfer apply only to records RISE already holds?
3. **Amending the merger prereg.** Two of its premises are shown false in
   SPEC.md §0, and no result exists yet. Amend it with a dated section, rewrite
   it, or leave it and score it as written?
4. **What a reader edits.** A reader's own forecast is turned into seats by
   statute (§1.270). The statute sizes entitlements from the combined ward and
   PR vote; the model's two ballots differ. Should a reader edit (a) the
   combined vote, (b) the PR vote converted with the model's per-party
   ward-to-PR ratios, or (c) something else?
5. **Contact verification at sign-up** for readers who save a forecast (see
   `worker-api/README.md`: some providers return an unverified email, and
   unverified contacts would never receive the post-election message). This is
   outside a pollster's usual scope; answer only if you have a view.

## Output

A specification under 1,500 words:
* numbered findings for Part A, each with the file and line it rests on, and
  whether you verified it or read it;
* a clear answer to each of the five questions.

Say where you are uncertain and what measurement would settle it.
