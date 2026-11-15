# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the simulator or the plots; the operating point and the margin are your decision.

# %%
import os, sys, subprocess
from pathlib import Path

IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    REPO_URL = "https://github.com/SDAIAAcademy/ae-403.git"
    if not Path("/content/ae-403").exists():
        subprocess.run(["git", "clone", "-q", REPO_URL, "/content/ae-403"], check=True)
    os.chdir("/content/ae-403/labs")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements-colab.txt"], check=True)
else:
    while not Path("_tools").exists() and Path.cwd() != Path.cwd().parent:
        os.chdir("..")  # solutions/ notebooks run from labs/
sys.path.insert(0, os.getcwd())
import relia as U
import math
import pandas as pd
import matplotlib.pyplot as plt

# %% [markdown]
# ## 1 · Run one load step and read its latencies
#
# `U.Engine()` simulates one replica of Athar's self-hosted engine: continuous batching, a
# key-value cache of 40,000 tokens, retrieval-sized prompts (about 900 to 2,800 tokens) and short
# answers. `closed_loop(c)` keeps `c` requests in flight, like a load generator in concurrency
# mode (inference-perf, k6 or Locust do the same against a real engine). Each row is a request.

# %%
engine = U.Engine()
DURATION, WARMUP = 120, 20
step = engine.closed_loop(8, duration_s=DURATION, warmup_s=WARMUP)
print(step[["cls", "lang", "prompt", "out", "ttft_ms", "tpot_ms", "preempted"]].head())
print("first-token p95:", step.ttft_ms.quantile(0.95), "ms · per-token p95:", step.tpot_ms.quantile(0.95), "ms")
print("goodput:", U.goodput(step, DURATION - WARMUP), "requests a second within 1,500 ms and 100 ms a token")

# %% [markdown]
# ## 2 · Sweep concurrency and compute goodput
#
# ✏️ **Exercise** · For each concurrency level, run the engine and return one row: concurrency,
# throughput (served requests a second), goodput, first-token p95, per-token p95 and preemptions.
# Goodput counts only requests that met both thresholds.

# %%
LEVELS = U.pick([1, 2, 4, 8, 12, 16, 20, 24, 32, 48, 64], [1, 4, 8, 12, 16, 20, 24, 32])


def sweep(engine, levels) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for c in levels:
        d = engine.closed_loop(c, duration_s=DURATION, warmup_s=WARMUP)
        secs = DURATION - WARMUP
        rows.append({"concurrency": c, "throughput": round((d.status == 200).sum() / secs, 3),
                     "goodput": U.goodput(d, secs), "ttft_p95_ms": round(d.ttft_ms.quantile(0.95)),
                     "tpot_p95_ms": round(d.tpot_ms.quantile(0.95), 1), "preempted": int(d.preempted.sum())})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    curve = sweep(engine, LEVELS)
except NotImplementedError:
    curve = U.reference("lab_2_1_curve")
U.keep("lab_2_1_curve", curve)
print(curve.to_string(index=False))
fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(curve.concurrency, curve.throughput, marker="o", label="throughput")
ax.plot(curve.concurrency, curve.goodput, marker="o", label="goodput")
ax.set_xlabel("requests in flight")
ax.set_ylabel("requests a second")
ax.legend()
plt.show()
U.ok(curve.goodput.iloc[-1] < 0.5 * curve.goodput.max(), "past the knee, throughput holds but goodput collapses")

# %% [markdown]
# ## 3 · Find the knee and choose the operating point
#
# ✏️ **Exercise** · Choose the highest concurrency whose goodput is at least 95% of the peak
# goodput **and** whose first-token p95 is at most 80% of the 1,500 ms threshold. The 20% kept
# below the threshold is headroom for prompts longer than today's.

# %%
def operating_point(curve: pd.DataFrame) -> dict:
    # BEGIN SOLUTION
    peak = curve.goodput.max()
    ok_rows = curve[(curve.goodput >= 0.95 * peak) & (curve.ttft_p95_ms <= 0.8 * U.OBJ_TTFT_MS)]
    row = ok_rows.sort_values("concurrency").iloc[-1]
    return {"concurrency": int(row.concurrency), "goodput": float(row.goodput), "ttft_p95_ms": float(row.ttft_p95_ms),
            "peak_goodput": float(peak)}
    # END SOLUTION

# %%
try:
    op = operating_point(curve)
except NotImplementedError:
    op = U.reference("lab_2_1_operating_point")
U.keep("lab_2_1_operating_point", op)
print(op)
U.ok(op["concurrency"] == 16, f"operating point {op['concurrency']} requests in flight per replica")

# %% [markdown]
# ## 4 · Replicas and margin for the busiest hour
#
# `traffic_hourly.csv` holds a month of request rates per hour. ✏️ **Exercise** · Find the busiest
# hour, then the replicas needed so that the busiest hour uses at most 80% of the goodput at the
# operating point (25% headroom). Report the margin: total goodput over the busiest hour's rate,
# minus one.

# %%
traffic = U.load("traffic_hourly")


def replicas_for_busiest_hour(traffic: pd.DataFrame, op: dict, headroom: float = 0.25) -> dict:
    # BEGIN SOLUTION
    peak = traffic.loc[traffic.rps.idxmax()]
    need = math.ceil(peak.rps * (1 + headroom) / op["goodput"])
    return {"busiest_day": int(peak.day), "busiest_hour": int(peak.hour), "busiest_rps": float(peak.rps),
            "typical_daily_peak_rps": float(traffic.groupby("day").rps.max().median()),
            "replicas": need, "margin": round(float(need * op["goodput"] / peak.rps - 1), 3)}
    # END SOLUTION

# %%
try:
    plan = replicas_for_busiest_hour(traffic, op)
except NotImplementedError:
    plan = U.reference("lab_2_1_plan")
U.keep("lab_2_1_plan", plan)
print(plan)
U.ok(plan["margin"] >= 0.25, f"{plan['replicas']} replicas leave a {plan['margin']:.0%} margin at the busiest hour")

# %% [markdown]
# **Look at** the typical daily peak against the busiest hour: sizing for an ordinary evening
# would have left the sale day without capacity. The busiest hour sets the replicas; the
# operating point sets the admission limit of Lab 2.2.
#
# ✱ **Stretch** · Repeat the sweep with `engine.closed_loop(c, long_prompts=True)` and see the knee move.

# %% [markdown]
# ## Check yourself
#
# 1. Why does throughput stay flat past the knee while goodput falls to zero?
#    <details><summary>Answer</summary>The engine keeps finishing requests, but each one has waited in the queue longer than the first-token threshold, so it no longer counts as good.</details>
# 2. Why keep the operating point below the concurrency with the highest goodput?
#    <details><summary>Answer</summary>At the peak the first-token p95 is already close to the threshold; a small rise in prompt length or traffic pushes it over. Headroom buys time to scale.</details>
# 3. What changes when Arabic prompts are 35% longer in tokens?
#    <details><summary>Answer</summary>They use more prefill and more cache, so the knee arrives at a lower concurrency for Arabic-heavy traffic: sweep with the real language mix.</details>
#
# **Carry forward** · The operating point (`data/reference/lab_2_1_operating_point.json`) becomes the concurrency cap in Lab 2.2.
