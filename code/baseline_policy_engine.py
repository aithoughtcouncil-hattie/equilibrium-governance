"""
Baseline for comparison: a conventional policy engine with the SAME signed,
hash-chained, checkpointed audit log and action-bound tokens as the overlay.
Semantics follow common practice (e.g. a policy decision point with decision
logs): each request is evaluated once, at decision time, against the policy
currently loaded; required-evidence rules and limits are supported.
It has no case commitment across stages and no mid-decision HOLD.
"""
from overlay import AuditLog, H, canon
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

class PolicyEngine:
    def __init__(self, key=None):
        self.key = key or Ed25519PrivateKey.generate()
        self.log = AuditLog(self.key)

    def decide(self, request: dict, evidence: dict, action: dict, live_policy: dict):
        g = live_policy
        reasons = []
        if any(e not in evidence for e in g["required_evidence"]): reasons.append("missing evidence")
        if request["actor"] not in g["authorised_actors"]: reasons.append("unauthorised")
        if action.get("amount", 0) > g["criteria"]["max_amount"]: reasons.append("over limit")
        verdict = "BLOCK" if reasons else "PASS"
        body = {"policy_hash": H(g), "request": request, "action_digest": H(action),
                "verdict": verdict, "reasons": reasons}
        self.log.append("decision", body)
        if verdict == "PASS":
            token = {"action_digest": H(action), "policy_hash": H(g)}
            token["sig"] = self.key.sign(canon(token)).hex()
            return "PASS", token
        return "BLOCK", reasons
