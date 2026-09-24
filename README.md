# Equilibrium Governance

Coherent body of work on equilibrium-based control as a design philosophy,
applied to decision governance (Papers 1-3), verified by a measured energy
result on real silicon (Paper 4 + benchmark), and extended to a hardware
architecture (analytic eco chip model).

## Papers

Four peer-review drafts, in `/papers/`:

- **[Governance 1 — The Missing Layer](papers/Maclean_2026_Governance1_The_Missing_Layer.pdf)** ([md](papers/Maclean_2026_Governance1_The_Missing_Layer.md), [docx](papers/Maclean_2026_Governance1_The_Missing_Layer.docx))
  Verifiable decision governance for high-stakes systems. Protocol properties P1-P6.
- **[Governance 2 — Governed Measurement (NV)](papers/Maclean_2026_Governance2_Governed_Measurement_NV.pdf)** ([docx](papers/Maclean_2026_Governance2_Governed_Measurement_NV.docx))
  Governance overlay for room-temperature NV registers.
- **[Governance 3 — Governed Fusion Architecture](papers/Maclean_2026_Governance3_Governed_Fusion_Architecture.pdf)** ([md](papers/Maclean_2026_Governance3_Governed_Fusion_Architecture.md), [docx](papers/Maclean_2026_Governance3_Governed_Fusion_Architecture.docx))
  ICE fusion architecture under governance.
- **[Governance 4 — Equilibrium Energy](papers/Maclean_2026_Governance4_Equilibrium_Energy.pdf)** ([md](papers/Maclean_2026_Governance4_Equilibrium_Energy.md))
  Equilibrium-based control as a design philosophy for computing systems — measured cascade result plus analytic eco-chip model.

## Results

- **Cascade energy benchmark** — 36% of DistilBERT-alone energy per correct decision, 100% agreement in both directions on the fixed-template dataset (600 items, 3 reps, LHM package-power measurement with 60s idle baseline subtracted). See [`/bench/BENCH_ECOCHIP.md`](bench/BENCH_ECOCHIP.md) for the run report and [`/bench/`](bench/) for the harness and raw data.
- **Analytic eco chip model** — the patent's 2.74 TOPS/W claim falls inside the defensible analytic range [2.28, 2.87] with mid-scenario 2.61. Load-bearing sub-claim is the sustained-fraction assumption; if it collapses to the conventional value the TOPS/W falls below the 2.0 baseline. See [`/analytic/ANALYTIC_ECOCHIP.md`](analytic/ANALYTIC_ECOCHIP.md).
- **Ten-scenario evaluation of the governance overlay** — 10 of 10 scenarios match the specification, including tamper-evidence, gate-order enforcement, and permit-binding checks. See [`/results/RESULTS_scenarios.md`](results/RESULTS_scenarios.md).

## Code

MIT-licensed clean-room reference implementation in [`/code/`](code/):

- [`overlay.py`](code/overlay.py) — three-gate governance overlay (pre/mid/post) with signed audit log
- [`baseline_policy_engine.py`](code/baseline_policy_engine.py) — conventional policy-engine baseline for scenario comparison
- [`eval_scenarios.py`](code/eval_scenarios.py) — ten-scenario evaluation harness; regenerates `/results/RESULTS_scenarios.md` and `.csv`
- [`hallucination_gate_v1.py`](code/hallucination_gate_v1.py) / [`hallucination_gate_v2.py`](code/hallucination_gate_v2.py) — value-aware hallucination gate, v1 and v2
- [`toy_ledger.py`](code/toy_ledger.py) — public-audit toy ledger (8 checks)
- [`[redacted]_promotion.py`](code/[redacted]_promotion.py) — P1-P6 protocol demonstration
- [`bell_bias_sim.py`](code/bell_bias_sim.py), [`nv_governor_sweep.py`](code/nv_governor_sweep.py) — supporting simulations for Papers 2/3

Every result in the *Results* section above is reproducible from the code and data in this repo.

## Framework

[`/theory/[redacted].md`](theory/[redacted].md) is the plain-language framing document.

## Reproducing the results

Three main reproductions. Each takes seconds to a few minutes.

1. **Scenario evaluation** (regenerates `/results/RESULTS_scenarios.md` and `results_scenarios.csv`):
   ```bash
   python code/eval_scenarios.py
   ```

2. **Cascade energy benchmark** — follow [`bench/README.md`](bench/README.md). Full run needs `python bench/runner.py` (60s idle + 3 reps × 4 workloads ≈ 5 min), then `python bench/accuracy_check.py`, then `python bench/report.py`. Measured energy columns require LibreHardwareMonitor running as administrator with the Remote Web Server enabled on port 8085; without it the harness falls back to a CPU-time energy estimate.

3. **Analytic eco chip model**:
   ```bash
   bash analytic/harness/rerun.sh
   ```
   Pure arithmetic on documented inputs. No external dependencies beyond a standard Python install.

## Provenance

Clean-room reference implementation. MIT licensed. The production system that motivated this work is not in this repo.

Daniel Maclean, Thought Council · [thoughtcouncil.org](https://thoughtcouncil.org) · ORCID [0009-0004-7725-687X](https://orcid.org/0009-0004-7725-687X)
