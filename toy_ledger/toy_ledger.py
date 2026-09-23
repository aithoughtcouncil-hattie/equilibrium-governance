"""
Toy governed ledger: public governance chain + private transaction chain,
verifiable by a citizen holding only the genesis hash (+ a signed checkpoint).
Demo for Document 1, banking application (CBDC Inventions S, U, V). Not a CBDC.
"""
import copy, os, hashlib
from overlay import Overlay, H, AuditLog, verify_log, canon

GOV = {"version": 1, "required_evidence": ["balance_check"], "authorised_actors": ["bank"],
       "criteria": {"max_amount": 1000, "permit_ttl_s": 30,
                    "semantic_pass_conf": 0.8, "semantic_block_conf": 0.8}}

class Ledger:
    def __init__(self):
        self.ov = Overlay(GOV)
        self.public = AuditLog(self.ov.key)          # anyone can read
        self.private = []                            # regulator / bank only
        self.public.append("genesis", {"h_gov": self.ov.h_gov})
        self.genesis = self.public.records[0]["digest"]

    def pay(self, frm, to, amount):
        tx = {"from": frm, "to": to, "amount": amount}
        v, case = self.ov.pre_gate({"actor": "bank", "action": tx},
                                   {"balance_check": {"ok": True}})
        if v == "PASS":
            self.ov.mid_gate(case, [])
            v, _ = self.ov.post_gate(case, tx, GOV)
        salt = os.urandom(16).hex()
        self.private.append({"tx": tx, "salt": salt, "outcome": v})
        # public record: outcome + salted commitment only, no amounts or names
        self.public.append("tx", {"h_gov": self.ov.h_gov, "outcome": v,
                                  "commit": H({"tx": tx, "salt": salt})})
        return v

def citizen_verify(export, genesis, checkpoint, pub):
    if not export or export[0]["digest"] != genesis:
        return False, "genesis mismatch"
    return verify_log(export, checkpoint, pub)

if __name__ == "__main__":
    L = Ledger()
    for amt in (50, 700, 5000, 120):
        L.pay("anna", "ben", amt)
    cp, ex, pub = L.public.checkpoint(), L.public.export(), L.public.pub
    res = []
    res.append(("L1 clean public chain verifies", citizen_verify(ex, L.genesis, cp, pub)[0] is True))
    t = copy.deepcopy(ex); t[2]["body"]["outcome"] = "PASS" if t[2]["body"]["outcome"] != "PASS" else "BLOCK"
    res.append(("L2 altered public outcome rejected", citizen_verify(t, L.genesis, cp, pub)[0] is False))
    res.append(("L3 wrong genesis rejected", citizen_verify(ex, "f" * 64, cp, pub)[0] is False))
    res.append(("L4 truncated chain rejected", citizen_verify(ex[:-1], L.genesis, cp, pub)[0] is False))
    # L5 guessing attack: try every amount 1..10000 against a public commitment
    target = ex[1]["body"]["commit"]
    hit = any(H({"tx": {"from": "anna", "to": "ben", "amount": a}, "salt": ""}) == target for a in range(1, 10001))
    res.append(("L5 salted commitment resists amount guessing", hit is False))
    unsalted = H({"tx": {"from": "anna", "to": "ben", "amount": 50}, "salt": ""})
    hit_u = any(H({"tx": {"from": "anna", "to": "ben", "amount": a}, "salt": ""}) == unsalted for a in range(1, 10001))
    res.append(("L5b control: unsalted commitment IS guessable", hit_u is True))
    # L6 auditor with private access: private record matches its public commitment
    p = L.private[0]; res.append(("L6 private record matches public commitment",
                                  H({"tx": p["tx"], "salt": p["salt"]}) == ex[1]["body"]["commit"]))
    res.append(("L7 over-limit payment (5000) blocked and recorded publicly",
                ex[3]["body"]["outcome"] == "BLOCK"))
    for name, ok in res: print(("PASS " if ok else "FAIL ") + name)
    print(f"\n{sum(o for _, o in res)} of {len(res)} checks passed")
