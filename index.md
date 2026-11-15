---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.1.0"
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/index.html"
---

# Reliability Engineering for AI Services

هندسة الاعتمادية لخدمات الذكاء الاصطناعي

AI Engineering Track · 4 teaching days + capstone day · 26 hours · Level 400

Set, measure and defend the reliability standards of an AI service: objectives, capacity, degraded modes, incidents, safe releases and verified models

Participants set and defend reliability standards for AI services that other teams build. For a fictional postal and parcels operator running a bilingual tracking assistant on a self-hosted open-weight model with retrieval, they write service level objectives for availability, latency and answer quality, set admission limits with headroom from measured goodput, design and chaos-test degradation paths, lead incident drills and blameless reviews, release through canaries with automated rollback, and admit models only after verifying signatures and bills of materials.

**Who it is for:** Specialists. Engineers who have completed the level 300 core or can show equivalent work: a production AI system they built, operated and can defend.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

## The case study

**Rasael Post and Parcels.** Rasael Post and Parcels is a fictional national postal and parcels operator whose bilingual assistant, Athar, answers tracking, redelivery and help questions on a self-hosted open-weight model with retrieval over 3,000 Arabic and English help articles. Participants set its objectives, decide its admission limit, design and chaos-test its degraded modes, run an incident drill on a silent quality regression, release through a canary, and admit models only after verifying signatures and bills of materials; all telemetry, traffic, answers, incidents and model artefacts are synthetic and generated with a fixed seed.

## The course

### Day 1: Objectives that match what users need

Slides: https://sdaiaacademy.github.io/ae-403/slides/day1.md

- **Session 1: AI services fail differently**
  - Name four ways an AI service fails while an uptime check stays green
  - Read per-minute telemetry by language and by mode
  - Separate what users felt from what the probe measured
  - [Lab 1.1: What the uptime check missed (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D1_1_uptime_blind_spots.ipynb)
- **Session 2: Indicators for latency and quality**
  - Define an indicator as good events over valid events
  - Exclude probes and client cancellations with a written reason
  - Estimate a sampled quality rate with its interval, by language
  - [Lab 1.2: Four indicators from one day (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D1_2_indicators.ipynb)
- **Session 3: Objectives and error budgets**
  - Set an objective from a user task, not from last month
  - Compute budget burn over a month and per week
  - Write a release policy that decides from the remaining budget
  - [Lab 1.3: Objectives, budget and release policy (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D1_3_error_budgets.ipynb)
- **Session 4: Objectives for multi-step tasks**
  - Explain why per-call success hides failed tasks
  - Define completion, cost and escalation indicators for a flow
  - Set objectives a flow can be held to
  - [Lab 1.4: Indicators for the redelivery flow (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D1_4_task_objectives.ipynb)

### Day 2: Capacity and failure

Slides: https://sdaiaacademy.github.io/ae-403/slides/day2.md

- **Session 1: Capacity with headroom**
  - Read tail latency and goodput from a concurrency sweep
  - Choose an operating point and justify it against the objectives
  - Size replicas for the busiest hour with a stated margin
  - [Lab 2.1: Goodput curve and operating point (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D2_1_goodput_operating_point.ipynb)
- **Session 2: Admission control and shedding**
  - Set a concurrency cap from the operating point
  - Rank traffic into priority classes with a reason
  - Show by replay that priority traffic keeps its objective
  - [Lab 2.2: A cap and priority shedding (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D2_2_admission_shedding.ipynb)
- **Session 3: Degraded modes**
  - Design degraded modes with entry and exit conditions
  - Measure answer quality in each mode by language
  - Keep personal answers out of any cache and tell users plainly
  - [Lab 2.3: Fallback model and cached answers (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D2_3_degraded_modes.ipynb)
- **Session 4: Chaos experiments**
  - Write a chaos experiment as a falsifiable hypothesis
  - Inject dependency failures and measure the minimum service
  - Stop a retry storm with a retry budget and backoff
  - [Lab 2.4: Outage, timeout and retry storm (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D2_4_chaos.ipynb)

### Day 3: Incidents and safe releases

Slides: https://sdaiaacademy.github.io/ae-403/slides/day3.md

- **Session 1: Finding silent regressions**
  - Compute burn rate on a quality indicator
  - Build a multi-window, multi-burn-rate alert
  - Locate a regression in time and in a slice
  - [Lab 3.1: A burn-rate alert on quality (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D3_1_quality_burn_rate.ipynb)
- **Session 2: Running an incident**
  - Run an incident in three roles with a decision log
  - Mitigate before diagnosing
  - Decide on breach notification from the facts
  - [Lab 3.2: Game day: a model-update regression (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D3_2_game_day.ipynb)
- **Session 3: Canary and rollback**
  - Design canary steps with analysis at each step
  - Size the minimum sample for a quality gate
  - Roll back automatically on latency or quality
  - [Lab 3.3: Canary with automated rollback (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D3_3_canary_rollback.ipynb)
- **Session 4: Learning from incidents**
  - Write a blameless timeline and contributing factors
  - Write corrective actions with an owner and a test
  - Turn an incident's failing cases into a regression test
  - [Lab 3.4: Blameless review and regression test (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D3_4_blameless_review.ipynb)

### Day 4: Integrity and readiness

Slides: https://sdaiaacademy.github.io/ae-403/slides/day4.md

- **Session 1: The model supply chain**
  - Trace a model artefact to its source and revision
  - Hash every file and compare with the publisher's list
  - Name where tampering hides in a model folder
  - [Lab 4.1: Provenance and the tampered file (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D4_1_provenance.ipynb)
- **Session 2: Signing and verification**
  - Sign a model folder as a manifest of hashed files
  - Verify the signature at admission
  - Explain what a signature proves and what it does not
  - [Lab 4.2: Sign and verify a model folder (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D4_2_signing.ipynb)
- **Session 3: Bills of materials and admission**
  - Write a CycloneDX ML-BOM for a model
  - Write an admission policy with logged reasons
  - Run the gate on valid, tampered and unlicensed artefacts
  - [Lab 4.3: Bill of materials and admission gate (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D4_3_bom_admission.ipynb)
- **Session 4: Production readiness reviews**
  - Apply a readiness checklist to another team's evidence
  - Rank findings by likelihood and impact
  - Set a launch decision with dated conditions
  - [Lab 4.4: Readiness review of Taqdir (25 min)](https://sdaiaacademy.github.io/ae-403/labs/D4_4_readiness_review.ipynb)

### Capstone: Readiness review defences

Slides: https://sdaiaacademy.github.io/ae-403/slides/capstone.md

## Capstone

A production readiness review of a peer's or a supplied AI service, covering objectives, capacity, degradation, incidents and release integrity with measured evidence in a public repository, defended before a panel of experienced engineers. The follow-up task applies one reliability standard to a service in the participant's own team or an open-source deployment

**What you submit:** A public GitHub repository link: the readiness review (objectives, capacity, degradation, incident drill, release integrity) with its measured evidence, logs and commit history

**Rubric:**

- Objectives and alerts: 20%
- Capacity and degradation: 25%
- Incident drill and review: 20%
- Release integrity: 15%
- Readiness decision: 20%

## Outcomes

- **LO1** Design service level objectives for availability, latency and answer quality, with error budgets and a release policy, given a month of synthetic telemetry and a sampled online quality signal (Performance) Evidence: an objectives document defended against a reviewer's challenges
- **LO2** Decide an admission limit and shedding priorities that keep headroom for the busiest hour, given the self-hosted model, a recorded traffic trace and the service objectives (Performance) Evidence: a justified operating point and margin, and an overload replay in which priority traffic still meets its objective
- **LO3** Design degradation for overload and dependency failure using load shedding, a smaller fallback model and a cached-answer mode, given overload, retrieval outage and provider timeout scenarios (Performance) Evidence: chaos test results showing each path keeps the minimum service, with quality measured in each mode
- **LO4** Lead an incident drill from detection to recovery and write a blameless review, given a silent quality regression after a model update (Performance) Evidence: a timeline, a decision log, owned corrective actions and a new regression test
- **LO5** Build a release gate that verifies model signatures, a bill of materials and licences before deployment, given signed, tampered and unlicensed model artefacts (Performance) Evidence: a pipeline run that admits the valid artefact and rejects the others, with logs
- **LO6** Review another team's AI service for production readiness and set launch conditions, given a peer's service, its telemetry and a readiness checklist (Performance) Evidence: ranked findings and a launch decision defended before a panel

## Tools

- **Inference engine:** vLLM, SGLang, llama.cpp server
- **Load generation:** inference-perf, k6, Locust
- **Metrics, traces and alerting:** Prometheus with Grafana, an OpenTelemetry collector
- **Fault injection:** Chaos Mesh, Toxiproxy
- **Progressive delivery:** Argo Rollouts, Flagger
- **Signing, bills of materials and admission:** OpenSSF Model Signing, CycloneDX ML-BOM, Kyverno
- **Single-node cluster:** kind, k3s

## Prerequisites

- AE-305 Operating Machine Learning and Language Model Systems
- AE-307 Container Orchestration and Cloud Infrastructure for AI Workloads
- Has written alerting rules on service metrics
- Runs containers on a single-node cluster
- Has released a service through a canary or blue-green rollout
- Reads a goodput-versus-concurrency curve (the measurement method is taught in AE-401)
- Setup: a laptop CPU with uv, or Google Colab. Nothing downloads a model; the self-hosted engine is a calibrated simulator and the answers are recorded. Run 00_setup_check before Day 1; see labs/README.md.

## Sources

### Objectives, alerts and incidents

- [Google SRE Workbook: Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [Google SRE Workbook: Example Error Budget Policy](https://sre.google/workbook/error-budget-policy/)
- [Google SRE Workbook: Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)
- [Google SRE Workbook: Incident Response](https://sre.google/workbook/incident-response/)
- [Google SRE Book: Postmortem Culture: Learning from Failure](https://sre.google/sre-book/postmortem-culture/)
- [Google SRE Book: The Evolving SRE Engagement Model (production readiness reviews)](https://sre.google/sre-book/evolving-sre-engagement-model/)
- [OpenTelemetry semantic conventions for generative AI: metrics](https://github.com/open-telemetry/semantic-conventions-genai)

### Capacity, overload and degradation

- [Google SRE Book: Handling Overload](https://sre.google/sre-book/handling-overload/)
- [Google SRE Book: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- [vLLM documentation: Metrics](https://docs.vllm.ai/en/latest/design/metrics.html)
- [inference-perf: a benchmarking tool for generative AI inference (Kubernetes SIGs)](https://github.com/kubernetes-sigs/inference-perf)
- [Toxiproxy](https://github.com/Shopify/toxiproxy)
- [Chaos Mesh documentation](https://chaos-mesh.org/docs/)

### Releases and model integrity

- [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/)
- [Argo Rollouts: Analysis and Progressive Delivery](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/)
- [Flagger documentation](https://docs.flagger.app/)
- [OpenSSF Model Signing (sigstore/model-transparency)](https://github.com/sigstore/model-transparency)
- [CycloneDX: Machine Learning Bill of Materials (ML-BOM)](https://cyclonedx.org/capabilities/mlbom/)
- [CycloneDX specification overview](https://cyclonedx.org/specification/overview/)
- [Kyverno: validate rules](https://kyverno.io/docs/policy-types/cluster-policy/validate/)

### National references

- [Personal Data Protection Law (SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataProtectionLaw.pdf)
- [Personal Data Breach Incidents procedural guide (SDAIA)](https://sdaia.gov.sa/en/SDAIA/about/Documents/PersonalDataBreachIncidents.pdf)
- [NDMO Data Classification Policy](https://sdaia.gov.sa/en/SDAIA/about/Documents/DataClassificationPolicy.pdf)
- [National Cybersecurity Authority: Cloud Cybersecurity Controls (CCC)](https://nca.gov.sa/en/regulatory-documents/controls-list/ccc/)
- [National AI Risk Management Framework: executive summary (SDAIA)](https://sdaia.gov.sa/en/MediaCenter/KnowledgeCenter/ResearchLibrary/ExecutiveSummaryEn.pdf)

---

SDAIA Academy · AI Engineering Track · Reliability Engineering for AI Services

Course version 2027.1.0 · engine 1.0.0 · built 2026-11-15 · commit d44e8c9
