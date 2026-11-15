# Reliability Engineering for AI Services: labs

Sixteen 25-minute labs on one synthetic case, Rasael Post and Parcels and its bilingual assistant
Athar. Every lab starts from supplied files and reference results in `data/`, so none depends on
an earlier one, and every lab has a solution in `solutions/`.

## Quick start

- **Google Colab:** open a notebook from the table below; its first cell clones this repository
  and installs `requirements-colab.txt`. Run `00_setup_check.ipynb` first.
- **Locally** (Python 3.12 or 3.13, [uv](https://docs.astral.sh/uv/)):

  ```bash
  git clone https://github.com/SDAIAAcademy/ae-403.git
  cd ae-403/labs
  uv run jupyter lab
  ```

  On Windows, run `git config --global core.longpaths true` once, and set
  `UV_PROJECT_ENVIRONMENT` to a short path outside the course (for example `C:/uv403`) before
  `uv run`.

Nothing downloads a model and no key is needed. A laptop CPU is enough; no GPU and no cluster.

| Unit | Session | Notebook |
|---|---|---|
| Setup | Before Day 1 | [`00_setup_check.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/00_setup_check.ipynb) |
| Day 1 | 1.1 · What the uptime check missed | [`D1_1_uptime_blind_spots.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_1_uptime_blind_spots.ipynb) |
| Day 1 | 1.2 · Four indicators from one day | [`D1_2_indicators.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_2_indicators.ipynb) |
| Day 1 | 1.3 · Objectives, budget and release policy | [`D1_3_error_budgets.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_3_error_budgets.ipynb) |
| Day 1 | 1.4 · Indicators for the redelivery flow | [`D1_4_task_objectives.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_4_task_objectives.ipynb) |
| Day 2 | 2.1 · Goodput curve and operating point | [`D2_1_goodput_operating_point.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_1_goodput_operating_point.ipynb) |
| Day 2 | 2.2 · A cap and priority shedding | [`D2_2_admission_shedding.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_2_admission_shedding.ipynb) |
| Day 2 | 2.3 · Fallback model and cached answers | [`D2_3_degraded_modes.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_3_degraded_modes.ipynb) |
| Day 2 | 2.4 · Outage, timeout and retry storm | [`D2_4_chaos.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_4_chaos.ipynb) |
| Day 3 | 3.1 · A burn-rate alert on quality | [`D3_1_quality_burn_rate.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_1_quality_burn_rate.ipynb) |
| Day 3 | 3.2 · Game day: a model-update regression | [`D3_2_game_day.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_2_game_day.ipynb) |
| Day 3 | 3.3 · Canary with automated rollback | [`D3_3_canary_rollback.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_3_canary_rollback.ipynb) |
| Day 3 | 3.4 · Blameless review and regression test | [`D3_4_blameless_review.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_4_blameless_review.ipynb) |
| Day 4 | 4.1 · Provenance and the tampered file | [`D4_1_provenance.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_1_provenance.ipynb) |
| Day 4 | 4.2 · Sign and verify a model folder | [`D4_2_signing.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_2_signing.ipynb) |
| Day 4 | 4.3 · Bill of materials and admission gate | [`D4_3_bom_admission.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_3_bom_admission.ipynb) |
| Day 4 | 4.4 · Readiness review of Taqdir | [`D4_4_readiness_review.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_4_readiness_review.ipynb) |

## How a lab works

- Exercises are marked ✏️ and raise `NotImplementedError` until you write them. When an exercise
  is not done, the next cell loads its reference result from `data/reference/`, so the rest of the
  lab still runs.
- Each lab prints ✅ or ❌ checks as it goes, and ends with three "Check yourself" questions.
- `RELIA_QUICK=1` runs the longer simulations shorter (the trainer's dry run; the figures on the
  slides come from the full run). `RELIA_STRICT=1` turns every ❌ into an error.
- Work files go to `artifacts/`, which git ignores; Lab 4.2 writes a private key there.

## The model, and why there is no GPU

The case runs Athar on a self-hosted open-weight model. The labs do not download one: `relia.py`
holds a calibrated simulator of a continuous-batching engine (a KV cache, preemption, time to
first token and per-token time), a gateway with a concurrency cap and priority queues, the
service's dependencies with injectable faults, and a canary. Answers are recorded and graded by
code against the facts of each question. `relia.live_answer` calls a free hosted model on
OpenRouter when `OPENROUTER_API_KEY` is set and falls back to the recording otherwise. The cluster
tools appear as supplied files in `release/` (an Argo Rollouts analysis template and a Kyverno
admission policy) that the labs read and map to their gates.

## The data

`prepare_data.py` writes everything in `data/` from a fixed seed (403), using the standard library
only; run it again and every file comes out byte for byte the same.

| File | What it holds |
|---|---|
| `help_articles.jsonl` | 3,000 help articles in Arabic and English |
| `questions.jsonl`, `answers.jsonl` | 240 questions with their facts, and graded recorded answers per mode |
| `answer_cache.jsonl` | 137 cached answers for the cached-answer mode |
| `telemetry_week.csv`, `probe_week.csv` | A week of per-minute telemetry and the uptime probe's view of it |
| `requests_day.csv` | One day of requests for the indicators |
| `telemetry_month.csv`, `release_requests.csv` | A month of daily indicators per language and the releases requested in it |
| `redelivery_sessions.jsonl` | Multi-step redelivery sessions, call by call |
| `traffic_hourly.csv`, `overload_trace.csv` | A year of hourly traffic and a recorded overload by priority |
| `replay_day.csv`, `deploy_log.csv` | A day of graded answers per slot and the deployments in it |
| `incident/` | INC-0412's record and twelve failing cases |
| `models/` | Three small model artefacts (random weights), their provenance, signatures and Rasael's release key |
| `taqdir/` | The readiness checklist and Taqdir's evidence pack |
| `reference/` | The reference result of every exercise |

## What is planted in the data

So that trainers know what the labs should find:

- **Week telemetry:** five incidents; the uptime probe sees one. Empty answers and wrong answers
  return HTTP 200.
- **Month:** the Arabic quality budget is mostly spent; two requested releases should be frozen.
- **Redelivery:** each call succeeds about 99% of the time, the whole task about 80%.
- **Overload:** without priority shedding, P1 tracking misses its objective.
- **Answer cache:** 9 tracking answers with personal data and 7 stale answers that must be removed.
- **Replay day:** a model update at slot 130 silently breaks Arabic-Indic digits in parcel numbers.
- **Canary:** the int4 candidate passes a gate that decides on a small Arabic sample.
- **Models:** the mirror's second weight shard is tampered; the tiny model is licensed for research
  use only.
- **Taqdir:** the team's latency claim does not meet Rasael's standard, and its fallback model is
  unsigned.

## Editing the labs

The notebooks are generated from the percent-format sources in `_src/` by `_tools/py2nb.py`
(`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `solutions/`.
Edit the sources, not the notebooks. `_tools/sign_artifacts.py` signs the model artefacts
after `prepare_data.py` with a one-time key that it then discards; running it again changes the
signatures and `release_key.pub`, which is expected. `solutions/answer_key.md` lists the expected
results of every lab.
