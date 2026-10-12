# Step 8 writer brief: the stale-spec refusal (2026-10-10)

One writer. Branch `remediation`, starting at `7405e21`. M1-M4 are committed
and reviewed, fix rounds included (`reviews/M*-SUMMARY.md`, SPEC R3.6 addenda).

## Read first
- `CLAUDE.md`, `QC.md`.
- `audits/2026-10-09-model-fixes/spec/SPEC.md`:
  - §1.9, item 10's first row (the stale or unreadable pool spec stops the run);
  - §3's G10 row;
  - §5 (re-emit and batching), §7 step 8;
  - Revision 3 through the last R3.6 addendum (the known-red list).
- `src/montecarlo.py` around `run_model`'s pools block (`_stale`,
  `scenario["_pools_stale"]`, the `02_pools_artefact` stage) and every reader
  of `_pools_stale`; `pools.stale_reason`.

## Scope: writing-order step 8, one commit
1. `_stale` truthy refuses: `SystemExit` naming the file, the reason, and
   "Re-emit (POOLS-REEMIT-QUEUE.md)". The `except Exception` path refuses the
   same way with `exc!r`. Refuse before anything downstream reads the spec.
2. The only escape is `scenario["allow_stale_pools"] = True`: not in
   `DEFAULTS`, not settable by a city file (add it to the same kind of register
   as `DERIVED_NOT_CITY`, or refuse it in `apply_city` by the same rule), set
   explicitly by a diagnostic run. When it is used, the run prints the stale
   reason, and the trace (`02_pools_artefact`) and `forecast_summary.json`
   record that the escape was used. Check the stage-field pin in
   `tests/test_stage_inputs.py` and change it once, deliberately.
3. G10 in `tests/test_stage_inputs.py`, constructed: a spec with a moved
   `pools_sha` makes `run_model` raise; a `stale_reason` that raises makes it
   refuse; `allow_stale_pools=True` runs and records it. Each mutation (the
   refusal removed; the `except` path failing open) is caught, and the test
   goes quiet when it is reverted.
4. Docs in the same commit: the docstring, `MACHINERY.md`, `POOLS-REEMIT-QUEUE.md`
   (a stale spec now refuses rather than warns), and a JUDGEMENT-CALLS or
   register entry only if the escape is a lever.

Every spec is stale until the window re-emits (`stale_reason` reports it now),
so this refusal turns red every test that runs the model on a real spec. That
is by design. List each such test in a dated SPEC R3.6 addendum, grouped by
cause, with the count per module. Do not weaken a test to pass, and do not set
`allow_stale_pools` in a test to keep it green unless the test's subject is
not the spec (say which, and why, in the addendum).

**Not in step 8:** the pre-registration (step 9), the window, the measurement,
the suite.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`: no `--emit`, no `compare_history`, no bare `montecarlo.py`.
  In-process `run_model` writing to temp is allowed. `-k temporal` rewrites two
  `data/processed` files by design; avoid it unless the change reaches it.
- **Every party, the same rule.** Nothing here names a party.
- Targeted modules after the last edit, quoted in the commit body: pass and
  fail counts per module, every failure assigned to R3.2, R3.5 or R3.6, or
  fixed. Include `-k stage_inputs -k regressions -k provenance_gates
  -k register -k model_index -k blended_centres`, plus whatever else it reaches.
- If credit runs short, stop. Never leave a half-made step committed.

End each message with:

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
- The commit hash, what changed, the test table.
- Every deviation from the spec, and why.
- The full list of tests the refusal turns red, by module.
- Anything the pre-registration (step 9) or the window must now do differently.
