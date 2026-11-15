# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the gateway code; the cap, the classes and the shedding order are yours to decide and defend.

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
import pandas as pd

# %% [markdown]
# ## 1 · Replay the overload trace with no admission control
#
# `overload_trace.csv` is one replica's share of a sale-day surge: requests a second per class,
# 20 minutes long, with a 10-minute spike to about 1.7 times the replica's goodput.
#
# | Class | Traffic | First-token objective |
# |---|---|---|
# | P1 | tracking for a parcel out for delivery: the customer is at the door | 1,500 ms for 95% |
# | P2 | general help questions | 1,500 ms for 95% |
# | P3 | staff summaries of long complaint threads (batch, can wait) | 30 s |
#
# The operating point from Lab 2.1 is 16 requests in flight per replica (loaded below).

# %%
trace = U.load("overload_trace")
OBJ = {"P1": 1500, "P2": 1500, "P3": 30000}
try:
    op = U.reference("lab_2_1_operating_point")
except FileNotFoundError:
    op = {"concurrency": 16}
engine = U.Engine()
if U.QUICK:
    trace = trace[trace.second < 900]
base = engine.replay(trace)
print(U.class_report(base, OBJ).to_string(index=False))

# %% [markdown]
# **Look at** the first-token p95: minutes, for every class. With no admission, the engine admits
# everything into its own queue, the cache overflows, requests are preempted and recomputed, and
# all three classes miss together. This is the retry storm's breeding ground (Lab 2.4).
#
# ## 2 · Add the concurrency cap and a bounded queue
#
# ✏️ **Exercise** · Build a `U.Gateway` with the cap at the operating point and a bounded queue
# per class (20 for each class), but no priorities in the queues' sizes yet. Replay.

# %%
def cap_only(cap: int):
    # BEGIN SOLUTION
    return U.Gateway(cap=cap, queue_limits={"P1": 20, "P2": 20, "P3": 20})
    # END SOLUTION

# %%
try:
    capped = engine.replay(trace, gateway=cap_only(op["concurrency"]))
    rep_cap = U.class_report(capped, OBJ)
except NotImplementedError:
    rep_cap = U.reference("lab_2_2_cap_only")
U.keep("lab_2_2_cap_only", rep_cap)
print(rep_cap.to_string(index=False))
U.ok(rep_cap.set_index("cls").loc["P1", "met_objective"] < 0.95, "a cap alone protects the engine, not the customers at the door")

# %% [markdown]
# ## 3 · Add priority classes and shed from the lowest
#
# ✏️ **Exercise** · Configure the gateway so that P1 keeps its objective during the spike:
# - release P1 first, then P2, then P3 (the gateway's default order);
# - limit P3 to 2 requests in flight (`class_caps`): its prompts are three times longer and fill the cache;
# - keep P1's queue long (20) and P2's and P3's short (6 and 4), so P2 and P3 are shed first;
# - drop a P2 request that has waited more than 1 second (`deadline_s`): it would miss its objective anyway.

# %%
def priority_gateway(cap: int):
    # BEGIN SOLUTION
    return U.Gateway(cap=cap, queue_limits={"P1": 20, "P2": 6, "P3": 4},
                     class_caps={"P3": 2}, deadline_s={"P2": 1.0})
    # END SOLUTION

# %%
try:
    shed = engine.replay(trace, gateway=priority_gateway(op["concurrency"]))
    rep_pri = U.class_report(shed, OBJ)
except NotImplementedError:
    rep_pri = U.reference("lab_2_2_priority")
U.keep("lab_2_2_priority", rep_pri)
print(rep_pri.to_string(index=False))

# %% [markdown]
# ## 4 · Check each class against its objective
#
# ✏️ **Exercise** · Return, per class, whether it met its objective (at least 95% of offered
# requests within the first-token limit for P1 and P2), and the share shed. Then write one
# sentence per class for the service owner.

# %%
def verdict(rep: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    out = rep.copy()
    out["shed_share"] = (out.shed / out.offered).round(3)
    out["meets"] = out.met_objective >= 0.95
    out["for_the_owner"] = [
        "keeps its objective through the spike" if (r.meets) else
        ("sheds early and keeps answered requests fast; retry after the spike" if r.cls == "P2" else
         "deferred: batch summaries resume when the spike ends")
        for r in out.itertuples()]
    return out[["cls", "offered", "shed_share", "met_objective", "meets", "for_the_owner"]]
    # END SOLUTION

# %%
try:
    final = verdict(rep_pri)
except NotImplementedError:
    final = U.reference("lab_2_2_verdict")
U.keep("lab_2_2_verdict", final)
print(final.to_string(index=False))
U.ok(bool(final.set_index("cls").loc["P1", "meets"]), "priority traffic meets its objective through the overload replay")

# %% [markdown]
# **Look at** P2: it pays for P1. That is the decision you defend: which users wait, which are
# told "try again shortly", and why. Shedding is a design choice written in advance, not an
# accident of the queue.
#
# ✱ **Stretch** · Shed by deadline for P1 as well: drop a queued P1 request after 1.2 seconds. Does P1 do better or worse?

# %% [markdown]
# ## Check yourself
#
# 1. Why does a cap at the operating point not protect P1 by itself?
#    <details><summary>Answer</summary>The queue in front of the cap is first come, first served: P1 waits behind P2 and long P3 requests.</details>
# 2. Why does P3 get its own in-flight limit?
#    <details><summary>Answer</summary>Its prompts are long; a few of them fill the key-value cache and slow every other request's first token.</details>
# 3. Why shed a request at the gateway instead of letting it time out in the engine?
#    <details><summary>Answer</summary>A shed request costs almost nothing and returns at once with a clear message; a timed-out one used capacity and still failed.</details>
#
# **Carry forward** · The gateway settings are in `data/reference/lab_2_2_verdict.json`; Lab 2.4 reuses the idea against a retry storm.
