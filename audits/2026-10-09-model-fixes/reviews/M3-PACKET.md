# Slice M3 diff review packet (items 11a, 16, 17, 12, 13/18)

Issued to one fresh reviewer, 2026-10-09. The review is blind: you get the
specification and the diff `git diff 309481f..22dadaa`, not the writer's
account of it.

## Ground rules
- **Read-only.** Edit nothing.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`, and nothing remote:
  - not `group_share_record.py --emit`;
  - in-process imports and tests are allowed, writing to temp directories only.
- **Use scratch trees for before/after comparisons:** `git archive` of each
  commit, with a copy of `data/`. Run with `PYTHONHASHSEED=0` and a fixed seed.
- Use `.venv/bin/python`. Do not sub-delegate. Credit is limited, so be
  economical.
- **Read:**
  - `CLAUDE.md` (§1–§4, especially "level and shape" and the four-part
    absence rule) and `QC.md`;
  - `audits/2026-10-09-model-fixes/BRIEF.md`, including every owner decision
    (items 11–13, 16–18);
  - `spec/SPEC.md`: §0 O1, O2 and O8; §1.10–§1.12; §1.9a; §3 G13–G15; and R2.1,
    R2.2, R2.3, R2.6 and R2.7;
  - Revision 3 and every R3.6 addendum (the expected-red list is there).
  - `reviews/M3-WRITER-BRIEF.md`, the brief the writer worked to.

## Questions
1. **Item 11a.**
   - Is the size centre evaluated at the party's current size, for every party,
     in one shared body?
   - Do `theta_prior` and `_shrunk`/`spine` agree party for party?
   - Is any second definition left? Name one in `src/theta_residual.py` or
     anywhere else.
2. **Item 16.**
   - Is the similarity window derived from data, not typed?
   - Is the derivation free of the target's own result: does the window's error
     table read only elections before the target?
   - Re-derive one window yourself. Check the 2026 θ window and say whether
     the method is estimation or tuning in CLAUDE.md §4's sense. Fitting
     against a ratio defined on our own output is barred.
   - Are the registered constants in §A52 judgement calls, and stated
     concretely?
3. **Item 17.**
   - Does a party with no record take the size-group average and range at its
     current size?
   - Is `level_shock_sd` the one definition of a party's level sd?
   - Does `level_sd_default` still bind anywhere, and what in the code says so?
4. **Item 12.**
   - Does the tripwire change no drawn number? Re-derive this: run with the
     record present and with it absent, and compare the drawn arrays.
   - Is its threshold the registered one: record plus the largest one-cycle
     rise, at the share of draws in §A54?
   - Can G14 see a firing, and go quiet when it is reverted?
   - Is G15 a real regeneration test, or does it pass by never rewriting? The
     isolation is a fresh output directory only.
5. **Items 13/18.**
   - Is the SACP now on the generic entrant route, with nothing about it
     special left in the code or the judgement file?
   - Is the public methodology change accurate?
6. **Baselines re-recorded.** The writer re-recorded the KEY 4 and PIT
   baselines in a885b28.
   - Is the re-record deliberate, with the reason written down (CLAUDE.md §2)?
   - Was it measured against real elections, not against a prior output?
   - Does anything else now compare against a value that moved without a
     record?
7. **Guards.** For each of G13, G14, G15 and G19–G22, check the four-part rule.
   Name any that can pass while blind.
8. **`41_guards`.** The field pin gained `bounds_base`, `level_sd_at_size` and
   `group_share_tripwire`. Is each written, read and checked consistently? Is
   any new exemption delegated to what the drawer records?
9. **Cost.** `size_window` adds wall time to every model-running test.
   Is that a correctness risk, for example a timeout, or a caching shortcut
   that would make a stale result look current?
10. **Expected red.** Is each failing test on the R3.6 list red for the cause
    given?

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
