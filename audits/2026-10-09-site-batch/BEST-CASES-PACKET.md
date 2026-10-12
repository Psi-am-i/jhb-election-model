# Item 8 packet: each party's best case, and what had to happen

One agent. **Write only to `audits/2026-10-09-site-batch/best-cases/`.** Do not
run `src/montecarlo.py` as a script, `compare_history`, `build_site`, or
anything that writes `data/`, `site/`, `content/` or `publications/`. Reading the
published draws (`site/draws/`, `data/processed/seat_detail_draws.csv`,
`ward_draws.csv`) is allowed. So is an in-process `run_model` at the published
seed (5,000 draws), if you need per-draw quantities the files lack; output goes
only to this directory. Use `.venv/bin/python`. Do not sub-delegate.

Read `CLAUDE.md`, `STYLE.md` (rule 11: a single simulation is neither a
forecast nor a prediction), `src/scenarios.py` (`matching`, `modal_winners`,
`flips`), `src/reweight.py` (pool turnouts), `MACHINERY.md` on what each draw
varies, and `src/render_map.py` (map drawing).

For each party with a real chance of seats (ANC, DA, ActionSA, EFF, PA, MK, and
any other party whose best 1% reaches 5 or more seats):

1. **Its best 1% of simulations** by its total seats; state the cut. Report:
   - the seat range across that group;
   - its ward seats and its list seats;
   - how often excessive seats fired for it or for others;
   - the largest party and the coalitions that reach a majority, at the
     group's median.
2. **What those simulations have in common, against all simulations:**
   - turnout by voter group (`pool_turnout`);
   - the party's ward-ballot and list-ballot share, and its rivals';
   - which wards it wins that it usually loses, and where they are, by region
     or area if the repository names areas (`content/joburg/areas.toml`);
   - every per-draw driver the model records, as named in MACHINERY or the
     trace.

   Separate drivers from consequences. For example, more ANC wards is an
   outcome, not a cause. Say which variables the model draws and which follow
   from them.
3. **One representative map:** the simulation in the group closest to the
   group's median on the six main parties' seats. Draw it with `/forecast`'s
   colours, solid winners, labelled "One of the 5,000 simulations: <party>'s
   best 1%". Also draw the group's ward-win frequency for the party as a
   shaded map.
4. **Plain-language findings** per party, three to five sentences each, in
   STYLE.md's voice. Every figure carries what it is and over which group. Say
   what the model can and cannot explain. Where the model's drivers are too
   coarse to say why (it has no campaign or candidate variables), say so
   directly.

Return: the per-party findings, the file list, and the variables you used,
marked as drawn or derived.
