# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the fault injector; the hypothesis, the minimum service and the abort condition are yours.

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
# ## 1 · Write the hypothesis and the minimum service
#
# `U.Service` is Athar's request path: gateway, retrieval, the model (with a fallback model),
# and the tracking API. Faults are switched on by name, the way Toxiproxy adds a toxic to a
# connection or Chaos Mesh injects a fault into a pod: `retrieval_outage`, `provider_timeout`.
#
# ✏️ **Exercise** · Write the experiment as data: a hypothesis that could be false, the minimum
# service as numbers, the blast radius (which traffic is exposed) and the abort condition.

# %%
def experiment() -> dict:
    # BEGIN SOLUTION
    return {
        "hypothesis": "With retrieval down or the model provider timing out, Athar still answers tracking questions within 5 s and answers or plainly declines every help question",
        "minimum_service": {"tracking_answered": 0.95, "p95_latency_ms": 5000, "silent_failures": 0},
        "blast_radius": "the simulated service only; in production, one replica's share of traffic behind a flag",
        "abort_if": "tracking answered below 90% for one minute, or any personal data in a degraded answer",
    }
    # END SOLUTION

# %%
try:
    EXP = experiment()
except NotImplementedError:
    EXP = U.reference("lab_2_4_experiment")
U.keep("lab_2_4_experiment", EXP)
MIN = EXP["minimum_service"]
print(EXP["hypothesis"])
N = U.pick(4000, 1500)


def run(service, n=N, seed=0) -> pd.DataFrame:
    """n requests: 40% tracking, 60% help, 60% Arabic. One row per request."""
    rows = []
    for i in range(n):
        kind = "tracking" if service.rng.random() < 0.4 else "help"
        lang = "ar" if service.rng.random() < 0.6 else "en"
        mode, lat, ok = service.handle(kind, lang)
        # a help question the service cannot answer gets a plain "not now" message: declined, not silent
        declined = mode == "unanswered"
        rows.append({"kind": kind, "lang": lang, "mode": mode, "latency_ms": lat, "ok": ok, "declined": declined})
    return pd.DataFrame(rows)


def summary(df: pd.DataFrame) -> dict:
    t = df[df.kind == "tracking"]
    return {"tracking_answered": round(float(t.ok.mean()), 3),
            "help_answered": round(float(df[df.kind == "help"].ok.mean()), 3),
            "p95_latency_ms": round(float(df.latency_ms.quantile(0.95))),
            "silent_failures": int(((~df.ok) & (~df.declined)).sum()),
            "modes": df["mode"].value_counts().to_dict()}


print("steady state:", summary(run(U.Service())))

# %% [markdown]
# ## 2 · Retrieval outage: does the cached mode hold?
#
# ✏️ **Exercise** · Run the service with the `retrieval_outage` fault, once with the cache on and
# once with it off, and return both summaries.

# %%
def retrieval_outage():
    # BEGIN SOLUTION
    out = {}
    for cache in (True, False):
        s = U.Service(cache=cache)
        s.faults = {"retrieval_outage"}
        out["cache on" if cache else "cache off"] = summary(run(s))
    return out
    # END SOLUTION

# %%
try:
    r_out = retrieval_outage()
except NotImplementedError:
    r_out = U.reference("lab_2_4_retrieval")
U.keep("lab_2_4_retrieval", r_out)
for k, v in r_out.items():
    print(k, v)
U.ok(r_out["cache on"]["tracking_answered"] >= MIN["tracking_answered"] and r_out["cache on"]["silent_failures"] == 0,
     "with the cache on, tracking holds and every unanswered help question is declined plainly")
U.ok(r_out["cache off"]["silent_failures"] > 0, "with the cache off, help questions fail with errors")

# %% [markdown]
# ## 3 · Provider timeout: does the fallback take over?
#
# ✏️ **Exercise** · Inject `provider_timeout` with the fallback on, for client timeouts of 3, 6 and
# 10 seconds. Which timeout keeps the p95 latency within the minimum service?

# %%
def provider_timeout(timeouts=(3000, 6000, 10000)) -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for t in timeouts:
        s = U.Service(timeout_ms=t)
        s.faults = {"provider_timeout"}
        rows.append({"timeout_ms": t, **{k: v for k, v in summary(run(s)).items() if k != "modes"}})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    p_out = provider_timeout()
except NotImplementedError:
    p_out = U.reference("lab_2_4_provider")
U.keep("lab_2_4_provider", p_out)
print(p_out.to_string(index=False))
good_t = p_out[p_out.p95_latency_ms <= MIN["p95_latency_ms"]].timeout_ms.tolist()
U.ok(good_t == [3000], "only the 3-second timeout hands over to the fallback fast enough")

# %% [markdown]
# ## 4 · Retry storm, then a retry budget with backoff
#
# A 30-second fault (seconds 60 to 90) on a replica set that serves 8.5 requests a second, with
# 6 a second offered. `U.retry_storm` models clients that retry failed requests up to three times.
#
# ✏️ **Exercise** · Run it three ways: immediate retries, retries with a 10% retry budget, and the
# budget plus exponential backoff with jitter. Return, for each, the peak offered load and the
# second the service recovered (no failures), or `None`.

# %%
def storms() -> pd.DataFrame:
    # BEGIN SOLUTION
    rows = []
    for name, kw in [("immediate retries", {}), ("backoff only", {"backoff": True}), ("10% retry budget", {"retry_budget": 0.1}),
                     ("budget and backoff", {"retry_budget": 0.1, "backoff": True})]:
        d = U.retry_storm(6.0, 8.5, 300, (60, 90), **kw)
        after = d[(d.second >= 90) & (d.failed < 0.1)]
        rows.append({"policy": name, "peak_offered_rps": float(d.offered.max()),
                     "recovered_at_s": int(after.second.iloc[0]) if len(after) else None,
                     "failed_requests": round(float(d.failed.sum()))})
    return pd.DataFrame(rows)
    # END SOLUTION

# %%
try:
    st = storms()
except NotImplementedError:
    st = U.reference("lab_2_4_storms")
U.keep("lab_2_4_storms", st)
print(st.to_string(index=False))
naive = U.retry_storm(6.0, 8.5, 300, (60, 90))
fig, ax = plt.subplots(figsize=(8, 3))
ax.plot(naive.second, naive.offered, label="offered")
ax.plot(naive.second, naive.served, label="served")
ax.axvspan(60, 90, alpha=0.15)
ax.set_xlabel("second")
ax.legend()
plt.show()
U.ok(pd.isna(st.recovered_at_s.iloc[0]) and st.recovered_at_s.iloc[2] == 90,
     "immediate retries never recover after a 30-second fault; a retry budget recovers when the fault ends")

# %% [markdown]
# **Look at** the plot: the fault lasted 30 seconds, the outage lasts as long as the retries do.
# The failure outlives its cause. That is why a retry budget belongs in the client library
# every team uses, and why a chaos experiment includes a retry storm.
#
# ✱ **Stretch** · Run the three faults at once (`s.faults = {"retrieval_outage", "provider_timeout"}` plus the storm) and say which mode the users get.

# %% [markdown]
# ## Check yourself
#
# 1. What makes a chaos experiment different from breaking things?
#    <details><summary>Answer</summary>A written hypothesis that could be false, a measured minimum service, a limited blast radius and an abort condition decided before it starts.</details>
# 2. Why is a long client timeout worse during a provider failure?
#    <details><summary>Answer</summary>Every request waits the whole timeout before the fallback starts, so the fallback's answer arrives after users have given up.</details>
# 3. Why does the service stay down after a 30-second fault without a retry budget?
#    <details><summary>Answer</summary>Retries multiply the load past the knee, goodput collapses, more requests fail and are retried: the overload sustains itself.</details>
#
# **Carry forward** · The experiment record (`data/reference/lab_2_4_experiment.json`) is the template for the capstone's chaos evidence.
