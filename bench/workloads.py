"""
Four workloads for BENCH_ECOCHIP.

A1  overlay_only        — three-gate ICE overlay decides each item (no ML).
A2  distilbert_only     — DistilBERT sentiment classifier on each item.
B1  distilbert_alone    — same as A2 but on the mixed decidable/ambiguous set.
B2  cascade             — overlay short-circuits decisive items via a lexicon
                          rule; ambiguous items fall through to DistilBERT.

A1+A2 answer:  what does each system cost per decision, on the same inputs?
B1+B2 answer:  if you use the overlay to skip clear cases, what happens
               to the classifier bill?
"""
import os, sys

# make `code/` importable so we get the shipped overlay
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(_HERE), "code"))

from overlay import Overlay                        # noqa: E402
from dataset import lexicon_decide                 # noqa: E402


# --- overlay setup shared by A1 and B2 --------------------------------------

def make_overlay():
    """Governance envelope for a 'publish this review?' decision."""
    gov = {
        "required_evidence": ["text_hash"],
        "authorised_actors": ["reviewer_bot"],
        "criteria": {
            "max_amount": 10 ** 9,
            "semantic_pass_conf": 0.7,
            "semantic_block_conf": 0.7,
            "permit_ttl_s": 60,
        },
    }
    # deterministic evaluator so the mid-gate always passes cleanly
    ov = Overlay(gov, evaluator=lambda claim, ev: ("entails", 0.99))
    return ov, gov


def overlay_decide_one(ov, gov, text: str) -> str:
    """Full pre -> mid -> post pipeline for one item.  Returns the verdict."""
    import hashlib
    ev = {"text_hash": hashlib.sha256(text.encode()).hexdigest()}
    req = {"actor": "reviewer_bot", "action": {"kind": "publish", "text": text}}
    v, pre = ov.pre_gate(req, ev)
    if v != "PASS":
        return "BLOCK_pre"
    v = ov.mid_gate(pre, [{"claim": "review passes", "cites": ["text_hash"]}])
    if v == "BLOCK":
        return "BLOCK_mid"
    v, _ = ov.post_gate(pre, req["action"], gov)
    return v


# --- distilbert setup shared by A2, B1, B2 ----------------------------------

_MODEL = None
_TOK = None
_MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"

def load_distilbert():
    global _MODEL, _TOK
    if _MODEL is not None:
        return _TOK, _MODEL
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    torch.set_grad_enabled(False)
    _TOK = AutoTokenizer.from_pretrained(_MODEL_NAME)
    _MODEL = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
    _MODEL.eval()
    return _TOK, _MODEL


def distilbert_predict_one(text: str) -> int:
    import torch
    tok, model = load_distilbert()
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=128)
    with torch.no_grad():
        logits = model(**inputs).logits
    return int(logits.argmax(dim=-1).item())


# --- workload factories -----------------------------------------------------
# Each factory returns a fresh work_fn(i) closure over pre-loaded state,
# so the measure() harness times only the decision, not the setup.

def workload_A1_overlay_only(items):
    ov, gov = make_overlay()
    def work(i):
        overlay_decide_one(ov, gov, items[i]["text"])
    return work, len(items)


def workload_A2_distilbert_only(items):
    load_distilbert()          # pre-warm outside the measured section
    def work(i):
        distilbert_predict_one(items[i]["text"])
    return work, len(items)


def workload_B1_distilbert_alone(items):
    load_distilbert()
    def work(i):
        distilbert_predict_one(items[i]["text"])
    return work, len(items)


def workload_B2_cascade(items):
    ov, gov = make_overlay()
    load_distilbert()
    def work(i):
        text = items[i]["text"]
        pred, decisive = lexicon_decide(text)
        if decisive:
            overlay_decide_one(ov, gov, text)      # signed permit for the lexicon label
        else:
            distilbert_predict_one(text)
    return work, len(items)
