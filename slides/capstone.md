---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.1.0"
deck: "capstone"
day: 5
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/slides/capstone.html"
---

# Reliability Engineering for AI Services

## Capstone: Readiness review defences

A production readiness review defended before a panel, with a live fault to diagnose

#### [capstone#title] Readiness review defences

*SDAIA Academy · Reliability Engineering for AI Services*

Capstone: A production readiness review defended before a panel, with a live fault to diagnose

AI Engineering Track · 4 teaching days + capstone day · 10 min talk and demo · 5 min Q&A · AE-403

#### [capstone#agenda] How the day runs

*Capstone*

- **Exit check and final prep**: the supervised check without AI, the rubric, a last rehearsal
- **Defences**: ten minutes of review, five of questions with a live fault
- **Review and closing**: peer feedback, the trainer's review, the follow-up task

#### [capstone#deliverable] A readiness review of a real or supplied service, with measured evidence

*The capstone*

- A public GitHub repository: the review, the code and notebooks behind every number, the logs
- Load-test, chaos and pipeline logs, the drill's decision log, and a commit history that shows the work
- Findings ranked by risk, a launch decision, and dated conditions that each name their proof
- Synthetic data only: no personal data, no keys, no private model weights

- **Brief and template.** `labs/capstone/README.md` and `TEMPLATE_README.md`. The supplied service is Athar v2.7 (`athar_v27_pack.json`), running on the course's simulator.

#### [capstone#rubric] The rubric

*How reviews are scored*

| Item | Value |
| --- | --- |
| Objectives and alerts | 20% |
| Capacity and degradation | 25% |
| Incident drill and review | 20% |
| Release integrity | 15% |
| Readiness decision | 20% |

> **Every claim carries a number and the log it came from.** "Met" is the team's word; a review shows the measurement.

#### [capstone#format] Ten minutes of review, then five of questions with a live fault

*Format*

- **1 · The service.** What it does, for whom, its objectives. Two minutes.
- **2 · The evidence.** Capacity, degradation, the drill, the release gate: measured. Five minutes.
- **3 · The decision.** The top three findings, the decision, the conditions. Three minutes.

> **Peer feedback.** After each defence, everyone writes one strength, one question and one suggestion.

#### [capstone#live-fault] The panel injects a fault; you diagnose it aloud

*In the questions*

1. **1 · Inject** the assessor starts one fault, unannounced
2. **2 · Detect** which indicator moved, and which alert fires
3. **3 · Mitigate** the first action, and why before the root cause
4. **4 · Explain** what your review predicted, and what it missed

> **The reasoning is scored, not the speed.** Say what you look at first and why; a wrong first guess that you correct from the data is a good answer.

#### [capstone#week-recap] The week in four questions

*What the panel will look for*

- **What does good mean?** Indicators per language, budgets that change releases.
- **What survives the busiest hour?** An operating point with margin, shedding by priority, honest degraded modes.
- **Who acts when it breaks?** Roles, a decision log, a canary that rolls back, a review without blame.
- **What are we running?** Hashes, signatures, a bill of materials, a ranked launch decision.

#### [capstone#running-order] Who defends when

*Running order*

| # | Presenter | Service reviewed |
| --- | --- | --- |
| 1 |  |  |
| 2 |  |  |
| 3 |  |  |
| 4 |  |  |
| 5 |  |  |
| 6 |  |  |
| 7 |  |  |
| 8 |  |  |

#### [capstone#final-prep] Final prep · 20 minutes

*Before the first defence*

Rehearse once, record a backup, open your service or the simulator on this screen.

#### [capstone#now-presenting] Now presenting

*Now defending*

#### [capstone#review] What the reviews showed

*Trainer review*

- **Strongest patterns.** What several reviews got right.
- **Common gaps.** What most reviews would fix next.
- **One surprise.** Something the live faults showed.

#### [capstone#what-next] Keep going

*After the course*

- **The follow-up task:** within 30 days, apply one standard from the course to a service in your team or an open-source deployment, and send the evidence
- **Your review stays yours:** keep it reproducible and act on the first condition you named today
- **The AE Expert badge:** this course is one of the AE-400 courses that help prepare for it

#### [capstone#thanks] Thank you

*SDAIA Academy*

Reliability Engineering for AI Services
