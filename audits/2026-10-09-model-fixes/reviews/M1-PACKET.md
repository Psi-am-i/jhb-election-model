# Slice M1 diff review packet (the seat law and its records)

Issued to one fresh reviewer, 2026-10-09. Blind: you get the specification and
the diff, not the writer's account of it.

## Ground rules
- **Read-only.** Edit nothing.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`, and nothing remote. In-process imports and pure tests are
  allowed, writing to temp directories only.
- Use `.venv/bin/python`. Do not sub-delegate.
- **Read:**
  - `CLAUDE.md` and `QC.md`;
  - `audits/2026-10-09-model-fixes/BRIEF.md`, including all of the owner's
    decisions;
  - `spec/SPEC.md`, including Revision 2. M1 is writing-order steps 1 and 2:
    items 1, 2, 4 and 5 and their guards;
  - `audits/2026-10-09-site-batch/law/SUMMARY.md` (D1–D10) and the statute
    PDFs in `law/sources/`.
- The diff is at the path given to you.

## Questions
1. **Statute fidelity.**
   - Integer surpluses: an equal surplus goes to the higher vote, as items
     13(2)(b) and 16(4)(c) say.
   - The seeded lot applies only where the statute is silent.
   - Ward ties are settled by lot, as item 8(2) says.
   - Check each against the saved Act text.
2. **The lot.**
   - It is deterministic, with no party name in its seed.
   - Every caller passes it.
   - A tie with no key raises; it is never silently decided by input order.
   - The build, the page, the Worker and the scorer share one key scheme.
   - Name any caller that still breaks ties by order.
3. **Draws.** Can any change move a draw that has no tie? Re-derive this
   in-process: a short run at the published seed, compared with the published
   draws.
4. **Laingsburg.** Is `test_overhang` now pinned to the IEC's real votes? Does
   it reproduce the published council and round-two ranking? Is its
   wrong-denominator check a real detector?
5. **One definition.** Is there a second tie rule, surplus computation or lot
   scheme anywhere?
6. **The guards.** For each of G1–G6: the population is stated and checked both
   ways, a constructed violation is caught and goes quiet when reverted, and
   the input is constructed rather than observed. Can any pass while blind?
7. **Records.** JUDGEMENT-CALLS §Q2, §Q5, §Q6 and §M1, MACHINERY, and the
   docstrings: accurate against the statute and the code, with no typed
   figures.
8. **Deployment risk.** The writer notes that the new `reader_seats` requires
   the lot, and that the page's `forecast.json` must carry it before the seat
   Worker is redeployed. Is that order recorded where a deployer will read it?
9. **The check-step list.** Is any module missing? The coordinator ruled that
   the whole suite runs once, at the end of the batch, not after this slice. Is
   there a risk that ruling misses something only a whole run would catch now?

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
