# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the log fields or the interval formula; the exclusions and their reasons are yours.

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
# ## 1 · Read the request log and its fields
#
# One row per request to Athar over one day. `client` is `app`, `web` or `probe` (the uptime
# check). `status`: 200 served; 499 the user closed the chat before the answer; 429 rate limited
# by the gateway; 500 and 503 server failures. `ttft_ms` and `tpot_ms` exist for served requests.
# About 6% of served answers are graded by the quality team (`graded`, `passed`).

# %%
log = U.load("requests_day")
print(log.client.value_counts().to_dict())
print(log.status.value_counts().to_dict())
naive = (log.status == 200).mean()
print(f"naive availability over every row: {naive:.4f}")

# %% [markdown]
# ## 2 · Write the valid-event filter and its exclusions
#
# An indicator is good events over valid events. ✏️ **Exercise** · Return the valid requests and
# a dictionary of exclusions, each with a one-line reason. Decide: is the probe a user? Is a 499
# the service's fault? Is a 429 from Athar's own gateway a failure the user felt?

# %%
def valid_requests(log: pd.DataFrame):
    # BEGIN SOLUTION
    exclusions = {
        "probe": "synthetic traffic: a tiny English prompt that measures the probe, not users",
        "499": "the user left before the answer; no answer was owed (counted separately as an abandonment signal)",
    }
    valid = log[(log.client != "probe") & (log.status != 499)]
    return valid, exclusions
    # END SOLUTION

# %%
try:
    valid, exclusions = valid_requests(log)
except NotImplementedError:
    exclusions = U.reference("lab_1_2_exclusions")
    valid = log[(log.client != "probe") & (log.status != 499)]
U.keep("lab_1_2_exclusions", exclusions)
for k, v in exclusions.items():
    print(f"excluded {k}: {v}")
U.ok(not (valid.client == "probe").any(), "no probe request is counted as a user")
U.ok((valid.status == 429).any(), "429 stays valid: the user asked and Athar refused")

# %% [markdown]
# ## 3 · Latency indicators: first token and per token
#
# ✏️ **Exercise** · Among valid requests that were served, the share with first token within
# 1,500 ms, and the share with per-token time within 100 ms. A request that failed has no latency:
# it counts in availability, not here.

# %%
def latency_indicators(valid: pd.DataFrame) -> dict:
    # BEGIN SOLUTION
    served = valid[valid.status == 200]
    return {"ttft_within_1500ms": round(float((served.ttft_ms <= 1500).mean()), 4),
            "tpot_within_100ms": round(float((served.tpot_ms <= 100).mean()), 4)}
    # END SOLUTION

# %%
try:
    lat = latency_indicators(valid)
except NotImplementedError:
    lat = U.reference("lab_1_2_latency")
U.keep("lab_1_2_latency", lat)
print(lat)
with_probe = (log[log.status == 200].ttft_ms <= 1500).mean()
print(f"the same first-token share with the probe left in: {with_probe:.4f}")

# %% [markdown]
# ## 4 · Availability as good over valid requests

# %%
def availability(valid: pd.DataFrame) -> float:
    # BEGIN SOLUTION
    return round(float((valid.status == 200).mean()), 4)
    # END SOLUTION

# %%
try:
    avail = availability(valid)
except NotImplementedError:
    avail = U.reference("lab_1_2_availability")
U.keep("lab_1_2_availability", avail)
users_and_probe = log[log.status != 499]
print(f"availability {avail:.4f} · naive, cancels counted as failures {naive:.4f} · with the probe counted as a user {(users_and_probe.status == 200).mean():.4f}")
U.ok(naive < avail < (users_and_probe.status == 200).mean(), "each wrong filter moves the number: cancels pull it down, the probe pushes it up")

# %% [markdown]
# ## 5 · Quality grade by language, with a 95% interval
#
# ✏️ **Exercise** · For each language, the pass rate of graded answers and its Wilson interval
# (`U.wilson(passed, n)`). A pass rate without its interval invites an argument nobody can settle.

# %%
def quality_by_language(valid: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for lang, g in valid[valid.graded == 1].groupby("lang"):
        n, p = len(g), int(g.passed.sum())
        lo, hi = U.wilson(p, n)
        rows.append({"lang": lang, "graded": n, "passed": p, "rate": round(p / n, 4), "low": lo, "high": hi})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    quality = quality_by_language(valid)
except NotImplementedError:
    quality = U.reference("lab_1_2_quality")
U.keep("lab_1_2_quality", quality)
print(quality)
ar, en = quality.set_index("lang").loc["ar"], quality.set_index("lang").loc["en"]
U.ok(ar.high < en.rate, "Arabic quality is lower than English, and the interval says it is not noise")

# %% [markdown]
# **Look at** the two quality rows. Averaged together they hide a gap that one language's users
# feel every day. Every quality objective in this course is sliced by language.
#
# ✱ **Stretch** · How many graded samples per day would narrow the Arabic interval to two points?
# Try `U.wilson` with larger `n` at the same rate.

# %% [markdown]
# ## Check yourself
#
# 1. Why does leaving the probe in raise the first-token indicator?
#    <details><summary>Answer</summary>The probe is one fast request a minute, always within the threshold; it adds good events no user received.</details>
# 2. Why is a 429 from Athar's own gateway a bad event, while a 499 is excluded?
#    <details><summary>Answer</summary>A 429 is Athar refusing a user who wanted an answer; a 499 is the user leaving before the answer was due.</details>
# 3. What does the Wilson interval add to a pass rate?
#    <details><summary>Answer</summary>How far the true rate could be from the sampled one; with small samples, two rates that look different may not be.</details>
#
# **Carry forward** · The four definitions feed Lab 1.3; reference values are in `data/reference/lab_1_2_*.json`.
