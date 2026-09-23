# The Missing Layer: Verifiable Decision Governance for High-Stakes Systems

Daniel Maclean · Thought Council, Plymouth, UK · ORCID 0009-0004-7725-687X · DRAFT, September 2026

> Every number in this draft comes from code in the accompanying repository or from the benchmarks cited. The one remaining placeholder is the release DOI [PENDING T6].

## Abstract

High-stakes systems in finance, artificial intelligence and experimental physics share a gap. They can log what they decided, but an outsider usually cannot check whether a decision followed rules fixed in advance, under evidence that was checked, through every required step. This paper specifies a three-gate decision protocol that runs beside a host system without replacing its security. A pre-decision gate commits the governing rules and evidence to a cryptographic hash; a mid-decision gate checks each stated reasoning step against those commitments and holds uncertain cases; a post-decision gate accepts only a case whose earlier gates are recorded, recomputes the commitments, binds the final action to them and issues a signed permit. Gate outcomes enter a hash-chained log with signed checkpoints, and two offline verifiers check, respectively, the integrity of the record and its compliance with the gate order. These checks establish what the operator recorded; they cannot show that an operator holding the signing key recorded truthfully. In ten scenarios, a reference implementation behaved as specified in all ten, and differed from a conventional policy engine with the same signed log in three: detecting criteria changed after commitment, detecting a final action that differs from the committed request, and holding an ambiguous case. Applied to AI output on a published human-annotated benchmark, a deterministic numeric gate that requires no language-model inference caught 80% of number and citation hallucinations while flagging 32% of clean answers. On a 300-answer sample, using it as the first stage of a two-stage check left its observed recall unchanged, reduced flagged clean answers from 34% to 26%, and required a model call for 41% of answers. The protocol guarantees consistency with committed rules, not their correctness: a permissive rule committed from the start passes.

**Keywords:** decision governance; audit integrity; cryptographic commitment; protocol compliance; AI verification; hallucination

## 1 The problem

A bank, an AI service and a physics laboratory make very different decisions. Each can still fail in the same three ways. The rules applied can be swapped during processing. The evidence can be missing or fabricated. The record can be edited or cut short afterwards. Existing security protects access, confidentiality and availability. It does not give an outside party proof that a particular decision followed the rules that were in force when it started.

Three recent pressures make that record valuable. Regulators increasingly require organisations to demonstrate, not assert, that automated decisions followed policy. Generative AI produces fluent output containing numbers and citations that no source supports. Experimental science faces well-publicised replication problems, where the conditions under which data were accepted cannot be reconstructed.

The contribution here is a single layer that addresses all three, sitting beside the host rather than inside it. The host keeps its own authentication, fraud controls, replay protection and machine safety. The overlay adds commitment, ordered checking and a verifiable record. It is the operational form of the Initial Condition Ethics principle, that governing the initial conditions of a decision is more robust than intervening afterwards [11].

## 2 Relationship to existing work

Policy frameworks such as XACML separate policy decision from enforcement [1]; the overlay can use such engines for its predicates. SHA-256 [2] over a canonical encoding [3] provides binding identifiers. Certificate Transparency's signed tree heads [4] and RFC 3161 time-stamps [5] show how authenticated log commitments support independent checking; the checkpoint design below follows that pattern. Natural language inference [6] can support semantic checks, but it is fallible under adversarial cases [7], so the protocol treats it as an assessment with an explicit uncertainty outcome, never as proof.

No novelty is claimed for hashing, signatures, policy engines, signed logs or action-bound tokens. A policy engine with signed, hash-chained decision logs and tokens bound to the authorised action already provides record integrity and prevents a token being used for a different action. The question is what an ordered, multi-stage protocol adds to that combination. Section 4 answers it empirically by running the same scenarios against such a baseline. The differences are confined to properties that require state across stages: evaluating a case against the criteria committed when it began rather than those loaded when it ends; requiring the final action to equal the committed request, rather than merely satisfying the policy; and a mid-decision state that holds uncertain cases instead of deciding them. The contribution is the specification of that protocol, its offline compliance check, and its evaluation, not new cryptography.

## 3 Architecture

### 3.1 Roles and trust model

A requester submits a decision request. Evidence providers supply records. A decision producer (a human, an AI model or an instrument) proposes the action. The overlay runs the three gates and keeps the log. The host executes the action. The governance authority approves rule versions. The overlay assumes collision-resistant hashing, authentic verification keys and an execution path that honours permits. A compromised signing key, a colluding governance authority or a dishonest evidence source defeats the guarantees outside those assumptions.

### 3.2 Commitments

Let C be a canonical encoding and H a cryptographic hash. The governance envelope G contains the rule version, authorised actors, required evidence types, executable criteria and evaluator configuration.

```
H_gov = H(C(G))
H_case = H(C(case_id, H_gov, request, {k: H(e_k)}, criteria))
```

H_gov identifies the approved rules. H_case binds one decision to its request, its evidence digests and a frozen copy of the criteria.

### 3.3 The three gates

Each case moves through the states pre, mid and post. Every gate record carries the case identifier and H_case, and each later record points to the digest of the record before it, so the order is itself committed.

**Algorithm 1: Pre-decision gate**
```
input: request R, evidence set E
1  for each required evidence type t in G: if t not in E -> log(pre_block); return BLOCK
2  if R.actor not in G.authorised_actors -> log(pre_block); return BLOCK
3  K <- deep copy of G.criteria            // frozen criteria
4  case_id <- fresh identifier
5  H_case <- H(C(case_id, H_gov, R, digests(E), K))
6  d_pre <- log(pre_pass, case_id, H_case); case.stage <- pre; return case
```

**Algorithm 2: Mid-decision gate**
```
input: case, reasoning steps S
1  if case.stage != pre or no logged pre_pass (d_pre, case_id, H_case) -> log(mid_block); return BLOCK
2  for each step s in S:
3     if s cites evidence not in case.E -> hard finding
4     (verdict, confidence) <- evaluator(s.claim, cited evidence)
5     if verdict = contradicts and confidence >= K.block_conf -> hard finding
6     else if verdict != entails or confidence < K.pass_conf -> soft finding
7  d_mid <- log(mid_record, case_id, H_case, after = d_pre, findings); case.stage <- mid
8  return BLOCK if any hard finding; HOLD if any soft finding; else PASS
```

**Algorithm 3: Post-decision gate**
```
input: case, final action A, live governance G'
1  if case.stage != mid or no logged pre_pass (d_pre) or mid_record (d_mid) for this case
                                            -> BLOCK "gate sequence incomplete"
2  if H(C(G')) != case.H_gov                 -> BLOCK "governance changed"
3  if recompute(H_case) != case.H_case        -> BLOCK "case altered"
4  if A != case.R.action                      -> BLOCK "action differs"
5  for each deterministic predicate p in K: if not p(case, A) -> BLOCK p.name
6  if unresolved findings                     -> log(post_hold); return HOLD
7  permit <- {permit_id, case_id, H(A), H_case, H_gov, expiry}
8  permit.sig <- Sign(C(permit)); log(post_pass, case_id, H_case, after = d_mid); return permit
```

Step 1 of Algorithm 3 means a permit cannot be issued for a case whose mid-gate never ran: absence of findings is not treated as a pass. Deterministic predicates (limits, identities, time windows) are evaluated in code, never by a language model: a stated amount of 1,200 cannot pass a limit of 1,000 on a favourable semantic score.

### 3.4 Audit log and offline verification

Each log record holds a sequence number, kind, body and the previous record's digest; its own digest covers all four. Hash chaining detects alteration, but not truncation, because a valid prefix is still a valid chain. The overlay therefore publishes signed checkpoints committing to the log's length and head digest. Two verifiers run offline.

**Algorithm 4: Record-integrity verifier**
```
input: exported records X, checkpoint cp, public key pk
1  verify cp.sig over (cp.length, cp.head) with pk, else REJECT
2  prev <- zero digest
3  for i, r in X: if r.seq != i or r.prev != prev or H(r without digest) != r.digest -> REJECT "tampered at i"
4     prev <- r.digest
5  if |X| != cp.length or prev != cp.head -> REJECT "incomplete"
6  return VERIFIED
```

**Algorithm 5: Protocol-compliance verifier**
```
input: exported records X
1  for each post_pass record q in X:
2     m <- record with digest q.after;  p <- record with digest m.after
3     require m is mid_record and p is pre_pass for the same case_id and H_case, else REJECT
4     require p.seq < m.seq < q.seq, else REJECT "out of order"
5     require m.findings is empty, else REJECT "permit despite findings"
6  return COMPLIANT
```

**What verification establishes.** Algorithm 4 shows that the exported log is complete and unaltered relative to a checkpoint the auditor holds. Algorithm 5 shows that every recorded permit is preceded by recorded pre-gate and mid-gate outcomes for the same case, in order and without open findings. Neither shows that the checks were actually performed as recorded, or that recorded outcomes are truthful. An operator who holds the signing key can fabricate a complete, internally consistent sequence (Section 4, scenario 12). Stronger assurance requires separating the signing key from the operator, for example through independent witnesses that countersign checkpoints or trusted execution for the gates; these are outside the scope of this paper.

### 3.5 Host hand-off

The permit binds one exact action by digest and carries an identifier and an expiry. Rejecting a second use of the same permit and rejecting expired permits are the host's responsibility; banks, AI services and instruments already implement such controls. The overlay supplies the data those controls need rather than duplicating them.

## 4 Evaluation

### 4.1 Method

Ten scenarios exercise the behaviours the protocol owns. They include a clean case, a deliberately permissive rule that should pass, a case whose mid-gate is skipped, and a log into which a key holder inserts a permit record without gate records and then re-signs the checkpoint. Each scenario was run against the reference implementation, against an earlier prototype of the author's with the same design intent, not released, where the scenario applies, and against a baseline policy engine. The baseline evaluates each request once, at decision time, against the currently loaded policy, supports required-evidence rules and limits, writes to the same signed, hash-chained and checkpointed log, and issues tokens bound to the authorised action. The scenarios are deterministic; each was repeated 20 times only to measure timing. They test specified behaviours, not broader security coverage.

### 4.2 Results

| # | Scenario | Expected | Reference implementation | Policy-engine baseline | Earlier prototype |
|---|---|---|---|---|---|
| 1 | Clean case | PASS | PASS | PASS | ALLOW |
| 2 | Criteria edited after commit | BLOCK | BLOCK | PASS | ALLOW |
| 3 | Final action differs from request (50 to 500) | BLOCK | BLOCK | PASS | NARROWED |
| 6 | Missing mandatory evidence | BLOCK | BLOCK | BLOCK | not implemented |
| 7 | Ambiguous claim at mid-gate | HOLD | HOLD | PASS (no HOLD state) | not implemented |
| 8 | Audit export truncated | REJECT | REJECT | REJECT | not implemented |
| 9 | Record altered mid-chain | REJECT | REJECT | REJECT | REJECT |
| 10 | Permissive rule committed at start | PASS | PASS | PASS | ALLOW |
| 11 | Mid-gate skipped | BLOCK | BLOCK | not applicable | not tested |
| 12 | Forged permit record, log re-signed by key holder | integrity VERIFIED; protocol REJECT | as expected | not applicable | not tested |

The reference implementation behaved as specified in all ten scenarios. It differed from the baseline in scenarios 2, 3 and 7. In scenario 2 the baseline evaluated the case against the edited criteria and passed it; it recorded the new policy hash, so the change was visible afterwards, but the decision went through. In scenario 3 the baseline passed the larger amount because it satisfied the policy; the protocol blocked it because it differed from the committed request. Scenarios 6, 8, 9 and 10 show properties the baseline shares. Scenario 12 shows the limit stated in Section 3.4: the integrity verifier accepted the re-signed log, and only the protocol verifier detected the missing gate records. A key holder who fabricated the gate records as well would not be detected. The earlier prototype matched the expected outcome in 3 of the 8 scenarios that applied to it; its main gap was scenario 2, because it computed H_gov but did not recompute it at decision time.

Median latency per scenario was 0.07–0.83 ms on an Intel i7-8700 at 3.2 GHz with 32 GB RAM, Windows 10, Python 3.12, including key generation; the two record-level scenarios (11 and 12) took 0.12 ms and 0.47 ms. This indicates the checks are inexpensive; it is not a production benchmark.

## 5 Applications

### 5.1 AI output: catching fabricated numbers and citations

Today, a model's answer is released with whatever figures and references it generated. The overlay's post-gate adds a deterministic predicate: every number and citation in the answer must be traceable to the committed source set; untraced answers are held for review. The check is narrow by design: it does not judge whether an answer is wise, only whether its checkable claims have a source.

**Development.** A first version matched numbers as exact strings. On a constructed adversarial set of 287 items it agreed with a careful human judgement on only 3%: it blocked every honest restatement (rounding, "1.2 million", unit conversion) and missed every fabricated number that looked legitimate. A second version compares values rather than strings. It parses number words from zero to ninety-nine, including hyphenated and two-word compounds, and scale words following a number ("six million"), converts units, matches at the stated precision, derives percentages from pairs of source values, and requires each number to be attached to the same claim as in the source. Its code was then frozen and recorded by hash. On a held-out constructed set of 210 items from unseen sources it agreed with human judgement on 78% (95% CI 72–83%), against 79% during development. The similar figures are consistent with limited overfitting to the development set but do not establish its absence, because both sets were constructed by the same procedure. It routed 90% of fabricated figures and citations to review (83–94%) and passed 64% of honest restatements (54–73%).

**Real model output.** The frozen gate, which requires no language-model inference, was then scored on the test split of RAGTruth [13], a published corpus of language-model answers to retrieved documents with human-annotated hallucinations. On the 2,069 answers that were either clean or contained a numeric or citation hallucination, the gate caught 80% of those hallucinations (76–84%). Its precision was low: 31% of flagged answers contained a hallucination, and 32% of clean answers were flagged. False flags concentrated in data-to-text answers, which restate structured records and reformat nearly every number (65% flagged). On all 2,700 test answers, including non-numeric hallucinations the gate does not target, recall was 56%.

**Two-stage check.** On a random sample of 300 numeric-subset answers, fixed before any second-stage result was seen, five configurations were compared (Table 2). The second-stage checkers were a language-model self-check (gpt-4o-mini, strict fact-checking prompt, temperature 0) and MiniCheck, a published fact-support classifier [14], in its RoBERTa-Large variant run on CPU. In a cascade, an answer is held only if the gate flags it and the second stage confirms.

| Configuration | Recall | Precision | Clean answers flagged | Model calls |
|---|---|---|---|---|
| Gate alone | 0.85 (0.70–0.93) | 0.27 (0.20–0.35) | 0.34 (0.29–0.40) | 0 |
| Self-check alone | 1.00 (0.91–1.00) | 0.19 (0.15–0.25) | 0.62 (0.56–0.68) | 300 |
| MiniCheck alone | 0.46 (0.32–0.61) | 0.16 (0.10–0.23) | 0.38 (0.32–0.44) | 300 |
| Gate, then self-check | 0.85 (0.70–0.93) | 0.33 (0.25–0.43) | 0.26 (0.21–0.31) | 123 (41%) |
| Gate, then MiniCheck | 0.38 (0.25–0.54) | 0.27 (0.17–0.40) | 0.15 (0.11–0.20) | 123 (41%) |

*Table 2. Numeric-subset sample (n = 300; 39 hallucinated). 95% Wilson intervals.*

On this sample, the cascade of gate then self-check left the gate's observed recall unchanged, reduced flagged clean answers from 34% (gate) and 62% (self-check) to 26%, and needed a model call for only 41% of answers. No single checker dominated: each configuration is a different point on the trade-off between catching errors and flagging honest answers. The deterministic gate's role is a first filter that requires no language-model inference and whose every decision is logged; the second stage is a pluggable evaluator, as in the architecture of Section 3.

**Limits of this evaluation.** The sample contains only 39 hallucinated answers, so recall intervals are wide. The self-check prompt is strict and was not tuned; MiniCheck was run in its smallest CPU variant, and larger variants score higher on RAGTruth's own leaderboard. Published trained detectors outperform the gate as standalone detectors; its contribution is cost and auditability, not accuracy. The gate does not address non-numeric hallucinations.

### 5.2 AI learning: governed rule promotion

Developmental agents that learn rules from experience face a governance question: what was promoted to core policy, on what evidence, and who approved it? The overlay treats each promotion as a governed decision. The pre-gate commits the rule's statistics and the promotion thresholds; the mid-gate records the evaluator's judgement on whether the rule generalises; the post-gate checks thresholds and approver authority, then logs the permit. In a demonstration with a mocked host (no model calls), the overlay promoted a qualifying rule, blocked a low-confidence rule, blocked an unauthorised approver, blocked a mid-case threshold change, held an uncertain generalisation, and produced an offline-verifiable trail of all of it (6 of 6 checks). Running the wrapper against a live promotion queue is left to future work.

### 5.3 Banking: a citizen-verifiable ledger

A central-bank digital currency must be private and publicly accountable at once. The overlay supports this by splitting the record. A private chain holds transaction details for the operator and regulator. A public chain holds, per transaction, only the governance hash, the gate outcome and a salted commitment to the private record. A citizen holding the genesis hash and a signed checkpoint can verify the whole public history offline.

In the toy ledger all eight checks passed: clean verification, rejection of an altered outcome, rejection of a wrong genesis hash, rejection of a truncated chain, resistance of salted commitments to amount guessing, a control showing unsalted commitments are guessable by brute force over 10,000 amounts, private-to-public consistency for an auditor, and public recording of a blocked over-limit payment. The control result matters: a public hash of a predictable value leaks that value. Offline verification scaled linearly on the same laptop: 0.06 s for 10^4 records, 0.71 s for 10^5 and 6.4 s for 10^6, with export sizes of 3.7, 36.8 and 368.9 MB. This is a design demonstration, not a currency system.

### 5.4 Quantum measurement

Quantum experiments decide which data count. A standard acceptance rule for entanglement, a CHSH value S above 2, can be satisfied by a purely classical model when detection is biased. In the accompanying simulation a local model reaches S = 2.69 at conditional detection efficiency 0.853: it passes the naive rule and stays below the quantum bound of 2√2, but fails the detection-aware bound 4/η − 2 [8, 9]. Loophole-free tests closed this gap experimentally, including with NV centres in diamond [10]. The overlay's contribution is procedural: the correct rule is committed before the run and checked against measured conditions. The full application is specified in the companion proposal (Document 2).

### 5.5 Fusion operation

Fusion experiments run as discrete shots within operating envelopes. The overlay applies directly: commit the envelope before each shot, gate acceptance of the shot's data against it, and log the result. This governs the experiment, not the plasma physics. The application is specified in the companion proposal (Document 3).

## 6 Limitations

The protocol checks consistency with committed rules, not the rules' correctness. Scenario 10 shows a permissive rule, committed openly, authorising a harmful action with a valid, compliant record.

Verification is bounded by trust in the operator. The verifiers establish that a record is complete, unaltered and in protocol order relative to a checkpoint; they do not establish that recorded checks ran or that recorded outcomes are true. A key holder can fabricate a consistent record. Evidence authenticity is also assumed at admission, and offline verification cannot reveal events after the latest checkpoint an auditor holds.

The mid-gate's semantic evaluator is fallible, which is why uncertain judgements hold rather than pass. The numeric gate covers numbers and citations only, not other kinds of hallucination. It parses number words up to ninety-nine and scale words after a number, but misses longer spelled-out forms such as "one hundred and twelve", words used as quantities such as "a dozen", "half" or "a million", fractions and ordinals; in the held-out set it caught 72% of spelled-out wrong numbers. It also flags many honest restatements, especially reformatted structured data.

The AI evaluation's comparison sample contains 39 hallucinated answers, so its recall intervals are wide, and the cascade finding is an observation on that sample. The self-check prompt was not tuned, and MiniCheck was run in its smallest CPU variant. The reference implementation uses a simple canonical JSON encoding rather than a full RFC 8785 implementation and signs with a single key. Additional gates add latency and can falsely block valid decisions; the costs must be measured per deployment.

## 7 What others can take further

Each item below is stated so that another group can act on it without contacting the author. The code, benchmarks and scenario definitions are released under an MIT licence.

**Remove the trusted-operator assumption.** The verifiers establish what was recorded, not that it is true (Section 3.4). The natural next step is to separate the signing key from the operator: independent witnesses countersigning checkpoints, publication of checkpoints to a public transparency log, or execution of the gates in a trusted environment. Each changes what an auditor can conclude, and the change should be stated as precisely as the current guarantee.

**Test the protocol against a production policy engine.** The baseline here is a minimal engine written for comparison. A stronger test implements the three gates over an established engine with decision logging and a transparency log, and reports which of the ten scenarios each configuration passes, along with the engineering cost of the case-commitment state.

**Extend and re-evaluate the numeric gate.** Its known gaps are longer spelled-out numbers, quantity words, fractions and ordinals (Section 6). Closing them and re-running the RAGTruth evaluation would show how much of the residual 20% of missed hallucinations is parsing rather than method. The frozen version and its hash are released so that any improvement can be compared against the same starting point.

**Map the cost curve of the second stage.** This paper reports one cascade configuration on a 300-answer sample. A fuller study varies the first-stage threshold, measures recall, false flags and model calls across the range, and reports cost per detected hallucination for several second-stage checkers, including larger MiniCheck variants and trained detectors.

**Evaluate on other corpora and other tasks.** RAGTruth covers question answering, data-to-text and summarisation. Factual-consistency corpora with different annotation schemes would show whether the 80% recall on numeric hallucinations holds elsewhere, and where a deterministic gate stops being useful.

**Run the domain applications.** The quantum protocol is specified with kill criteria for a laboratory to run [companion paper]; the fusion application proposes replaying a past campaign's acceptance decisions through the gates using open shot data [companion paper]. Both are specified to be executed by groups with the facilities, not by the author.

**Try to break it.** The scenario suite tests specified behaviours, not adversarial ingenuity. An independent attempt to obtain a permit that the protocol should refuse, or to construct a log that passes both verifiers while misrepresenting what happened, would be more informative than further scenarios written by the author.

## 8 Conclusion

A three-gate protocol can give high-stakes systems a record that outsiders can check: that each decision was evaluated against rules committed in advance, on declared evidence, through every required step, in a complete and unaltered log. Against a conventional policy engine with the same signed log, the protocol's measurable additions are detection of criteria changed mid-case, binding of the final action to the committed request, and a hold state for uncertain cases. The strongest practical result is in AI output checking, where a deterministic gate requiring no model inference caught most numeric hallucinations on a published benchmark and, on a sample, reduced the model calls and false flags of a second-stage checker. The applications to payments, AI learning, quantum measurement and fusion operation show the same protocol in other hosts. Its boundary is stated plainly: it makes rule substitution, skipped steps and incomplete records detectable in the record; it cannot make a bad rule good or an untrustworthy operator honest.

## Code availability

Reference implementation, baseline policy engine, scenario suite, benchmark scripts, applications and simulations: https://github.com/aithoughtcouncil-hattie/missing-layer — MIT licence. Archived release: **[PENDING T6: Zenodo DOI.]**

## Declarations

The author holds related UK patent applications (GB2606620.9, GB2606946.8, GB2606948.4). AI tools assisted drafting and code; all results were produced by the released code.

## References

[1] OASIS. eXtensible Access Control Markup Language (XACML) Version 3.0. 2013.
[2] NIST. Secure Hash Standard. FIPS 180-4. 2015. doi:10.6028/NIST.FIPS.180-4
[3] Rundgren A, Jordan B, Erdtman S. JSON Canonicalization Scheme. RFC 8785. 2020.
[4] Laurie B, Messeri E, Stradling R. Certificate Transparency Version 2.0. RFC 9162. 2021.
[5] Adams C et al. Internet X.509 PKI Time-Stamp Protocol. RFC 3161. 2001.
[6] Williams A, Nangia N, Bowman SR. A Broad-Coverage Challenge Corpus for Sentence Understanding through Inference. NAACL 2018.
[7] McCoy RT, Pavlick E, Linzen T. Right for the Wrong Reasons. ACL 2019.
[8] Larsson J-Å. Bell's inequality and detector inefficiency. Phys. Rev. A 57, 3304 (1998).
[9] Garg A, Mermin ND. Detector inefficiencies in the Einstein-Podolsky-Rosen experiment. Phys. Rev. D 35, 3831 (1987).
[10] Hensen B et al. Loophole-free Bell inequality violation using electron spins separated by 1.3 kilometres. Nature 526, 682 (2015).
[11] Maclean D. Initial Condition Ethics. ASI Series Paper 4. Zenodo (2026). doi:10.5281/zenodo.22845539
[12] Josefsson S, Liusvaara I. Edwards-Curve Digital Signature Algorithm (EdDSA). RFC 8032. 2017.
[13] Niu C, Wu Y, Zhu J, et al. RAGTruth: A hallucination corpus for developing trustworthy retrieval-augmented language models. ACL 2024. arXiv:2401.00396.
[14] Tang L, Laban P, Durrett G. MiniCheck: Efficient fact-checking of LLMs on grounding documents. EMNLP 2024. arXiv:2404.10774.
