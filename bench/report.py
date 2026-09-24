"""
Read bench/results.json and write BENCH_ECOCHIP.md at the repo root.

Reports what the machine measured.  Does not extrapolate.
"""
import json, os, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = _HERE  # writes into bench/ per repo layout


def fmt(v, digits=4):
    if v is None: return "n/a"
    if isinstance(v, float):
        if v == 0: return "0"
        return f"{v:.{digits}g}"
    return str(v)


def row(key, s, has_meas, has_delta):
    def g(k): return s.get(k + "_mean")
    def gsd(k): return s.get(k + "_std")
    cells = [key,
             f"{fmt(g('wall_ms_per_decision_mean'))} ± {fmt(gsd('wall_ms_per_decision_mean'))}",
             fmt(g('wall_ms_per_decision_median')),
             fmt(g('wall_ms_per_decision_p95')),
             f"{fmt(g('cpu_ms_per_decision'))} ± {fmt(gsd('cpu_ms_per_decision'))}",
             fmt(g('peak_mem_mb')),
             f"{fmt(g('energy_j_estimated_per_decision')*1000)} ± {fmt(gsd('energy_j_estimated_per_decision')*1000)}"]
    if has_meas:
        v = g('energy_j_measured_per_decision')
        sd = gsd('energy_j_measured_per_decision')
        cells.append(f"{fmt(v*1000)} ± {fmt(sd*1000)}" if v is not None else "n/a")
    if has_delta:
        v = g('energy_j_delta_per_decision')
        sd = gsd('energy_j_delta_per_decision')
        cells.append(f"{fmt(v*1000)} ± {fmt(sd*1000)}" if v is not None else "n/a")
    return "| " + " | ".join(cells) + " |"


def ratio(a, b):
    if a is None or b is None or b == 0: return "n/a"
    return f"{a/b:.3f}"


def _history_block(prev: dict, cur_results: dict, cur_acc: dict | None) -> str:
    """Render a 'Changes since previous run' block from snapshotted v1 files."""
    pr, pa = prev["results"], prev["accuracy"]

    def pull(res, k, wl):
        return res["results"][wl]["summary"].get(k)

    def diff(a, b, digits=4):
        if a is None or b is None: return "n/a"
        return f"{a:.{digits}g} → {b:.{digits}g}"

    rows = []
    for wl in ("A1_overlay_only", "A2_distilbert_only",
               "B1_distilbert_alone", "B2_cascade"):
        if wl not in pr["results"] or wl not in cur_results["results"]:
            continue
        rows.append("| " + " | ".join([
            wl,
            diff(pull(pr, "wall_ms_per_decision_mean_mean", wl),
                 pull(cur_results, "wall_ms_per_decision_mean_mean", wl)),
            diff(pull(pr, "energy_j_estimated_per_decision_mean", wl) * 1000
                 if pull(pr, "energy_j_estimated_per_decision_mean", wl) is not None else None,
                 pull(cur_results, "energy_j_estimated_per_decision_mean", wl) * 1000
                 if pull(cur_results, "energy_j_estimated_per_decision_mean", wl) is not None else None),
            (diff(pull(pr, "energy_j_delta_per_decision_mean", wl) * 1000
                  if pull(pr, "energy_j_delta_per_decision_mean", wl) is not None else None,
                  pull(cur_results, "energy_j_delta_per_decision_mean", wl) * 1000
                  if pull(cur_results, "energy_j_delta_per_decision_mean", wl) is not None else None)),
        ]) + " |")

    cm_prev = pa["confusion_matrix"]["matrix"]
    ag_prev = pa["agreement_rate"]
    ag_cur  = cur_acc["agreement_rate"] if cur_acc else None
    cm_cur  = cur_acc["confusion_matrix"]["matrix"] if cur_acc else None

    return f"""## Changes since previous run

**Previous run (v1, {pr.get('timestamp','?')})** used sentiment templates
whose "clear negative" family shared slot names with the "clear positive"
family, so negative-template items filled with positive words and read
as positive to the lexicon.  Every one of the 596 scored decisive items
in v1 landed on `lexicon=positive`; the negative direction of the
lexicon rule was untested.  Four items the dataset tagged decisive were
abstained on by the lexicon at eval time — same root cause.

**This run (v2, {cur_results.get('timestamp','?')})** uses the fixed
templates in `bench/dataset.py`: POS slots draw from POS only, NEG slots
from NEG only, and `_fill` samples words without replacement so each
decisive template contributes ≥2 distinct sentiment words.
`decidable_split` also alternates positive/negative decisive templates
so both classes are represented equally, and every emitted item is
verified against `_decisive(text)` before being tagged.

### Per-workload comparison (mean values)

| workload | wall ms/dec | energy mJ/dec (estimate) | energy mJ/dec (LHM delta) |
|---|---|---|---|
{chr(10).join(rows) if rows else '_(no matching workloads)_'}

### Accuracy comparison

| | v1 (buggy templates) | v2 (fixed templates) |
|---|---|---|
| Decisive items scored | {pa['decisive_items_scored']} | {cur_acc['decisive_items_scored'] if cur_acc else 'n/a'} |
| Lexicon abstentions on tagged-decisive | {pa['lexicon_abstentions_on_supposedly_decisive']} | {cur_acc['lexicon_abstentions_on_supposedly_decisive'] if cur_acc else 'n/a'} |
| Agreement rate | {ag_prev*100:.2f}% | {ag_cur*100:.2f}% |
| Positive-direction items | {cm_prev[1][0]+cm_prev[1][1]} | {cm_cur[1][0]+cm_cur[1][1] if cm_cur else 'n/a'} |
| Negative-direction items | {cm_prev[0][0]+cm_prev[0][1]} | {cm_cur[0][0]+cm_cur[0][1] if cm_cur else 'n/a'} |
| Confusion matrix (rows=lex, cols=DB) | `{cm_prev}` | `{cm_cur if cm_cur else 'n/a'}` |

The v1 confusion matrix has both `lexicon=negative` rows empty — that's
the artefact of the template bug.  In v2 both rows carry weight so
positive-direction and negative-direction agreement can be reported
separately (see the Accuracy section above).

Raw v1 outputs are preserved at `bench/results_v1.json` and
`bench/accuracy_v1.json` for auditability.  This section is not
overwritten on subsequent regens — the earlier caveat stays visible.

"""


def _accuracy_block(a: dict) -> str:
    cm = a["confusion_matrix"]["matrix"]
    ag = a["agreement_rate"]
    # Direction-split agreement: row 0 = lexicon-negative items; row 1 = lexicon-positive items.
    row_neg = cm[0][0] + cm[0][1]
    row_pos = cm[1][0] + cm[1][1]
    neg_dir_ag = (cm[0][0] / row_neg) if row_neg else None
    pos_dir_ag = (cm[1][1] / row_pos) if row_pos else None
    if ag >= 0.95:
        verdict = ("**Verdict: PASS (≥95%).** The cascade result reported "
                   "above stands — the compute saving is not being bought "
                   "by mislabelling.")
    elif ag < 0.90:
        verdict = ("**Verdict: FAIL (<90%).** The cascade's cost saving is at "
                   "least partly an accuracy loss.  Do not quote the B2 "
                   "energy number externally without the accuracy caveat.")
    else:
        verdict = ("**Verdict: MID (90–95%).** Cost saving is real but the "
                   "cascade drops a non-trivial number of items DistilBERT "
                   "would have classified differently.  Tune the lexicon "
                   "rule or raise the threshold before quoting externally.")

    per = a["per_metric_energy_per_correct"]
    def r(k):
        e = per.get(k, {})
        b1 = e.get("B1_per_decision"); b2 = e.get("B2_per_decision")
        b2c = e.get("B2_per_correct"); rr = e.get("ratio_B2_per_correct_over_B1")
        def f(v, s=4): return "n/a" if v is None else f"{v:.{s}g}"
        return f"| {k} | {f(b1)} | {f(b2)} | {f(b2c)} | {f(rr, 3)} |"

    metrics = ["wall_ms_per_decision", "cpu_ms_per_decision",
               "energy_j_estimated_per_decision",
               "energy_j_measured_per_decision",
               "energy_j_delta_per_decision"]

    return f"""## Accuracy of the cascade (DistilBERT as ground truth)

The cascade only saves compute if the lexicon rule's label on decisive
items agrees with what DistilBERT would have said.  This section runs
DistilBERT on every item B2 routed to the overlay path and reports
agreement.

### Agreement

- **Decisive items scored**: {a['decisive_items_scored']}
  (of {a['decisive_share_of_input']*a['n']:.0f} the dataset tagged
  decisive; {a['lexicon_abstentions_on_supposedly_decisive']} were abstained
  on by the lexicon at eval time — a dataset-vs-rule mismatch, non-fatal).
- **Overall agreement rate**: **{ag*100:.2f}%**  ({a['decisive_items_scored']-a['disagreement_count']} agree, {a['disagreement_count']} disagree)
- **Positive-direction agreement** (of items where lexicon said positive, share DistilBERT also said positive):
  **{'n/a' if pos_dir_ag is None else f'{pos_dir_ag*100:.2f}%'}**  ({row_pos} items)
- **Negative-direction agreement** (of items where lexicon said negative, share DistilBERT also said negative):
  **{'n/a' if neg_dir_ag is None else f'{neg_dir_ag*100:.2f}%'}**  ({row_neg} items)
- Positive-class precision: **{fmt(a['positive_class_precision'])}**, recall **{fmt(a['positive_class_recall'])}**
- Negative-class precision: **{fmt(a['negative_class_precision'])}**, recall **{fmt(a['negative_class_recall'])}**

### Confusion matrix (rows = lexicon label, cols = DistilBERT label)

|  | DistilBERT: neg (0) | DistilBERT: pos (1) |
|---|---|---|
| **Lexicon: neg (0)** | {cm[0][0]} | {cm[0][1]} |
| **Lexicon: pos (1)** | {cm[1][0]} | {cm[1][1]} |

{verdict}

### Energy per **correct** decision (DistilBERT as ground truth)

DistilBERT-alone (B1) is correct by definition (it *is* the truth).
Cascade (B2) is correct on the ambiguous items (they go through
DistilBERT) plus `agreement_rate` of the decisive items.  With
decisive share {a['decisive_share_of_input']:.2f} and ambiguous share
{a['ambiguous_share_of_input']:.2f}, the cascade's correct share is
**{a['correct_share_cascade_under_distilbert_truth']*100:.2f}%**.

| metric | B1 per decision | B2 per decision | B2 per **correct** decision | B2-per-correct / B1 |
|---|---|---|---|---|
{chr(10).join(r(m) for m in metrics)}

Because the cascade's correct share is very close to 1, "per correct"
is barely different from "per decision" here.  If agreement had been
lower, the per-correct column would have inflated B2 sharply.

"""


def main():
    src = os.path.join(_HERE, "results.json")
    if len(sys.argv) > 1: src = sys.argv[1]
    with open(src) as f:
        d = json.load(f)
    acc_path = os.path.join(_HERE, "accuracy.json")
    acc = None
    if os.path.exists(acc_path):
        with open(acc_path) as f:
            acc = json.load(f)
    prev_results_path = os.path.join(_HERE, "results_v1.json")
    prev_acc_path = os.path.join(_HERE, "accuracy_v1.json")
    prev = None
    if os.path.exists(prev_results_path) and os.path.exists(prev_acc_path):
        with open(prev_results_path) as f:
            prev_r = json.load(f)
        with open(prev_acc_path) as f:
            prev_a = json.load(f)
        prev = {"results": prev_r, "accuracy": prev_a}

    env = d["env"]; idle = d["idle_baseline"]; results = d["results"]; params = d["params"]

    has_meas = any("energy_j_measured_per_decision_mean" in r["summary"] for r in results.values())
    has_delta = any("energy_j_delta_per_decision_mean" in r["summary"] for r in results.values())

    hdr_cells = ["workload", "wall ms/dec (mean ± sd)", "wall ms/dec (median)", "wall ms/dec (p95)",
                 "cpu ms/dec (mean ± sd)", "peak mem MB",
                 "energy mJ/dec — estimate (mean ± sd)"]
    if has_meas: hdr_cells.append("energy mJ/dec — LHM measured")
    if has_delta: hdr_cells.append("energy mJ/dec — LHM delta over idle")
    hdr = "| " + " | ".join(hdr_cells) + " |"
    sep = "|" + "|".join(["---"] * len(hdr_cells)) + "|"

    def block(keys, title):
        rows = [hdr, sep]
        for k in keys:
            if k in results:
                rows.append(row(k, results[k]["summary"], has_meas, has_delta))
        return "\n".join([f"### {title}", "", *rows, ""])

    # ratios (Comparison A: A2/A1; Comparison B: B2/B1)
    ratios = []
    def rat_line(a, b, label, metric_key):
        if a in results and b in results:
            va = results[a]["summary"].get(metric_key)
            vb = results[b]["summary"].get(metric_key)
            ratios.append(f"- **{label}**: {metric_key} ratio {b}/{a} = {ratio(vb, va)}")

    metrics_for_ratio = [
        "wall_ms_per_decision_mean_mean",
        "cpu_ms_per_decision_mean",
        "energy_j_estimated_per_decision_mean",
    ]
    if has_delta:
        metrics_for_ratio.append("energy_j_delta_per_decision_mean")
    elif has_meas:
        metrics_for_ratio.append("energy_j_measured_per_decision_mean")

    for m in metrics_for_ratio:
        rat_line("A1_overlay_only", "A2_distilbert_only", "A: DistilBERT ÷ overlay", m)
    ratios.append("")
    for m in metrics_for_ratio:
        rat_line("B1_distilbert_alone", "B2_cascade", "B: cascade ÷ DistilBERT-alone", m)

    md = f"""# BENCH_ECOCHIP

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
- **DistilBERT sentiment** (`{env.get('transformers', '?')}` + torch
  `{env.get('torch', '?')}`, CPU): the pretrained
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

- **N decisions per run**: {params['n']}
- **Reps per workload**: {params['reps']} (mean ± sample sd reported)
- **Data**: deterministic sentiment templates (seed=42) in
  `bench/dataset.py`.  `sentiment_pairs` is a fixed mix; `decidable_split`
  is `{int(params.get('decisive_frac', 0.6)*100)}%` lexicon-decisive / rest ambiguous.
- **Idle baseline**: {idle.get('duration_s', 0):.0f}s of no measured workload,
  mean package power = **{fmt(idle.get('mean_w'))} W**
  (total {fmt(idle.get('total_j'))} J).  For LHM-measured energy, the reported
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
  `cpu_seconds × {65/6:.2f}` J on this box (i7-8700, 65W TDP, 6 physical cores).
  Labelled as an estimate everywhere; it assumes each core at TDP when busy
  and does not account for turbo, uncore, or platform draw.
- **Between-reps cool-down**: 2s + `gc.collect()`.

## Environment

- CPU: **{env['processor']}** ({env['cpu_count_physical']} physical / {env['cpu_count_logical']} logical cores)
- RAM: {env['total_ram_gb']} GB
- OS: {env['platform']}
- Python: {env['python']}  |  torch: {env.get('torch','?')}  |  transformers: {env.get('transformers','?')}  |  cryptography: {env.get('cryptography','?')}
- torch threads: {env.get('torch_threads','?')}
- LibreHardwareMonitor available at run time: **{env.get('lhm_available', False)}**
- Assumed TDP for CPU-time estimate: {env.get('assumed_tdp_w', 65)} W

## Results

{block(['A1_overlay_only', 'A2_distilbert_only'], 'Comparison A — same sentiment inputs')}

{block(['B1_distilbert_alone', 'B2_cascade'], 'Comparison B — DistilBERT alone vs cascade (overlay pre-filter + DistilBERT)')}

### Ratios

{chr(10).join(ratios) if ratios else '(no ratios computed)'}

{_accuracy_block(acc) if acc else ''}

{_history_block(prev, d, acc) if prev else ''}

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

Timestamp of this run: {d.get('timestamp','?')}
"""
    out = os.path.join(REPO, "BENCH_ECOCHIP.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"[wrote] {out}")


if __name__ == "__main__":
    main()
