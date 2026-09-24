| # | Scenario | Expected | Overlay | As expected | Policy-engine baseline | Median ms (overlay) |
|---|---|---|---|---|---|---|
| 1 | Clean case | PASS | PASS | yes | PASS | 0.23 |
| 2 | Criteria edited after commit | BLOCK | BLOCK | yes | PASS | 0.14 |
| 3 | Final action differs from request | BLOCK | BLOCK | yes | PASS | 0.16 |
| 6 | Missing mandatory evidence | BLOCK | BLOCK | yes | BLOCK | 0.07 |
| 7 | Ambiguous claim at mid-gate | HOLD | HOLD | yes | PASS (no HOLD state) | 0.17 |
| 8 | Audit export truncated | REJECT | REJECT | yes | REJECT | 0.83 |
| 9 | Record altered mid-chain | REJECT | REJECT | yes | REJECT | 0.78 |
| 10 | Permissive rule committed at start | PASS | PASS | yes | PASS | 0.22 |
| 11 | Mid-gate skipped | BLOCK | BLOCK | yes | n/a (single decision) | 0.12 |
| 12 | Forged permit record, re-signed log | chain VERIFIED; protocol REJECT | chain VERIFIED; protocol REJECT | yes | n/a (no protocol record) | 0.47 |

Overlay behaved as expected in 10 of 10 scenarios. Scenario 10 passing is the designed limit. Scenario 12: the chain verifier alone cannot detect a forged record from a key holder; the protocol verifier detects the missing gate records, but a key holder who fabricates a complete, consistent sequence is not detectable from the log.
