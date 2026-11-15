# Readiness review: <service name>

Reviewer: <your name> · Service owner: <team> · Review date: <date>

## Decision

<launch / launch with conditions / do not launch>, in two sentences.

## 1 · Objectives and alerts

Indicators (good / valid, with exclusions and reasons), objectives per language, budget status,
release policy, alert rules and their replay.

## 2 · Capacity and degradation

Goodput curve, operating point and margin for the busiest hour; overload replay per priority
class; degraded modes with quality per language; chaos experiments (hypothesis, minimum service,
abort condition, results).

## 3 · Incident drill and review

Decision log of the drill, blameless review, owned corrective actions, the regression test and
where it runs.

## 4 · Release integrity

Signature verification, bill of materials, licence rule; the pipeline log for a valid, a
tampered and an unlicensed artefact.

## 5 · Findings and conditions

| Rank | Finding | Likelihood | Impact | Risk | Condition | Due | Proof |
|---|---|---|---|---|---|---|---|

## How to reproduce

Commands that rebuild every number in this review from the repository.
