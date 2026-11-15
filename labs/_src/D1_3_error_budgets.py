# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may check your arithmetic; it does not set the objectives or the policy thresholds.

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
# ## 1 · Write the four objectives with their windows
#
# `telemetry_month.csv`: 30 days in five-minute slots, per language: `valid` requests, `ok`
# (served), `ttft_good` (first token within 1,500 ms), `graded` and `passed` answers.
#
# ✏️ **Exercise** · Write Athar's objectives as data: name, target, the indicator's good and valid
# columns, and the language slice when there is one. Use a rolling 30-day window for all four:
# availability 99.5%, first token within 1,500 ms for 95% of served requests, and answer quality
# 95% for each language separately.

# %%
def objectives() -> list[dict]:
    # BEGIN SOLUTION
    return [
        {"name": "availability", "target": 0.995, "good": "ok", "valid": "valid", "lang": None},
        {"name": "ttft", "target": 0.95, "good": "ttft_good", "valid": "ok", "lang": None},
        {"name": "quality_ar", "target": 0.95, "good": "passed", "valid": "graded", "lang": "ar"},
        {"name": "quality_en", "target": 0.95, "good": "passed", "valid": "graded", "lang": "en"},
    ]
    # END SOLUTION

# %%
try:
    OBJ = objectives()
except NotImplementedError:
    OBJ = U.reference("lab_1_3_objectives")
U.keep("lab_1_3_objectives", OBJ)
month = U.load("telemetry_month")
print(pd.DataFrame(OBJ))

# %% [markdown]
# ## 2 · Compute the budget and what the month burned
#
# The error budget is the share of valid events allowed to be bad: `1 - target`. ✏️ **Exercise** ·
# For each objective return the indicator over the month, the budget in events, the bad events
# and the share of the budget burned.

# %%
def budget(month: pd.DataFrame, o: dict) -> dict:
    # BEGIN SOLUTION
    x = month if o["lang"] is None else month[month.lang == o["lang"]]
    valid, good = int(x[o["valid"]].sum()), int(x[o["good"]].sum())
    allowed = (1 - o["target"]) * valid
    bad = valid - good
    return {"objective": o["name"], "indicator": round(good / valid, 5), "budget_events": round(allowed),
            "bad_events": bad, "burned": round(bad / allowed, 3), "remaining": round(1 - bad / allowed, 3)}
    # END SOLUTION

# %%
try:
    report = pd.DataFrame([budget(month, o) for o in OBJ])
except NotImplementedError:
    report = U.reference("lab_1_3_budget")
U.keep("lab_1_3_budget", report)
print(report)
U.ok(report.set_index("objective").loc["quality_ar", "remaining"] < 0.25, "Arabic quality has less than a quarter of its budget left")

# %% [markdown]
# ## 3 · Find the week that burned most and why
#
# ✏️ **Exercise** · Bad events per week (days 1 to 7 are week 1) for each objective. Then read
# `month` around the worst week to say what happened: an outage, slow evenings, a language drop.

# %%
def weekly_bad(month: pd.DataFrame, OBJ: list[dict]) -> pd.DataFrame:
    # BEGIN SOLUTION
    m = month.assign(week=(month.day - 1) // 7 + 1)
    out = {}
    for o in OBJ:
        x = m if o["lang"] is None else m[m.lang == o["lang"]]
        g = x.groupby("week")[[o["valid"], o["good"]]].sum()
        out[o["name"]] = g[o["valid"]] - g[o["good"]]
    return pd.DataFrame(out).reset_index()
    # END SOLUTION

# %%
try:
    weeks = weekly_bad(month, OBJ)
except NotImplementedError:
    weeks = U.reference("lab_1_3_weeks")
U.keep("lab_1_3_weeks", weeks)
print(weeks)
worst = weeks.set_index("week")[["ttft", "quality_ar"]].sum(axis=1).idxmax()
U.ok(worst == 3, f"week {worst} burned most first-token and Arabic quality budget")
d = month[(month.day.between(15, 21))].groupby("day")[["ok", "ttft_good"]].sum()
print("week 3, share within 1,500 ms by day:\n", (d.ttft_good / d.ok).round(3).to_dict())

# %% [markdown]
# ## 4 · Write the release policy and decide five requests
#
# ✏️ **Exercise** · Write `decide(request, remaining)` where `remaining` maps each objective to
# its remaining budget share. Policy: a security or reliability fix always goes; otherwise look
# at the objectives the change touches and take the lowest remaining budget among them:
# 50% or more `go`, 25% to 50% `go with canary`, below 25% `freeze`. Return the decision and the
# reason in one sentence.

# %%
def decide(request: dict, remaining: dict) -> tuple[str, str]:
    # BEGIN SOLUTION
    if request["kind"] in ("security", "reliability"):
        return "go", f"{request['kind']} fixes are exempt from the freeze"
    touched = request["touches"].split()
    name = min(touched, key=lambda t: remaining[t])
    low = remaining[name]
    if low >= 0.50:
        return "go", f"lowest remaining budget is {name} at {low:.0%}"
    if low >= 0.25:
        return "go with canary", f"{name} has {low:.0%} left: release behind a canary"
    return "freeze", f"{name} has {low:.0%} of its budget left: only fixes until it recovers"
    # END SOLUTION

# %%
requests = U.load("release_requests")
remaining = dict(zip(report.objective, report.remaining))
try:
    decisions = pd.DataFrame([{"id": r.id, "change": r.change, **dict(zip(("decision", "reason"), decide(r._asdict(), remaining)))}
                              for r in requests.itertuples()])
except NotImplementedError:
    decisions = U.reference("lab_1_3_decisions")
U.keep("lab_1_3_decisions", decisions)
print(decisions.to_string(index=False))
U.ok(list(decisions.decision) == ["freeze", "go", "go", "go", "freeze"], "the model update and the Arabic index refresh wait")

# %% [markdown]
# **Look at** RR-1: a new model version is the change most likely to *fix* Arabic quality, and
# the policy freezes it. Policies need an escape the owner can use on evidence: Lab 3.3's canary.
#
# ✱ **Stretch** · Add a policy line for a budget spent by a dependency, not by a release.

# %% [markdown]
# ## Check yourself
#
# 1. The month's availability is 99.82% against 99.5%. How much of the budget is left?
#    <details><summary>Answer</summary>About 64%: 0.18% bad out of the 0.5% allowed is 36% burned.</details>
# 2. Why does a 95% quality objective leave little room when Arabic normally passes 97.2%?
#    <details><summary>Answer</summary>Normal operation already burns more than half the budget (2.8% of 5%); one two-day drop spends the rest.</details>
# 3. Why is a freeze decided per objective, not for the whole service?
#    <details><summary>Answer</summary>A change that only touches an objective with budget left (RR-3) carries no risk to the one that is exhausted.</details>
#
# **Carry forward** · The objectives are in `data/reference/lab_1_3_objectives.json`; Day 3 alerts on the quality one.
