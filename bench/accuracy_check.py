"""
Accuracy check on B2's decisive items.

The cascade routes an item to the overlay (via a tiny lexicon rule)
whenever the rule is "decisive"; ambiguous items fall through to DistilBERT.
That saves compute only if the lexicon rule's labels actually agree with
what DistilBERT would have said — otherwise the saving is really an
accuracy loss.

This script:
  1. Rebuilds the exact mixed dataset run in B2 (same seed, same fraction).
  2. Runs DistilBERT on every decisive item.
  3. Reports agreement rate and confusion matrix (lexicon vs DistilBERT).
  4. Recomputes energy-per-CORRECT-decision, using DistilBERT as truth.
  5. Writes bench/accuracy.json.

Usage:
  python bench/accuracy_check.py                     # uses N and decisive_frac from results.json
  python bench/accuracy_check.py --n 1000 --decisive-frac 0.6
"""
import argparse, json, os, sys, time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from dataset import decidable_split, lexicon_decide
from workloads import distilbert_predict_one, load_distilbert


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--decisive-frac", type=float, default=None)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--results", default=os.path.join(_HERE, "results.json"))
    ap.add_argument("--out", default=os.path.join(_HERE, "accuracy.json"))
    args = ap.parse_args()

    # Pull defaults from the last bench run so we're checking the same data
    with open(args.results) as f:
        run = json.load(f)
    n = args.n if args.n is not None else run["params"]["n"]
    df = args.decisive_frac if args.decisive_frac is not None else run["params"]["decisive_frac"]

    items = decidable_split(n, decisive_frac=df, seed=args.seed)
    decisive = [x for x in items if x["decisive"]]
    ambiguous = [x for x in items if not x["decisive"]]
    print(f"[data] N={n} decisive_frac={df}  -> decisive={len(decisive)}  ambiguous={len(ambiguous)}")

    load_distilbert()  # pre-warm

    # Confusion matrix: rows = lexicon label (0=neg, 1=pos), cols = distilbert
    cm = [[0, 0], [0, 0]]
    lex_abstain = 0
    disagreements = []
    t0 = time.perf_counter()
    for i, x in enumerate(decisive):
        lex_pred, is_dec = lexicon_decide(x["text"])
        if not is_dec or lex_pred is None:
            lex_abstain += 1
            continue
        db_pred = distilbert_predict_one(x["text"])
        cm[lex_pred][db_pred] += 1
        if lex_pred != db_pred and len(disagreements) < 20:
            disagreements.append({"text": x["text"], "lexicon": lex_pred, "distilbert": db_pred})
        if (i + 1) % 100 == 0:
            print(f"  ...{i+1}/{len(decisive)}  agree={cm[0][0]+cm[1][1]}  disagree={cm[0][1]+cm[1][0]}")
    dur = time.perf_counter() - t0

    total_scored = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1]
    agree = cm[0][0] + cm[1][1]
    disagree = cm[0][1] + cm[1][0]
    agreement_rate = agree / total_scored if total_scored else 0.0

    # Precision / recall of the lexicon vs DistilBERT-as-truth
    # Class 1 (positive):
    tp = cm[1][1]; fp = cm[1][0]; fn = cm[0][1]; tn = cm[0][0]
    pos_prec = tp / (tp + fp) if (tp + fp) else None
    pos_rec  = tp / (tp + fn) if (tp + fn) else None
    neg_prec = tn / (tn + fn) if (tn + fn) else None
    neg_rec  = tn / (tn + fp) if (tn + fp) else None

    # Energy per correct decision (DistilBERT = ground truth)
    # Cascade over N items:
    #   correct = decisive_count * agreement_rate + ambiguous_count * 1.0
    # DistilBERT-alone:
    #   correct = N   (truth by definition)
    dec_share = len(decisive) / n
    amb_share = len(ambiguous) / n
    correct_share_cascade = dec_share * agreement_rate + amb_share * 1.0

    def pull(key, workload):
        return run["results"][workload]["summary"].get(key)

    b1 = "B1_distilbert_alone"; b2 = "B2_cascade"
    metrics = {}
    for label, src_key in [
        ("wall_ms_per_decision", "wall_ms_per_decision_mean_mean"),
        ("cpu_ms_per_decision", "cpu_ms_per_decision_mean"),
        ("energy_j_estimated_per_decision", "energy_j_estimated_per_decision_mean"),
        ("energy_j_measured_per_decision", "energy_j_measured_per_decision_mean"),
        ("energy_j_delta_per_decision", "energy_j_delta_per_decision_mean"),
    ]:
        b1v = pull(src_key, b1); b2v = pull(src_key, b2)
        entry = {"B1_per_decision": b1v, "B2_per_decision": b2v}
        if b2v is not None:
            entry["B2_per_correct"] = b2v / correct_share_cascade
            if b1v is not None:
                entry["ratio_B2_per_correct_over_B1"] = (b2v / correct_share_cascade) / b1v
        metrics[label] = entry

    payload = {
        "n": n,
        "decisive_frac": df,
        "decisive_items_scored": total_scored,
        "lexicon_abstentions_on_supposedly_decisive": lex_abstain,
        "confusion_matrix": {
            "rows_are_lexicon_label__cols_are_distilbert_label": True,
            "labels": ["neg=0", "pos=1"],
            "matrix": cm,
            "TN_lex_neg_db_neg": cm[0][0],
            "FN_lex_neg_db_pos": cm[0][1],
            "FP_lex_pos_db_neg": cm[1][0],
            "TP_lex_pos_db_pos": cm[1][1],
        },
        "agreement_rate": agreement_rate,
        "disagreement_count": disagree,
        "positive_class_precision": pos_prec,
        "positive_class_recall": pos_rec,
        "negative_class_precision": neg_prec,
        "negative_class_recall": neg_rec,
        "decisive_share_of_input": dec_share,
        "ambiguous_share_of_input": amb_share,
        "correct_share_cascade_under_distilbert_truth": correct_share_cascade,
        "per_metric_energy_per_correct": metrics,
        "example_disagreements": disagreements,
        "duration_s": dur,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"[done] agreement={agreement_rate:.4f}  disagree={disagree}/{total_scored}  wrote {args.out}")

    # Verdict banding per spec
    if agreement_rate >= 0.95:
        verdict = "PASS_ABOVE_95"
    elif agreement_rate < 0.90:
        verdict = "FAIL_BELOW_90"
    else:
        verdict = "MID_90_TO_95"
    print(f"[verdict] {verdict}")


if __name__ == "__main__":
    main()
