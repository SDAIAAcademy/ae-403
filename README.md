<!-- academy:title -->
# Reliability Engineering for AI Services

هندسة الاعتمادية لخدمات الذكاء الاصطناعي

AI Engineering Track · SDAIA Academy · AE-403 · Level 400

REPLACE: one line under the title: what participants can do after the course

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
| 1.1 | Day 1 · Session 1 | Read a week of synthetic telemetry and list the incidents an uptime check would miss | [`D1_1_read_week_synthetic.ipynb`](labs/D1_1_read_week_synthetic.ipynb) |
| 1.2 | Day 1 · Session 2 | Define indicators for first-token time, per-token time, availability and a sampled quality grade | [`D1_2_define_indicators_first.ipynb`](labs/D1_2_define_indicators_first.ipynb) |
| 1.3 | Day 1 · Session 3 | Set objectives, compute budget burn from a supplied month and write the release policy | [`D1_3_set_objectives_compute.ipynb`](labs/D1_3_set_objectives_compute.ipynb) |
| 1.4 | Day 1 · Session 4 | Define completion, cost and escalation indicators for the redelivery booking flow | [`D1_4_define_completion_cost.ipynb`](labs/D1_4_define_completion_cost.ipynb) |
| 2.1 | Day 2 · Session 1 | Load-test the model at rising concurrency, find where goodput falls and set the operating point | [`D2_1_load_test_model.ipynb`](labs/D2_1_load_test_model.ipynb) |
| 2.2 | Day 2 · Session 2 | Add a concurrency cap and priority shedding, then replay the overload trace | [`D2_2_add_concurrency_cap.ipynb`](labs/D2_2_add_concurrency_cap.ipynb) |
| 2.3 | Day 2 · Session 3 | Configure a smaller fallback model and a cached-answer mode and measure quality in each | [`D2_3_configure_smaller_fallback.ipynb`](labs/D2_3_configure_smaller_fallback.ipynb) |
| 2.4 | Day 2 · Session 4 | Inject a retrieval outage, a provider timeout and a retry storm and check the minimum service holds | [`D2_4_inject_retrieval_outage.ipynb`](labs/D2_4_inject_retrieval_outage.ipynb) |
| 3.1 | Day 3 · Session 1 | Build a burn-rate alert on the quality indicator and locate the regression in a replayed day | [`D3_1_build_burn_rate.ipynb`](labs/D3_1_build_burn_rate.ipynb) |
| 3.2 | Day 3 · Session 2 | Run a game day on a model-update regression as incident lead, operator and scribe | [`D3_2_run_game_day.ipynb`](labs/D3_2_run_game_day.ipynb) |
| 3.3 | Day 3 · Session 3 | Release a new model version as a canary with automated rollback on a latency and quality gate | [`D3_3_release_new_model.ipynb`](labs/D3_3_release_new_model.ipynb) |
| 3.4 | Day 3 · Session 4 | Write a blameless review of a supplied incident and turn its cases into a regression test | [`D3_4_write_blameless_review.ipynb`](labs/D3_4_write_blameless_review.ipynb) |
| 4.1 | Day 4 · Session 1 | Trace the provenance of three model artefacts and find the tampered file by its hash | [`D4_1_trace_provenance_three.ipynb`](labs/D4_1_trace_provenance_three.ipynb) |
| 4.2 | Day 4 · Session 2 | Sign a manifest of model files and show that a changed file fails verification | [`D4_2_sign_manifest_model.ipynb`](labs/D4_2_sign_manifest_model.ipynb) |
| 4.3 | Day 4 · Session 3 | Write a bill of materials and a policy that rejects unsigned or unlicensed models | [`D4_3_write_bill_materials.ipynb`](labs/D4_3_write_bill_materials.ipynb) |
| 4.4 | Day 4 · Session 4 | Apply the readiness checklist to a supplied service and rank the findings by risk | [`D4_4_apply_readiness_checklist.ipynb`](labs/D4_4_apply_readiness_checklist.ipynb) |
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
