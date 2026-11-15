# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may help you read the evidence; the scores, the ranking and the launch decision are yours to defend.

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
# ## 1 · Read the checklist and the evidence pack
#
# The cross-border parcels team wants to launch Taqdir, an assistant that estimates delivery
# dates for international parcels, on the same platform as Athar. Ruwaida asks you for a
# readiness review. `taqdir/checklist.csv` is Rasael's readiness checklist: 13 items in six
# areas, each with the likelihood (1 to 5) that its absence causes an incident and the impact
# (1 to 5) if it does. `taqdir/evidence.json` is what the team submitted, one entry per item.

# %%
checklist = U.load("taqdir_checklist")
evidence = U.load("taqdir_evidence")
print(evidence["service"])
print(checklist.to_string(index=False))

# %% [markdown]
# ## 2 · Score each item from the evidence
#
# ✏️ **Exercise** · Add a column `status` (`met`, `partial`, `missing`) and a column `note` from
# the evidence. Read each note: the status is the team's own claim, and a reviewer checks it.
# One claim does not survive reading: find it and correct it.

# %%
def score(checklist: pd.DataFrame, evidence: dict) -> pd.DataFrame:
    # BEGIN SOLUTION
    out = checklist.copy()
    out["status"] = [evidence[e]["status"] for e in out.evidence]
    out["note"] = [evidence[e]["note"] for e in out.evidence]
    # the team claims its latency objective is met, but the objective is 2 s against Rasael's 1.5 s standard
    out.loc[out.id == "O1", "status"] = "partial"
    out.loc[out.id == "O1", "note"] += " (Rasael's standard is 1.5 s: partial)"
    return out
    # END SOLUTION

# %%
try:
    scored = score(checklist, evidence)
except NotImplementedError:
    scored = U.reference("lab_4_4_scored")
U.keep("lab_4_4_scored", scored)
print(scored[["id", "item", "status"]].to_string(index=False))
U.ok(scored.set_index("id").loc["O1", "status"] == "partial", "the 2-second first-token objective does not meet the 1.5-second standard")

# %% [markdown]
# ## 3 · Rank the findings by risk
#
# ✏️ **Exercise** · Risk = likelihood × impact × gap, where the gap is 1 for `missing`, 0.5 for
# `partial` and 0 for `met`. Return the findings (gap above 0) ranked by risk, highest first.

# %%
def rank(scored: pd.DataFrame) -> pd.DataFrame:
    # BEGIN SOLUTION
    gap = scored.status.map({"missing": 1.0, "partial": 0.5, "met": 0.0})
    out = scored.assign(risk=scored.likelihood * scored.impact * gap)
    return out[out.risk > 0].sort_values(["risk", "impact"], ascending=False)[["id", "area", "item", "status", "impact", "risk", "note"]].reset_index(drop=True)
    # END SOLUTION

# %%
try:
    ranked = rank(scored)
except NotImplementedError:
    ranked = U.reference("lab_4_4_ranked")
U.keep("lab_4_4_ranked", ranked)
print(ranked[["id", "item", "status", "risk"]].to_string(index=False))
U.ok(list(ranked.id[:3]) == ["C1", "S1", "O2"], "busiest-hour capacity, the unsigned model and the English-only quality objective lead")

# %% [markdown]
# ## 4 · Launch decision and conditions
#
# ✏️ **Exercise** · Decide: `launch`, `launch with conditions` or `do not launch`. Rasael's rule:
# any missing item with impact 5 blocks the launch until it is fixed; other findings with risk 8
# or more become dated conditions, each with what proves it is met.

# %%
PROOF = {"objectives": "the objective per language with its samples and interval",
         "capacity": "a goodput curve to the busiest hour and the replica plan",
         "degradation": "chaos results for each mode, quality measured per language",
         "incidents": "a runbook with roles and the log of one game day",
         "release": "a canary run that rolls back a seeded regression",
         "integrity": "an admission log showing a verified signature and an allowed licence"}


def decide(ranked: pd.DataFrame) -> dict:
    # BEGIN SOLUTION
    blocking = list(ranked[(ranked.status == "missing") & (ranked.impact == 5)].id)
    conditions = [{"id": r.id, "condition": r.item, "within_days": 0 if r.id in blocking else (14 if r.risk >= 10 else 30),
                   "proof": PROOF[r.area]} for r in ranked[ranked.risk >= 8].itertuples()]
    return {"decision": "do not launch" if blocking else ("launch with conditions" if conditions else "launch"),
            "blocking": blocking, "conditions": conditions,
            "relaunch": "relaunch review once every blocking item is met; the other conditions run on their dates"}
    # END SOLUTION


# %%
try:
    D = decide(ranked)
except NotImplementedError:
    D = U.reference("lab_4_4_decision")
U.keep("lab_4_4_decision", D)
print(D["decision"], "· blocking:", D["blocking"])
print(pd.DataFrame(D["conditions"]).to_string(index=False))
U.ok(D["decision"] == "do not launch" and "S1" in D["blocking"], "an unsigned model from a mirror blocks the launch")
U.ok(all(c["proof"] for c in D["conditions"]), "every condition says what proves it is met")

# %% [markdown]
# **Look at** the order: the team's own summary led with its met items. A readiness review
# ranks by risk to users and to Rasael, and says exactly what would change the decision.
#
# ✱ **Stretch** · Choose the capstone service (a peer's, or the supplied Athar release pack in
# `capstone/`) and the first three checklist items you will test with measured evidence.

# %% [markdown]
# ## Check yourself
#
# 1. Why is the team's "met" on the latency objective corrected to "partial"?
#    <details><summary>Answer</summary>Their objective is 2 s to first token; Rasael's standard is 1.5 s. Meeting a weaker objective does not meet the standard.</details>
# 2. Why does an unsigned model block the launch even with everything else fixed?
#    <details><summary>Answer</summary>A missing control with impact 5: nobody can show the weights are the publisher's, and Lab 4.1 found a tampered mirror.</details>
# 3. What makes a launch condition usable?
#    <details><summary>Answer</summary>An owner can meet it, it has a date, and it names the evidence that proves it is met.</details>
#
# **Carry forward** · The capstone applies this checklist to a service with measured evidence; `capstone/README.md` has the brief.
