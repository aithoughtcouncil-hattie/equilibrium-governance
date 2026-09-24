# The ICE Fusion Architecture with Governed Operation


Daniel Maclean · Thought Council, Plymouth, UK · ORCID 0009-0004-7725-687X · Revised draft, September 2026 (supersedes March 2026 preprint)

> Cost and timeline figures are planning projections, not quotes or measurements.

## Abstract

This paper proposes an engineering architecture for fusion energy that integrates structure, cooling, sensing and control into one continuous lattice, and a governance layer that makes the resulting experimental programme verifiable. It proposes no new plasma physics. Its central claim is that fusion engineering has been limited by domain imbalance: plasma performance advancing faster than the structural, thermal and control systems needed to exploit it reliably. Nine concepts are presented in two tiers. Six require no new physics and need engineering validation. Three need computational validation with existing open fusion codes before any experiment. Three further concepts from the earlier preprint are set aside in an appendix, with reasons, because they do not survive a check against established plasma physics. A new chapter applies a general decision-governance overlay [13] to fusion operation: operating envelopes are committed before each shot, data acceptance is gated against them, and every decision is recorded in an offline-verifiable log. A staged roadmap runs from a GPU workstation to a mid-scale plasma experiment. Each stage has a stated test and a stated way to fail.

**Keywords:** fusion energy; system architecture; SiC composites; embedded cooling; distributed control; disruption prediction; digital twin; experimental governance

**Terminology.** In this paper "ICE" in the architecture sense means Integrated Condition Equilibrium: the principle that a working reactor needs equilibrium across several engineering domains at once. The governance layer in Section 5 comes from separate work under the name Initial Condition Ethics [13]; to avoid confusion it is called "the governance overlay" throughout.

## 1 The integration problem

Fusion engineering is usually advanced domain by domain. Plasma physicists improve confinement, materials scientists develop first-wall materials, magnet engineers improve coils, and control engineers develop plasma control. Integration comes later, when separately optimised systems must work together in one device under conditions none of them individually specified.

The result is domain imbalance. Plasma performance can exceed what thermal management sustains. Magnets can be optimised beyond what the structure supports under disruption loads. A centralised control system can be too slow for spatially distributed thermal events. Individual components are excellent; the system fails at the interfaces.

This diagnosis is standard in systems engineering [10]. The contribution here is its application to fusion and an architectural response: design the reactor as one system from the start, with domain interfaces as primary design constraints.

## 2 The framework: fusion as a multi-domain stability problem

The engineering threshold for a practical reactor is not one parameter. It is a surface in a space defined by plasma performance, structural integrity, thermal management, sensing resolution and control response. Advancing one dimension while others stay fixed moves along the surface without crossing it.

Four domains must reach equilibrium together. Structure carries mechanical loads. Cooling removes heat that would otherwise damage the structure and degrade plasma performance. Sensing supplies the real-time information control needs. Control keeps the plasma within its operating window while protecting the structure and cooling from excursions.

These domains are coupled. When one physical structure also carries coolant and sensors, a disruption load, the resulting thermal excursion and the coolant response involve the same hardware. The architecture's central design idea is one integrated system performing four functions, rather than four systems that must be coordinated.

**How the framework could be wrong.** A reactor built on these principles should show measurable gains on the metrics the framework names as binding: first-wall lifetime, thermal management under disruption loads, maintenance downtime and availability. If an instrumented device shows no improvement against a conventional design of similar plasma parameters, the framework is wrong.

## 3 The architecture: nine concepts in two tiers

### 3.1 Tiering

Conflating established and speculative concepts is a common failure in fusion proposals. Each concept below carries the status it has earned. Tier 1 means no new physics is required; it does not mean the concept is validated.

| Tier | Concept | What it is | Validation needed |
|---|---|---|---|
| 1 | Integrated Condition Equilibrium framework | Reactor design as a multi-domain stability problem | Engineering comparison against a conventional design |
| 1 | Continuous geodesic lattice | One SiC-composite structure serving as frame, thermal path, coolant carrier and sensor network | Fabrication, irradiation and thermal-mechanical testing |
| 1 | Embedded cooling network | Coolant channels in every strut, node manifolds, multi-path redundancy | Channel fabrication in SiC; flow and thermal testing |
| 1 | Suspended reactor assembly | Assembly suspended from an exoframe to attenuate disruption impulse | Suspension design and impulse testing |
| 1 | Distributed node intelligence | Sensors and local response loops at each lattice node, with global coordination | Sensor survivability; control latency testing |
| 1 | Geodesic exoframe | Steel support frame carrying services and maintenance access | Structural and remote-handling design |
| 2 | Lattice-plasma boundary interaction | Whether the lattice geometry changes edge-plasma behaviour | Simulation with edge codes |
| 2 | AI thermal balancing | Reinforcement-learning control of distributed cooling | Training in a coupled thermal-structural simulation |
| 2 | Disruption prediction from node sensors | Machine-learning prediction from dense structural sensing | Training on simulated disruption datasets |

### 3.2 Tier 1: no new physics required

**The continuous geodesic lattice.** The fullerene-derived geodesic geometry distributes loads across many members, reducing stress concentrations under thermal expansion, irradiation swelling and disruption loads. A continuous radial structure replaces the separate shells of conventional first-wall and blanket designs, removing interfaces that are common failure sites.

SiC/SiC composites are studied as an advanced option for fusion structures because of their high-temperature capability and low activation [8]. The European DEMO baseline uses reduced-activation ferritic-martensitic steel (EUROFER) as its structural material, with SiC composites as a longer-term option [7]. Using SiC as the primary load-bearing structure is therefore more demanding than current baseline designs and requires qualification work, not just application of existing data.

**Open engineering requirement: tritium breeding.** A single lattice that replaces the blanket shells must still breed tritium at a ratio above one, which requires lithium-bearing breeder material and neutron multiplication within the structure. The earlier preprint did not address this. Any lattice design must show where the breeder sits and what breeding ratio it achieves. This is stated as an open requirement: a breeding-blanket integration concept and a neutronics estimate, for example with the open-source OpenMC code, are needed before the lattice can be assessed as a reactor structure.

**Embedded cooling network.** Coolant channels formed into every strut, fed by manifolds at the vertex nodes, follow standard practice in aerospace thermal management, electronics cooling and heat exchangers. Fabricating them in SiC composites is the engineering task. The multi-path flow topology lets coolant reach any node by several routes, so a blocked strut is compensated by rerouting, detected and managed by the node sensing and control system.

**Suspended reactor assembly.** Disruptions release stored magnetic energy as mechanical impulse into the surrounding structure. Suspending the assembly from the exoframe, rather than clamping it, limits load transfer to the stiffness of the suspension elements. The principle is the same as precision instrument mounting, seismic isolation and aircraft engine mounts. Interaction with magnet alignment tolerances must be checked in the suspension design.

**Distributed node intelligence.** Each vertex node carries temperature, strain, neutron-flux and flow sensors. Local loops adjust coolant flow and raise alerts without waiting for a central controller; a global layer uses the full sensor field to anticipate problems. Reinforcement-learning plasma control on the TCV tokamak [1] is the nearest precedent, extended here from plasma shape to thermal and structural management.

Sensor survival near a fusion plasma is a known hard problem: 14 MeV neutron flux, gamma heating and high temperatures degrade most electronics and many sensor types. Node packages nearest the plasma will need radiation-hard or passive sensing (for example optical fibre sensors), and the node density achievable is a design outcome, not an assumption.

**Geodesic exoframe.** An eight-module steel frame at the cube corners supports the assembly, carries coolant, power and data routing, and provides maintenance access. Separating it from the reactor assembly through the suspension mounts allows maintenance on one without disturbing the other. Reactor economics depend on availability, so an architecture designed for rapid module replacement has a structural advantage over designs where maintenance was added late.

### 3.3 Tier 2: computational validation required

**Lattice-plasma boundary interaction.** SiC composites are non-magnetic and poorly conducting, so a passive lattice will not reshape the confining magnetic field in any significant way. The earlier preprint framed this concept as field-geometry coupling; that framing is withdrawn. The real question is plasma-wall interaction: whether a non-axisymmetric lattice first wall changes heat-flux distribution, neutral recycling and impurity sources at the edge. These effects are the domain of scrape-off-layer codes such as SOLPS-ITER, with BOUT++ [2] for edge turbulence. Two further items belong here: eddy currents induced in any conducting lattice elements during disruptions, and the basis for the lattice standoff distance, which the earlier preprint stated (1.13 R) without derivation. That figure is withdrawn here pending a derivation; the standoff is treated as a design variable to be set by the plasma-wall simulations.

**AI thermal balancing.** A reinforcement-learning policy for the distributed cooling network needs a simulation environment that models coupled thermal-structural behaviour under fusion-relevant heat loads. Building that environment is the main Phase 2 task. The trained policy can then be tested on the physical thermal rig (Section 6) before any plasma experiment.

**Disruption prediction from node sensors.** Disruption precursors develop over tens to hundreds of milliseconds. The hypothesis is that dense structural sensing detects them earlier or more reliably than conventional sparse diagnostics. Testing it means training a model on simulated disruptions from JOREK [3], with the lattice sensor field mapped onto simulation output, and evaluating on held-out cases. The comparison baseline must be existing disruption predictors that use conventional plasma diagnostics.

## 4 Relationship to existing fusion simulation

The plasma physics this architecture depends on is already modelled by mature, validated codes: BOUT++ for edge physics, GENE for gyrokinetic turbulence, JOREK for disruption MHD, TRANSP for transport and heating, and SOLPS-ITER for the scrape-off layer and divertor. These codes supply boundary conditions for the architectural simulations: heat flux at the first wall, disruption impulse and neutron flux distribution. The architectural simulations then show how the lattice responds. The interface between the two is where this programme's new work lies.

## 5 Governed operation: making the programme verifiable

### 5.1 Why a fusion programme needs a governance layer

A fusion device runs as a sequence of shots, each inside an operating envelope of plasma current, field, heating power, density limits and wall loading. Machine-protection systems already stop shots that leave safe bounds; that is the host's safety function, and the overlay does not replace it. What those systems do not provide is an outside-verifiable record of which envelope each shot was planned under, whether it changed during a campaign, and which shots' data were accepted as valid results. As programmes grow across sites, suppliers and control codes, that record is what makes results comparable and reproducible [10].

### 5.2 The three gates applied to a shot

| Gate | What is committed or checked | Failure it catches |
|---|---|---|
| Pre-shot | Operating envelope, control-code version, diagnostic calibration set and acceptance criteria hashed into a governance commitment and a per-shot case commitment | A shot run on an uncalibrated diagnostic or under an envelope that was never approved |
| During shot | Diagnostic streams recorded against the committed envelope; out-of-envelope intervals become findings | An excursion machine protection tolerated but which invalidates the data for the planned analysis |
| Post-shot | Commitments recomputed; data accepted, held or rejected against the unchanged criteria; decision signed and logged | A threshold relaxed after seeing results, so a marginal shot counts as a success |

The same gates apply to simulation campaigns in Phases 1 to 3: commit the code version, inputs and acceptance criteria before each run, so every reported simulation result is reproducible from its record.

### 5.3 What it adds, and what it does not

It adds a campaign-level audit trail, verifiable offline; detection of criteria changed mid-campaign, with legitimate changes going through a recorded amendment; and a basis for comparing results across devices, because each accepted dataset carries the hash of the rules it was accepted under.

It does not improve confinement, heating or materials. It does not replace machine protection or plasma control. It cannot make a poorly chosen envelope safe or a poorly chosen acceptance criterion meaningful. Its value is procedural and grows with programme scale. A reference implementation and attack-scenario results are reported in [13].

### 5.4 First test someone could run

The overlay can be tested on existing data without new hardware. Commit acceptance criteria for a past campaign, replay the recorded shots through the three gates, and compare the accepted set with the campaign's published accepted set. Disagreements show where acceptance decisions were undocumented or changed. Two public resources make this feasible now: UKAEA's FAIR-MAST open data release of MAST shot data (mastapp.site, CC BY-SA 4.0) [14], and the open-source TORAX tokamak transport simulator [15], which can generate synthetic campaigns for a first pass.

**Kill criteria.** The overlay is not worth adopting in a programme if replay across a full campaign shows no disagreement between committed and published acceptance decisions, or if its logging overhead delays shot turnaround beyond tolerance. Either outcome should be reported.

## 6 Roadmap

All costs and durations are planning projections.

| Phase | Work | Platform | Projected cost | Projected duration | Test that could fail it |
|---|---|---|---|---|---|
| 1 Exploration | Thermal topology optimisation; basic structural FEA; edge-interaction scoping | 4-GPU workstation | about £10,000 | 3–6 months | Lattice shows no thermal or structural advantage over a conventional shell of equal mass |
| 2 Validation | Coupled thermal-structural model; coolant CFD; RL cooling policy; disruption predictor training | 8–16 GPU cluster plus cloud | £100,000–150,000 | 12–18 months | RL policy or predictor does not beat conventional baselines on held-out cases |
| 3 High resolution | Full disruption-load simulation; plasma-wall interaction; digital-twin prototype | National HPC access | £50,000–200,000 | 18–36 months | Plasma-wall effects of the lattice are adverse and cannot be designed out |
| 4 Thermal rig | SiC lattice shell (3–5 m), embedded cooling, node sensing, internal heat source; no plasma | University or national facility | £5–15M | 36–60 months | Fabrication, cooling or sensing performance falls short of simulation |
| 5 First plasma | Standard tokamak core inside the validated architecture | Mid-scale device (MAST-U or DIII-D class) | £50–200M | 60–96 months | No improvement on first-wall lifetime, thermal efficiency, disruption damage or downtime against a comparable conventional device |

Phase 4 matters most: engineering problems found at £10 million are far cheaper than problems found at £100 million. The governance overlay (Section 5) runs across all five phases from the first simulation.

### 6.1 Digital twin

The computational programme continues as a digital twin: a real-time simulation updated from the node sensor stream, predicting behaviour ahead of events and recommending control actions. Other programmes, including ITER and SPARC, are also developing digital twins. The architecture's potential advantage is sensor density; the achievable density, and therefore the advantage, depends on the sensor-survivability work in Section 3.2.

## 7 Relationship to the wider fusion programme

The architecture complements ITER rather than competing with it. ITER tests sustained high-gain plasma physics; this architecture addresses the engineering around the plasma. It is most relevant to the DEMO phase, where first-wall lifetime, thermal management, maintenance downtime and availability become binding [7]. It is also plasma-approach agnostic in principle: the lattice, cooling, sensing and control concepts could apply to tokamaks and to alternative configurations, subject to each device's geometry.

The distributed node intelligence follows design principles also argued for AI systems in general: distributed rather than centralised control, transparent sensing, conservative response to uncertainty and human override at every level [5]. The governance overlay in Section 5 is the operational form of the same principles.

## 8 Conclusion

The architecture proposes engineering integration around proven plasma physics. Six concepts need engineering validation and no new physics. Three need computational validation with existing codes. Three earlier concepts are set aside because they conflict with established physics or restate existing confinement approaches. The governance overlay makes every stage of the programme verifiable, from the first simulation to the first plasma. Each stage has a named test and a named way to fail, and the engineering gaps the earlier preprint left open, tritium breeding and sensor survivability, are now stated as requirements.

## Appendix A: Concepts set aside after viability check

| Concept (March 2026 preprint) | Why set aside | What survives |
|---|---|---|
| Spiral plasma orbit (extended-path confinement via lattice field geometry) | A passive SiC lattice is non-magnetic and poorly conducting; it cannot generate the field geometry needed to guide particle orbits. Shaping field lines in three dimensions is what stellarators already do with coils [4]. Longer particle paths do not by themselves raise the fusion rate, which depends on density, temperature and confinement time. | If the lattice were to carry coils, it becomes a question of stellarator-compatible structural support, a Tier 1 engineering question. |
| Dynamic lattice geometry (moving elements to adjust confinement) | Confinement is set by the magnetic field, not by wall shape. Moving structural elements near the plasma adds major mechanical and irradiation risk for no confinement benefit. Real-time shape control is already done with coil currents. | Movable limiters and adjustable first-wall elements already exist for heat-load management. |
| Closed-loop plasma recirculation (alternative to toroidal confinement) | Toroidal confinement is already a closed-loop geometry. Particle loss in toroidal devices is dominated by transport across field lines, which closed paths do not address. | None as a separate concept. |

These concepts may have motivated the architecture, but its value does not rest on them. Removing them strengthens the remaining claims.

## References

[1] Degrave J et al. Magnetic control of tokamak plasmas through deep reinforcement learning. Nature 602, 414–419 (2022).
[2] Dudson BD et al. BOUT++: A framework for parallel plasma fluid simulations. Computer Physics Communications 180, 1467–1480 (2009).
[3] Hoelzl M et al. The JOREK non-linear extended MHD code and applications to large-scale instabilities and their control in magnetically confined fusion plasmas. Nuclear Fusion 61, 065001 (2021).
[4] Klinger T et al. Overview of first Wendelstein 7-X high-performance operation. Nuclear Fusion 59, 112004 (2019).
[5] Maclean D. ASI Series, Papers 0–5. Zenodo (2026). Paper 4: doi:10.5281/zenodo.22845539.
[6] Maclean D. Geometric Confinement: The Integrated Fullerene Plasma Cage. Preprint, thoughtcouncil.org (2026). **[Check: if this paper's claims depend on the Appendix A concepts, it needs the same revision.]**
[7] Federici G et al. European DEMO design strategy and consequences for materials. Nuclear Fusion 57, 092002 (2017). *(Year corrected from 2019.)*
[8] Raffray AR et al. SiC/SiC composites for fusion applications. **[Verify: authors, journal and year could not be confirmed; replace with a confirmed SiC/SiC fusion review if needed.]**
[9] Shimada M et al. Progress in the ITER Physics Basis. Nuclear Fusion 47, S1 (2007).
[10] Greenwald M. Verification and validation for magnetic fusion. Physics of Plasmas 17, 058101 (2010).
[11] Maclean D. Build the Vessel Before the Flood: A Global Water Security Framework. Preprint, thoughtcouncil.org (2026).
[12] Maclean D. The Architecture of Peace. Thought Council Discussion Paper (2026).
[14] UKAEA. FAIR-MAST: open MAST experimental data. https://mastapp.site/ (accessed September 2026).
[15] Google DeepMind. TORAX: a differentiable tokamak transport simulator. https://github.com/google-deepmind/torax (accessed September 2026).
[13] Maclean D. The Missing Layer: Verifiable Decision Governance for High-Stakes Systems. Thought Council preprint (2026). Code: https://github.com/aithoughtcouncil-hattie/missing-layer. **[PENDING T6: DOI.]**
