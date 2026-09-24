# BENCH_ECOCHIP

Energy-per-decision benchmark of the ICE overlay against a conventional
neural network (DistilBERT SST-2), run on one physical machine.  Reports
what the machine measured.  No extrapolation to fleets, data centres, or
production workloads — the numbers here reflect a single desktop under a
single toy sentiment workload.

## What is being compared

Two systems that both produce "a decision" on each input, but do very
different work:

- **ICE overlay** (`code/overlay.py`): a three-gate (pre / mid / post)
  policy-decision pipeline with an SHA-256 hash-chained audit log and an
  Ed25519-signed permit per PASS.  It does not classify anything; it checks
  rules committed in advance and issues a signed receipt.
- **DistilBERT sentiment** (`5.17.0` + torch
  `2.12.0+cpu`, CPU): the pretrained
  `distilbert-base-uncased-finetuned-sst-2-english` model doing binary
  sentiment classification via a single forward pass and argmax over 2 classes.

The energy ratio between them primarily reflects that a few hashes plus one
signature is much cheaper than a 66M-parameter forward pass.  It is not a
like-for-like efficiency claim about "the same task".  Two comparisons are
run to keep this honest:

- **Comparison A — overlay-only vs DistilBERT-only** on the same sentiment
  inputs.  Answers "what does each system cost per decision on this box?"
- **Comparison B — DistilBERT alone vs DistilBERT + overlay pre-filter.**
  A tiny lexicon rule inside the overlay short-circuits the clearly-positive
  and clearly-negative items and issues a signed permit for them; only the
  ambiguous residual falls through to DistilBERT.  This is the eco-chip-
  relevant scenario: when the cheap gate can safely dispose of most traffic,
  the expensive model runs less often.  Accuracy is not evaluated here — the
  point is the compute cost.

## Method

- **N decisions per run**: 1000
- **Reps per workload**: 3 (mean ± sample sd reported)
- **Data**: deterministic sentiment templates (seed=42) in
  `bench/dataset.py`.  `sentiment_pairs` is a fixed mix; `decidable_split`
  is `60%` lexicon-decisive / rest ambiguous.
- **Idle baseline**: 60s of no measured workload,
  mean package power = **10.2 W**
  (total 599.9 J).  For LHM-measured energy, the reported
  "delta over idle" column is `E_measured - idle_mean_w * wall_seconds`
  — i.e. the extra package energy attributable to the workload.
- **Wall-clock**: `time.perf_counter()` around each decision.
- **CPU time**: `time.process_time()` totalled over the run.
- **Memory**: process RSS sampled at 20 Hz by a background thread; peak reported.
- **Energy — LHM measured**: LibreHardwareMonitor's Remote Web Server
  exposes package power at `http://localhost:8085/data.json`.  A background
  thread polls the `CPU Package` sensor at 1 Hz during the run; the
  trapezoidal integral is the reported energy.  System-wide, not per-process.
- **Energy — CPU-time estimate**: `cpu_seconds × (TDP / physical_cores)` =
  `cpu_seconds × 10.83` J on this box (i7-8700, 65W TDP, 6 physical cores).
  Labelled as an estimate everywhere; it assumes each core at TDP when busy
  and does not account for turbo, uncore, or platform draw.
- **Between-reps cool-down**: 2s + `gc.collect()`.

## Environment

- CPU: **Intel64 Family 6 Model 158 Stepping 10, GenuineIntel** (6 physical / 12 logical cores)
- RAM: 31.9 GB
- OS: Windows-10-10.0.19045-SP0
- Python: 3.12.10  |  torch: 2.12.0+cpu  |  transformers: 5.17.0  |  cryptography: 49.0.0
- torch threads: 6
- LibreHardwareMonitor available at run time: **True**
- Assumed TDP for CPU-time estimate: 65.0 W

## Results

### Comparison A — same sentiment inputs

| workload | wall ms/dec (mean ± sd) | wall ms/dec (median) | wall ms/dec (p95) | cpu ms/dec (mean ± sd) | peak mem MB | energy mJ/dec — estimate (mean ± sd) | energy mJ/dec — LHM measured | energy mJ/dec — LHM delta over idle |
|---|---|---|---|---|---|---|---|---|
| A1_overlay_only | 0.4421 ± 0.00374 | 0.4403 | 0.6973 | 0.4479 ± 0.009021 | 224.3 | 4.852 ± 0.09773 | n/a | n/a |
| A2_distilbert_only | 13.06 ± 0.1462 | 12.89 | 15.09 | 78.21 ± 0.7977 | 623.3 | 847.3 ± 8.642 | 870 ± 22 | 736.7 ± 20.69 |


### Comparison B — DistilBERT alone vs cascade (overlay pre-filter + DistilBERT)

| workload | wall ms/dec (mean ± sd) | wall ms/dec (median) | wall ms/dec (p95) | cpu ms/dec (mean ± sd) | peak mem MB | energy mJ/dec — estimate (mean ± sd) | energy mJ/dec — LHM measured | energy mJ/dec — LHM delta over idle |
|---|---|---|---|---|---|---|---|---|
| B1_distilbert_alone | 13.2 ± 0.2529 | 13.12 | 15.01 | 79.1 ± 1.33 | 623.4 | 856.9 ± 14.4 | 908.4 ± 24.69 | 773.7 ± 25.58 |
| B2_cascade | 5.618 ± 0.07011 | 0.7843 | 14.66 | 33.61 ± 0.3619 | 623.4 | 364.2 ± 3.92 | 334.2 ± 32.33 | 276.9 ± 31.73 |


### Ratios

- **A: DistilBERT ÷ overlay**: wall_ms_per_decision_mean_mean ratio A2_distilbert_only/A1_overlay_only = 29.551
- **A: DistilBERT ÷ overlay**: cpu_ms_per_decision_mean ratio A2_distilbert_only/A1_overlay_only = 174.616
- **A: DistilBERT ÷ overlay**: energy_j_estimated_per_decision_mean ratio A2_distilbert_only/A1_overlay_only = 174.616
- **A: DistilBERT ÷ overlay**: energy_j_delta_per_decision_mean ratio A2_distilbert_only/A1_overlay_only = n/a

- **B: cascade ÷ DistilBERT-alone**: wall_ms_per_decision_mean_mean ratio B2_cascade/B1_distilbert_alone = 0.426
- **B: cascade ÷ DistilBERT-alone**: cpu_ms_per_decision_mean ratio B2_cascade/B1_distilbert_alone = 0.425
- **B: cascade ÷ DistilBERT-alone**: energy_j_estimated_per_decision_mean ratio B2_cascade/B1_distilbert_alone = 0.425
- **B: cascade ÷ DistilBERT-alone**: energy_j_delta_per_decision_mean ratio B2_cascade/B1_distilbert_alone = 0.358

## Accuracy of the cascade (DistilBERT as ground truth)

The cascade only saves compute if the lexicon rule's label on decisive
items agrees with what DistilBERT would have said.  This section runs
DistilBERT on every item B2 routed to the overlay path and reports
agreement.

### Agreement

- **Decisive items scored**: 600
  (of 600 the dataset tagged
  decisive; 0 were abstained
  on by the lexicon at eval time — a dataset-vs-rule mismatch, non-fatal).
- **Overall agreement rate**: **100.00%**  (600 agree, 0 disagree)
- **Positive-direction agreement** (of items where lexicon said positive, share DistilBERT also said positive):
  **100.00%**  (300 items)
- **Negative-direction agreement** (of items where lexicon said negative, share DistilBERT also said negative):
  **100.00%**  (300 items)
- Positive-class precision: **1**, recall **1**
- Negative-class precision: **1**, recall **1**

### Confusion matrix (rows = lexicon label, cols = DistilBERT label)

|  | DistilBERT: neg (0) | DistilBERT: pos (1) |
|---|---|---|
| **Lexicon: neg (0)** | 300 | 0 |
| **Lexicon: pos (1)** | 0 | 300 |

**Verdict: PASS (≥95%).** The cascade result reported above stands — the compute saving is not being bought by mislabelling.

### Energy per **correct** decision (DistilBERT as ground truth)

DistilBERT-alone (B1) is correct by definition (it *is* the truth).
Cascade (B2) is correct on the ambiguous items (they go through
DistilBERT) plus `agreement_rate` of the decisive items.  With
decisive share 0.60 and ambiguous share
0.40, the cascade's correct share is
**100.00%**.

| metric | B1 per decision | B2 per decision | B2 per **correct** decision | B2-per-correct / B1 |
|---|---|---|---|---|
| wall_ms_per_decision | 13.2 | 5.618 | 5.618 | 0.426 |
| cpu_ms_per_decision | 79.1 | 33.61 | 33.61 | 0.425 |
| energy_j_estimated_per_decision | 0.8569 | 0.3642 | 0.3642 | 0.425 |
| energy_j_measured_per_decision | 0.9084 | 0.3342 | 0.3342 | 0.368 |
| energy_j_delta_per_decision | 0.7737 | 0.2769 | 0.2769 | 0.358 |

Because the cascade's correct share is very close to 1, "per correct"
is barely different from "per decision" here.  If agreement had been
lower, the per-correct column would have inflated B2 sharply.



## Changes since previous run

**Previous run (v1, 2026-09-24T04:07:35)** used sentiment templates
whose "clear negative" family shared slot names with the "clear positive"
family, so negative-template items filled with positive words and read
as positive to the lexicon.  Every one of the 596 scored decisive items
in v1 landed on `lexicon=positive`; the negative direction of the
lexicon rule was untested.  Four items the dataset tagged decisive were
abstained on by the lexicon at eval time — same root cause.

**This run (v2, 2026-09-24T04:29:57)** uses the fixed
templates in `bench/dataset.py`: POS slots draw from POS only, NEG slots
from NEG only, and `_fill` samples words without replacement so each
decisive template contributes ≥2 distinct sentiment words.
`decidable_split` also alternates positive/negative decisive templates
so both classes are represented equally, and every emitted item is
verified against `_decisive(text)` before being tagged.

### Per-workload comparison (mean values)

| workload | wall ms/dec | energy mJ/dec (estimate) | energy mJ/dec (LHM delta) |
|---|---|---|---|
| A1_overlay_only | 0.4444 → 0.4421 | 4.852 → 4.852 | n/a |
| A2_distilbert_only | 12.89 → 13.06 | 836.7 → 847.3 | 759.9 → 736.7 |
| B1_distilbert_alone | 13.19 → 13.2 | 856.2 → 856.9 | 760.4 → 773.7 |
| B2_cascade | 5.521 → 5.618 | 358.7 → 364.2 | 284.4 → 276.9 |

### Accuracy comparison

| | v1 (buggy templates) | v2 (fixed templates) |
|---|---|---|
| Decisive items scored | 596 | 600 |
| Lexicon abstentions on tagged-decisive | 4 | 0 |
| Agreement rate | 99.66% | 100.00% |
| Positive-direction items | 596 | 300 |
| Negative-direction items | 0 | 300 |
| Confusion matrix (rows=lex, cols=DB) | `[[0, 0], [2, 594]]` | `[[300, 0], [0, 300]]` |

The v1 confusion matrix has both `lexicon=negative` rows empty — that's
the artefact of the template bug.  In v2 both rows carry weight so
positive-direction and negative-direction agreement can be reported
separately (see the Accuracy section above).

Raw v1 outputs are preserved at `bench/results_v1.json` and
`bench/accuracy_v1.json` for auditability.  This section is not
overwritten on subsequent regens — the earlier caveat stays visible.



## Interpretation

- Comparison A is a floor: it shows the raw cost gap between the two
  mechanisms on this hardware, not a claim that they are substitutes.
- Comparison B is the useful number: the cascade's per-decision cost is a
  weighted average of the cheap overlay path and the full DistilBERT path,
  with the weighting set by how many inputs the lexicon rule can decide.
  A higher `--decisive-frac` moves it toward overlay-only; a lower one moves
  it toward DistilBERT-only.  Accuracy of the lexicon rule against
  DistilBERT-as-truth is reported in the **Accuracy of the cascade**
  section above; the cost-saving is only meaningful under the caveats
  stated there.
- LibreHardwareMonitor's package sensor is system-wide.  Even after
  subtracting the idle mean, background processes that happen to be active
  during the run remain attributed to the workload.  The CPU-time estimate
  is process-scoped but assumes TDP power per busy core.  Neither is a
  substitute for RAPL via `perf stat -e power/energy-pkg/` on Linux, which
  would be the honest next step.
- The LHM poller runs at 1 Hz.  A workload that finishes in under ~2 seconds
  (e.g. A1 at N=1000, which completes in ~0.5s) produces too few samples
  for a trapezoidal integral, and the measured-energy columns show `n/a`
  for it.  The CPU-time estimate is still meaningful there.  To get a
  measured number for A1, raise `--n` until the run takes several seconds.
- Accuracy check caveat: the sentiment templates in `bench/dataset.py`
  fill positive-word slots with positive words even inside the "clear
  negative" templates (a template bug — negative words only appear as the
  fixed phrase "regret" or "do not recommend").  As a result, every
  decisive item in this run landed on `lexicon=positive`, so the
  agreement number really only stresses the positive direction of the
  lexicon rule.  The negative-direction agreement is untested here; fix
  the templates and re-run before claiming the rule is safe both ways.
- Numbers reflect this box only.  Do not extrapolate.

## Reproducing

Full run (matches this file):

```bash
python bench/runner.py
python bench/accuracy_check.py
python bench/report.py
```

Options:

```bash
python bench/runner.py --quick                       # smoke test
python bench/runner.py --n 500 --reps 2              # override
python bench/runner.py --only A1_overlay_only,B2_cascade
python bench/runner.py --no-idle                     # skip baseline
```

For package-power energy, install LibreHardwareMonitor
(https://github.com/LibreHardwareMonitor/LibreHardwareMonitor), launch it
**as administrator**, then **Options → Remote Web Server → Run** (default
port 8085).  The harness polls `http://localhost:8085/data.json` and
integrates the `CPU Package` sensor.  Without LHM running, only the
CPU-time estimate is produced.

Timestamp of this run: 2026-09-24T04:29:57
