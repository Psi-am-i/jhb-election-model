# 2. Recheck of 1j v3 (targeted)

Targeted recheck of `step1/1j-universal-draw-design-v3.md` (0c3700f) against
the items of `2-recheck-1j-v2.md`. The same constraints apply: read-only on
code, no model run, no `compare_history`, no emit, nothing under `data/`, no
sub-delegation. My scripts are `review1j/r30.py` (anchors and fit tests) and
`r31.py` (Johannesburg 2026). They are my own code, they run before v3's
location fixed point, and none of `uni3/` is imported.

## Verdict

**Ready for the owner's checkpoint, once the owner-choice text is corrected.**
Both blocking items from the v2 recheck are resolved. No new blocking item.
The decisive numbers reproduce.

The presentation of option A against option B overstates B (findings 3a-3c).
Those are wording corrections to the summary and §2.3 and need no new analysis.
Make them before the owner sees the choice.

## 1. The two blocking items

### 1a. The 5-20% bridge: resolved

v3 rejects my single anchor at 38.8%, because the large rows then score a mean
`u²` of 0.20 at 20-30%. That rejection is correct. I tested only the middle
when I proposed it, and the proposal was wrong.

Measured, 2026 record (mean `u²`; 1 means the width fits):

| construction | 5-20% established (12) | large 20-30% (12) | large ≥ 30% (32) | σ at 11.7% / 11.0% / 9.1% / 5.8% |
|---|---|---|---|---|
| one large anchor at 38.8% | 1.53 (v3 1.54) | **0.20** (0.20) | 0.49 (0.49) | 0.366 / 0.383 / 0.431 / 0.547 |
| A: two large anchors | 1.98 (2.00) | 0.77 (0.76) | 0.77 (0.77) | 0.305 / 0.323 / 0.379 / 0.510 |
| B: two large anchors plus the 5-20% root | 0.88 (0.88) | 0.69 (0.68) | 0.77 (0.77) | 0.477 / 0.510 / 0.606 / 0.676 |

The anchors reproduce: 25.58% (0.074), 45.37% (0.043), 1.94% (0.834) and
8.92% (0.615). The 2021 and 2016 records also match v3 §2.2 to 0.04 or better.
For example, the 2016 record gives A 3.90 / 1.08 / 0.78 and B 0.99 / 1.08 / 0.78.

Two anchors at their rows' centres is the right construction for the large
end. It is what my v2-recheck alternative ("two large anchors from the record")
proposed.

### 1b. §11 judgement entry: resolved, with one should-fix (2c)

| requirement | v3 | verdict |
|---|---|---|
| one key set | `support` / `overperform` (existing) with the existing combination rule; v2's `centre_share` / `centre_ratio` dropped | met |
| σ_J beyond the model's own centre error | §11.1.2: `σ(c_J)` holds the model's usual centre error; `σ_J = 0` means as reliable as the model; σ_J replaces δ_deb or δ_seed, never adds | met; no double count |
| arrival factor for a judged seed | dropped, with the reason | met; consistent with `uni2/v2.py` |
| run-time keying outside the hash | four keys excluded from `_judgements_sha` and read in `make_drawer`; the `pools.py` change is batched | met for the specs; see 2c for the forecast's own declaration |
| backtests ignore and record | `35_widths.judgements_ignored` with the register row and reason; no refusal, so 2026 runs later as a backtest | met |

The worked rows in §11.3 reproduce from the option-B widths:

- σ(5.8%) 0.676;
- σ(1.98%) 0.834, with √(0.834² + 0.3²) = 0.89;
- √(0.62² + 0.46²) = 0.77;
- √(0.84² + 0.6²) = 1.03.

## 2. The two should-fix items, and one new

- **2a. The 1.01 explanation: fixed.** §0.1 states the all-band against
  within-band count, and §2.5 prints it as a sensitivity.
- **2b. The stop rule: fixed, and it can now fire.** It leaves one band out. It
  fires under A at 1-5% (root 0.840, interpolation without it 0.575, interval
  0.617-0.968) and is quiet under B. Its construction test, fire and then go
  quiet when reverted, is specified in §9. I did not re-run the bootstraps.
- **2c (new, should-fix). Excluding the keys from the spec hash reopens the
  staleness hole for the forecast.** `_judgements_sha` went into the pool key
  because a hand edit to the judgements file changed the model while every
  artefact went on reporting itself current (`pools.py:480-490`). v3 takes the
  four strength keys out of that hash. It records judgement dates in
  `35_widths`, but names no key that the forecast's own artefacts carry. An edit
  to `support` after a run would leave the published forecast declaring itself
  current. Fix: the forecast artefacts declare a hash of the applied strength
  entries (and `35_widths` carries it), and `declares.py --verify` /
  `test_intermediates_are_current` compare it with the live file. It is one
  line in the writer's order.

## 3. The owner-choice table: mostly fair, three corrections

The decisive numbers reproduce:

- **5-20% fit:** A 1.98, B 0.88.
- **Johannesburg 2026, A** (citywide simulation, seed 7 log-sd): DA 0.13, ANC
  0.13, ASA 0.28, EFF 0.31, MK 0.56, PA 0.50. v3: 0.13, 0.13, 0.28, 0.31,
  0.56, 0.50.
- **Johannesburg 2026, B:** DA 0.16, ANC 0.16, ASA 0.43, EFF 0.47, MK 0.69, PA
  0.66. v3: 0.16, 0.17, 0.44, 0.48, 0.70, 0.67.
- **Draws where an established party under 1% last time exceeds 5%** (4 seeds):
  A 23.0, B 24.2 (v3 22.8 and 24.0).
- **Draws where the largest new party exceeds 18.12%:** A 318, B 456 (v3 325
  and 471).

I did not re-run the backtest CRPS rows.

The corrections:

- **3a. B's in-band fit is in-sample.** B's middle anchor is the root of those
  same 12 results, so its 0.88 (and 0.99 on the 2021 and 2016 records) is close
  to 1 by construction. A's 1.98 is out-of-sample. The out-of-sample test of
  the middle is the leave-one-out row in §2.4. Under A, the interpolation
  without the band (0.386) lies **inside** the band root's interval
  (0.204-0.750), so the middle record does not reject A. The summary's "A fits
  the twelve results too narrowly … B fits them", and §2.3's "B is the
  construction that passes every record test", must say that B's fit is by
  construction and that the 5-20% leave-one-out test is quiet for both. What
  does separate them is the 1-5% leave-one-out test. It fires under A, and it
  says width does not fall in a straight log line from 0.5% to 25%. That
  evidence is real and is stated fairly.
- **3b. B uses a root below MIN_EFF.** The 5-20% band has 5 party-elections
  against `MIN_EFF` = 8, and 4 on the 2011-only record used for 2016. Choosing
  B is an exception to the design's own minimum, so declare it in §7 beside the
  A-side exemption of the stop rule. Each option then carries one declared
  exception.
- **3c. The summary table is incomplete.** Option A's "large parties' spread"
  cell is blank. B's "about half of today's" fits the ANC (0.17 against 0.34)
  but not the DA (0.16 against 0.21). Measured against arm E:

  | option | DA | ANC | ASA | EFF |
  |---|---|---|---|---|
  | A | 0.62 | 0.38 | 0.56 | 0.54 |
  | B | 0.76 | 0.50 | 0.88 | 0.84 |

  Fill both rows with these ratios.

Those three apart, the table is fair. It shows both fits, both stop-rule
results, both backtest scores, including that B fails the middle CRPS rule by
more and why, and the Johannesburg 2026 consequences side by side.

## 4. Anything new and wrong

Nothing beyond 2c and 3a-3c. Checked and correct:

- anchors at weighted row centres;
- the within-band count;
- the §0.2 correction about v1's 0.05;
- increments under both options (δ_deb 0.477 and 0.457 used in my simulation;
  results consistent);
- the summary's 23-24 draws against 403.

## Not checked

The location fixed point, the stop-rule bootstraps, the backtest CRPS and
coverage for A and B, the seat proxy, and anything through the real drawer.
