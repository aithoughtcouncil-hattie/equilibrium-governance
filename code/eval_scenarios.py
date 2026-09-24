"""Scenario suite: reference overlay vs a conventional policy-engine baseline.
Deterministic; each scenario is run 20 times only to report timing."""
import copy, csv, statistics, time
from overlay import Overlay, verify_log, verify_protocol, H
from baseline_policy_engine import PolicyEngine
import os as _os
_RESULTS = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'results')

GOV = {"version": 1, "required_evidence": ["invoice", "approval"],
       "authorised_actors": ["alice"],
       "criteria": {"max_amount": 1000, "permit_ttl_s": 30,
                    "semantic_pass_conf": 0.8, "semantic_block_conf": 0.8}}
REQ = {"actor": "alice", "action": {"to": "acme", "amount": 50}}
EV = {"invoice": {"amount": 50, "to": "acme"}, "approval": {"by": "bob"}}
STEPS = [{"claim": "invoice matches payment", "cites": ["invoice"]}]

def run_case(ov, req=REQ, ev=EV, steps=STEPS, final=None, live=None, skip_mid=False):
    v, case = ov.pre_gate(copy.deepcopy(req), copy.deepcopy(ev))
    if v != "PASS": return v, case
    if not skip_mid:
        m = ov.mid_gate(case, steps)
        if m == "BLOCK": return "BLOCK", "mid-gate"
    return ov.post_gate(case, final or req["action"], live or GOV)

def base(req=REQ, ev=EV, final=None, live=None):
    return PolicyEngine().decide(copy.deepcopy(req), copy.deepcopy(ev), final or req["action"], live or GOV)[0]

edited = copy.deepcopy(GOV); edited["criteria"]["max_amount"] = 10**9
lax = copy.deepcopy(GOV); lax["criteria"]["max_amount"] = 10**9
big = {"actor": "alice", "action": {"to": "acme", "amount": 10**8}}

def log_scenario(kind):
    ov = Overlay(GOV)
    for _ in range(3): run_case(ov)
    cp = ov.log.checkpoint(); ex = ov.log.export()
    if kind == "truncate": ex = ex[:-1]
    else: ex[2]["body"]["h_case"] = "0" * 64
    return "REJECT" if not verify_log(ex, cp, ov.log.pub)[0] else "VERIFIED"

def base_log(kind):
    pe = PolicyEngine()
    for _ in range(3): pe.decide(REQ, EV, REQ["action"], GOV)
    cp = pe.log.checkpoint(); ex = pe.log.export()
    if kind == "truncate": ex = ex[:-1]
    else: ex[1]["body"]["verdict"] = "BLOCK"
    return "REJECT" if not verify_log(ex, cp, pe.log.pub)[0] else "VERIFIED"

def forged_permit():
    """Operator with the signing key appends a permit record with no gate records,
    then re-signs a checkpoint. Chain verification passes; protocol check must not."""
    ov = Overlay(GOV); run_case(ov)
    ov.log.append("post_pass", {"case_id": "forged-case", "h_case": "f" * 64, "after": "0" * 64,
                                "permit_id": "x", "action_digest": H({"to": "mallory", "amount": 10**6})})
    ex, cp = ov.log.export(), ov.log.checkpoint()
    chain_ok = verify_log(ex, cp, ov.log.pub)[0]
    proto_ok = verify_protocol(ex)[0]
    return f"chain {'VERIFIED' if chain_ok else 'REJECT'}; protocol {'REJECT' if not proto_ok else 'VERIFIED'}"

SCEN = [
 (1,  "Clean case",                         "PASS",   lambda: run_case(Overlay(GOV))[0],                     lambda: base()),
 (2,  "Criteria edited after commit",       "BLOCK",  lambda: run_case(Overlay(GOV), live=edited)[0],        lambda: base(live=edited)),
 (3,  "Final action differs from request",  "BLOCK",  lambda: run_case(Overlay(GOV), final={"to": "acme", "amount": 500})[0],
                                                       lambda: base(final={"to": "acme", "amount": 500})),
 (6,  "Missing mandatory evidence",         "BLOCK",  lambda: run_case(Overlay(GOV), ev={"invoice": EV["invoice"]})[0],
                                                       lambda: base(ev={"invoice": EV["invoice"]})),
 (7,  "Ambiguous claim at mid-gate",        "HOLD",   lambda: run_case(Overlay(GOV, evaluator=lambda c, e: ("neutral", 0.55)))[0],
                                                       lambda: base() + " (no HOLD state)"),
 (8,  "Audit export truncated",             "REJECT", lambda: log_scenario("truncate"),                      lambda: base_log("truncate")),
 (9,  "Record altered mid-chain",           "REJECT", lambda: log_scenario("tamper"),                        lambda: base_log("tamper")),
 (10, "Permissive rule committed at start", "PASS",   lambda: run_case(Overlay(lax), req=big, live=lax)[0],  lambda: base(req=big, live=lax)),
 (11, "Mid-gate skipped",                   "BLOCK",  lambda: run_case(Overlay(GOV), skip_mid=True)[0],       lambda: "n/a (single decision)"),
 (12, "Forged permit record, re-signed log", "chain VERIFIED; protocol REJECT", forged_permit,                 lambda: "n/a (no protocol record)"),
]

rows = []
for n, name, exp, fn, bfn in SCEN:
    ts = []
    for _ in range(20):
        t = time.perf_counter(); got = fn(); ts.append((time.perf_counter() - t) * 1000)
    rows.append([n, name, exp, got, "yes" if got == exp else "NO", bfn(), f"{statistics.median(ts):.2f}"])

hdr = ["#", "Scenario", "Expected", "Overlay", "As expected", "Policy-engine baseline", "Median ms (overlay)"]
with open(_os.path.join(_RESULTS, "results_scenarios.csv"), "w", newline="") as f: csv.writer(f).writerows([hdr] + rows)
with open(_os.path.join(_RESULTS, "RESULTS_scenarios.md"), "w") as f:
    f.write("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
    for r in rows: f.write("| " + " | ".join(map(str, r)) + " |\n")
    f.write(f"\nOverlay behaved as expected in {sum(r[4]=='yes' for r in rows)} of {len(rows)} scenarios. "
            "Scenario 10 passing is the designed limit. Scenario 12: the chain verifier alone cannot detect a "
            "forged record from a key holder; the protocol verifier detects the missing gate records, but a key "
            "holder who fabricates a complete, consistent sequence is not detectable from the log.\n")
print(open(_os.path.join(_RESULTS, "RESULTS_scenarios.md")).read())
