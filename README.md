# Missing Layer — reference demos

Companion code for the three-paper package by Daniel Maclean
(ORCID 0009-0004-7725-687X): *The Missing Layer* (Doc 1),
*NV-Governed Measurement* (Doc 2), *ICE Fusion Architecture* (Doc 3).
Papers are in `papers/`.

Each folder is a small, self-contained demo. They are demonstrations of the
governance overlay applied to a specific setting, not production
implementations. Every demo prints its own PASS/FAIL lines.

**Provenance.** This is a **clean-room reference implementation** of the
protocol specified in the papers, licensed MIT. The production system
that the design derives from is not in this repository and is not
covered by this licence.

## Setup

```
pip install cryptography numpy scipy matplotlib
```

Python 3.10+ is expected. No API keys required for the demos below.

## Demos

| Folder | What it shows | Run | Limits |
|---|---|---|---|
| `reference/` | The governance overlay itself: `Overlay`, `AuditLog`, canonical hashing (`overlay.py`), plus a single-decision `baseline_policy_engine.py` used for comparison in the evaluation. All other demos import the overlay. | (imported) | Reference implementation; not hardened. |
| `eval/` | The 10-scenario overlay evaluation table (Doc 1 §4). Scenario 12 is included **as a demonstrated limit** — the integrity verifier accepts a re-signed log, and only the protocol verifier notices missing gate records; a key holder who fabricates a complete, consistent sequence is not detectable from the log. | `python eval_overlay.py` | Synthetic scenarios; latencies depend on hardware. |
| `bell_gate/` | Detection-loophole-aware CHSH gate: shows the "S = 2.690 at η = 0.853" trap and the correct audit verdict (Doc 1 §5.4, Doc 2 worked example). Also writes `bell_bias_S_vs_eta.png`. | `python bell_bias_sim.py` | Idealised biased-sampling model; no error bars, no real detector physics. |
| `nv_sweep/` | NV-centre governor sweep (Doc 2). Version 1 gates on measurement, Version 2 on predicted fidelity, Version 3 does a two-system double check. Reports BAF (bad-action fraction) and GRF (good-run rejection fraction) against pre-stated targets. | `python nv_governor_sweep.py` | Simulated system, not a real NV rig. Batches within a session are correlated; point estimates only. |
| `[redacted]_promotion/` | Governance around a promotion decision for a hypothetical [redacted]: qualifying rule, authorised approver, threshold, mid-case tampering, evaluator uncertainty, offline audit trail (Doc 1 §5.2). | `python [redacted]_promotion.py` | Toy governance rules; no real learning system involved. |
| `toy_ledger/` | Public governance chain + private transaction chain, verifiable by a citizen holding only the genesis hash and a signed checkpoint (Doc 1 §5.3). | `python toy_ledger.py` | Toy; single-node; no consensus, no replay resistance beyond the chain. |
| `hallucination/` | Numbers-and-citations gate. Two versions: `hallucination_gate.py` (v1, token-equality) and `hallucination_gate_v2.py` (v2, **value-aware** — parses digits and number words, converts units, precision-aware match, derived percentages, claim-binding by nearby content words, plus citation check). **Both are deterministic and require no language-model inference.** SHA-256 of v2 is pinned in `hallucination_gate_v2.sha256`. | `python hallucination_gate.py` (smoke), or `python hallucination_gate.py data.jsonl` / `python hallucination_gate_v2.py data.jsonl` on a labelled corpus | v1 known blind spot: spelled-out numbers ("ninety"). v2 handles those but is still a numeric/citation gate — non-numeric hallucinations are not its target. |
| `papers/` | *The Missing Layer* (Doc 1), *NV-Governed Measurement* (Doc 2), *ICE Fusion Architecture* (Doc 3), each in `.md`, `.docx` and `.pdf`. | — | See each paper for scope and limits. |

## What "PASS" means here

Each script prints PASS/FAIL for pre-stated checks. PASS means the overlay
behaved as specified. It does NOT mean the underlying scientific claim is
proven — see the paper for what each demo does and does not settle.

## License

MIT — see `LICENSE`. Applies to this reference implementation only; see
**Provenance** above.

## Cite

See `CITATION.cff`.
