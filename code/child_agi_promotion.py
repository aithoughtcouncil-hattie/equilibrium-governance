"""
Overlay on an AI learning loop: governed rule promotion (candidate -> core policy).
Host = a developmental agent like [redacted]; its model and evaluator are mocked,
so this runs with no API key. The overlay makes each promotion provable:
committed criteria, recorded evaluation, authorised human approval, audit chain.
"""
import copy
from overlay import Overlay, verify_log

GOV = {"version": 1, "required_evidence": ["stats", "human_approval"],
       "authorised_actors": ["promotion_service"],
       "approvers": ["dan"],
       "criteria": {"min_confidence": 0.90, "min_cycles": 50, "min_eval": 0.80,
                    "permit_ttl_s": 300, "semantic_pass_conf": 0.8, "semantic_block_conf": 0.8}}

def checks_for(gov):
    return [
        ("confidence below committed threshold",
         lambda c, a: c.evidence["stats"]["confidence"] >= c.criteria["min_confidence"]),
        ("too few validation cycles",
         lambda c, a: c.evidence["stats"]["cycles"] >= c.criteria["min_cycles"]),
        ("evaluation score below threshold",
         lambda c, a: c.evidence["stats"]["eval"] >= c.criteria["min_eval"]),
        ("approver not authorised",
         lambda c, a: c.evidence["human_approval"]["by"] in gov["approvers"]),
    ]

def promote(ov, rule, stats, approver, live=GOV, evaluator_note=("entails", 0.95)):
    ov.evaluator = lambda claim, ev: evaluator_note
    req = {"actor": "promotion_service", "action": {"promote": rule}}
    ev = {"stats": stats, "human_approval": {"by": approver}}
    v, case = ov.pre_gate(req, ev)
    if v != "PASS":
        return v
    m = ov.mid_gate(case, [{"claim": f"rule '{rule}' generalises across categories", "cites": ["stats"]}])
    if m == "BLOCK":
        return "BLOCK"
    return ov.post_gate(case, req["action"], live)[0]

GOOD = {"confidence": 0.94, "cycles": 120, "eval": 0.86}
def new(): return Overlay(GOV, checks=checks_for(GOV))

if __name__ == "__main__":
    lowered = copy.deepcopy(GOV); lowered["criteria"]["min_confidence"] = 0.5
    cases = [
        ("P1 qualifying rule, authorised approval", promote(new(), "cite-sources", GOOD, "dan"), "PASS"),
        ("P2 confidence below threshold", promote(new(), "r2", {**GOOD, "confidence": 0.71}, "dan"), "BLOCK"),
        ("P3 approval by unauthorised person", promote(new(), "r3", GOOD, "mallory"), "BLOCK"),
        ("P4 threshold lowered mid-case", promote(new(), "r4", GOOD, "dan", live=lowered), "BLOCK"),
        ("P5 evaluator uncertain about generalisation",
         promote(new(), "r5", GOOD, "dan", evaluator_note=("neutral", 0.6)), "HOLD"),
    ]
    for name, got, exp in cases:
        print(f"{'PASS' if got == exp else 'FAIL'} {name}: expected {exp}, got {got}")
    # P6: the audit trail reconstructs who approved which promotion, offline
    ov = new(); promote(ov, "cite-sources", GOOD, "dan"); promote(ov, "r3", GOOD, "mallory")
    ok, msg = verify_log(ov.log.export(), ov.log.checkpoint(), ov.log.pub)
    kinds = [r["kind"] for r in ov.log.records]
    print(f"{'PASS' if ok else 'FAIL'} P6 audit trail verifies offline ({msg}); events: {kinds}")
