# %% [markdown]
# @header
#
# AI policy: **AI-off.** The game day is run without any AI assistant, as the entry and exit checks are. Work in a group of three: incident lead, operator, scribe.

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
# ## 1 · Read the roles and the first page
#
# | Role | Does | Does not |
# |---|---|---|
# | Incident lead | decides, sets priorities, talks to the service owner | type commands |
# | Operator | runs the mitigation, reports what the system shows | decide alone on customer messages |
# | Scribe | keeps the decision log: minute, role, decision, reason | debug |
#
# Minutes count from the page (T+0). The simulator `U.GameDay` replays the incident: events
# arrive at fixed minutes, and every minute without mitigation costs wrong answers and, here,
# answers that carry another customer's data. The actions you can take are in `U.ACTIONS`.

# %%
game = U.GameDay()
print(game.PAGE)
for minute, event in game.EVENTS.items():
    print(f"T+{minute}: {event}")
print()
for k, v in U.ACTIONS.items():
    print(f"{k:20s} {v}")

# %% [markdown]
# ## 2 · Detect and declare: first decisions
#
# ✏️ **Exercise** · Start the plan: a list of decisions, each `{"minute", "role", "action", "reason"}`.
# The scribe writes the reason for every decision: a log without reasons cannot be reviewed.
# Declare first, and assign the roles.
#
# ## 3 · Mitigate: choose and apply the action
#
# Continue the plan. Mitigate before you diagnose: the release 35 minutes before the page is the
# likeliest cause, and a rollback is reversible.
#
# ## 4 · Personal data in answers: the breach decision
#
# At T+9 a customer received another person's delivery address. Under SDAIA's procedural guide
# for personal data breaches, the controller notifies SDAIA within 72 hours of becoming aware,
# when the breach is expected to harm the data subjects, and tells affected customers without
# undue delay when it harms them. Continue the plan: page the data protection officer, preserve
# the evidence, assess, and record the decision on notification with its reason.
#
# ## 5 · Close and hand over the log
#
# Finish the plan: a status update for customer services and the start of root-cause analysis.

# %%
def plan() -> list[dict]:
    # BEGIN SOLUTION
    return [
        {"minute": 1, "role": "lead", "action": "declare", "reason": "Arabic quality alert on a paging tier; release 35 minutes earlier"},
        {"minute": 2, "role": "lead", "action": "assign_roles", "reason": "one decider, one operator, one scribe before anyone touches production"},
        {"minute": 5, "role": "lead", "action": "rollback_model", "reason": "complaints confirm user impact; v2.4 is the only recent change and a rollback is reversible"},
        {"minute": 6, "role": "operator", "action": "status_update", "reason": "customer services need words for callers while we recover"},
        {"minute": 10, "role": "lead", "action": "page_dpo", "reason": "a customer saw another customer's address: possible personal data breach"},
        {"minute": 11, "role": "operator", "action": "preserve_evidence", "reason": "the affected answers and logs are needed for the assessment and the notice"},
        {"minute": 20, "role": "lead", "action": "assess_breach", "reason": "count the answers and customers affected and judge the harm with the DPO"},
        {"minute": 40, "role": "lead", "action": "notify_sdaia", "reason": "names and addresses exposed to other customers: harm is likely, so SDAIA is notified within 72 hours of awareness"},
        {"minute": 45, "role": "lead", "action": "notify_customers", "reason": "affected customers are told plainly, with what we did and who to contact"},
        {"minute": 50, "role": "operator", "action": "root_cause", "reason": "service recovered and the breach is handled; now find why v2.4 broke Arabic"},
    ]
    # END SOLUTION

# %%
try:
    PLAN = plan()
except NotImplementedError:
    PLAN = U.reference("lab_3_2_plan")
U.keep("lab_3_2_plan", PLAN)
log, report = game.run(PLAN)
U.keep("lab_3_2_report", report)
print(log.to_string(index=False))
print()
for k, v in report.items():
    print(f"{k:38s} {v}")
U.ok(report["time_to_mitigate"] is not None and report["time_to_mitigate"] <= 15, "mitigated within 15 minutes of the page")
U.ok(report["dpo_paged_at"] is not None and report["dpo_paged_at"] <= 15, "data protection officer paged soon after the data report")
U.ok(report["sdaia_notified_at"] is not None, "the notification decision is in the log")
U.ok(report["entries_without_reason"] == 0, "every decision has a reason")

# %% [markdown]
# **Look at** the cost of a plan that diagnoses first. Run it and compare the wrong answers and
# the answers carrying another customer's data.

# %%
diagnose_first = [
    {"minute": 1, "role": "lead", "action": "declare", "reason": "alert"},
    {"minute": 3, "role": "operator", "action": "root_cause", "reason": "understand before acting"},
    {"minute": 35, "role": "lead", "action": "rollback_model", "reason": "root cause found in the template"},
]
_, slow = game.run(diagnose_first)
print({k: slow[k] for k in ("time_to_mitigate", "wrong_arabic_answers", "answers_with_other_customers_data")})
print({k: report[k] for k in ("time_to_mitigate", "wrong_arabic_answers", "answers_with_other_customers_data")})
U.ok(slow["answers_with_other_customers_data"] > report["answers_with_other_customers_data"], "every minute spent diagnosing first exposed more customers")

# %% [markdown]
# ✱ **Stretch** · Rerun the drill with `arabic_to_fallback` as the first action instead of the
# rollback. Compare time to mitigate, and ask what the fallback's Arabic quality (Lab 2.3) means
# for that choice.

# %% [markdown]
# ## Check yourself
#
# 1. Why roll back before knowing the cause?
#    <details><summary>Answer</summary>The rollback is reversible and stops the harm; diagnosis can continue on a copy, without users paying for each minute.</details>
# 2. From when do the 72 hours run?
#    <details><summary>Answer</summary>From the time the controller becomes aware of the breach: here, the report at T+9, not the release.</details>
# 3. What does the scribe's log add that the chat history does not?
#    <details><summary>Answer</summary>Every decision with its time, its owner and its reason, in one place: the material of the blameless review.</details>
#
# **Carry forward** · Lab 3.4 reviews the same incident from its record (`data/incident/INC-0731.json`).
