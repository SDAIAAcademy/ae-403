# Answer key: expected results of the labs

The figures come from the solution notebooks in their full run (not `RELIA_QUICK=1`), on the data
written by `prepare_data.py` with seed 403. The full reference results are in `data/reference/`.
Answers written by participants differ in wording; the numbers and decisions should match.

## Day 1 · Objectives that match what users need

| Lab | Expected result |
|---|---|
| 1.1 What the uptime check missed | Five incidents in the week; the uptime probe saw one of them and missed four (empty answers, wrong answers, slow first tokens and an Arabic-only failure all returned HTTP 200). |
| 1.2 Four indicators from one day | Availability counted honestly (good over valid events, with exclusions stated) is 98.95%; the naive count is lower (96.58%) because it counts invalid requests, and adding the probe barely changes it (99.06%). Latency is time to first token and time per output token at the 95th percentile; quality is the graded pass rate per language with its sample size. |
| 1.3 Objectives, budget and release policy | The Arabic quality budget is the most spent (about 81% burned, 19% left). Of the release requests, RR-1 (new model for all languages) and RR-5 are frozen; RR-4, a security patch, is exempt; the others go. |
| 1.4 Indicators for the redelivery flow | Per call 98.9% success, per task 79.5%: an objective per call overstates what users get. The task objective and its cost per completed task go into the objectives document. |

## Day 2 · Capacity and failure

| Lab | Expected result |
|---|---|
| 2.1 Goodput curve and operating point | Operating point at 16 concurrent requests per replica, 2.13 requests per second of goodput (peak 2.16), 95th-percentile first token 211 ms. Busiest hour 7.64 requests per second (day 27, 20:00); 5 replicas with a 39% margin. |
| 2.2 A cap and priority shedding | With a cap alone, P1 tracking misses its objective in the spike. With priority shedding, P1 is never shed and meets its objective (96.3%); P2 sheds 29%, P3 67% and resumes after the spike. |
| 2.3 Fallback model and cached answers | The smaller fallback model keeps answering but its Arabic quality falls to about 73%. The cache is cleaned first: 9 tracking answers with personal data and 7 stale answers are removed. Routing Arabic help questions to the cleaned cache gives 91.1% with the engine down; every degraded answer is disclosed. |
| 2.4 Outage, timeout and retry storm | The experiment states a hypothesis, a minimum service, a blast radius and abort conditions. Retrieval outage and provider timeout keep the minimum service with the degraded modes. Without the cache, the retrieval outage gives 2,377 silent failures; with it, none. Immediate retries never recover (4,638 failed requests); backoff alone recovers at 153 s; a 10% retry budget recovers at 90 s with 197 failed requests. |

## Day 3 · Incidents and safe releases

| Lab | Expected result |
|---|---|
| 3.1 A burn-rate alert on quality | On the replay day the model update at slot 130 breaks Arabic answers. The quality tier (1 h and 5 min windows at burn rate 6) fires first, about 35 minutes after the regression starts; the slow-page tier fires hours later; the fast-page tier and any alert on all traffic combined never fire. |
| 3.2 Game day: a model-update regression | Roles assigned at 2 minutes, incident declared at 1, mitigation (rollback) at 5 minutes. The decision log has 10 entries, each with a reason. Rolling back first exposes 32 answers carrying another customer's data, against 56 when the team diagnoses first (35 minutes); the data protection officer is paged, the breach assessed, and SDAIA notified well inside 72 hours of awareness. |
| 3.3 Canary with automated rollback | The old gate promotes both v2.6 and the int4 candidate, deciding on 27 Arabic samples. The designed gate (minimum sample per language, comparison with stable) promotes v2.6 and rolls back v2.6-int4 at the 25% step. |
| 3.4 Blameless review and regression test | The twelve failing cases become a regression test: v2.4 passes 0 of 12, v2.4.1 passes 12 of 12. Corrective actions each have an owner and a date; none names a person as the cause. |

## Day 4 · Integrity and readiness

| Lab | Expected result |
|---|---|
| 4.1 Provenance and the tampered file | Only `athar-small-v1-mirror` differs from the publisher's list, in one file: `model-00002-of-00002.safetensors`. The finding says the bytes differ, not who changed them; decision: do not admit. `athar-tiny-q4` matches but is licensed for research use only. |
| 4.2 Sign and verify a model folder | The signature verifies; after one character of `tokenizer.json` changes, verification fails naming that file; with the wrong public key, verification fails. The private key stays in `artifacts/`, which git ignores. |
| 4.3 Bill of materials and admission gate | The ML-BOM validates against CycloneDX 1.7. The gate admits `athar-small-v1`, rejects the mirror on its signature (and its bill of materials hashes), and rejects `athar-tiny-q4` on its licence alone. |
| 4.4 Readiness review of Taqdir | O1 (latency) is corrected from "met" to "partial": 2 s against Rasael's 1.5 s standard. The top three findings are C1 (risk 16), S1 (15) and O2 (10). Decision: do not launch; S1, the unsigned fallback model, blocks until fixed; C1 and O2 are conditions within 14 days, each with its proof. |
