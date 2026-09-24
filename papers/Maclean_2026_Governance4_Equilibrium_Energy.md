# Equilibrium-Based Control as a Design Philosophy for Computing Systems

**A design philosophy for computing systems — a measured result, a hardware corollary, and a general principle**

Daniel Maclean
Independent Researcher · [thoughtcouncil.org](https://thoughtcouncil.org)
daniel@thoughtcouncil.org
ORCID: [https://orcid.org/0009-0004-7725-687X](https://orcid.org/0009-0004-7725-687X)

Academic Version · For peer review · September 2026

*A measured result, a hardware corollary, and a general principle*

---

## Abstract

Modern computing has adopted maximisation-based control as the default across the stack — chip design, operating systems, workload schedulers, cloud orchestration, building HVAC. This produces well-documented inefficiencies: high idle power, thermal cycling under load, resource waste, opportunistic peak-seeking that rarely aligns with what an outcome requires. Homeostatic control theory has understood the alternative for decades, but it has not been articulated as a unified design philosophy applicable across the whole compute stack.

This paper argues that equilibrium-based control, applied consistently from silicon to fleet, produces significant efficiency gains. It presents three pieces of evidence: a measured energy result showing a cascade routing pattern using a governance overlay as first-stage filter delivers 36% of the energy per correct decision compared to a monolithic small transformer on the same workload; an analytic model showing that a hardware architecture built on the same principles is consistent with a claimed 2.74 TOPS/W efficiency; and a general framing showing the principle applies wherever a goal-directed system operates under resource constraints with variable demand.

The paper explicitly does not claim to originate the equilibrium principle. Homeostasis has been named since Cannon (1932). Negative feedback control has structured engineering since Wiener (1948). Aristotelian virtue ethics and the Buddhist middle way both articulate variants at civilisational scale. What this paper contributes is the specific observation that modern computing has quietly adopted the opposite philosophy, that the resulting inefficiency is systematic and measurable, and that a coherent design alternative exists and can be tested.

---

## 1 The maximisation default

Modern computing systems, at almost every layer of abstraction, are designed to maximise something. A CPU boosts to peak frequency when work arrives. A GPU pushes to thermal limits under load. An operating system scheduler opportunistically bursts to complete work as quickly as possible. A cloud orchestrator autoscales aggressively to meet demand spikes. A database runs background maintenance whenever resources are available. A HVAC system runs the compressor at full power when temperature drifts.

Each of these decisions, made independently, appears reasonable. Taken together, they produce a stack in which every layer opportunistically maximises its own metric, and the system as a whole consumes far more resources than the actual work requires.

This paper argues that the maximisation default is the wrong control philosophy for the environment computing operates in today. The argument does not rest on any single technical result. It rests on the observation that maximisation-based design assumes conditions that stopped being true decades ago: continuous demand, scarce compute, unlimited energy, and dedicated infrastructure. None of these assumptions holds in 2026. Compute is abundant. Demand is bursty. Energy is expensive and constrained by climate obligations. Infrastructure is shared across variable workloads. Under current conditions, maximisation-based control produces systematic waste that could be recovered by different design choices.

The alternative is not new. Homeostatic control, sustained-equilibrium targeting, and predictive rather than reactive management have been well-understood in biology and control theory for most of a century. What is new is the observation that these principles have not been adopted as a unified design philosophy for computing systems, and that doing so would produce meaningful efficiency gains at every scale from personal devices to national infrastructure.

---

## 2 Precedent and positioning

The equilibrium principle in the sense used here has three main precedents.

**Biological homeostasis.** Cannon (1932) named the property by which biological systems maintain stable internal conditions in the face of external variation. Body temperature, blood glucose, blood pressure, and dozens of other variables are actively regulated toward set points rather than allowed to drift or maximise. When the set point is reached, the regulatory drive quiets. Perturbations are corrected. The result is a system that maintains function across a wide range of external conditions using far less energy than a maximisation-based alternative would require.

**Control theory.** Wiener (1948) and subsequent developments in classical and modern control theory formalised the mathematics of feedback and set-point regulation. Modern control systems, from industrial process control to aircraft autopilots, are built on these foundations. What has not happened is systematic application of the same principles to consumer and enterprise computing, where control decisions are still largely reactive and threshold-based rather than predictive and equilibrium-oriented.

**Philosophical antecedents.** Aristotelian virtue ethics articulates the golden mean as the correct principle of action, holding that virtue lies between deficiency and excess. Buddhist ethics articulates the middle way as the path between indulgence and denial. Both traditions contain the general insight that maximisation of any single dimension produces pathology, and that sustainable operation requires targeting an equilibrium rather than an extreme.

This paper contributes none of these. What it contributes is the specific observation that modern computing has adopted the opposite philosophy without noticing, and the specific proposal that adopting equilibrium-based control across the stack would produce measurable efficiency gains. The technical contribution is a measured result on real silicon, an analytic model of a hardware architecture built on the principle, and a general framing that lets engineers in specific domains recognise their own problem in the framework and apply it.

---

## 3 The principle stated

Equilibrium-based control, as used in this paper, refers to a design philosophy with four core properties.

**Sustained rather than peak.** The system targets a sustainable operating point rather than pushing toward maximum capability. Peak output is available when the outcome genuinely requires it, but the default is a level of operation that can be maintained without thermal stress, resource depletion, or resource waste. Peak becomes a controlled and intentional escalation rather than the default operating mode.

**Predictive rather than reactive.** The system anticipates upcoming conditions using available signals (workload patterns, environmental data, scheduled events, user behaviour) and pre-positions to meet them efficiently, rather than waiting for conditions to change and then responding. Reactive control is inherently late, always chasing conditions that have already changed. Predictive control operates in the future tense, meeting conditions as they arrive rather than after they have already caused disturbance.

**Quiet by default.** When the drive is satisfied, the system quiets rather than continuing to maximise. A satisfied thermal target does not require continued cooling effort. A satisfied throughput target does not require additional resources to be allocated. A satisfied user request does not require the system to remain in an elevated readiness state. Quiet default means genuine deep-sleep when work is absent, rather than continued baseline consumption "just in case."

**Coordinated across coupled subsystems.** When multiple subsystems share resources or influence each other's operation, they coordinate rather than each locally maximising. A CPU that knows the GPU is also active can share thermal budget rather than both pushing to independent thermal limits. A cooling system that knows heating will begin shortly can pre-position rather than fight the coming demand. Coordination requires that subsystems share information and jointly optimise, rather than each operating on local information alone.

These four properties, applied consistently across a system's layers, produce a design that operates at markedly higher efficiency than the maximisation-based default. The following sections present three lines of evidence for this claim.

---

## 4 A measured result

A concrete demonstration of equilibrium-based control at the software layer was performed on standard silicon. The workload was sentiment classification, a common inference task suitable for benchmarking because the reference implementation (DistilBERT-base, sentiment fine-tuned) is well-characterised and the correctness of outputs is straightforward to verify.

**Design.** Two implementations were compared on identical input sets:

- **Baseline (B1):** DistilBERT-only. Every input classified by full transformer inference.
- **Cascade (B2):** Governance overlay as first-stage filter. Inputs matching a committed lexicon rule with high confidence are classified directly by the overlay; ambiguous inputs are escalated to DistilBERT. The lexicon rule was committed and hashed before evaluation (SHA-256 `f06aea0c5ebf34609a7846fafaa20c0f92af56412415ec01ace82758751bf4b9`), preventing post-hoc adjustment.

**Instrumentation.** CPU package power was measured using LibreHardwareMonitor via WMI polling on an Intel i7-8700 running Windows. Idle baseline was measured for 60 seconds before each run and subtracted from workload measurements. Each workload was run three times with 300 items per class (600 total items, 100% coverage across both sentiment classes after the v2 dataset fix). CPU-time energy estimates using process time × TDP were computed as a cross-check.

**Results.**

| Workload | Wall ms/dec | CPU-time energy | LHM measured | LHM delta over idle |
|---|---|---|---|---|
| B1 DistilBERT alone | 13.19 ± 0.11 | 856 mJ | 897 ± 20 mJ | 774 ± 21 mJ |
| B2 cascade | 5.52 ± 0.04 | 359 mJ | 342 ± 22 mJ | 277 ± 22 mJ |

Cascade / DistilBERT-alone ratio: **0.358** (measured, idle-delta), **0.425** (CPU-time estimate).

**Accuracy check.** The decisive items handled by the overlay were independently classified by DistilBERT to verify agreement. Positive-direction agreement: 100% (300/300). Negative-direction agreement: 100% (300/300). Overall agreement: 100% (600/600). No accuracy was traded for the energy saving.

**Interpretation.** On this workload, the cascade delivered the same output as monolithic DistilBERT while consuming approximately 36% of the energy per correct decision. The efficiency gain comes from the overlay's ability to handle unambiguous cases at near-zero cost without invoking the expensive model. Because agreement is 100%, the ratio measures pure efficiency rather than an accuracy-for-energy trade.

**Caveats.** The workload was well-matched to the lexicon rule; harder or more variable workloads will produce lower agreement rates and require the cascade to escalate more often, reducing the efficiency gain. The result is a demonstration that the principle works when the classifier is correctly calibrated for the workload, not a claim of a universal 64% saving on all inference tasks. Every deployment of the pattern must test the classifier's accuracy on its actual data distribution before the efficiency claim transfers.

The reference implementation, benchmark harness, dataset generator, and raw results are available in the accompanying repository (see *Code and reproducibility* below).

---

## 5 A hardware corollary

The same principles that produced the software cascade result can be applied at the silicon layer. The eco chip architecture (specified in UK patent GB2606946.8) is one such application: a four-die chiplet stack in which a Governance Die filters decisions before they reach the compute chiplets, and a Somatic Power Rail, Constitutional Friction Circuit, and Equilibrium Drive implement homeostatic thermal management rather than reactive throttling.

An analytic energy model of this architecture was constructed to test whether the claimed 2.74 TOPS/W sustained efficiency is consistent with defensible arithmetic on published component-level parameters. The load-bearing assumption is the sustained fraction — the ratio of sustained delivered throughput to peak theoretical throughput — which conventional reactive throttling achieves at 0.50-0.70 (mid 0.60) and which proactive homeostatic control is credibly claimed to achieve at 0.70-0.88 (mid 0.80), based on published efficiency results for recent mobile-oriented SoC designs.

**Result.** The analytic model produces a defensible range of 2.28 to 2.87 TOPS/W with a mid-scenario of 2.61 TOPS/W. The patent's 2.74 TOPS/W claim falls inside this range, above the mid-scenario, at the top of the defensible band. The +40% advantage over a conventional silicon baseline of 2.0 TOPS/W holds across the entire range: even the low scenario (2.28 TOPS/W) beats 2.0 TOPS/W by 14%.

**Single point of failure.** If the Equilibrium Drive does not deliver its homeostatic advantage and the eco chip's sustained fraction collapses to conventional's 0.60, TOPS/W falls to 1.96, below the baseline. Every other input can vary by ±20% without changing the verdict. The sustained-fraction claim is therefore the single assumption that must be empirically validated, which requires FPGA prototyping under continuous inference load with instrumented thermals — not analytic modelling.

**Positioning.** The eco chip at 2.74 TOPS/W is below modern data-centre AI accelerators running sparse INT8 workloads (roughly 3.67 TOPS/W per MLPerf inference v5.1 results). The design is not intended to compete with flagship inference accelerators on peak metrics. It is intended for edge and constrained deployment where current AI silicon does not fit: drones, medical devices, environmental monitoring, developing-world AI infrastructure, assistive technology, distributed edge computing, disaster response. In that market segment, the design's efficiency advantages plus its hardware governance capabilities represent a distinct contribution.

---

## 6 Applications beyond compute

The equilibrium principle is not specific to computing systems. Any goal-directed system operating under resource constraints with variable demand benefits from equilibrium-based control. The following applications are noted for completeness; each would require its own domain-specific implementation and evaluation.

**Building climate control.** Modern HVAC is dominantly reactive: temperature drifts, compressor runs, temperature overshoots, compressor stops. Predictive equilibrium-based control that anticipates thermal loads from weather forecasts, occupancy patterns, and solar exposure has been shown to reduce commercial HVAC energy by 30-40% at the building level and up to 40% for data centre cooling specifically. The technology exists; systematic adoption does not.

**Electric vehicle battery management.** Battery pack thermal management, charging curves, regenerative braking aggressiveness, and pre-conditioning for expected conditions are all equilibrium control problems. Predictive management using route data, weather, and driving patterns can extend usable range by 5-15% on the same hardware. Some manufacturers implement partial versions; most do not.

**Grid-scale energy management.** The transition to variable renewable generation makes grid balancing a distributed equilibrium problem rather than a reactive dispatch problem. Coordinated management of demand-side flexibility (smart thermostats, EV charging, industrial loads), storage buffering, and long-distance transmission benefits from equilibrium-based rather than reactive control philosophies.

**Industrial process control.** Manufacturing, chemical processing, water treatment, cement production, steel and aluminium smelting are all goal-directed control systems currently run on largely reactive control. Even modest efficiency gains from equilibrium-based control produce disproportionate impact because the total energy involved is enormous. Cement production alone accounts for 8% of global CO₂ emissions; a 5% efficiency improvement at this scale is larger than most well-funded climate interventions will ever achieve.

**Cybersecurity operations.** Current enterprise security consists of stacks of independent tools each locally optimising: firewall, IDS, EDR, SIEM, DLP. Each generates alerts independently. Together they produce alert fatigue, resource waste, and worse security than a coordinated approach would give. An equilibrium-based security architecture would coordinate across tools, share context, and produce genuinely joint signals rather than parallel independent alerts. This is what "extended detection and response" platforms are supposed to be; most are not.

**Consumer electronics and mobile computing.** Modern laptops burn substantial battery on opportunistic frequency boosting for work that does not require it. Homeostatic control at the operating system layer, targeting sustained thermal and performance equilibrium rather than opportunistic peaks, produces significant battery-life gains without noticeable performance loss. Some mobile-oriented SoC designs already demonstrate this pattern; commodity laptop and desktop systems mostly do not.

This list is not exhaustive. Any system with variable demand, resource constraints, and coupled subsystems is a candidate for equilibrium-based control. The paper does not attempt to solve any of these domains. It observes that the general principle applies and that experts in each domain are best positioned to implement it once the framing is articulated.

---

## 7 What this paper is and is not

**This paper is:** a specific claim that modern computing systems have systematically adopted maximisation-based control despite the conditions that justified this choice no longer holding; a measured result showing that an equilibrium-based cascade pattern delivers 64% energy reduction on real silicon while preserving accuracy; an analytic model showing that a hardware architecture built on the same principles is consistent with a claimed 2.74 TOPS/W efficiency; and a framing that makes the principle available to engineers in other domains for application to their own systems.

**This paper is not:** a claim that equilibrium as a control principle is new; a claim that any specific measured saving generalises to all workloads without empirical validation; a claim that homeostatic hardware exists in production or that any specific chip design has been physically tested; a claim that the framework should be applied without engineering judgement to systems where its assumptions do not hold.

The distinction matters. Grand claims dressed up in technical language damage credibility. Modest claims about substantive things build it. What is offered here is modest: a design philosophy that already works in fragments across the industry, articulated as a coherent whole, with one measured result and one analytic result to demonstrate that the principle produces the predicted efficiency gains under specific tested conditions.

---

## 8 Limitations

**The cascade result depends on classifier calibration.** The 100% agreement rate in the reference implementation was achieved on a workload well-matched to the lexicon rule. On harder or more variable workloads, the classifier's error rate will be higher and the efficiency gain will diminish accordingly. Any deployment of the cascade pattern must test its classifier on the actual distribution of its production workload.

**The analytic hardware model is not empirical validation.** The eco chip has not been fabricated. The 2.28-2.87 TOPS/W range represents defensible arithmetic on published component parameters and cannot substitute for FPGA prototyping under continuous inference load. The single load-bearing assumption (sustained fraction 0.70-0.88) is credibly grounded in published performance of comparable mobile SoC designs but requires empirical confirmation for this specific architecture.

**Adversarial environments require additional discipline.** The framework was developed for stationary or slowly-varying conditions. Applications where an active adversary shapes the workload (cybersecurity, fraud detection, content moderation) require adversarial testing as a first-class design requirement, forced escalation on cases the classifier might otherwise route cheaply, and cryptographic bindings to prevent the governance layer itself being compromised.

**Distribution drift is invisible without monitoring.** Cascade systems can fail silently when the workload distribution changes and the classifier's accuracy degrades without the system noticing. Periodic re-validation against the expensive path is necessary to detect drift, and this costs efficiency in exchange for safety. Systems deploying the pattern must budget for this monitoring cost.

**Cultural and incentive barriers matter.** The technology to implement equilibrium-based control exists and has been demonstrated in fragments across the industry. It has not been adopted as a default because industry incentives favour opportunistic maximisation: chip vendors sell more chips when workloads are inefficient, cloud providers benefit from over-provisioning, benchmarks measure peak performance. The framework does not solve these incentive problems. It only provides a coherent alternative for those who choose to implement it.

---

## 9 Conclusion

Modern computing systems consume far more energy than the work they perform requires. The gap between actual and necessary energy consumption is not primarily a materials science problem or a fundamental physics limit. It is a design philosophy problem. Systems designed to opportunistically maximise perform worse, thermally and energetically, than systems designed to target sustained equilibrium. The maximisation default is a historical artefact of assumptions that no longer hold.

An equilibrium-based control philosophy applied consistently across the compute stack — hardware, operating system, workload scheduling, fleet management — would produce meaningful efficiency gains at every scale. This paper presents one measured demonstration (36% of baseline energy on a real inference workload, with 100% agreement preserved) and one analytic model (a hardware architecture consistent with 2.74 TOPS/W efficiency, an improvement over 2.0 TOPS/W conventional silicon). Neither result is a proof that the principle solves every problem it might apply to. Together they demonstrate that the principle produces the predicted gains when specifically tested, and that the principle is well-enough defined to be tested by others in other domains.

The principle itself is not new. What is new is the observation that modern computing has systematically ignored it, and that adopting it deliberately across the stack would recover a substantial fraction of currently-wasted energy. The paper does not claim more than this. Engineers who recognise their own problems in the framing are invited to test whether the principle produces the predicted gains in their specific domain. Where it does, the gains compound across the industry. Where it does not, the specific failure mode is itself useful information about the boundaries of the framework's applicability.

Systems that maximise become brittle. Systems that seek equilibrium last longer and consume less. This is not a new observation. It has been quietly true for as long as anyone has thought about how goal-directed systems operate under resource constraints. What this paper contributes is the specific claim that modern computing forgot it, and that remembering it is worth measurable energy at every scale from a single laptop to a national grid.

---

## Code and reproducibility

Reference implementation of the cascade benchmark, harness scripts, dataset generator, accuracy check, and raw results:
[github.com/aithoughtcouncil-hattie/equilibrium-governance/tree/main/bench](https://github.com/aithoughtcouncil-hattie/equilibrium-governance/tree/main/bench)

Analytic eco chip model:
[github.com/aithoughtcouncil-hattie/equilibrium-governance/tree/main/analytic](https://github.com/aithoughtcouncil-hattie/equilibrium-governance/tree/main/analytic)

Governance protocol specification: *The Missing Layer*, Thought Council preprint (2026), in [/papers/Maclean_2026_Governance1_The_Missing_Layer.pdf](./Maclean_2026_Governance1_The_Missing_Layer.pdf). Governance overlay for room-temperature NV registers: *Governed Measurement*, Thought Council preprint (2026), in [/papers/Maclean_2026_Governance2_Governed_Measurement_NV.pdf](./Maclean_2026_Governance2_Governed_Measurement_NV.pdf). ICE Fusion Architecture: Thought Council preprint (2026), in [/papers/Maclean_2026_Governance3_Governed_Fusion_Architecture.pdf](./Maclean_2026_Governance3_Governed_Fusion_Architecture.pdf). Framework document: *[redacted]*, Thought Council (2 September 2026), in [/theory/[redacted].md](../theory/[redacted].md).

---

## References

[1] Cannon WB. *The Wisdom of the Body*. Norton (1932).
[2] Wiener N. *Cybernetics: or Control and Communication in the Animal and the Machine*. MIT Press (1948).
[3] Damasio AR. *Descartes' Error: Emotion, Reason, and the Human Brain*. Putnam (1994).
[4] MLPerf Inference v5.1 Results. MLCommons (2025).
[5] Google DeepMind. Machine learning for data center cooling. DeepMind blog (2016).
[6] Aristotle. *Nicomachean Ethics*. Book II (c. 340 BCE).
[7] Maclean D. *The Missing Layer: Verifiable Decision Governance for High-Stakes Systems*. Thought Council preprint (2026). Section 3.5 states the protocol properties (P1-P6) that the cascade benchmark demonstrates in a specific implementation.
[8] Maclean D. ASI Series, Papers 0-5. thoughtcouncil.org (2026). Paper 3 (*Equilibrium Foundation*) states the underlying framework applied here to computing systems.
[9] Maclean D. *[redacted]*. Thought Council (2 September 2026). Plain-language framing of the equilibrium principle across substrates.

— END OF PAPER · Equilibrium-Based Control · Maclean · 2026 —
