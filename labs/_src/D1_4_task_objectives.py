# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the session format; the indicators and the objectives are yours.

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
# ## 1 · Read the sessions and their steps
#
# Athar's redelivery flow books a new delivery slot in four steps: `identify_parcel`,
# `check_eligibility`, `offer_slots`, `confirm_booking`. Each session lists its model and tool
# calls (`step`, `ok`, `tokens`) and its `outcome`: `completed`, `escalated` (handed to a
# person) or `abandoned`. The engine's cost is SAR 0.002 per 1,000 tokens (a synthetic internal
# rate for the self-hosted model).

# %%
sessions = U.load("sessions")
print(len(sessions), "sessions; the first:")
print(sessions[0])
SAR_PER_1K = 0.002

# %% [markdown]
# ## 2 · Per-call success against per-task completion
#
# ✏️ **Exercise** · Return the share of calls with `ok` true, and the share of sessions that
# completed. The first is what a request dashboard shows.

# %%
def call_and_task_success(sessions: list[dict]) -> dict:
    # BEGIN SOLUTION
    calls = [c for s in sessions for c in s["calls"]]
    return {"per_call": round(sum(c["ok"] for c in calls) / len(calls), 4),
            "per_task": round(sum(s["outcome"] == "completed" for s in sessions) / len(sessions), 4)}
    # END SOLUTION

# %%
try:
    succ = call_and_task_success(sessions)
except NotImplementedError:
    succ = U.reference("lab_1_4_success")
U.keep("lab_1_4_success", succ)
print(succ)
U.ok(succ["per_call"] - succ["per_task"] > 0.15, "per-call success hides one booking in five that never happened")

# %% [markdown]
# ## 3 · Cost per completed booking, with the loops
#
# ✏️ **Exercise** · Total cost of all sessions divided by completed bookings (failed sessions
# cost too). Then the same for the sessions with more than 10 calls, which loop on `offer_slots`.

# %%
def cost_per_completed(sessions: list[dict]) -> dict:
    # BEGIN SOLUTION
    def cost(s):
        return sum(c["tokens"] for c in s["calls"]) / 1000 * SAR_PER_1K
    total = sum(cost(s) for s in sessions)
    done = sum(s["outcome"] == "completed" for s in sessions)
    loops = [s for s in sessions if len(s["calls"]) > 10]
    return {"sar_per_completed": round(total / done, 5),
            "sessions_looping": len(loops),
            "loop_share_of_cost": round(sum(cost(s) for s in loops) / total, 3),
            "loop_completion": round(sum(s["outcome"] == "completed" for s in loops) / max(len(loops), 1), 3)}
    # END SOLUTION

# %%
try:
    cost = cost_per_completed(sessions)
except NotImplementedError:
    cost = U.reference("lab_1_4_cost")
U.keep("lab_1_4_cost", cost)
print(cost)
U.ok(cost["loop_share_of_cost"] > 2 * cost["sessions_looping"] / len(sessions), "looping sessions cost far more than their share")

# %% [markdown]
# ## 4 · Escalation rate and objectives for the flow
#
# ✏️ **Exercise** · Compute the escalation and abandonment rates by language. Then write the
# flow's objectives as a list of dictionaries: completion, cost per completed booking and
# escalation, each with a target you can defend from these numbers and a sentence of reason.

# %%
def flow_rates(sessions: list[dict]) -> pd.DataFrame:
    # BEGIN SOLUTION
    df = pd.DataFrame([{"lang": s["lang"], "outcome": s["outcome"]} for s in sessions])
    return (pd.crosstab(df.lang, df.outcome, normalize="index").round(3).reset_index())
    # END SOLUTION


def flow_objectives() -> list[dict]:
    # BEGIN SOLUTION
    return [
        {"indicator": "completion", "target": ">= 85% of sessions over 30 days, per language",
         "reason": "today 79%; loops and abandoned confirmations are fixable, ineligible parcels are not"},
        {"indicator": "cost per completed booking", "target": "<= SAR 0.012",
         "reason": "today about SAR 0.0133; ending the slot loop removes most of the excess"},
        {"indicator": "escalation", "target": "<= 9%, and every escalation reaches a person",
         "reason": "escalation is the right answer for ineligible parcels; a lost hand-over is the failure"},
    ]
    # END SOLUTION

# %%
try:
    rates = flow_rates(sessions)
    flow_obj = flow_objectives()
except NotImplementedError:
    rates, flow_obj = U.reference("lab_1_4_rates"), U.reference("lab_1_4_objectives")
U.keep("lab_1_4_rates", rates)
U.keep("lab_1_4_objectives", flow_obj)
print(rates)
print(pd.DataFrame(flow_obj).to_string(index=False))
U.ok(len(flow_obj) == 3 and all(o["reason"] for o in flow_obj), "three objectives, each with a reason")

# %% [markdown]
# **Look at** escalation: it is not a failure to be pushed to zero. A flow that never escalates
# books parcels that are not eligible. The objective is on the hand-over, not on the count.
#
# ✱ **Stretch** · Find the step where most abandoned sessions stop.

# %% [markdown]
# ## Check yourself
#
# 1. Why can per-call success be 98.9% while one booking in five fails?
#    <details><summary>Answer</summary>Retried tool errors succeed on the second call, and most failed sessions fail on calls that worked: the customer left, or the flow looped.</details>
# 2. Why divide total cost by completed bookings, not by sessions?
#    <details><summary>Answer</summary>The service is paid for outcomes; abandoned sessions cost tokens and deliver nothing, so they belong in the numerator.</details>
# 3. What makes escalation a quality signal rather than a failure?
#    <details><summary>Answer</summary>Some parcels cannot be rebooked online; the right answer is a person. The failure is an escalation nobody picks up.</details>
#
# **Carry forward** · The flow's objectives are in `data/reference/lab_1_4_objectives.json`; the capstone asks for one multi-step objective.
