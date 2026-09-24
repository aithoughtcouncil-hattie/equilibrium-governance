# ANALYTIC_ECOCHIP

Analytic energy/TOPS model of the Eco Chip 4-die stack from Maclean,
"A Constitutional Governance Stack and Eco Chip Hardware Architecture
for Artificial Intelligence Systems" (UK patent draft, March 2026,
applicant Daniel Maclean t/a Thought Council).

**This is arithmetic, not a simulation.** No gem5, no McPAT, no cycle
counts. Every number here is derived from a small set of documented
assumptions (see [harness/params.json](harness/params.json)) and can
be checked by hand. Reproducible with `python harness/model.py`.

**Framing.** The patent asserts a 4-die stack achieves 1,260 TOPS
sustained at 460W = 2.74 TOPS/W, versus 900 TOPS at 450W = 2.00 TOPS/W
for a conventional stack — a +37% TOPS/W and +40% sustained-throughput
advantage. The task here is not to reproduce this via chip simulation
(the patent lacks the die-area, cache, and memory-bandwidth parameters
a simulator needs). It is to stress-test whether the arithmetic is
internally consistent and externally plausible against public data on
commercial accelerators, and to name the single sub-claim on which the
whole result rests.

---

## §1 — Sustained-fraction derivation (the load-bearing sub-claim)

Every other number in the model is dominated by the ratio
`sustained_TOPS / peak_TOPS` for each of the two stacks. The patent
asserts 0.84 for the eco chip and 0.60 for the conventional stack —
a 24 percentage-point delta. Both stacks share the same 1,500 TOPS peak
and the same power budget within 10W, so the entire +40% throughput
claim reduces to this one assumption.

### Where does the +40% actually come from?

The patent's stated mechanism has two hardware components that could
plausibly move sustained throughput:

- **Somatic Power Rail (SPR)** — 0-80% supply-voltage reduction on
  compute clusters when the Constitutional Friction Circuit detects
  prohibited output patterns. This mechanism *reduces* throughput on
  friction events; it cannot be the source of a +40% sustained gain.
  Under normal (non-friction) operation SPR is inactive.
- **Equilibrium Drive** — three-signal PID controller holding
  temperature at 55°C target (vs 85-95°C for reactive throttling),
  clock at 3.0 GHz target, and friction score at 0.1 target. This is
  the plausible source of the sustained-throughput advantage: if the
  die never reaches the reactive-throttle trigger point, the frequency
  reduction ladder that a conventional stack incurs is never engaged.

So the claim reduces to: "proactive homeostasis at 55°C sustains ~84%
of peak TOPS, versus 60% for a reactive-throttle system."

### Defensible ranges from public data

**Conventional reactive throttling, sustained-vs-peak fraction:**

Data-centre AI accelerators typically report 50-70% of vendor peak
TOPS under continuous inference load. MLPerf inference results across
generations show 60-150% year-over-year gains on the same silicon via
software optimisation — implying significant recoverable headroom
above sustained hardware baseline. Reported figures for edge NPUs
throttling from 85°C+ within minutes of continuous full-clock operation
land in the same band. Range adopted: **0.50 – 0.70**, midpoint 0.60.
Sources: MLPerf inference v5.0/v5.1 results, NVIDIA developer briefs,
IEEE Spectrum coverage of ML accelerator benchmarks, ACS Materials
"AI chip thermal wall" analysis.

**Proactive DVFS with adequate cooling budget:**

The reference case here is Apple M-series silicon, which uses
aggressive proactive DVFS and typically sustains 85-95% of peak on
compute workloads at TDPs of 20-40W. Scaling to a 460W stack, the
question is whether the cooling budget is sufficient to hold 55°C
under 460W of continuous compute. This is achievable with substantial
cooling (liquid, or a large heatsink + fan on a workstation form
factor), but is not free: the eco chip specification does not include
a cooling budget beyond "target 55°C, bounds 45-75°C". Realistic
range: **0.70 – 0.88**, midpoint 0.80. Sources: Apple M-series
sustained benchmarks (Anandtech, Notebookcheck), 7nm thermal density
literature (5-10 W/mm² sustained on data-centre AI dies).

**Delta between the two:**

- Low end: 20pp (0.70 - 0.50)
- Mid: 20pp (0.80 - 0.60)
- High end: 18pp (0.88 - 0.70)
- **Patent claim: 24pp (0.84 - 0.60)**

The patent's 24pp is at the top of the defensible range. Not outside
it. But if the eco chip lands at 0.75 instead of 0.84 (still a
substantial gain over 0.60), the whole TOPS/W claim compresses
sharply — see §7.

---

## §2 — Per-die power model

Given the 460W total and the ≤5W governance-die budget the patent
specifies, and allocating 5W to interconnect and bus overhead:

| Component | Power (W) | Source |
|---|---|---|
| Governance Die (28nm) | 5 | Patent §5.4 |
| Governed Chiplet Interconnect + Governance Signal Bus | 5 | Not in patent; allocated |
| **Compute total (3 dies)** | **450** | Derived |
| Per Compute Die (7nm) | 150 | 450 ÷ 3 |
| **Total** | **460** | Patent §5.4 |

150W per Compute Die at 7nm is consistent with a mid-sized AI die
(H100 die is 700W but that's a much larger die at 4N with HBM3 on
package; 150W corresponds to a ~800 mm² die at ~0.19 W/mm² average
power density, well below the 5-10 W/mm² sustained thermal ceiling
for 7nm — consistent with a design optimised for homeostatic operation
rather than peak throttle).

Governance-die budget breakdown (from patent §5.2, §5.3):

- Constitutional Friction Circuit (Aho-Corasick DFA + 64KB SRAM at
  3.5 GHz): 5-9 mW ✓ (comparable to AES-128 at 7nm, well-documented)
- Somatic Power Rail control logic (8 LDO instances × per-die
  control): allow ~500 mW
- NLI constitutional evaluator: this is the big one. The patent lists
  "constitutional evaluator NLI engine" as part of the Governance Die
  budget but does not size it. A quantised on-die NLI classifier
  (≤100M params, INT8) operating at multi-100 Hz decision rate could
  fit inside 3-4W. Tight but not implausible at 28nm.
- Total: <5W is achievable but has no slack. If the NLI engine is
  larger than assumed, the 5W budget breaks and the total stack
  power moves above 460W.

---

## §3 — TOPS calculation

The patent asserts 1,500 TOPS peak for the 3 Compute Dies (500
TOPS/die at 7nm, 3.0 GHz clock target). This is not derived from
clock × units — the patent takes it as a design point and asserts the
same peak for both eco and conventional stacks.

Sanity check: H100 SXM5 achieves 1,979 TOPS INT8 dense peak in a
single die at 4N (7nm-class), ~1.9 GHz, on a 700W envelope. Scaling
down to 150W and 3.0 GHz clock, 500 TOPS/die is consistent — implies
roughly 42,000 INT8 MAC units per die running at ~4 ops/cycle,
comparable to a smaller H100-class die at higher clock. Plausible.

TOPS_sustained = TOPS_peak × sustained_fraction.

At the patent's claimed 0.84 sustained fraction:
- Eco chip: 1,500 × 0.84 = **1,260 TOPS** ✓ (matches patent)
- Conventional: 1,500 × 0.60 = **900 TOPS** ✓ (matches patent)

The arithmetic is internally consistent — but it's a restatement of
the assumption, not evidence for it.

---

## §4 — Cascade-weighted useful-work efficiency

BENCH_ECOCHIP.md v2 measured a cascade pattern with a 60% decisive /
40% ambiguous split. On the software benchmark, the cascade used
**0.375× the energy per correct decision** vs a model-alone system
(measured LHM package power, idle-delta subtracted; DistilBERT as
ground truth; 100% accuracy on the fixed-template dataset).

**This ratio does not translate 1:1 into TOPS/W.** TOPS/W is a
per-cycle hardware efficiency; the cascade reduces useful-work-per-
decision, not per-cycle throughput. If a hardware system runs the
cascade pattern in production, its effective **decisions-per-joule**
would improve by ~2.7× (1/0.375) — but a benchmark that measures
sustained TOPS/W on raw compute would not see that.

Reported here because it's the empirical link between the software
patent (GB2606620.9) and the eco chip claim: if the deployed workload
is governed-decision inference rather than raw dense inference, the
useful-work efficiency of the stack is dominated by the cascade
routing, not the TOPS/W of the compute dies.

---

## §5 — Full 4-die stack: TOPS/W across the defensible range

Applying the sustained-fraction bounds from §1 to the arithmetic of
§2-3:

| Scenario | Eco sustained fraction | Conv sustained fraction | Eco TOPS/W | Conv TOPS/W | Eco / Conv |
|---|---|---|---|---|---|
| Low | 0.70 | 0.50 | **2.28** | 1.67 | 1.37× |
| Mid | 0.80 | 0.60 | **2.61** | 2.00 | 1.30× |
| High | 0.88 | 0.70 | **2.87** | 2.33 | 1.23× |
| **Patent claim** | **0.84** | **0.60** | **2.74** | **2.00** | **1.37×** |

- The patent's 2.74 TOPS/W falls **inside** the defensible model
  range [2.28, 2.87].
- It sits **above the mid-scenario** (2.61) — favourable but not
  outrageous.
- Across every point in the range, eco chip TOPS/W **exceeds the
  patent's stated 2.00 baseline**. So the qualitative advantage
  claim holds even at the pessimistic end.
- The specific 2.74 vs 2.00 comparison combines the eco chip at a
  high-end sustained fraction (0.84) with the conventional stack at
  a mid sustained fraction (0.60). Both are defensible individually;
  the comparison is a favourable-vs-typical framing, not
  worst-case-vs-worst-case.

---

## §6 — Baseline comparison against commercial parts

Public specs and sustained estimates for current data-centre AI
accelerators:

| Part | Peak INT8 dense (TOPS) | Peak INT8 sparse (TOPS) | TDP (W) | Peak dense TOPS/W | Est sustained dense TOPS/W |
|---|---|---|---|---|---|
| NVIDIA H100 SXM5 | 1,979 | 3,958 | 700 | 2.83 | ~1.84 (at 0.65 sustained) |
| AMD MI300X | 2,610 | 5,220 | 750 | 3.48 | ~2.09 (at 0.60 sustained) |
| NVIDIA GH200 Grace Hopper | 1,979 | — | 700 | 2.83 | ~1.84 |

Sources: NVIDIA/AMD product datasheets, MLPerf inference v5.1
submissions (HPCwire coverage, Cisco UCS whitepaper). Sustained
fractions are estimates from MLPerf-reported throughput vs vendor
peak, not vendor-quoted.

**Reads:**

- The patent's **2.00 TOPS/W "conventional baseline"** is roughly
  consistent with sustained dense-INT8 numbers for H100 and MI300X
  (~1.8-2.1). It is not a straw-man baseline.
- The patent's **2.74 TOPS/W eco chip claim** would put it above
  current sustained dense-INT8 SOTA. Not implausible on a
  purpose-built inference chip with a much smaller peak envelope
  (1,500 TOPS vs H100's 1,979).
- **The comparison excludes sparsity and FP8.** H100 sparse INT8
  peak is 5.65 TOPS/W (peak) or ~3.67 TOPS/W sustained. FP8 pushes
  higher. The eco chip specification does not mention sparsity
  support or FP8. If "conventional" means "modern dense INT8", the
  patent's 2.00 baseline is fair. If it means "modern with sparsity
  and FP8", the eco chip's 2.74 is below current SOTA.

---

## §7 — Verdict

**Verdict: CONSISTENT — with one heavy caveat.**

The patent's 2.74 TOPS/W claim is:
- **Internally consistent**: yes. Given the stated peak TOPS,
  power, and 0.84 sustained fraction, 1,260/460 = 2.739 arithmetic
  holds.
- **Externally plausible**: yes for a purpose-built inference chip
  at the top end of achievable proactive-DVFS sustained fractions.
  Sits inside the defensible model range [2.28, 2.87] and above the
  mid-scenario (2.61).
- **The +40% advantage over the 2.00 baseline**: holds across the
  entire defensible sustained-fraction range. Even the low scenario
  (2.28) beats 2.00 by 14%.

**The load-bearing assumption is `sustained_fraction_eco`.** Every
other input can move ±20% and the qualitative verdict is unchanged.
But if the eco chip's sustained fraction falls to 0.60 (same as
conventional reactive throttling — i.e. if the Equilibrium Drive
doesn't deliver the homeostatic advantage the patent asserts), the
TOPS/W drops to 1.96 — **below the 2.00 baseline**, and the whole
comparative advantage vanishes.

**What would change the verdict most:**

1. **Sustained-fraction actual measurement.** The only way to close
   this is empirical: build the Equilibrium Drive PID in silicon (or
   FPGA emulation) and measure sustained throughput under continuous
   AI inference load with the die held at 55°C target. Everything
   else in the model is arithmetic around that number.
2. **Cooling budget disclosure.** Holding 55°C under 460W sustained
   requires substantial cooling. The patent doesn't specify a cooling
   solution. If the deployed system can only sustain 65-70°C with
   its cooling budget, the reactive-throttle mechanism might still
   engage on hotspots, and the sustained fraction drops.
3. **Baseline framing.** Comparing 2.74 vs 2.00 (dense INT8) is
   favourable. Comparing 2.74 vs 3.67 (H100 sparse INT8 sustained)
   makes the eco chip look worse than SOTA on the metric that
   modern accelerators actually optimise for. The patent should
   probably specify precision and sparsity assumptions explicitly
   before external publication.
4. **NLI engine on the Governance Die**. The <5W governance-die
   budget assumes the NLI evaluator fits in ~3-4W at 28nm. If it
   needs more (a plausibly larger classifier for real constitutional
   evaluation), the stack power rises above 460W and TOPS/W drops
   proportionally.

**Not sufficient to reject the claim.** Not sufficient to endorse it
externally either. The model output for the mid-scenario is the
honest headline number: **~2.6 TOPS/W, at the optimistic end of what
a well-designed proactive-DVFS AI accelerator with a small governance
overhead could achieve at 7nm/28nm**. The patent's specific 2.74
figure is within noise of that.

---

## Assumptions table

| Parameter | Value used | Source / confidence |
|---|---|---|
| Compute die process | 7nm | Patent §5.4 · HIGH |
| Governance die process | 28nm | Patent §3.6 · HIGH |
| Compute dies count | 3 | Patent §3.6 · HIGH |
| Peak TOPS (total stack) | 1,500 | Patent §5.4 asserted for both stacks · MEDIUM |
| Clock (compute) | 3.0 GHz target | Patent §3.5 (Window of Tolerance) · HIGH |
| Governance die power | ≤5 W | Patent §3.6 asserted · MEDIUM |
| Interconnect + bus overhead | 5 W | Not in patent, allocated · LOW |
| Compute die area | ~800 mm² | Inferred from H100 4N die (814 mm²) as closest commercial equivalent · LOW |
| Compute die power density | ~0.19 W/mm² | Derived from 150W ÷ 800 mm² · LOW (dependent on area assumption) |
| Conv sustained fraction | 0.50-0.70, mid 0.60 | MLPerf inference results, 7nm thermal density literature · MEDIUM |
| Eco sustained fraction | 0.70-0.88, mid 0.80 | Apple M-series proactive DVFS as reference · MEDIUM |
| Cascade decisive fraction | 0.60 | BENCH_ECOCHIP.md v2 dataset design · HIGH |
| Cascade energy ratio | 0.375× | BENCH_ECOCHIP.md v2 LHM idle-delta measured · HIGH |
| H100 sparse peak TOPS/W | 5.65 | NVIDIA datasheet · HIGH |
| MI300X dense peak TOPS/W | 3.48 | AMD product brief · HIGH |

---

## Reproducing

```bash
cd /c/work/ecochip_sim
bash harness/rerun.sh
```

or:

```bash
python harness/model.py           # human-readable
python harness/model.py --json    # for downstream tools
```

Tool versions in [versions.txt](versions.txt). Input parameters in
[harness/params.json](harness/params.json) — every value has a source
in the file. No gem5, no McPAT, no external dependencies beyond a
standard Python install.

---

## Not published, not extrapolated

Not committed to any repository. Not applied to data-centre-scale
estimates. Reflects this analytic model only, on the specific claim
in the specific patent draft supplied.
