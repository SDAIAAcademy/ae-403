# Reliability Engineering for AI Services: labs

## Quick start

- Google Colab: open a notebook from the course page; its first cell clones this repository.
- Locally: clone the repository, then open the notebooks in `labs/` with Jupyter.

| Unit | Session | Notebook |
|---|---|---|
| Day 1 | Session 1 · AI services fail differently | [`D1_1_read_week_synthetic.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_1_read_week_synthetic.ipynb) |
| Day 1 | Session 2 · Indicators for latency and quality | [`D1_2_define_indicators_first.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_2_define_indicators_first.ipynb) |
| Day 1 | Session 3 · Objectives and error budgets | [`D1_3_set_objectives_compute.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_3_set_objectives_compute.ipynb) |
| Day 1 | Session 4 · Objectives for multi-step tasks | [`D1_4_define_completion_cost.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D1_4_define_completion_cost.ipynb) |
| Day 2 | Session 1 · Capacity with headroom | [`D2_1_load_test_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_1_load_test_model.ipynb) |
| Day 2 | Session 2 · Admission control and shedding | [`D2_2_add_concurrency_cap.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_2_add_concurrency_cap.ipynb) |
| Day 2 | Session 3 · Degraded modes | [`D2_3_configure_smaller_fallback.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_3_configure_smaller_fallback.ipynb) |
| Day 2 | Session 4 · Chaos experiments | [`D2_4_inject_retrieval_outage.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D2_4_inject_retrieval_outage.ipynb) |
| Day 3 | Session 1 · Finding silent regressions | [`D3_1_build_burn_rate.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_1_build_burn_rate.ipynb) |
| Day 3 | Session 2 · Running an incident | [`D3_2_run_game_day.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_2_run_game_day.ipynb) |
| Day 3 | Session 3 · Canary and rollback | [`D3_3_release_new_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_3_release_new_model.ipynb) |
| Day 3 | Session 4 · Learning from incidents | [`D3_4_write_blameless_review.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D3_4_write_blameless_review.ipynb) |
| Day 4 | Session 1 · The model supply chain | [`D4_1_trace_provenance_three.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_1_trace_provenance_three.ipynb) |
| Day 4 | Session 2 · Signing and verification | [`D4_2_sign_manifest_model.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_2_sign_manifest_model.ipynb) |
| Day 4 | Session 3 · Bills of materials and admission | [`D4_3_write_bill_materials.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_3_write_bill_materials.ipynb) |
| Day 4 | Session 4 · Production readiness reviews | [`D4_4_apply_readiness_checklist.ipynb`](https://colab.research.google.com/github/SDAIAAcademy/ae-403/blob/main/labs/D4_4_apply_readiness_checklist.ipynb) |

The notebooks are generated from the percent-format sources in `labs/_src/` by `labs/_tools/py2nb.py` (`uv run python _tools/py2nb.py` from `labs/`), which also writes the solutions to `labs/solutions/`. Edit the sources, not the notebooks.
