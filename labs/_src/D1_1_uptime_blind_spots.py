# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain pandas or the telemetry fields; you decide what counts as an incident.

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
import matplotlib.pyplot as plt

# %% [markdown]
# ## 1 · Load the week and plot requests, probe and errors
#
# `telemetry_week.csv` has one row per minute and language: requests, server errors, the 95th
# percentile of first-token and per-token time, empty answers, and the sampled quality grade
# (`graded` answers checked, `passed` of them correct). `probe_week.csv` is the uptime check: one
# tiny English prompt a minute. Minutes count from the start of the week (day 0).

# %%
week = U.load("telemetry_week")
probe = U.load("probe_week")
print(week.head(4))
print("minutes:", week.minute.nunique(), "· probe failures:", int((probe.probe_ok == 0).sum()), "minutes")

per_min = week.groupby("minute").agg(requests=("requests", "sum"), errors=("errors", "sum")).reset_index()
fig, ax = plt.subplots(2, 1, figsize=(12, 4), sharex=True)
ax[0].plot(per_min.minute / 1440, per_min.requests, lw=0.5)
ax[0].set_ylabel("requests / min")
ax[1].plot(probe.minute / 1440, probe.probe_ok, lw=0.8, color="tab:green")
ax[1].set_ylabel("probe ok")
ax[1].set_xlabel("day")
plt.tight_layout()
plt.show()

# %% [markdown]
# **Look at** the probe line: it is green almost all week. Now look at what users got.
#
# ## 2 · Find the minutes where the probe was green and users were not
#
# ✏️ **Exercise** · Build one row per minute with a boolean `user_bad`, true when any of these
# held for users (not for the probe):
#
# - server errors above 5% of requests;
# - first-token p95 above 2,000 ms, or per-token p95 above 120 ms (the worst language that minute);
# - empty answers above 5% of requests (careful: `df.empty` is a pandas attribute, use `df["empty_answers"]`);
# - the 30-minute rolling pass rate of a language below 0.85, when at least 40 answers were graded in those 30 minutes.
#
# Then keep the minutes where `user_bad` and the probe was ok.

# %%
def user_bad_minutes(week: pd.DataFrame, probe: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    m = week.groupby("minute").agg(requests=("requests", "sum"), errors=("errors", "sum"),
                                   ttft=("ttft_p95_ms", "max"), tpot=("tpot_p95_ms", "max"),
                                   empty_answers=("empty_answers", "sum")).reset_index()
    quality_bad = pd.Series(False, index=m.index)
    for lang in ("ar", "en"):
        x = week[week.lang == lang].set_index("minute").sort_index()
        n = x.graded.rolling(30, min_periods=1).sum()
        rate = x.passed.rolling(30, min_periods=1).sum() / n
        quality_bad |= ((rate < 0.85) & (n >= 40)).values
    req = m.requests.clip(lower=1)
    m["user_bad"] = ((m.errors / req > 0.05) | (m.ttft > 2000) | (m.tpot > 120)
                     | (m["empty_answers"] / req > 0.05) | quality_bad)
    m = m.merge(probe, on="minute")
    return m[["minute", "user_bad", "probe_ok"]]
    # END SOLUTION

# %%
# Check, with a safety net: the cells below still run when the exercise is not done yet
try:
    minutes = user_bad_minutes(week, probe)
except NotImplementedError:
    minutes = U.reference("lab_1_1_minutes")
U.keep("lab_1_1_minutes", minutes)
missed = minutes[minutes.user_bad & (minutes.probe_ok == 1)]
U.ok(len(missed) > 250, f"{len(missed)} minutes where users had a bad service and the probe said all was well")

# %% [markdown]
# ## 3 · Group them into incidents with a start, a duration and a signal
#
# ✏️ **Exercise** · Join bad minutes separated by at most 10 good minutes (`U.runs(mask, gap=10)`),
# keep groups of at least 15 minutes, and give each one its day, its minute of the day, its
# duration and whether the probe failed at any point during it. Single-minute blips at night are
# noise from small numbers: the 15-minute rule drops them.

# %%
def incidents(minutes: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for a, b in U.runs(minutes.user_bad.values, gap=10):
        if b - a + 1 < 15:
            continue
        span = minutes.iloc[a:b + 1]
        start = int(span.minute.iloc[0])
        rows.append({"start": start, "day": start // 1440, "minute_of_day": start % 1440,
                     "minutes": b - a + 1, "probe_caught": bool((span.probe_ok == 0).any())})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    found = incidents(minutes)
except NotImplementedError:
    found = U.reference("lab_1_1_incidents")
U.keep("lab_1_1_incidents", found)
print(found)
U.ok(len(found) == 5, f"{len(found)} incidents in the week")
U.ok(int((~found.probe_caught).sum()) == 4, f"{int((~found.probe_caught).sum())} of them never turned the probe red")

# %% [markdown]
# ## 4 · Name the indicator that would have caught each one
#
# ✏️ **Exercise** · For each incident, say which signal was bad: `quality_ar`, `quality_en`,
# `ttft`, `tpot`, `empty`, `errors`. Read the rows of the incident and return the signal that
# was bad in most of its minutes.

# %%
def signal_of(week: pd.DataFrame, start: int, minutes: int) -> str:
    # BEGIN SOLUTION
    w = week[(week.minute >= start) & (week.minute < start + minutes)]
    m = w.groupby("minute").agg(requests=("requests", "sum"), errors=("errors", "sum"), ttft=("ttft_p95_ms", "max"),
                                tpot=("tpot_p95_ms", "max"), empty_answers=("empty_answers", "sum"))
    req = m.requests.clip(lower=1)
    score = {"errors": (m.errors / req > 0.05).mean(), "ttft": (m.ttft > 2000).mean(), "tpot": (m.tpot > 120).mean(),
             "empty": (m["empty_answers"] / req > 0.05).mean()}
    for lang in ("ar", "en"):
        x = w[w.lang == lang]
        rate = x.passed.sum() / max(x.graded.sum(), 1)
        score[f"quality_{lang}"] = 1.0 if rate < 0.85 else 0.0
    return max(score, key=score.get)
    # END SOLUTION

# %%
try:
    found["signal"] = [signal_of(week, r.start, r.minutes) for r in found.itertuples()]
except NotImplementedError:
    found = U.reference("lab_1_1_signals")
U.keep("lab_1_1_signals", found)
print(found)
U.ok(sorted(found.signal) == sorted(["quality_ar", "ttft", "tpot", "empty", "errors"]),
     "each incident has its own signal; only the outage shows in errors")

# %% [markdown]
# **Look at** the four incidents the probe missed. The probe sends one short English prompt: it
# cannot see Arabic quality, a queue that only long prompts wait in, slow streaming or empty
# answers. Each of the four needs its own indicator: that is the work of Lab 1.2.
#
# ✱ **Stretch** · Repeat the search for Arabic and English separately and compare.

# %% [markdown]
# ## Check yourself
#
# 1. Why does a synthetic probe report the evening queueing incident as healthy?
#    <details><summary>Answer</summary>Its prompt is tiny and arrives once a minute: it waits in the queue for very little and needs no long prefill, so its first token is fast while users with retrieval-sized prompts wait seconds.</details>
# 2. Why must the quality rule require at least 40 graded answers in the window?
#    <details><summary>Answer</summary>At night only a handful of answers are graded; one or two failures then look like a collapse. A minimum sample keeps noise from paging.</details>
# 3. Which incident would an uptime objective of 99.9% have counted against the service?
#    <details><summary>Answer</summary>Only the 12-minute outage. The other four cost users more minutes but leave availability untouched.</details>
#
# **Carry forward** · The five incidents are in `data/reference/lab_1_1_signals.json`; Lab 1.2 defines the indicators that see them.
