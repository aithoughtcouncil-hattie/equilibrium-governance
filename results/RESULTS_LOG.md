# RESULTS_LOG

Change log for the repository's reproducible results and structural updates.
One entry per commit that lands new results or restructures the repo.

---

## 2026-09-24 — Restructure for full equilibrium governance package

**Commit:** `3cb9b5e` (before amend for encoding-bug fix)

**What changed**

- Repository renamed from `missing-layer` to `equilibrium-governance` (rename executed on GitHub; redirects handle old URL references).
- New directory layout: `/papers/`, `/code/`, `/bench/`, `/analytic/`, `/results/`, `/theory/`. Old subject-specific folders (`reference/`, `eval/`, `hallucination/`, `toy_ledger/`, `[redacted]_promotion/`, `bell_gate/`, `nv_sweep/`) removed; contents moved to `/code/` (and one figure to `/results/`) using `git mv` so file history is preserved.
- Paper 4 added: *Equilibrium-Based Control as a Design Philosophy for Computing Systems* (Governance 4). PDF from source, `.md` transcription authored from PDF text (source `.docx` not available; noted in README).
- Papers renamed to `Maclean_2026_GovernanceN_...` scheme. Paper 2 has no `.md` (only `.docx` + `.pdf`) — flagged in README.
- Analytic eco chip model added under `/analytic/` (ported from local scratch location).
- `bench/BENCH_ECOCHIP.md` moved into `/bench/`; benchmark harness path references updated.
- Cascade energy benchmark harness (`/bench/`) — `run_all.py` renamed to `runner.py`; import paths updated to reference `/code/` instead of `/reference/`.
- `code/eval_scenarios.py` (renamed from `eval/eval_overlay.py`) updated to write outputs to `/results/` using script-relative paths.
- Root `README.md` rewritten to reflect full four-paper package scope.
- `CITATION.cff` updated: primary DOI `10.5281/zenodo.22912122` (code archive); placeholder Zenodo DOIs for each of the four papers.
- `.gitignore` added (Python cache, editor swap files, OS metadata, model caches).

**Reproducible results, re-run before commit**

| Script | Result |
|---|---|
| `code/eval_scenarios.py` | 10 of 10 scenarios match expected behaviour. Fresh `results/RESULTS_scenarios.md` and `results/results_scenarios.csv` regenerated. |
| `code/toy_ledger.py` | 8 of 8 checks pass. |
| `code/[redacted]_promotion.py` | P1-P6 all pass (`PASS P1` through `PASS P6`). |
| `code/hallucination_gate_v2.py` | One-line encoding fix applied: `open(argv[1], encoding="utf-8")`. Verified with UTF-8 input file; module runs to completion and prints per-class agreement plus totals. 

**Not re-run**

- `bench/runner.py` — full 5-minute cascade energy benchmark. Existing `results.json`, `results_v1.json`, `accuracy.json`, `accuracy_v1.json` retained as the canonical measured record. Re-running requires LibreHardwareMonitor running with admin rights and Remote Web Server enabled; done in a prior session and not part of the restructure re-run gate.

**Files added / moved / deleted — full list**

Added:
- `.gitignore`
- `papers/Maclean_2026_Governance4_Equilibrium_Energy.pdf` (from `Downloads/`)
- `papers/Maclean_2026_Governance4_Equilibrium_Energy.md` (transcription from PDF)
- `theory/[redacted].md` (from Idea audit root)
- `analytic/ANALYTIC_ECOCHIP.md`, `analytic/versions.txt`, `analytic/harness/{model.py,params.json,rerun.sh}` (from local scratch `C:/work/ecochip_sim/`)
- `results/RESULTS_LOG.md` (this file)
- Root: `bench/`, `code/`, `results/`, `theory/`, `analytic/` directories

Moved / renamed (git mv, history preserved):
- `reference/{overlay,baseline_policy_engine}.py` → `code/`
- `eval/eval_overlay.py` → `code/eval_scenarios.py`
- `hallucination/hallucination_gate.py` → `code/hallucination_gate_v1.py`
- `hallucination/hallucination_gate_v2.py` → `code/hallucination_gate_v2.py`
- `hallucination/hallucination_gate_v2.sha256` → `code/hallucination_gate_v2.sha256`
- `toy_ledger/toy_ledger.py` → `code/toy_ledger.py`
- `[redacted]_promotion/[redacted]_promotion.py` → `code/[redacted]_promotion.py`
- `bell_gate/bell_bias_sim.py` → `code/bell_bias_sim.py`
- `bell_gate/bell_bias_S_vs_eta.png` → `results/bell_bias_S_vs_eta.png`
- `nv_sweep/nv_governor_sweep.py` → `code/nv_governor_sweep.py`
- `papers/Doc1_The_Missing_Layer.{md,docx,pdf}` → `papers/Maclean_2026_Governance1_The_Missing_Layer.{md,docx,pdf}`
- `papers/Doc2_NV_Governed_Measurement_Rev5.{docx,pdf}` → `papers/Maclean_2026_Governance2_Governed_Measurement_NV.{docx,pdf}`
- `papers/Doc3_ICE_Fusion_Architecture_Governed.{md,docx,pdf}` → `papers/Maclean_2026_Governance3_Governed_Fusion_Architecture.{md,docx,pdf}`
- `bench/run_all.py` → `bench/runner.py`
- `BENCH_ECOCHIP.md` (repo root) → `bench/BENCH_ECOCHIP.md`
- Untracked `results_overlay.csv` / `RESULTS_overlay.md` → `results/results_scenarios.csv` / `results/RESULTS_scenarios.md`

Deleted:
- Empty parent directories after moves: `reference/`, `eval/`, `hallucination/`, `toy_ledger/`, `[redacted]_promotion/`, `bell_gate/`, `nv_sweep/`
- `__pycache__/` directories in `bench/`, `code/`, `reference/`

Content edits (non-paper):
- `README.md` — rewritten
- `CITATION.cff` — rewritten with placeholder paper DOIs and primary Zenodo DOI
- `bench/workloads.py` — import path `reference/` → `code/`
- `bench/README.md` — filename refs `run_all.py` → `runner.py`; sibling path for `BENCH_ECOCHIP.md`
- `bench/report.py` — code-availability ref `reference/overlay.py` → `code/overlay.py`; `bench/run_all.py` → `bench/runner.py`; output path stays inside `bench/`
- `code/eval_scenarios.py` — output paths now script-relative under `../results/`

**Deliberately not modified**

- Paper `.md` contents (per restructure-only scope). This preserves one flagged issue in Paper 4 §5 where the cited patent number `GB2606946.8` corresponds to LG Display's unrelated Display Apparatus patent, not the eco-chip design. Should be corrected in the next paper revision.
- Any [redacted] / [redacted] / [redacted] / [redacted]-pitch material — swept for and confirmed absent per the 17 September exclusion.

---
