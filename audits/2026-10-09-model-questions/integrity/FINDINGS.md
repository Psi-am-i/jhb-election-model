# Model integrity review, 2026-10-09 (condensed from the reviewer's report; its write was refused)

Run: in-process `run_model`, published seed, `PYTHONHASHSEED=0`, at commit
75123b3. **The live tree reproduces the published draws: all 5,000 seat
vectors are identical**, so every finding below describes the published
forecast. Scripts are in `scripts/`.

**Coordinator check (verified):** none of the seven certified-roster parties in
F4 appears among the run's 74 parties.

| # | finding | severity |
|---|---|---|
| F1 | The PA's ward/list ratio is clipped at 2.0, and no real case exceeds 1.53 (PA's own maximum is 1.10). Real elasticity of the ratio to contestation is 0.54, against the code's 1.0 (289 transitions). Holding slates at 2021: PA 24.1 → 16.6 seats. Its clip literal is a second copy, separate from `WARD_PR_RATIO_MIN/MAX`. The comment at `montecarlo.py:4792-4795` is stale | high |
| F2 | The PA takes a median 87% of the Coloured vote cast (p95 98%), against its fitted 2021 rate of 0.515. The capacity guard cannot fire: every party has weight in every pool, so its capacity is the whole electorate. Multiplying the PA's centre ×12 gave a 45% PA, and every counter stayed at zero. MACHINERY lines 154 and 426-429 describe the guard as if it worked | high |
| F3 | The canary: 46 seeded parties have no level shock, because the arrival band "carries" the uncertainty, and that band is read by nothing (§1.198). They are not narrow: the Dirichlet gives them an sd(log) of 1.7–2.3 | high (the record is false) |
| F4 | Seven certified-roster parties with a 2021 local record (0.30% together) get zero votes in every draw. The run's party list is built from the 2024 national baseline plus seeds (`montecarlo.py:4387`). Nothing checks roster → universe (CLAUDE.md §4 item 0) | medium |
| F5 | A group's turnout swing never reaches the ward layer: per-VD turnout has no pool term. Separately, the pool turnout bands are wider than any observed year; citywide turnout falls outside Johannesburg's observed range in 30% of draws | medium |
| F6 | A stale or unreadable pool spec only warns, and the run continues. If the staleness check itself crashes, the spec is treated as unverified | medium |
| F7 | The run uses the 2024 roll. The 2026 roll is read by nothing, yet preflight reports it `[ok]`. Ward totals disagree with the IEC's by sd 17% in wards with split VDs. Rescaling moves no measurable seat | low |
| F8 | `levels._citywide` still returns `{}` for a renamed party column. Latent: the run path reads cleaned files | low |
| F9 | `bounds_checked` counts draws, not checks. PLAN_BOUNDS violations (ANC 56% of draws) are never acted on. The orphan guard only warns | low |
| F10 | Unregistered defaults: γ = 1.0 for 56 parties, MK included; a city-mean turnout fallback for 40 VDs (1.9% of the roll). The manifest publishes centres before normalisation. Spoilt ballots sit inside turnout, with no seat effect | low |

**Q2: real-world variation against the model.**
- **New parties.** Arrivals from nothing: median 1.7% of the vote. Real mass new
  to the ballot: median 6.1%.
- **Candidates and independents.** Ignored. Independents took 0.3–8.3% of the
  ward ballot and won 12 wards across the panel.
- **Ward-level local effects.** Comparable to real results (sd 0.12 against
  0.084–0.112).
- **Split tickets.** Fixed per party. The PA is outside every real case.
- **Registration.** Fixed at the 2024 roll.

**Rejected claims, with the evidence that killed each:**
- "The published draws came from code that has since moved": the live run
  matches all 5,000 seat vectors.
- "`level_sd_default` binds": no party takes it.
- "The 2026 roll explains the PA": rescaling moves the PA by −0.08 seats.
- "Spoilt ballots bias seats": the allocation is scale-free.
- "The by-election clamp silently uses PLAN_BOUNDS": the clamps use the θ band.
