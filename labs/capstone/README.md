# Capstone: a production readiness review

You review an AI service that another team built and decide whether it may launch. You defend
the review before a panel of experienced engineers, who inject a fault into a running service
and ask you to diagnose it live.

## Choose the service

- **A peer's service**: a service another participant (or their team) runs, with its telemetry.
  Agree the scope with the owner and the trainer on Day 4.
- **The supplied pack**: Athar v2.7, a release candidate of Rasael's assistant. Its facts are in
  `athar_v27_pack.json`; the course's data, `relia.Engine`, `relia.Service` and the labs' gates
  are its environment. Every lab's supplied file is a starting point.

## What the review covers

| Rubric criterion (weight) | Evidence you show, measured |
|---|---|
| Objectives and alerts (20) | Indicators and objectives per language, budgets, the release policy; burn-rate alerts replayed on data |
| Capacity and degradation (25) | Goodput curve, operating point and margin for the busiest hour; an overload replay; chaos results per mode with quality measured per language |
| Incident drill and review (20) | A drill with a decision log, a blameless review, owned actions and a new regression test |
| Release integrity (15) | A pipeline run that admits a verified artefact and rejects a tampered and an unlicensed one, with logs |
| Readiness decision (20) | Findings ranked by risk, the launch decision and dated conditions with proofs |

## Submission

A **public GitHub repository** with the review (start from `TEMPLATE_README.md`), the code and
notebooks that produced every number, the logs (load test, chaos, pipeline, the drill's decision
log) and a commit history that shows the work. Synthetic data only: no personal data, no secrets.

## The defence

A 10-minute talk and 5 minutes of panel questions. During the questions the assessor injects a
fault into a running service (the simulator or the peer's service) and you diagnose it aloud.
AI assistants are allowed while you prepare (AI-full); the defence is live.

## The follow-up task

Within 30 days, apply one reliability standard from the course (an objective with its alert, an
admission limit, a degraded mode, a release gate or model admission) to a service in your own
team or to an open-source deployment, and send the evidence to the trainer.
