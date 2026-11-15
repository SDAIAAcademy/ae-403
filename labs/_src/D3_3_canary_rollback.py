# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the analysis template; the gate's thresholds and sample sizes are yours.

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
# ## 1 · Read the steps and the gate
#
# Two candidate model versions wait for release: `v2.6` and `v2.6-int4` (the same model with
# 4-bit weights: faster and cheaper). `U.canary_window(candidate, percent, minutes, step)` returns
# what one canary step observed: graded answers per language and first-token p95, for the canary
# and the stable arm over the same minutes. Canary answers are graded at 30%, stable ones at 5%.
#
# The gate, per step: canary first-token p95 at most 1.2 times stable's, and canary pass rate per
# language at least stable's minus 3 points. The old pipeline used `U.FAST_STEPS`: ten minutes
# at 5%, then everyone.

# %%
print("old pipeline:", U.FAST_STEPS, "· designed:", U.CANARY_STEPS)
print(U.canary_window("v2.6-int4", 5, 10, 0))

# %% [markdown]
# ## 2 · Write the analysis for one step
#
# ✏️ **Exercise** · `analyze(obs)` returns `"pass"` or `"fail"` and the reasons, from one step's
# observations. No minimum sample yet: this is the gate the old pipeline had.

# %%
def rate(arm, lang):
    return arm[f"passed_{lang}"] / arm[f"graded_{lang}"] if arm[f"graded_{lang}"] else 1.0


def analyze(obs: dict) -> tuple[str, list[str]]:
    # BEGIN SOLUTION
    c, s = obs["canary"], obs["stable"]
    reasons = []
    if c["ttft_p95_ms"] > 1.2 * s["ttft_p95_ms"]:
        reasons.append(f"first token p95 {c['ttft_p95_ms']:.0f} ms against stable {s['ttft_p95_ms']:.0f} ms")
    for lang in ("ar", "en"):
        if rate(c, lang) < rate(s, lang) - 0.03:
            reasons.append(f"{lang} quality {rate(c, lang):.3f} against stable {rate(s, lang):.3f} (n={c[f'graded_{lang}']})")
    return ("fail" if reasons else "pass"), reasons
    # END SOLUTION


def run_canary(candidate, steps, gate):
    """Walk the steps; roll back at the first failed step. Returns the decision and the log."""
    log = []
    cum = None
    for i, (pct, minutes) in enumerate(steps):
        if pct == 100:
            log.append({"step": i, "percent": 100, "verdict": "promoted", "reasons": ""})
            return "promoted", pd.DataFrame(log)
        obs = U.canary_window(candidate, pct, minutes, i)
        cum = obs if cum is None else {arm: {k: (cum[arm][k] + obs[arm][k]) if k.startswith(("graded", "passed", "requests")) else obs[arm][k]
                                             for k in obs[arm]} for arm in obs}
        verdict, reasons = gate(obs, cum)
        log.append({"step": i, "percent": pct, "verdict": verdict, "graded_ar": cum["canary"]["graded_ar"], "reasons": "; ".join(reasons)})
        if verdict == "fail":
            return "rolled back", pd.DataFrame(log)
    return "promoted", pd.DataFrame(log)

# %%
try:
    naive = {c: run_canary(c, U.FAST_STEPS, lambda obs, cum: analyze(obs)) for c in ("v2.6", "v2.6-int4")}
    naive_result = {c: d for c, (d, _) in naive.items()}
except NotImplementedError:
    naive_result = U.reference("lab_3_3_naive")
U.keep("lab_3_3_naive", naive_result)
print(naive_result)
U.ok(naive_result["v2.6-int4"] == "promoted", "the old gate promoted the int4 model on 27 graded Arabic answers")

# %% [markdown]
# ## 3 · Add the minimum-sample rule
#
# ✏️ **Exercise** · Write `gate(obs, cum)`: latency is judged on each step; quality is judged on
# the **cumulative** canary samples and only once each language has at least `N_MIN` graded
# answers. Before that the step is `"continue"`: it may move to the next traffic step but the
# release can never reach 100% without a quality verdict.

# %%
N_MIN = 200


def gate(obs: dict, cum: dict) -> tuple[str, list[str]]:
    # BEGIN SOLUTION
    c, s = obs["canary"], obs["stable"]
    if c["ttft_p95_ms"] > 1.2 * s["ttft_p95_ms"]:
        return "fail", [f"first token p95 {c['ttft_p95_ms']:.0f} ms against stable {s['ttft_p95_ms']:.0f} ms"]
    cc, cs = cum["canary"], cum["stable"]
    if min(cc["graded_ar"], cc["graded_en"]) < N_MIN:
        return "continue", [f"quality not judged yet: {cc['graded_ar']} Arabic and {cc['graded_en']} English samples"]
    bad = [f"{l} quality {rate(cc, l):.3f} against stable {rate(cs, l):.3f} (n={cc[f'graded_{l}']})"
           for l in ("ar", "en") if rate(cc, l) < rate(cs, l) - 0.03]
    return ("fail", bad) if bad else ("pass", [f"quality judged on {cc['graded_ar']} Arabic and {cc['graded_en']} English samples"])
    # END SOLUTION

# %% [markdown]
# ## 4 · Run both candidates and read the decisions

# %%
def run_designed(candidate):
    decision, log = run_canary(candidate, U.CANARY_STEPS, gate)
    if decision == "promoted" and not (log.verdict == "pass").any():
        decision = "held: no quality verdict"
    return decision, log

try:
    designed = {c: run_designed(c) for c in ("v2.6", "v2.6-int4")}
    for c, (d, log) in designed.items():
        print(c, "→", d)
        print(log.to_string(index=False), "\n")
    designed_result = {c: d for c, (d, _) in designed.items()}
except NotImplementedError:
    designed_result = U.reference("lab_3_3_designed")
U.keep("lab_3_3_designed", designed_result)
U.ok(designed_result == {"v2.6": "promoted", "v2.6-int4": "rolled back"}, "v2.6 is promoted; the int4 model is rolled back on Arabic quality")

# %% [markdown]
# **Look at** the int4 model's latency: it was faster at every step. A latency-only canary, or
# a quality gate on 26 samples, ships it. The rollback was automatic: no meeting decided it.
#
# ✱ **Stretch** · Translate the gate into the supplied Argo Rollouts analysis template,
# `labs/release/analysis-template.yaml`: which of your rules does it express, and which need a metric you would have to add?

# %% [markdown]
# ## Check yourself
#
# 1. Why did the old gate pass the int4 model?
#    <details><summary>Answer</summary>Ten minutes at 5% produced about 27 graded Arabic answers; the regression hides in that noise.</details>
# 2. Why judge quality on cumulative samples?
#    <details><summary>Answer</summary>Each step alone is small; together they reach the sample size a decision needs, and the canary still stops early on latency.</details>
# 3. Why grade canary answers at a higher rate than stable ones?
#    <details><summary>Answer</summary>The canary is small and the decision is urgent; grading more of its answers buys the sample size in minutes instead of hours.</details>
#
# **Carry forward** · The gate (`data/reference/lab_3_3_designed.json`) is the release gate the capstone review checks; Lab 3.4 adds a regression test to it.
