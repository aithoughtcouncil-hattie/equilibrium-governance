"""
Reference implementation: verifiable decision-governance overlay.

The overlay sits beside a host system (bank, AI service, lab instrument).
The host keeps its own security; the overlay proves each decision followed
rules committed in advance, under checked evidence, with a complete,
tamper-evident record. It does not make the rules correct.

Host hand-off: the overlay issues a signed permit bound to one exact action.
Replay protection and expiry enforcement are the host's job; the permit
carries the id and expiry the host needs to do it.

Licence: MIT (clean-room; not derived from proprietary prototypes).
"""
import hashlib, json, time, uuid
from dataclasses import dataclass, field
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ---------- canonical encoding + hashing ----------
def canon(obj) -> bytes:
    """Deterministic JSON (sorted keys, no whitespace). Stand-in for RFC 8785."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def H(obj) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()

# ---------- audit log with signed checkpoints ----------
class AuditLog:
    def __init__(self, key: Ed25519PrivateKey):
        self.key, self.records = key, []
        self.pub = key.public_key()

    def append(self, kind: str, body: dict) -> dict:
        prev = self.records[-1]["digest"] if self.records else "0" * 64
        rec = {"seq": len(self.records), "kind": kind, "body": body, "prev": prev}
        rec["digest"] = H(rec)
        self.records.append(rec)
        return rec

    def checkpoint(self) -> dict:
        """Signed commitment to log length and head. Given to auditors out of band."""
        cp = {"length": len(self.records), "head": self.records[-1]["digest"]}
        cp["sig"] = self.key.sign(canon(cp)).hex()
        return cp

    def export(self) -> list:
        return json.loads(json.dumps(self.records))

def verify_log(records: list, checkpoint: dict, pub) -> tuple:
    """Offline verifier: needs only the export, a checkpoint and the public key."""
    cp = {k: checkpoint[k] for k in ("length", "head")}
    try:
        pub.verify(bytes.fromhex(checkpoint["sig"]), canon(cp))
    except Exception:
        return False, "checkpoint signature invalid"
    prev = "0" * 64
    for i, r in enumerate(records):
        body = {k: r[k] for k in ("seq", "kind", "body", "prev")}
        if r["seq"] != i or r["prev"] != prev or H(body) != r["digest"]:
            return False, f"tampered at record {i}"
        prev = r["digest"]
    if len(records) != cp["length"] or prev != cp["head"]:
        return False, f"incomplete: {len(records)} of {cp['length']} records"
    return True, "verified"

def verify_protocol(records: list) -> tuple:
    """Offline protocol check: every permit must follow a pre-gate and a mid-gate
    record for the same case, in order, each pointing at its predecessor.
    This checks what the log RECORDS; it cannot prove an honest overlay produced it."""
    by_digest = {r["digest"]: r for r in records}
    problems = []
    for r in records:
        if r["kind"] != "post_pass":
            continue
        cid, hc = r["body"]["case_id"], r["body"]["h_case"]
        mid = by_digest.get(r["body"].get("after"))
        pre = by_digest.get(mid["body"].get("after")) if mid else None
        if not mid or mid["kind"] != "mid_record" or mid["body"]["case_id"] != cid or mid["body"]["h_case"] != hc:
            problems.append(f"permit for {cid[:8]} without a valid mid-gate record"); continue
        if not pre or pre["kind"] != "pre_pass" or pre["body"]["case_id"] != cid or pre["body"]["h_case"] != hc:
            problems.append(f"permit for {cid[:8]} without a valid pre-gate record"); continue
        if not (pre["seq"] < mid["seq"] < r["seq"]):
            problems.append(f"gates out of order for {cid[:8]}")
        if mid["body"]["findings"]:
            problems.append(f"permit for {cid[:8]} issued despite mid-gate findings")
    return (not problems), problems

# ---------- the three gates ----------
@dataclass
class Case:
    case_id: str
    h_gov: str
    request: dict
    evidence: dict
    criteria: dict
    h_case: str
    findings: list = field(default_factory=list)
    stage: str = "pre"            # pre -> mid -> post
    pre_digest: str = ""
    mid_digest: str = ""

class Overlay:
    def __init__(self, governance: dict, evaluator=None, key=None, checks=None):
        self.key = key or Ed25519PrivateKey.generate()
        self.log = AuditLog(self.key)
        self.governance = governance            # committed rule envelope G_v
        self.h_gov = H(governance)
        self.evaluator = evaluator or (lambda claim, ev: ("entails", 0.99))
        # deterministic post-gate predicates: [(name, fn(case, action) -> bool)]
        self.checks = checks if checks is not None else [
            ("amount exceeds committed limit",
             lambda c, a: "max_amount" not in c.criteria or a.get("amount", 0) <= c.criteria["max_amount"])]
        self.log.append("governance_commit", {"h_gov": self.h_gov})

    def _case_hash(self, case_id, request, evidence, criteria):
        return H({"case_id": case_id, "h_gov": self.h_gov, "request": request,
                  "evidence": {k: H(v) for k, v in evidence.items()}, "criteria": criteria})

    def _logged(self, digest, kind, case):
        return any(r["digest"] == digest and r["kind"] == kind and r["body"].get("case_id") == case.case_id
                   and r["body"].get("h_case") == case.h_case for r in self.log.records)

    # PRE: authority, evidence manifest, criteria projection -> commit
    def pre_gate(self, request: dict, evidence: dict):
        g = self.governance
        missing = [e for e in g["required_evidence"] if e not in evidence]
        if missing:
            self.log.append("pre_block", {"request": request, "missing": missing})
            return "BLOCK", f"missing evidence: {missing}"
        if request["actor"] not in g["authorised_actors"]:
            self.log.append("pre_block", {"request": request, "reason": "unauthorised"})
            return "BLOCK", "actor not authorised"
        criteria = json.loads(json.dumps(g["criteria"]))    # frozen copy
        cid = str(uuid.uuid4())
        case = Case(cid, self.h_gov, request, evidence, criteria,
                    self._case_hash(cid, request, evidence, criteria))
        case.pre_digest = self.log.append("pre_pass", {"case_id": cid, "h_case": case.h_case})["digest"]
        return "PASS", case

    # MID: each reasoning step checked against committed evidence + criteria
    def mid_gate(self, case: Case, steps: list):
        if case.stage != "pre" or not self._logged(case.pre_digest, "pre_pass", case):
            self.log.append("mid_block", {"case_id": case.case_id, "reason": "no valid pre-gate record"})
            return "BLOCK"
        for s in steps:
            bad_refs = [e for e in s["cites"] if e not in case.evidence]
            if bad_refs:
                case.findings.append({"step": s["claim"], "issue": f"cites unknown {bad_refs}", "hard": True})
                continue
            verdict, conf = self.evaluator(s["claim"], [case.evidence[e] for e in s["cites"]])
            if verdict == "contradicts" and conf >= case.criteria["semantic_block_conf"]:
                case.findings.append({"step": s["claim"], "issue": "contradicted", "hard": True})
            elif verdict != "entails" or conf < case.criteria["semantic_pass_conf"]:
                case.findings.append({"step": s["claim"], "issue": f"uncertain ({verdict}, {conf})", "hard": False})
        case.mid_digest = self.log.append("mid_record", {"case_id": case.case_id, "h_case": case.h_case,
                                         "after": case.pre_digest, "findings": case.findings})["digest"]
        case.stage = "mid"
        if any(f["hard"] for f in case.findings):
            return "BLOCK"
        return "HOLD" if case.findings else "PASS"

    # POST: recompute commitments, check final action, issue action-bound permit
    def post_gate(self, case: Case, final_action: dict, live_governance: dict):
        def block(reason):
            self.log.append("post_block", {"case_id": case.case_id, "reason": reason})
            return "BLOCK", reason
        # gate order: a completed pre-gate and mid-gate record for this case must exist in the log
        if case.stage != "mid" or not self._logged(case.pre_digest, "pre_pass", case) \
                or not self._logged(case.mid_digest, "mid_record", case):
            return block("gate sequence incomplete")
        case.stage = "post"
        if H(live_governance) != case.h_gov:
            return block("governance changed since commit")
        if self._case_hash(case.case_id, case.request, case.evidence, case.criteria) != case.h_case:
            return block("case commitment altered")
        if final_action != case.request["action"]:
            return block("final action differs from committed request")
        for name, ok in self.checks:
            if not ok(case, final_action):
                return block(name)
        if case.findings:
            self.log.append("post_hold", {"case_id": case.case_id, "open": len(case.findings)})
            return "HOLD", "unresolved findings"
        permit = {"permit_id": str(uuid.uuid4()), "case_id": case.case_id,
                  "action_digest": H(final_action), "h_case": case.h_case,
                  "h_gov": self.h_gov, "expires": time.time() + case.criteria["permit_ttl_s"]}
        permit["sig"] = self.key.sign(canon(permit)).hex()
        self.log.append("post_pass", {"case_id": case.case_id, "h_case": case.h_case,
                                      "after": case.mid_digest, "permit_id": permit["permit_id"],
                                      "action_digest": permit["action_digest"]})
        return "PASS", permit
