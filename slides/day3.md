---
course: "Reliability Engineering for AI Services"
code: "AE-403"
version: "2027.1.0"
deck: "day3"
day: 3
language: "en"
view: "trainee"
source: "https://sdaiaacademy.github.io/ae-403/slides/day3.html"
---

# Reliability Engineering for AI Services

## Day 3: Incidents and safe releases

Burn-rate alerts on quality, incident leadership, canaries and blameless learning

#### [day3#title] Incidents and safe releases

*SDAIA Academy · Reliability Engineering for AI Services*

Day 3: Burn-rate alerts on quality, incident leadership, canaries and blameless learning

AI Engineering Track · 4 teaching days + capstone day · 4 sessions · 4 labs · AE-403

#### [day3#agenda] Incidents and safe releases

*Today*

- **Session 1 · Finding silent regressions**: A quality budget burns silently; multi-window burn-rate alerts, sliced by language, find it in minutes
- **Session 2 · Running an incident**: Roles, a decision log, mitigation before diagnosis, and personal data handled through the breach procedure
- **Session 3 · Canary and rollback**: A canary with enough samples and a per-language quality gate rolls back without a human
- **Session 4 · Learning from incidents**: Blameless reviews find contributing factors, own the actions and turn the cases into tests

#### [day3#review-day2] Which degraded mode for Arabic help questions?

*Review of Day 2*

**Question:** The engine is down. The fallback model passes 87% of English and 73% of Arabic test questions; the cache answers 63% of Arabic help questions, all correctly. The minimum service is 85% per language. What do Arabic help questions get?

- A. The fallback model, like English
- B. An apology for every Arabic question
- C. The cache first, the fallback on a miss, both disclosed
- D. The full cache, including saved tracking answers

### Session 1: Finding silent regressions

#### [day3#s1] Finding silent regressions

*Session 1*

- Compute burn rate on a quality indicator
- Build a multi-window, multi-burn-rate alert
- Locate a regression in time and in a slice

#### [day3#silent-regression] A model update can fail one language without a single error

*Silent regressions*

- Every request returns 200, latency is normal, the probe is green
- Arabic answers fail 38% of the time; English is unchanged
- Only the sampled quality indicator moves, and only in its Arabic slice

- **The replayed day.** `replay_day.csv`: 288 five-minute slots. Athar v2.4 goes out at slot 130.

#### [day3#burn-rate] Burn rate is how fast the budget is being spent

*Burn rate*

- **1×** spends the 30-day budget in 30 days
- **6×** spends 5% of it in 6 hours
- **14.4×** spends 2% of it in one hour

Burn rate = error rate in the window ÷ (1 − objective). With a 95% quality objective, 14.4× means 72% of answers failing.

#### [day3#two-windows] Two windows: one proves it matters, one proves it is still happening

*Multi-window alerts*

```
# file: Lab 3.1
def fires(g, long, short, rate):
    lw = U.burn_rate(g.bad, g.graded, 0.95, long)
    sw = U.burn_rate(g.bad, g.graded, 0.95, short)
    return (lw > rate) & (sw > rate)
```

Without the short window, the alert keeps firing for hours after the fix; without the long one, a single bad five minutes pages someone.

#### [day3#when-it-fires] The averaged alert never fires; the Arabic one fires in 35 minutes

*Lab 3.1 · the replay*

| Tier | All traffic | Arabic slice |
| --- | --- | --- |
| fast page: 1 h and 5 min at 14.4× | never | never |
| slow page: 6 h and 30 min at 6× | never | after 255 min |
| quality: 1 h and 5 min at 6× | never | after 35 min |

After the update Arabic burns at about 8×, English at about 0.6×, all traffic at about 5×.

#### [day3#locate-regression] Put the change log next to the slice: slot 131 against a deploy at 130

*Locating it*

- slot 40: help index refresh (English)
- slot 130: model update: athar-v2.4
- slot 210: gateway configuration

- Arabic 30-minute error rate above 10% from slot 131, for the rest of the day
- The English slice did not move: the change is language-specific
- A step change right after a release points at the release

#### [day3#alert-as-code] The alert is code in the repository, reviewed like code

*The rule*

```
# file: Prometheus rule (Lab 3.1)
- alert: AtharArabicQualityBurn
  expr: (athar:quality_bad:ratio_rate1h{lang="ar"} > (6 * 0.05))
    and (athar:quality_bad:ratio_rate5m{lang="ar"} > (6 * 0.05))
  labels:
    severity: page
```

#### [day3#check-averaged] Why did the alert stay silent?

*Checkpoint*

**Question:** After v2.4, 38% of Arabic answers fail and English is unchanged. Arabic is 60% of traffic. The 6× quality alert on all traffic never fires. Why?

- A. Too few answers are graded to see it
- B. The English slice keeps the combined burn rate near 5×, below the threshold
- C. The five-minute window is too short
- D. The 95% objective is too strict

#### [day3#lab-3-1] A burn-rate alert on quality

Lab 3.1 · 25 min

Build a burn-rate alert on the sampled quality indicator and locate the regression in a replayed day, first on all traffic and then by language.

[D3_1_quality_burn_rate.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D3_1_quality_burn_rate.ipynb)

- [ ] Quality burn rate per five minutes (5 min)
- [ ] Two windows and two burn rates (7 min)
- [ ] Replay the day: when does it fire? (5 min)
- [ ] Slice by language and locate the regression (8 min)
- [ ] ✱ Stretch: Write the alert as a Prometheus rule and count its pages over the month

### Session 2: Running an incident

#### [day3#s2] Running an incident

*Session 2*

- Run an incident in three roles with a decision log
- Mitigate before diagnosing
- Decide on breach notification from the facts

#### [day3#three-roles] Three roles keep deciding, doing and recording apart

*Incident roles*

- **Incident lead.** Decides and sets priorities. Talks to the service owner. Does not type commands.
- **Operator.** Runs the mitigation and reports what the system shows.
- **Scribe.** Keeps the decision log: minute, role, decision, reason.

#### [day3#mitigate-first] Mitigate first; diagnose on a copy

*The first rule*

- **5 min** to mitigate when the lead rolls back first: 32 exposed answers
- **35 min** when the team diagnoses first: 56 exposed answers

Lab 3.2's simulator. A rollback is reversible; the minutes customers spend receiving wrong answers are not.

#### [day3#decision-log] Every decision gets a minute, an owner and a reason

*The decision log*

| T+ | Role | Decision | Reason |
| --- | --- | --- | --- |
| 1 | lead | declare | quality alert; release 35 minutes earlier |
| 5 | lead | roll back v2.4 | complaints confirm impact; only recent change; reversible |
| 10 | lead | page the DPO | a customer saw another customer's address |
| 40 | lead | notify SDAIA | names and addresses exposed: harm likely |

#### [day3#breach-procedure] Personal data in answers is a breach: follow the procedure

*Responsible use*

1. **Contain** stop the exposure: the rollback
2. **Assess** data, people, likely harm, with the DPO
3. **Notify** SDAIA within 72 hours of awareness, if harm is expected
4. **Document** the notice, the actions, the lessons

#### [day3#awareness-clock] The 72 hours start at awareness, not at the root cause

*What goes wrong*

- Awareness came at T+9, when a customer reported another person's address
- Waiting for the root cause before assessing spends the clock on the wrong question
- Preserve the evidence before the rollback overwrites the logs you will need

#### [day3#check-first-action] Order the first actions

*Checkpoint*

**Question:** The Arabic quality alert pages you; v2.4 went out 35 minutes ago. Put the first four actions in order.

*Put these in the right order*

- Start root-cause analysis
- Roll back to v2.3
- Declare the incident and assign the roles
- Page the data protection officer once personal data is reported

#### [day3#lab-3-2] Game day: a model-update regression

Lab 3.2 · 25 min

Run a game day on a model-update regression as incident lead, operator and scribe, without AI assistance, keeping a decision log and deciding on breach notification.

[D3_2_game_day.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D3_2_game_day.ipynb)

- [ ] Read the roles and the first page (3 min)
- [ ] Detect and declare: first decisions (6 min)
- [ ] Mitigate: choose and apply the action (7 min)
- [ ] Personal data in answers: the breach decision (5 min)
- [ ] Close and hand over the log (4 min)
- [ ] ✱ Stretch: Rerun the drill with a different first action and compare time to mitigate

### Session 3: Canary and rollback

#### [day3#s3] Canary and rollback

*Session 3*

- Design canary steps with analysis at each step
- Size the minimum sample for a quality gate
- Roll back automatically on latency or quality

#### [day3#canary-recap] A canary is a release that can stop itself

*Recap from AE-305*

**5%** 10 min → **25%** 20 min → **50%** 20 min → **100%** promote

Analysis at every step; a failed step rolls back without a human. Progressive delivery tools such as Argo Rollouts or Flagger run the steps; your gate decides them.

#### [day3#old-gate] Ten minutes at 5% promoted the int4 model on 27 Arabic answers

*Lab 3.3 · the old pipeline*

- **Latency.** Canary p95 1,174 ms against stable 1,455 ms: the 4-bit model is faster.
- **Quality.** 26 of 27 graded Arabic answers passed. Its true Arabic rate is 90.5%, against 97% for stable.

#### [day3#minimum-sample] No quality verdict below 200 graded answers per language

*The minimum sample*

- Latency is judged at every step: it has thousands of samples
- Quality is judged on the cumulative canary samples, once each language has 200
- Before that the step continues, and the release cannot reach 100%
- Canary answers are graded at 30%, stable ones at 5%, to reach 200 in minutes

#### [day3#canary-decisions] v2.6 is promoted; the int4 model rolls back at 25%

*Lab 3.3 · the designed gate*

| Candidate | 5% | 25% | 50% | Decision |
| --- | --- | --- | --- | --- |
| v2.6 | continue (35 ar) | pass (305 ar) | pass | promoted |
| v2.6-int4 | continue (27 ar) | fail: ar 91.2% against 96.6% |  | rolled back |

#### [day3#gate-as-policy] The release gate is the error budget policy, automated

*The standard you set*

| Rule | Value |
| --- | --- |
| first-token p95 | at most 1.2 × stable, every step |
| quality per language | at least stable minus 3 points |
| minimum sample | 200 graded answers per language, cumulative |
| on failure | automatic rollback, alert to the release engineer |

#### [day3#check-canary] The canary passed; should it have?

*Checkpoint*

**Question:** A canary ran 10 minutes at 5% and passed with 25 of 26 Arabic answers correct, against 97% for stable. What do you do before promoting?

- A. Promote: 96% is within the 3-point margin
- B. Roll back: the sample is too small to trust
- C. Continue at a larger share until each language has the minimum sample
- D. Ask the evaluation team to approve by hand

#### [day3#lab-3-3] Canary with automated rollback

Lab 3.3 · 25 min

Release two candidate model versions as canaries with automated rollback on a latency and quality gate: one promotes, one rolls back on Arabic quality.

[D3_3_canary_rollback.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D3_3_canary_rollback.ipynb)

- [ ] Read the steps and the gate (3 min)
- [ ] Write the analysis for one step (7 min)
- [ ] Add the minimum-sample rule (6 min)
- [ ] Run both candidates and read the decisions (9 min)
- [ ] ✱ Stretch: Translate the gate into the supplied Argo Rollouts analysis template

### Session 4: Learning from incidents

#### [day3#s4] Learning from incidents

*Session 4*

- Write a blameless timeline and contributing factors
- Write corrective actions with an owner and a test
- Turn an incident's failing cases into a regression test

#### [day3#blameless] A blameless review asks what made the error easy, not who made it

*Blameless reviews*

- **Not a factor.** "The engineer did not test Arabic."
- **A factor.** "The evaluation set had no Arabic tracking questions and no Eastern Arabic digits."

The SRE book: a blameless postmortem focuses on the contributing causes without indicting any individual or team.

#### [day3#contributing-factors] Five conditions made the incident possible

*Lab 3.4 · INC-0731*

1. The offline evaluation set had no Arabic tracking questions
2. The v2.4 prompt template dropped digit normalisation
3. The tracking lookup fell back to the nearest parcel instead of refusing
4. The release went to everyone at once, with no quality gate
5. On-call had no written authority to roll back

#### [day3#owned-actions] An action has an owning role, a date and a check

*Corrective actions*

| Action | Owner | Days | Done when |
| --- | --- | --- | --- |
| Normalise digits in the gateway | model platform | 7 | unit test with Eastern Arabic digits passes |
| Lookup refuses inexact matches | tracking API team | 7 | unknown number returns "not found" |
| Every model release through the canary gate | release engineer | 21 | pipeline refuses a release without a verdict |

#### [day3#case-to-test] The incident's cases become a test that failed before the fix

*From case to test*

```
# file: Lab 3.4
def check_case(answer, case):
    a = U.normalise_digits(answer)
    problems = []
    if case["asked_parcel"] not in a:
        problems.append("does not name the parcel asked about")
    if [p for p in U.PARCEL_RE.findall(a) if p != case["asked_parcel"]]:
        problems.append("names another customer's parcel")
    return problems
```

v2.4 passes 0 of 12 cases; v2.4.1 passes 12 of 12.

#### [day3#review-template] Every review has the same five parts

*The standard you set*

- **Timeline.** from the decision log, in minutes from the page
- **Impact.** users, answers, data, budget spent
- **Factors.** conditions, each with evidence

- **Actions.** owned, dated, checked
- **Tests.** the cases, in the release gate

#### [day3#check-factor] Which line belongs in the review?

*Checkpoint*

**Question:** Four draft lines for INC-0731's contributing factors. Which one belongs in a blameless review?

- A. The release engineer should have checked Arabic before shipping
- B. Human error during the template change
- C. Arabic customers received wrong answers
- D. The release pipeline had no gate on Arabic answer quality

#### [day3#lab-3-4] Blameless review and regression test

Lab 3.4 · 25 min

Write a blameless review of a supplied incident and turn its failing cases into a regression test that fails on the bad version and passes on the fixed one.

[D3_4_blameless_review.ipynb](https://sdaiaacademy.github.io/ae-403/labs/D3_4_blameless_review.ipynb)

- [ ] Read the incident record (4 min)
- [ ] Timeline and contributing factors (7 min)
- [ ] Owned corrective actions (5 min)
- [ ] The regression test: fails before, passes after (9 min)
- [ ] ✱ Stretch: Add the test to the canary gate of Lab 3.3

#### [day3#wrap-up] Three things to keep

*Day 3 · wrap-up*

- **Alert per slice.** Quality alerts per language, with windows short enough for step changes.
- **Mitigate, then diagnose.** Roles, a decision log, and the breach procedure from awareness.
- **Gates and tests.** A canary with a minimum sample; every incident leaves a test behind.

#### [day3#next] Day 4: integrity and readiness

*Next*

- Where model files come from, how to prove they were not changed, and how to admit only verified models
- The last session starts the capstone: a readiness review of another team's service
