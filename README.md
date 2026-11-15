<!-- academy:title -->
# Reliability Engineering for AI Services

هندسة الاعتمادية لخدمات الذكاء الاصطناعي

AI Engineering Track · SDAIA Academy · AE-403 · Level 400

Set, measure and defend the reliability standards of an AI service: objectives, capacity, degraded modes, incidents, safe releases and verified models

Participants set and defend reliability standards for AI services that other teams build. For a fictional postal and parcels operator running a bilingual tracking assistant on a self-hosted open-weight model with retrieval, they write service level objectives for availability, latency and answer quality, set admission limits with headroom from measured goodput, design and chaos-test degradation paths, lead incident drills and blameless reviews, release through canaries with automated rollback, and admit models only after verifying signatures and bills of materials.

**Format:** Intensive: 4 teaching days of four sessions and a capstone day, with guided pre-work and a tracked follow-up task

**Course page:** https://sdaiaacademy.github.io/ae-403/
<!-- /academy:title -->

## Outcomes

| | Outcomes | Level | Evidence |
|---|---|---|---|
| LO1 | Design service level objectives for availability, latency and answer quality, with error budgets and a release policy, given a month of synthetic telemetry and a sampled online quality signal | Performance | an objectives document defended against a reviewer's challenges |
| LO2 | Decide an admission limit and shedding priorities that keep headroom for the busiest hour, given the self-hosted model, a recorded traffic trace and the service objectives | Performance | a justified operating point and margin, and an overload replay in which priority traffic still meets its objective |
| LO3 | Design degradation for overload and dependency failure using load shedding, a smaller fallback model and a cached-answer mode, given overload, retrieval outage and provider timeout scenarios | Performance | chaos test results showing each path keeps the minimum service, with quality measured in each mode |
| LO4 | Lead an incident drill from detection to recovery and write a blameless review, given a silent quality regression after a model update | Performance | a timeline, a decision log, owned corrective actions and a new regression test |
| LO5 | Build a release gate that verifies model signatures, a bill of materials and licences before deployment, given signed, tampered and unlicensed model artefacts | Performance | a pipeline run that admits the valid artefact and rejects the others, with logs |
| LO6 | Review another team's AI service for production readiness and set launch conditions, given a peer's service, its telemetry and a readiness checklist | Performance | ranked findings and a launch decision defended before a panel |

<!-- academy:units -->
## Units

| Unit | Title | Sessions | Slides |
|---|---|---|---|
| Day 1 | Objectives that match what users need | AI services fail differently; Indicators for latency and quality; Objectives and error budgets; Objectives for multi-step tasks | [`slides/day1.html`](slides/day1.html) |
| Day 2 | Capacity and failure | Capacity with headroom; Admission control and shedding; Degraded modes; Chaos experiments | [`slides/day2.html`](slides/day2.html) |
| Day 3 | Incidents and safe releases | Finding silent regressions; Running an incident; Canary and rollback; Learning from incidents | [`slides/day3.html`](slides/day3.html) |
| Day 4 | Integrity and readiness | The model supply chain; Signing and verification; Bills of materials and admission; Production readiness reviews | [`slides/day4.html`](slides/day4.html) |
| Capstone | Capstone project presentations |  | [`slides/capstone.html`](slides/capstone.html) |
<!-- /academy:units -->

## Case study

**REPLACE: the name of the fictional organisation every lab works on.** REPLACE: two sentences on the case study and its synthetic data

<!-- academy:labs -->
## Labs

Every lab is a notebook in `labs/`. Open it in Google Colab from the course page, or run it locally with `uv`. Exercises raise `NotImplementedError` until they are done; the reference versions are in `labs/solutions/`.

| | Session | Lab | File |
|---|---|---|---|
| 1.1 | Day 1 · Session 1 | What the uptime check missed | [`D1_1_uptime_blind_spots.ipynb`](labs/D1_1_uptime_blind_spots.ipynb) |
| 1.2 | Day 1 · Session 2 | Four indicators from one day | [`D1_2_indicators.ipynb`](labs/D1_2_indicators.ipynb) |
| 1.3 | Day 1 · Session 3 | Objectives, budget and release policy | [`D1_3_error_budgets.ipynb`](labs/D1_3_error_budgets.ipynb) |
| 1.4 | Day 1 · Session 4 | Indicators for the redelivery flow | [`D1_4_task_objectives.ipynb`](labs/D1_4_task_objectives.ipynb) |
| 2.1 | Day 2 · Session 1 | Goodput curve and operating point | [`D2_1_goodput_operating_point.ipynb`](labs/D2_1_goodput_operating_point.ipynb) |
| 2.2 | Day 2 · Session 2 | A cap and priority shedding | [`D2_2_admission_shedding.ipynb`](labs/D2_2_admission_shedding.ipynb) |
| 2.3 | Day 2 · Session 3 | Fallback model and cached answers | [`D2_3_degraded_modes.ipynb`](labs/D2_3_degraded_modes.ipynb) |
| 2.4 | Day 2 · Session 4 | Outage, timeout and retry storm | [`D2_4_chaos.ipynb`](labs/D2_4_chaos.ipynb) |
| 3.1 | Day 3 · Session 1 | A burn-rate alert on quality | [`D3_1_quality_burn_rate.ipynb`](labs/D3_1_quality_burn_rate.ipynb) |
| 3.2 | Day 3 · Session 2 | Game day: a model-update regression | [`D3_2_game_day.ipynb`](labs/D3_2_game_day.ipynb) |
| 3.3 | Day 3 · Session 3 | Canary with automated rollback | [`D3_3_canary_rollback.ipynb`](labs/D3_3_canary_rollback.ipynb) |
| 3.4 | Day 3 · Session 4 | Blameless review and regression test | [`D3_4_blameless_review.ipynb`](labs/D3_4_blameless_review.ipynb) |
| 4.1 | Day 4 · Session 1 | Provenance and the tampered file | [`D4_1_provenance.ipynb`](labs/D4_1_provenance.ipynb) |
| 4.2 | Day 4 · Session 2 | Sign and verify a model folder | [`D4_2_signing.ipynb`](labs/D4_2_signing.ipynb) |
| 4.3 | Day 4 · Session 3 | Bill of materials and admission gate | [`D4_3_bom_admission.ipynb`](labs/D4_3_bom_admission.ipynb) |
| 4.4 | Day 4 · Session 4 | Readiness review of Taqdir | [`D4_4_readiness_review.ipynb`](labs/D4_4_readiness_review.ipynb) |
<!-- /academy:labs -->

## Capstone

A production readiness review of a peer's or a supplied AI service, covering objectives, capacity, degradation, incidents and release integrity with measured evidence in a public repository, defended before a panel of experienced engineers. The follow-up task applies one reliability standard to a service in the participant's own team or an open-source deployment

**Submission:** REPLACE: what participants submit and how: a public repository link, or a shared folder for a course without code

## Prerequisites

- AE-305 Operating Machine Learning and Language Model Systems
- AE-307 Container Orchestration and Cloud Infrastructure for AI Workloads
- Has written alerting rules on service metrics
- Runs containers on a single-node cluster
- Has released a service through a canary or blue-green rollout
- Reads a goodput-versus-concurrency curve (the measurement method is taught in AE-401)

<!-- academy:tools -->
## Tools

Each line is a capability; the examples are interchangeable.

- **Inference engine:** vLLM, SGLang, llama.cpp server
- **Load generation:** inference-perf, k6, Locust
- **Metrics, traces and alerting:** Prometheus with Grafana, an OpenTelemetry collector
- **Fault injection:** Chaos Mesh, Toxiproxy
- **Progressive delivery:** Argo Rollouts, Flagger
- **Signing, bills of materials and admission:** OpenSSF Model Signing, CycloneDX ML-BOM, Kyverno
- **Single-node cluster:** kind, k3s
<!-- /academy:tools -->

<!-- academy:sources -->
## Sources

- REPLACE: every source the course cites, with its address, in course.json under "sources"; this list is written from there
<!-- /academy:sources -->

### National references

- Personal Data Protection Law and its implementing regulations, including the personal data breach procedure: REPLACE: the address of the official text
- NDMO Data Classification Policy: REPLACE: the address of the official text
- National Cybersecurity Authority (NCA) Cloud Cybersecurity Controls: REPLACE: the address of the official text
- National AI Risk Management Framework: REPLACE: the address of the official text
