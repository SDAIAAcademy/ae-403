---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.2.0"
deck: "day2"
day: 2
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/slides/day2.html"
---

# Reliability Engineering for AI Services

## Day 2: Capacity and failure

Admission limits from measured goodput, degraded modes and chaos experiments

#### [day2#title] Capacity and failure

*SDAIA Academy · Reliability Engineering for AI Services*

Day 2: Admission limits from measured goodput, degraded modes and chaos experiments

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-403

#### [day2#agenda] Capacity and failure

*Today*

- **Session 1 · Capacity with headroom**: Goodput falls past a concurrency the engine can sustain; the operating point leaves headroom for the busiest hour
- **Session 2 · Admission control and shedding**: Admit what the engine can serve, queue little, shed the least important traffic first
- **Session 3 · Degraded modes**: A smaller fallback model and a cached-answer mode keep a minimum service; each one is measured and disclosed
- **Session 4 · Chaos experiments**: A hypothesis, a blast radius and an abort condition; failures that retries make worse

#### [day2#review-day1] Which number goes on the objectives document?

*Review of Day 1*

**Question:** Over 30 days Athar's sampled quality was 97.8% in English and 95.9% in Arabic, 96.7% together. The objective is 95%. What do you report?

- A. 96.7%, within objective
- B. Each language against its own objective, with its remaining budget
- C. 97.8%, the higher of the two
- D. Nothing until every answer is graded

### Session 1: Capacity with headroom

#### [day2#s1] Capacity with headroom

*Session 1*

- Read tail latency and goodput from a concurrency sweep
- Choose an operating point and justify it against the objectives
- Size replicas for the busiest hour with a stated margin

#### [day2#queue-tail] Near capacity, the tail grows much faster than the load

*Queueing*

- Below capacity, a request waits for little more than its own prefill
- Near capacity, every burst queues, and the 95th percentile shows it first
- In a self-hosted engine the key-value cache is the hidden limit: when it fills, requests are preempted and computed again

> **What goes wrong.** Sizing on average throughput: the engine is "only 80% busy" while a third of users wait seconds for the first token.

#### [day2#goodput-definition] Goodput counts only the requests that met the objectives

*Goodput*

1. **Throughput** requests finished a second
2. **Filter** first token within 1,500 ms and 100 ms a token
3. **Goodput** good requests a second

A load generator holds a fixed number of requests in flight (inference-perf, k6 or Locust in concurrency mode) and you raise it step by step.

#### [day2#goodput-curve] Throughput holds past the knee; goodput collapses

*Lab 2.1 · one replica*

| In flight | Throughput | Goodput | First token p95 |
| --- | --- | --- | --- |
| 8 | 1.63 | 1.63 | 173 ms |
| 16 | 2.13 | 2.13 | 211 ms |
| 20 | 2.21 | 2.16 | 1,295 ms |
| 24 | 2.20 | 0.59 | 3,005 ms |
| 32 | 2.12 | 0.00 | 6,848 ms |

#### [day2#operating-point] Operate below the peak: 16 in flight, not 20

*The operating point*

- **The rule.** The highest concurrency with goodput within 95% of the peak **and** first-token p95 at most 80% of the threshold.
- **Why not 20.** Its p95 is 1,295 ms against 1,500: a slightly longer prompt or an Arabic-heavy hour tips it over.

16 in flight gives 2.13 good requests a second per replica, 99% of the peak.

#### [day2#busiest-hour] Size for the busiest hour of the month, not a normal evening

*Headroom*

- **4.98** requests a second, a typical daily peak
- **7.64** at the busiest hour: the sale day
- **5** replicas: a 39% margin

Replicas = busiest hour × 1.25 headroom ÷ 2.13 per replica, rounded up. Four replicas would leave 11.5%.

#### [day2#capacity-standard] A capacity standard has four lines

*The standard you set*

```
# file: Athar capacity standard
measure:   goodput curve per replica, real language mix, every engine or model change
operate:   16 in flight per replica (95% of peak goodput, p95 TTFT <= 1,200 ms)
size:      busiest hour of the last 30 days x 1.25, rounded up to whole replicas
review:    monthly, and before any planned sale or campaign
```

#### [day2#check-curve] Read the curve

*Checkpoint*

**Question:** A sweep gives goodput 3.1, 3.4, 3.5, 1.2 requests a second at 8, 12, 16 and 20 in flight. First-token p95 at 12 is 600 ms, at 16 it is 1,400 ms; the threshold is 1,500 ms. Where do you set the operating point?

- A. 16 in flight
- B. 12 in flight
- C. 8 in flight
- D. 20 in flight

#### [day2#lab-2-1] Goodput curve and operating point

Lab 2.1 · 25 min

Load-test the simulated self-hosted engine at rising concurrency, find where goodput falls, set the operating point and size the replicas for the busiest hour with a margin.

[D2_1_goodput_operating_point.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D2_1_goodput_operating_point.ipynb)

- [ ] Run one load step and read its latencies (4 min)
- [ ] Sweep concurrency and compute goodput (7 min)
- [ ] Find the knee and choose the operating point (6 min)
- [ ] Replicas and margin for the busiest hour (8 min)
- [ ] ✱ Stretch: Repeat the sweep with long prompts and see the knee move

### Session 2: Admission control and shedding

#### [day2#s2] Admission control and shedding

*Session 2*

- Set a concurrency cap from the operating point
- Rank traffic into priority classes with a reason
- Show by replay that priority traffic keeps its objective

#### [day2#no-admission] Without admission, overload fails every class at once

*Lab 2.2 · no admission control*

- **3.4%** of P1 tracking requests within 1.5 s
- **7 min** first-token p95, for every class

One replica, a 10-minute spike to about 1.7 times its goodput. The engine admits everything, its cache overflows, and requests are computed twice.

#### [day2#admission-first] Admit only what the engine can serve; decide what waits

*Admission control*

1. **Arrive** with a class
2. **Queue** bounded, per class
3. **Release** highest class first, up to the cap
4. **Shed** a full queue answers at once

> **The cap is the operating point:** 16 in flight per replica, from Lab 2.1.

#### [day2#priority-classes] Classes come from what the user is doing, not from who shouts

*Priority classes*

| Class | Traffic | Promise |
| --- | --- | --- |
| P1 | tracking a parcel out for delivery | first token within 1.5 s for 95% |
| P2 | general help questions | 1.5 s for 95%, or a clear "try shortly" |
| P3 | staff summaries of complaint threads | within 30 s, deferrable in a surge |

#### [day2#cap-not-enough] A cap protects the engine; priorities protect the customers

*Lab 2.2 · three configurations*

| Configuration | P1 met | P2 met | P2 shed | P3 shed |
| --- | --- | --- | --- | --- |
| none | 3.4% | 4.5% | 0% | 0% |
| cap of 16, equal queues | 80.4% | 8.3% | 18% | 65% |
| cap, P3 limited to 2, short P2 queue, 1 s P2 deadline | 96.3% | 70.7% | 29% | 67% |

#### [day2#shed-early] Shed early and cheaply, with a message the user understands

*Shedding*

- A request shed at the gateway costs microseconds and returns at once
- A request that times out in the engine used capacity and still failed
- A queued P2 request older than 1 s would miss its objective anyway: drop it
- Tell the user in their language: "Athar is busy; try again in a minute"

#### [day2#check-shed] Which traffic do you shed first?

*Checkpoint*

**Question:** During the sale-day surge Athar's replicas are at their cap. Which traffic should the gateway shed first?

- A. The most recent arrivals, whatever their class
- B. Tracking requests, because they are the most numerous
- C. Staff summaries of complaint threads
- D. Arabic requests, because their prompts are longer

#### [day2#lab-2-2] A cap and priority shedding

Lab 2.2 · 25 min

Add a concurrency cap and three priority classes in front of the engine, then replay the overload trace and check that priority traffic still meets its objective.

[D2_2_admission_shedding.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D2_2_admission_shedding.ipynb)

- [ ] Replay the overload trace with no admission control (4 min)
- [ ] Add the concurrency cap and a bounded queue (7 min)
- [ ] Add priority classes and shed from the lowest (7 min)
- [ ] Check each class against its objective (7 min)
- [ ] ✱ Stretch: Shed by deadline: drop a queued request that can no longer meet its objective

### Session 3: Degraded modes

#### [day2#s3] Degraded modes

*Session 3*

- Design degraded modes with entry and exit conditions
- Measure answer quality in each mode by language
- Keep personal answers out of any cache and tell users plainly

#### [day2#degraded-ladder] A ladder of modes keeps a minimum service when parts fail

*Degraded modes*

1. **Full**: model and retrieval (normal)
2. **Fallback**: a smaller model (engine overloaded or down)
3. **Cache**: saved answers (retrieval or model down)
4. **Template**: tracking API only (no model at all)

#### [day2#fallback-fails-arabic] The smaller model keeps English and fails Arabic

*Lab 2.3 · quality per mode*

| Item | Value |
| --- | --- |
| Full, English | 98.3% |
| Full, Arabic | 89.5% |
| Fallback, English | 87.1% |
| Fallback, Arabic | 72.6% |

Averaged, the fallback passes 79.6%: the number that would have been reported.

#### [day2#cache-rules] A cache serves what is general, fresh and nobody's personal data

*The cached-answer mode*

- **Never personal.** 9 of 137 saved answers named a customer, a parcel and a street. Refused.
- **Never stale.** 7 were older than their help article. Refused.
- **The rest is right.** Every answer served from the cache passed: 63% of Arabic and 58% of English help questions hit.

#### [day2#route-by-language] Route degraded traffic by language when the modes differ by language

*Routing*

| Engine down | Route | Pass rate |
| --- | --- | --- |
| English help | fallback, then cache | 87.1% |
| Arabic help | cache first, then fallback | 91.1% |
| Tracking | template from the tracking API, no model | all answered |

#### [day2#disclose-mode] Every degraded answer says so, in the user's language

*Responsible use*

**Customer:** What is the fee for a registered letter in Abha?

**Athar, cache mode:** Athar is answering from saved answers: details may not reflect the latest updates. *Then the saved answer.*

**Athar, fallback mode:** Athar is running in reduced mode: this answer may be less complete than usual. *Then the smaller model's answer.*

**أثر، الإجابات المحفوظة:** يجيب أثر حاليًا من إجابات محفوظة، وقد لا تعكس التفاصيل آخر التحديثات.

#### [day2#check-mode] The fallback passes overall

*Checkpoint*

**Question:** Shuaib reports that the fallback model passes 84% of the test set, against a minimum service of 85%, "close enough to ship". English passes 92%, Arabic 79%. What do you decide?

- A. Ship it: 84% is within a point
- B. Remove the fallback mode entirely
- C. Lower the minimum service to 80%
- D. Use it for English; route Arabic to the cache first and measure again

#### [day2#lab-2-3] Fallback model and cached answers

Lab 2.3 · 25 min

Configure a smaller fallback model and a cached-answer mode, route by health signals, measure quality in each mode by language and keep personal tracking answers out of the cache.

[D2_3_degraded_modes.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D2_3_degraded_modes.ipynb)

- [ ] Grade the full mode on the question set (4 min)
- [ ] Grade the fallback model by language (6 min)
- [ ] Build the cached-answer mode and its refusal rule (7 min)
- [ ] Route by health signals and disclose the mode (8 min)
- [ ] ✱ Stretch: Set the cache freshness limit from how often help articles change

### Session 4: Chaos experiments

#### [day2#s4] Chaos experiments

*Session 4*

- Write a chaos experiment as a falsifiable hypothesis
- Inject dependency failures and measure the minimum service
- Stop a retry storm with a retry budget and backoff

#### [day2#chaos-method] A chaos experiment is a hypothesis that could be false

*Chaos experiments*

1. **Steady state** measured
2. **Hypothesis** the minimum service holds
3. **Inject** one fault, small radius
4. **Compare** or abort

Fault injectors such as Chaos Mesh (in a cluster) or Toxiproxy (on a connection) do the injecting; the method is the same in the lab's simulator.

#### [day2#retrieval-outage] With the cache, a retrieval outage costs answers, not errors

*Lab 2.4 · retrieval outage*

|  | Tracking answered | Help answered | Silent failures |
| --- | --- | --- | --- |
| cache on | 100% | 64.8% | 0 |
| cache off | 100% | 0% | 2,377 |

4,000 simulated requests. Unanswered help questions get a plain "not available now" message.

#### [day2#timeout-length] The client timeout decides whether the fallback is in time

*Lab 2.4 · provider timeout*

| Item | Value |
| --- | --- |
| 3 s timeout | 3.9 s p95 |
| 6 s timeout | 6.9 s p95 |
| 10 s timeout | 10.9 s p95 |

Every request waits the full timeout before the fallback starts. Only 3 s keeps the 5 s minimum service.

#### [day2#retry-storm] A 30-second fault becomes an outage that never ends

*Lab 2.4 · retry storm*

| Client policy | Peak offered | Recovered |
| --- | --- | --- |
| immediate retries, up to 3 | 24 a second | never |
| exponential backoff only | 34 a second | 63 s after the fault |
| 10% retry budget | 6.6 a second | when the fault ends |

6 requests a second offered, 8.5 served at most. Past the knee goodput collapses, so retries keep the service overloaded.

#### [day2#minimum-service] Write the minimum service as numbers a test can check

*The standard you set*

```
# file: Athar minimum service
tracking answered:          >= 95%, any single dependency down
help questions:             answered, or declined in the user's language; never a raw error
degraded answer quality:    >= 85% per language, measured per mode
p95 latency in any mode:    <= 5 s
clients:                    3-second timeout, 10% retry budget, jittered backoff
```

#### [day2#check-storm] The fault is gone; the outage is not

*Checkpoint*

**Question:** A 30-second provider fault ended ten minutes ago. Athar still fails most requests, and the engine shows three times the normal request rate. What is the most likely cause?

- A. Client retries keep the load past the knee, so goodput stays near zero
- B. A new provider fault started
- C. Half of the replicas were lost during the fault
- D. A traffic surge from a marketing campaign

#### [day2#lab-2-4] Outage, timeout and retry storm

Lab 2.4 · 25 min

Inject a retrieval outage, a provider timeout and a retry storm into the simulated service and check that the minimum service holds in each.

[D2_4_chaos.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D2_4_chaos.ipynb)

- [ ] Write the hypothesis and the minimum service (4 min)
- [ ] Retrieval outage: does the cached mode hold? (6 min)
- [ ] Provider timeout: does the fallback take over? (6 min)
- [ ] Retry storm, then a retry budget with backoff (9 min)
- [ ] ✱ Stretch: Run the three faults at once and say which mode the users get

#### [day2#wrap-up] Three things to keep

*Day 2 · wrap-up*

- **Operate below the knee.** An operating point with headroom, sized for the busiest hour.
- **Decide who waits.** Priority classes and early shedding protect the users at the door.
- **Measure every mode.** Per language, disclosed, tested with injected faults and retries.

#### [day2#next] Day 3: incidents and safe releases

*Next*

- Session 2 is a game day without AI assistance: you will take the roles of incident lead, operator and scribe
- Optional reading: the SRE workbook chapter on alerting on SLOs
