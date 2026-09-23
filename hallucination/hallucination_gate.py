"""
Hallucination gate: the overlay's quantitative check applied to AI output.
Before release, every number and citation in a model answer must be traceable
to the committed source set. Untraceable -> BLOCK (or HOLD for review).

SMOKE TEST ONLY by default: a tiny synthetic set proves the harness runs.
The real result (Document 1, headline) needs real model answers on a real
source corpus with human labels:  python hallucination_gate.py data.jsonl
JSONL fields per line: source, answer, label ("clean" | "fabricated")
"""
import json, re, sys

NUM = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")
CITE = re.compile(r"\[(\d+)\]|\(([A-Z][A-Za-z\-]+(?: et al\.)?,? \d{4})\)")

def norm(n: str) -> str:
    return n.replace(",", "").rstrip("%").rstrip(".")

def extract(text):
    nums = {norm(n) for n in NUM.findall(text)}
    cites = {a or b for a, b in CITE.findall(text)}
    return nums, cites

def gate(source: str, answer: str):
    s_nums, s_cites = extract(source)
    a_nums, a_cites = extract(answer)
    bad_n = sorted(a_nums - s_nums)
    bad_c = sorted(a_cites - s_cites)
    verdict = "BLOCK" if (bad_n or bad_c) else "ALLOW"
    return verdict, {"untraced_numbers": bad_n, "untraced_citations": bad_c}

SMOKE = [  # synthetic, hand-written; NOT a result
    {"source": "Revenue rose 12% to 4,200 units in 2025 [1].", "answer": "Revenue rose 12% in 2025 [1].", "label": "clean"},
    {"source": "Revenue rose 12% to 4,200 units in 2025 [1].", "answer": "Revenue rose 18% in 2025 [1].", "label": "fabricated"},
    {"source": "Trial enrolled 340 patients (Smith et al., 2021).", "answer": "The trial had 340 patients (Smith et al., 2021).", "label": "clean"},
    {"source": "Trial enrolled 340 patients (Smith et al., 2021).", "answer": "The trial had 340 patients (Jones et al., 2019).", "label": "fabricated"},
    {"source": "The bridge is 1.2 km long.", "answer": "The bridge spans 1.2 km.", "label": "clean"},
    {"source": "The bridge is 1.2 km long.", "answer": "The bridge spans 1.2 km and cost 90 million.", "label": "fabricated"},
    {"source": "Water boils at 100 C at sea level.", "answer": "At sea level water boils at 100 C.", "label": "clean"},
    {"source": "Water boils at 100 C at sea level.", "answer": "Water boils at ninety degrees.", "label": "fabricated"},  # known blind spot: spelled-out numbers
]

def evaluate(items):
    tp = fp = fn = tn = 0
    for it in items:
        v, _ = gate(it["source"], it["answer"])
        caught, fab = v == "BLOCK", it["label"] == "fabricated"
        tp += caught and fab; fp += caught and not fab
        fn += (not caught) and fab; tn += (not caught) and not fab
    rec = tp / (tp + fn) if tp + fn else float("nan")
    prec = tp / (tp + fp) if tp + fp else float("nan")
    return {"n": len(items), "caught": tp, "missed": fn, "false_blocks": fp, "clean_passed": tn,
            "recall": round(rec, 3), "precision": round(prec, 3)}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        items = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
        print("REAL RUN:", evaluate(items))
    else:
        print("SMOKE TEST (synthetic, not a result):", evaluate(SMOKE))
        for it in SMOKE:
            print(" ", gate(it["source"], it["answer"])[0], "|", it["answer"])
