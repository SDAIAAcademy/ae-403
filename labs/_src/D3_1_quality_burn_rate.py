# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain rolling windows or the rule syntax; the windows, burn rates and slices are your choice.

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
import yaml
import matplotlib.pyplot as plt

# %% [markdown]
# ## 1 · Quality burn rate per five minutes
#
# `replay_day.csv` replays one day of Athar in five-minute slots (slot 0 to 287), per language:
# requests, graded answers and passed answers. The quality objective is 95% per language over
# 30 days, so the budget is 5% of graded answers. Burn rate 1 spends the budget exactly in 30
# days; burn rate 14.4 spends 2% of it in an hour.
#
# ✏️ **Exercise** · Return a frame indexed by slot with the bad and graded counts for `"all"`
# traffic and for each language, and the burn rate of each over a single slot.

# %%
day = U.load("replay_day")
OBJECTIVE = 0.95


def per_slot(day: pd.DataFrame) -> dict:
    # BEGIN SOLUTION
    out = {}
    for name, x in [("all", day), ("ar", day[day.lang == "ar"]), ("en", day[day.lang == "en"])]:
        g = x.groupby("slot")[["graded", "passed"]].sum()
        g["bad"] = g.graded - g.passed
        g["burn"] = (g.bad / g.graded) / (1 - OBJECTIVE)
        out[name] = g
    return out
    # END SOLUTION

# %%
try:
    slots = per_slot(day)
except NotImplementedError:
    slots = {k: pd.DataFrame(v["rows"], columns=v["columns"]).set_index("slot") for k, v in U.reference("lab_3_1_slots").items()}
U.keep("lab_3_1_slots", {k: {"columns": ["slot"] + list(v.columns), "rows": v.reset_index().values.tolist()} for k, v in slots.items()})
fig, ax = plt.subplots(figsize=(10, 3))
for k in ("all", "ar", "en"):
    ax.plot(slots[k].index, slots[k].burn.rolling(6, min_periods=1).mean(), label=k)
ax.axhline(6, ls="--", lw=0.8)
ax.set_xlabel("five-minute slot")
ax.set_ylabel("burn rate (30 min)")
ax.legend()
plt.show()

# %% [markdown]
# ## 2 · Two windows and two burn rates
#
# ✏️ **Exercise** · Write `fires(g, long, short, rate)`: a boolean series, true in a slot when the
# burn rate over the last `long` slots **and** over the last `short` slots both exceed `rate`
# (`U.burn_rate(bad, total, objective, window)`). The long window proves the problem is big; the
# short one proves it is still happening, so the alert also stops quickly.

# %%
def fires(g: pd.DataFrame, long: int, short: int, rate: float) -> pd.Series:
    # BEGIN SOLUTION
    lw = U.burn_rate(g.bad, g.graded, OBJECTIVE, long)
    sw = U.burn_rate(g.bad, g.graded, OBJECTIVE, short)
    return (lw > rate) & (sw > rate)
    # END SOLUTION

# %%
TIERS = {"page: 1 h and 5 min at 14.4": (12, 1, 14.4), "ticket: 6 h and 30 min at 6": (72, 6, 6.0),
         "quality: 1 h and 5 min at 6": (12, 1, 6.0)}


def first_fire(g, tier, name):
    try:
        f = fires(g, *TIERS[tier])
    except NotImplementedError:
        return U.reference("lab_3_1_detection")[tier][name]
    return int(f.idxmax()) if f.any() else None

# %% [markdown]
# ## 3 · Replay the day: when does it fire?
#
# The two workbook tiers on all traffic first, as most teams configure them.

# %%
detect = {}
for tier in TIERS:
    detect[tier] = {}
    for name in ("all", "ar", "en"):
        detect[tier][name] = first_fire(slots[name], tier, name)
U.keep("lab_3_1_detection", detect)
print(pd.DataFrame(detect).T)
U.ok(detect["page: 1 h and 5 min at 14.4"]["all"] is None and detect["ticket: 6 h and 30 min at 6"]["all"] is None,
     "on all traffic neither workbook tier ever fires")

# %% [markdown]
# ## 4 · Slice by language and locate the regression
#
# ✏️ **Exercise** · Find the first slot from which the Arabic error rate over a rolling 30 minutes
# stays above twice the budget (10%) for at least an hour. Then look it up in `deploy_log.csv`.

# %%
def regression_start(g: pd.DataFrame) -> int:
    # BEGIN SOLUTION
    rate = g.bad.rolling(6, min_periods=1).sum() / g.graded.rolling(6, min_periods=1).sum()
    high = rate > 2 * (1 - OBJECTIVE)
    for a, b in U.runs(high.values):
        if b - a + 1 >= 12:
            return int(g.index[a])   # a step change: the rolling rate crosses within a slot or two
    return None
    # END SOLUTION

# %%
try:
    start = regression_start(slots["ar"])
except NotImplementedError:
    start = U.reference("lab_3_1_start")
U.keep("lab_3_1_start", start)
deploys = U.load("deploy_log")
near = deploys.iloc[(deploys.slot - start).abs().argsort()[:1]]
print("regression starts around slot", start)
print(near.to_string(index=False))
U.ok(abs(start - 130) <= 3, "the Arabic regression starts with the model update at slot 130")
q = detect["quality: 1 h and 5 min at 6"]["ar"]
t = detect["ticket: 6 h and 30 min at 6"]["ar"]
print(f"detection after the update: quality tier {(q - 130) * 5} min, ticket tier {(t - 130) * 5} min")

# %% [markdown]
# **Look at** the three answers: the averaged alert never fires, the per-language ticket tier
# takes hours, and a quality tier with a one-hour window fires within the hour. Quality
# regressions after a model update are step changes: they need short windows and slices.
#
# ✱ **Stretch** · The rule below is Prometheus text. Count how many times the quality tier would
# page over the month of `telemetry_month.csv`.

# %%
rule = {"groups": [{"name": "athar-quality", "rules": [{
    "alert": "AtharArabicQualityBurn",
    "expr": "(athar:quality_bad:ratio_rate1h{lang=\"ar\"} > (6 * 0.05)) and (athar:quality_bad:ratio_rate5m{lang=\"ar\"} > (6 * 0.05))",
    "labels": {"severity": "page"},
    "annotations": {"summary": "Arabic answer quality is burning its 30-day budget six times too fast"}}]}]}
text = yaml.safe_dump(rule, sort_keys=False, allow_unicode=True)
print(text)
U.ok(yaml.safe_load(text) == rule, "the rule is valid YAML")

# %% [markdown]
# ## Check yourself
#
# 1. Why does an alert on all traffic miss a regression that affects 60% of the traffic?
#    <details><summary>Answer</summary>The English slice keeps the average burn below the threshold: about 5 times overall against 8 in Arabic, after the update.</details>
# 2. Why two windows?
#    <details><summary>Answer</summary>The long window shows enough budget is being spent to matter; the short one shows it is still happening, so the alert stops soon after the fix.</details>
# 3. Why is the workbook's 14.4 burn rate out of reach for this regression?
#    <details><summary>Answer</summary>With a 5% budget, 14.4 means 72% of answers failing; a regression that fails 38% of Arabic answers never gets there.</details>
#
# **Carry forward** · The regression slot and the rule feed Lab 3.2's game day, which starts with this page.
