# Making the model auditable: a graph structure, proposed

**Status: a proposal for discussion. Nothing here has been built.** It exists
because reviews of this model now cost more than the changes they review, and
that curve gets worse, not better.

---

## 1. Why auditing costs what it does — measured, not asserted

These are the numbers, taken from the current tree:

| | |
|---|---|
| `run_model` | **863 lines**, one function, `montecarlo.py:1760–2623` |
| distinct local names bound inside it | **223** |
| writes into the shared `scenario` dict inside it | **16** |
| **function-local imports** inside it | **7**, at lines 1812, 1875, 1911, 2310, 2311, 2345, 2394 |
| `run_model` call sites in the suite | 11, across 5 of 10 test files |
| full-suite wall clock | ~35 minutes |
| a single `compare_history` run | ~50 minutes at 1500 draws |

Four consequences follow directly, and each one has already cost this project
real time:

**There are no small units, so every check is a whole-model check.** Every
intermediate quantity in the level chain — the θ record, the shrunk estimator,
the spine blend, the by-election clamp, the capacity guard — exists only as a
local inside those 863 lines. To see one, you run all of it. That is why the
lever sweep runs about fifty full models to answer a question that is really
"which parameters does this constant reach".

**The dependency graph is invisible.** `levels.spine` is called at line 2345,
`levels.theta_prior` at 1911, `pools.contesting_parties` at 1875 — all through
imports written *inside the function body*. Nothing at the top of the file says
`montecarlo` depends on `levels` or `pools` at all. The order of the level chain
is not declared anywhere; it is wherever those lines happen to sit.

**The input is also the scratchpad.** `scenario` is passed in and then written
to sixteen times. That is why `apply_city` silently overwriting `DEFAULTS` was
so hard to see, and why `--set` has to be applied *after* `apply_city` with a
comment explaining that it is the only override that survives.

**The biggest edge in the system is a file.** `montecarlo` and `pools` are
joined by `data/processed/pools_*.json`, which is precomputed. Changing
`pools.py` does nothing until it is re-emitted, and re-emitting it changes the
baseline of every measurement anyone else is taking. `CLAUDE.md` carries a
whole section — *"one writer, and nobody measures while it writes"* — whose only
job is to compensate, by human discipline, for an edge that is untyped,
unversioned and unchecked. It has already failed twice: a lever sweep returned
different answers on two identical runs, and two `EXPECTED_INERT` reasons were
written from those unstable readings and had to be retracted.

**The pattern in the defects.** Look at what actually went wrong recently: a
ceiling that went blind and reported silence as success; a wrong-city ward roll
loaded by fallback; an arrival total read from the wrong aggregate; `theta_mode`
reading live because artefacts moved underneath the measurement; a `{CODE}`
template never substituted. **Not one of these is a modelling error.** Every one
is a boundary error — data crossing between stages without anything checking
what crossed. That is precisely the class of defect an explicit graph removes,
and precisely the class that more end-to-end testing does not.

---

## 2. The five primitives, mapped onto this model

Using the document's vocabulary — NODE, EDGE, STATE, ROUTER, GATE — against
what already exists.

### The nodes are already there; only the boundaries are missing

The model is not a tangle. It is a fairly clean pipeline wearing a monolith:

```
  baseline (preceding NPE citywide shares)
      |
      +-- theta record ---+
      |                   +--> shrunk estimator --> SPINE --+
      +-- rho record -----+                                 |
                                                            +--> ROUTER: which
  by-election evidence ---------------------------------->  |    route does this
  poll evidence ------------------------------------------> |    party take?
  arrival record (seeding) -------------------------------> +
                                                            |
                                                    compress_levels
                                                            |
  pool fit (ecological inference) --> Duncan-Davis bounds --+--> pool_spec / IPF
                                                            |
  turnout model ------------------------------------------> +
                                                            |
                                                        THE DRAW
                                            (level shock, copula, Dirichlet)
                                                            |
                                              ward allocation --> seats + overhang
                                                            |
                                                    scoring / calibration
```

Almost every box is already a function. What is missing is that a box has no
**contract** — no declared input, no structured output, no failure state — so
nothing can be checked at its edge, swapped behind it, or run without the rest.

### The router already exists and is the most-audited code in the repository

`blended_centres` chooses each party's level route by an `if/elif` chain: poll →
seeded arrival → spine → `theta_prior` → `theta_mode` → `individual_theta` →
`f_other`. That *is* a router. It is also where four dead branches have been
sitting, where `note_constant` was bolted on to find out which branch fired, and
where the in-sample provenance banner gets its content.

The question "why did this party take this route?" is asked constantly and
currently answered by instrumenting the code and re-running it. A router that
records its decision with the state that produced it answers it from the run
record, for every party, for free.

### The gates exist too, but as scattered assertions

The Duncan–Davis bound check, the pool-capacity guard, the IPF feasibility
refusal, the temporal-leak tests, the doc-vs-artefact test. These are gates. The
weakness is that each one decides locally what to do on failure, and the answer
has historically been `except Exception: pass` — which fired on 41.8% of the
published forecast's draws without anything reporting it.

### State is the part this model hides, exactly as the document warns

Right now state is: 223 function locals, one mutable `scenario` dict, and a set
of JSON artefacts with no version, no provenance and no hash.

---

## 3. What I would actually propose — staged, cheapest first

Each stage is useful alone, and none of the later ones is required to bank the
earlier one.

### Stage 0 — the run manifest. No refactor at all.

Emit, from every run, a record of what each stage read and produced: input
hashes, output hashes, parameters consumed, routing decisions taken, gates
fired. The pieces already half-exist — `constants_read`, `notes`,
`cap_moved`, `overhang_count`, `bounds_violations`.

This is a few days of work, changes no numbers, and would have caught **every
one of the boundary defects listed above**. It is the highest
value-per-unit-risk item on this list by a wide margin, and I would do it first
regardless of whether the rest ever happens.

### Stage 1 — give the level chain real contracts.

Extract the chain from `baseline` through `compress_levels` into nodes with
declared inputs and outputs. Reasons to start here and not elsewhere: it is
already a chain conceptually, `MACHINERY.md` §2a already documents it as one, it
is the most frequently audited area of the model, and it is where the last two
substantive changes landed. `run_model` becomes an orchestrator over it rather
than the place it lives.

### Stage 2 — kill the artefact edge.

Make `pools_*.json` content-addressed: keyed by city, target, code version and
config hash. A stale artefact then becomes *detectable* instead of being
prevented by a rule in `CLAUDE.md` that humans have to remember. This directly
retires the "one writer" protocol, which is a discipline tax on every session
and has already failed twice.

### Stage 3 — fan out the city-years.

The nine city-years are genuinely independent — a textbook diamond, and
currently a serial loop costing ~50 minutes. This is the single biggest
wall-clock win available, and it is *blocked* on Stage 2: they can only run
concurrently once each owns its artefacts. Note the ordering — parallelism is a
consequence of fixing the edge, not an alternative to it.

### Stage 4 — node-level tests displace some end-to-end tests.

"Which levers does this constant reach?" becomes a question answered from the
manifest rather than by fifty model runs. The end-to-end tests stay — they are
the guard on the whole — but they stop being the *only* instrument.

---

## 4. Where the graph idea is the wrong answer here, honestly

The document is written for **agent** systems, and most of its value does not
transfer:

- **Our nodes are deterministic functions, not model calls.** Routers over
  probabilistic judgement, verifiers that check an LLM's claims, and
  cycles-until-convergence are the parts of that document that solve problems we
  do not have. What transfers is narrower and duller: contracts, declared
  edges, durable state, local failure policy, parallel fan-out.
- **Do not build a graph engine.** The failure mode is spending weeks on a
  scheduler and ending with the same defects plus a framework. The value is in
  the contracts and the manifest; the orchestrator can stay a plain function
  calling nodes in order.
- **Some things must not be split.** The draw loop is a per-draw IPF over 1500
  draws sharing arrays for performance. That is one node, not 1500. Node
  boundaries belong where *data crosses a conceptual boundary*, not wherever a
  loop exists.
- **The document's own last check applies: "is the graph simpler than the
  problem it solves?"** For nine city-years and one pipeline, a 40-node graph
  would not be. I would expect roughly 12–16 nodes.

---

## 5. The constraint that governs all of it

**A refactor cannot improve prediction, so by `ITERATING.md` it can only be
neutral or bad.** Every number must be unchanged, and the golden prior is the
instrument that proves it — which means the goldens must **not** be re-recorded
at any point during the refactor. A re-record during a refactor destroys the
only evidence that the refactor was safe.

That argues for sequencing: **land the modelling work first, let the goldens
settle, then refactor against frozen numbers.** Doing both at once means the
goldens move for modelling reasons and the refactor's guarantee evaporates.

We are well placed for this: 124 tests, a golden prior on the drawer, a
nine-city-year scoreboard, and a committed artefact. That is an unusually good
harness to refactor behind — but only while it is holding still.

---

## 6. What I would want to agree before building anything

1. **Stage 0 alone, first?** It is cheap, safe, and independently valuable. I
   would recommend committing to it and deciding the rest afterwards, on
   evidence from it.
2. **Is wall-clock or auditability the real pain?** They point at different
   stages — 2 and 3 for wall clock, 0 and 1 for auditability. My reading is
   that auditability is the binding constraint and slowness is a symptom, but
   that is your call to make.
3. **How much behaviour change is acceptable?** My assumption is *none* — bit
   identical, goldens untouched. If some drift is acceptable the work gets much
   cheaper and much less safe.
4. **When?** I would not start while the level shrink's follow-ups (the tail,
   `SD_FLOOR`) are still moving the numbers.
