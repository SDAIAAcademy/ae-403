---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.1.0"
deck: "day1"
day: 1
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/slides/day1.html"
---

# Reliability Engineering for AI Services

## Day 1: Objectives that match what users need

Indicators and objectives for latency, availability and answer quality, sliced by language

#### [day1#title] Objectives that match what users need

*SDAIA Academy · Reliability Engineering for AI Services*

Day 1: Indicators and objectives for latency, availability and answer quality, sliced by language

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-403

#### [day1#agenda] Objectives that match what users need

*Today*

- **Session 1 · AI services fail differently**: An AI service can be up, fast on a probe and still wrong, slow or silent for its users
- **Session 2 · Indicators for latency and quality**: Indicators as good events over valid events: first-token time, per-token time, availability and a sampled quality grade
- **Session 3 · Objectives and error budgets**: Objectives tied to what users need, the budget they leave, and a release policy that spends it
- **Session 4 · Objectives for multi-step tasks**: A booking flow succeeds per task, not per call: completion, cost per completed task and escalation

#### [day1#setup-check] One notebook proves the setup: run it before Session 1

*Before the first lab*

- **Colab:** open `00_setup_check.ipynb` from the course page and run all cells
- **Laptop:** `uv sync` in `labs/`, then the same notebook
- It imports every library, reads one data file per day and runs the engine simulator once
- No model is downloaded and no key is needed

- **What every lab starts from.** A supplied file in `labs/data/`. No lab needs the result of another lab: if you fall behind, the next lab still starts level.

### Session 1: AI services fail differently

#### [day1#s1] AI services fail differently

*Session 1*

- Name four ways an AI service fails while an uptime check stays green
- Read per-minute telemetry by language and by mode
- Separate what users felt from what the probe measured

#### [day1#meet-athar] Athar answers parcel questions for Rasael in Arabic and English

*The case*

1. **Gateway** admission, priorities, rate limits
2. **Retrieval** 3,000 help articles, Arabic and English
3. **Self-hosted model** an open-weight model on Rasael's own engine
4. **Tracking API** the parcel's status for a parcel number

- **Your role.** The reliability lead who sets the standards other teams must meet, and defends them.
- **Data.** All synthetic, fixed seed: telemetry, traffic, answers, incidents, model files.

#### [day1#up-but-wrong] An AI service can be up and still fail its users

*Four new failure modes*

- **Wrong.** Fluent answers that are false, often in one language only.
- **Slow to start.** Long prompts wait in the queue; the first token takes seconds.
- **Slow to stream.** The answer arrives word by word, slower than reading speed.
- **Empty or cut.** A 200 with nothing useful: the output limit cut the answer.

> **All four return HTTP 200.** A status-code dashboard counts them as success.

#### [day1#probe-blind] A probe measures the probe, not the users

*Why the uptime check is green*

| The probe | A real Athar request |
| --- | --- |
| one tiny English prompt a minute | a question plus 1,000 to 3,000 tokens of retrieved articles |
| needs no retrieval | fails when the index is wrong or down |
| four output tokens | 60 to 300 tokens, streamed |
| never graded | right or wrong, in Arabic or English |

#### [day1#week-telemetry] A week of telemetry, per minute and per language

*Lab 1.1 · the data*

```
# file: data/telemetry_week.csv
minute,day,lang,requests,errors,ttft_p95_ms,tpot_p95_ms,empty_answers,graded,passed
0,0,ar,22,0,914,41.1,0,1,1
0,0,en,11,0,783,33.4,0,0,0
```

- **ttft**: time to first token; **tpot**: time per output token after it
- **graded / passed**: about 5% of answers are checked by the quality team
- Minutes count from the start of the week: no clock times, every cohort reads the same data

#### [day1#what-users-felt] Five incidents in one week; the probe saw one

*Lab 1.1 · the result*

| Day | Minutes | Signal | Probe |
| --- | --- | --- | --- |
| 1 | 105 | Arabic quality below 85% | green |
| 2 | 70 | first token over 2 s at the evening peak | green |
| 3 | 50 | streaming over 120 ms a token | green |
| 4 | 40 | empty answers over 5% | green |
| 5 | 17 | server errors: the engine restarted | red |

#### [day1#small-numbers] At night, small numbers look like incidents

*What goes wrong in the lab*

- Two failed answers out of eight graded is a 75% pass rate
- One empty answer out of ten requests is 10%
- Require a minimum sample (40 graded answers in 30 minutes) and a minimum duration (15 minutes)

- **The rule behind it.** An indicator without a sample size is an opinion. Every quality number this week comes with its count or its interval.

#### [day1#check-probe] Which incident turns the probe red?

*Checkpoint*

**Question:** Athar's uptime check sends one short English prompt a minute. Which of these incidents does it detect?

- A. Arabic answers wrong after an index refresh
- B. First token over four seconds at the evening peak
- C. The engine pods restart and refuse every request
- D. Answers cut short at the output limit

#### [day1#lab-1-1] What the uptime check missed

Lab 1.1 · 25 min

Read a week of Athar telemetry and list the incidents an uptime check would miss, with their duration and the indicator that shows each one.

[D1_1_uptime_blind_spots.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D1_1_uptime_blind_spots.ipynb)

- [ ] Load the week and plot requests, probe and errors (4 min)
- [ ] Find the minutes where the probe was green and users were not (7 min)
- [ ] Group them into incidents with a start, a duration and a signal (7 min)
- [ ] Name the indicator that would have caught each one (7 min)
- [ ] ✱ Stretch: Repeat the search for Arabic and English separately and compare

### Session 2: Indicators for latency and quality

#### [day1#s2] Indicators for latency and quality

*Session 2*

- Define an indicator as good events over valid events
- Exclude probes and client cancellations with a written reason
- Estimate a sampled quality rate with its interval, by language

#### [day1#good-over-valid] An indicator is good events divided by valid events

*An indicator*

1. **All events** every row in the log
2. **Valid** remove what the service owed nobody
3. **Good** met the threshold
4. **Indicator** good / valid

> **Write every exclusion down with its reason.** The exclusions are where an indicator is made to look better than the service.

#### [day1#exclusions-move-numbers] The same day gives three availabilities

*Lab 1.2 · one day of requests*

| Item | Value |
| --- | --- |
| Cancels counted as failures | 96.58% |
| Probe and cancels excluded | 98.95% |
| Probe counted as a user | 99.06% |

A 499 is a user who closed the chat; a 429 is Athar refusing a user. Only one of them is the service's fault.

#### [day1#two-latencies] First-token time and per-token time fail for different reasons

*Latency is two numbers*

- **Time to first token.** Queueing plus prefill of the whole prompt. Grows with load and with prompt length. Users feel it as "is it working?"
- **Time per output token.** One decode step of the batch. Grows with the batch size. Users feel it as reading slower than the text appears.

Athar's thresholds: first token within **1,500 ms**, then within **100 ms** a token. On the lab day 94.2% and 98.9% of served requests met them.

#### [day1#quality-is-sampled] Answer quality is a sampled indicator: report its interval

*Quality*

| Language | Graded | Pass rate | 95% interval |
| --- | --- | --- | --- |
| Arabic | 395 | 94.9% | 92.3% to 96.7% |
| English | 297 | 98.0% | 95.7% to 99.1% |

Graders follow a written rubric; the sample is random, not the answers someone complained about.

#### [day1#slice-by-language] Every quality objective is sliced by language

*Responsible use*

- Athar's traffic is 60% Arabic: an average lets English mask an Arabic failure
- Degraded modes and model updates fail one language more often than the other
- The slice is part of the objective, not a dashboard filter

- **The question for any review.** "Show me this number for Arabic users only." If the team cannot, the objective is not defined yet.

#### [day1#indicator-spec] An indicator specification fits on five lines

*Write it down*

```
# file: Athar indicators
availability: good = status 200; valid = users (not probe), not 499
first_token:  good = ttft_ms <= 1500 among served user requests
per_token:    good = tpot_ms <= 100 among served user requests
quality_ar:   good = passed; valid = graded Arabic answers (random 6%)
quality_en:   good = passed; valid = graded English answers (random 6%)
```

#### [day1#check-cancel] Is this request a bad event?

*Checkpoint*

**Question:** A customer closes the chat after two seconds, before Athar's first token. The gateway logs a 499. How should the availability indicator count it?

- A. As a bad event
- B. As a good event
- C. As half a bad event
- D. Excluded from valid events, and counted in its own abandonment signal

#### [day1#lab-1-2] Four indicators from one day

Lab 1.2 · 25 min

Define first-token time, per-token time, availability and a sampled quality grade on a day of request logs, with the exclusions written down and quality sliced by language with an interval.

[D1_2_indicators.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D1_2_indicators.ipynb)

- [ ] Read the request log and its fields (3 min)
- [ ] Write the valid-event filter and its exclusions (6 min)
- [ ] Latency indicators: first token and per token (6 min)
- [ ] Availability as good over valid requests (4 min)
- [ ] Quality grade by language, with a 95% interval (6 min)
- [ ] ✱ Stretch: How many graded samples per day would narrow the Arabic interval to two points?

### Session 3: Objectives and error budgets

#### [day1#s3] Objectives and error budgets

*Session 3*

- Set an objective from a user task, not from last month
- Compute budget burn over a month and per week
- Write a release policy that decides from the remaining budget

#### [day1#objective-from-task] Set the objective from the user's task, then check it against history

*An objective*

- **From the task.** A customer waiting at the door needs the parcel status before the courier leaves: a first token within 1.5 s, an answer that is right.
- **Not from last month.** "We had 99.82%, so the objective is 99.8%" makes every bad month a target and every good one a waste.

> **Athar's four:** availability 99.5%; first token within 1,500 ms for 95%; quality 95% for Arabic and 95% for English; all over a rolling 30 days.

#### [day1#budget-arithmetic] The error budget is the bad events the objective allows

*Budget arithmetic*

- **0.5%** of valid requests may fail at 99.5%
- **0.18%** failed in the month (99.82%)
- **36%** of the availability budget burned

Burned = bad events / (1 - target) / valid events. It is a count of users, not of minutes.

#### [day1#month-budgets] Arabic quality has spent four fifths of its budget

*Lab 1.3 · the month*

| Item | Value |
| --- | --- |
| Availability | 36% |
| First token | 46% |
| Quality, English | 43% |
| Quality, Arabic | 81% |

Normal Arabic operation (97.2% pass) already burns more than half; a 48-hour drop to 80% spent the rest.

#### [day1#tight-objective] An objective just below normal leaves no room to work

*What goes wrong*

- Arabic passes 97.2% on a normal day; the objective is 95%
- So 56% of the budget goes on days when nothing is wrong
- Either improve normal Arabic quality, or accept that every Arabic incident freezes releases
- Both are decisions for the service owner, made with the numbers, before the incident

#### [day1#release-policy] The policy decides from the remaining budget of what the change touches

*A release policy*

| Lowest remaining budget among the touched objectives | Decision |
| --- | --- |
| 50% or more | go |
| 25% to 50% | go behind a canary |
| below 25% | freeze: reliability and security fixes only |

The SRE workbook's example policy halts changes other than urgent and security fixes once a service exceeds its budget over four weeks.

#### [day1#five-requests] The policy freezes the change most likely to fix Arabic

*Lab 1.3 · five pending releases*

| Request | Touches | Decision |
| --- | --- | --- |
| RR-1 new model v2.5 | quality ar, en; first token | freeze (19% left) |
| RR-2 shorter English prompt | quality en | go (57%) |
| RR-3 larger engine batch | first token, availability | go (54%) |
| RR-4 gateway security patch | availability | go (exempt) |
| RR-5 Arabic index refresh | quality ar | freeze (19%) |

#### [day1#check-budget] How much budget is left?

*Checkpoint*

**Question:** Over 30 days Athar served 2,000,000 valid requests and 6,000 failed. The availability objective is 99.5%. What share of the error budget remains?

- A. 99.7%
- B. 0.3%
- C. 40%
- D. 167%

#### [day1#lab-1-3] Objectives, budget and release policy

Lab 1.3 · 25 min

Set objectives for Athar, compute the budget burned over a supplied month and write the release policy that decides five pending release requests.

[D1_3_error_budgets.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D1_3_error_budgets.ipynb)

- [ ] Write the four objectives with their windows (5 min)
- [ ] Compute the budget and what the month burned (7 min)
- [ ] Find the week that burned most and why (5 min)
- [ ] Write the release policy and decide five requests (8 min)
- [ ] ✱ Stretch: Add a policy line for a budget spent by a dependency, not by a release

### Session 4: Objectives for multi-step tasks

#### [day1#s4] Objectives for multi-step tasks

*Session 4*

- Explain why per-call success hides failed tasks
- Define completion, cost and escalation indicators for a flow
- Set objectives a flow can be held to

#### [day1#per-call-hides] Per-call success says 98.9%; one booking in five never happened

*Multi-step tasks*

- **98.9%** of model and tool calls succeeded
- **79.5%** of redelivery sessions booked a slot

2,000 sessions of the redelivery flow (Lab 1.4). Retried tool errors succeed; sessions fail on calls that worked.

#### [day1#task-indicators] Three indicators describe a flow: completion, cost and escalation

*Indicators for a flow*

- **Completion.** Sessions that reached the goal, per language. 78.2% Arabic, 81.3% English.
- **Cost per completed task.** All tokens, including failed sessions, over completed ones: SAR 0.0133 a booking.
- **Escalation.** Handed to a person: 8.1% Arabic, 7.2% English. A signal, not a failure.

#### [day1#loops-cost] 3% of sessions loop on slot offers and spend 10% of the tokens

*Lab 1.4 · the loops*

- customer: Not that slot.
- tool call: `offer_slots(parcel, after=slot_3)`
- customer: Not that one either.
- tool call: `offer_slots(parcel, after=slot_4)`
- after 6 to 12 offers: 70% of looping sessions are abandoned

#### [day1#escalation-signal] Escalation is the right answer for some parcels; the hand-over is the objective

*Escalation*

- A parcel held by customs cannot be rebooked online: escalating it is correct
- Pushing escalation to zero makes the assistant book what it should not
- Measure the hand-over: every escalated session reaches a person, in its language

#### [day1#flow-objectives] Objectives for a flow say what is fixable and what is not

*Objectives for the flow*

| Indicator | Objective | Reason |
| --- | --- | --- |
| Completion | 85% per language, 30 days | loops and timed-out confirmations are fixable; ineligible parcels are not |
| Cost per booking | SAR 0.012 or less | ending the loop removes most of the excess |
| Escalation | 9% or less, all handed over | the right answer for some parcels |

#### [day1#check-flow] Which indicator for the redelivery flow?

*Checkpoint*

**Question:** Ruwaida asks for one headline indicator for the redelivery booking flow on her monthly review. Which do you propose?

- A. Share of successful model and tool calls
- B. Share of sessions that booked a slot, per language
- C. Share of sessions not escalated to a person
- D. Median session duration

#### [day1#lab-1-4] Indicators for the redelivery flow

Lab 1.4 · 25 min

Define completion, cost and escalation indicators for the redelivery booking flow from 2,000 recorded sessions, and show what per-call success hides.

[D1_4_task_objectives.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D1_4_task_objectives.ipynb)

- [ ] Read the sessions and their steps (3 min)
- [ ] Per-call success against per-task completion (7 min)
- [ ] Cost per completed booking, with the loops (7 min)
- [ ] Escalation rate and objectives for the flow (8 min)
- [ ] ✱ Stretch: Find the step where most abandoned sessions stop

#### [day1#wrap-up] Three things to keep

*Day 1 · wrap-up*

- **Users, not probes.** Four of five incidents were invisible to the uptime check.
- **Every number has a slice and a sample.** Quality per language, with its interval.
- **Budgets decide releases.** Per objective, from the remaining budget, written before the incident.

#### [day1#next] Day 2: capacity and failure

*Next*

- Bring your objectives from Lab 1.3: Day 2 sizes the service to meet them at the busiest hour
- Optional reading: the SRE book chapters on handling overload and cascading failures
