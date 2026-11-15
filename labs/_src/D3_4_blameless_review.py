# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may comment on your wording; the contributing factors and the actions are your findings from the record.

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
import json
import re
import pandas as pd

# %% [markdown]
# ## 1 · Read the incident record
#
# `data/incident/INC-0412.json` is the record of the incident you drilled in Lab 3.2: a timeline
# in minutes from the page, chat extracts and measured facts. `data/incident/cases.jsonl` holds
# twelve failing cases: Arabic tracking questions with the parcel number in Eastern Arabic
# digits, and the answers of v2.4 and of the fixed v2.4.1.

# %%
inc = json.loads((U.DATA / "incident" / "INC-0412.json").read_text(encoding="utf-8"))
cases = [json.loads(l) for l in (U.DATA / "incident" / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
print(inc["summary"])
print(pd.DataFrame(inc["timeline"]).to_string(index=False))
print(inc["facts"])

# %% [markdown]
# ## 2 · Timeline and contributing factors
#
# ✏️ **Exercise** · Write the review's timeline (detect, declare, mitigate, assess, notify, with
# minutes) and at least four contributing factors. Each factor names a condition of the system
# or the process, with the evidence from the record. `blameless(text)` flags blaming language:
# names of people, "human error", "careless", "should have", "failed to".

# %%
BLAME = re.compile(r"human error|careless|should have|failed to|negligen|fault of|" +
                   "|".join(re.escape(n) for n in ["Thabit", "Ghufran", "Shuaib", "Sundus", "Ithar", "Ruwaida"]), re.I)


def blameless(text: str) -> bool:
    return BLAME.search(text) is None


def review() -> dict:
    # BEGIN SOLUTION
    return {
        "timeline": [
            {"minute": -35, "what": "v2.4 released to all traffic; offline evaluation passed on an English-only set"},
            {"minute": 0, "what": "Arabic quality burn-rate alert pages on-call"},
            {"minute": 7, "what": "incident declared, roles assigned"},
            {"minute": 14, "what": "rollback to v2.3; Arabic answers recover"},
            {"minute": 55, "what": "breach assessed with the data protection officer: harm likely"},
            {"minute": 180, "what": "SDAIA notified; affected customers told by text message"},
        ],
        "contributing_factors": [
            {"factor": "The offline evaluation set had no Arabic tracking questions and no Eastern Arabic digits",
             "evidence": "evaluation_set_arabic_share 0.0; release engineer's note at minute 30"},
            {"factor": "The v2.4 prompt template dropped the digit normalisation step",
             "evidence": "model platform's note at minute 41; all twelve failing cases use Eastern Arabic digits"},
            {"factor": "The tracking lookup falls back to the nearest parcel number instead of refusing",
             "evidence": "finding at minute 32; answers named parcels the customer did not ask about"},
            {"factor": "The release went to all traffic at once, with no canary and no quality gate",
             "evidence": "timeline at minute -35"},
            {"factor": "The on-call engineer had no written authority to roll back without the evaluation team",
             "evidence": "chat at minute 6"},
        ],
    }
    # END SOLUTION

# %%
try:
    R = review()
except NotImplementedError:
    R = U.reference("lab_3_4_review")
U.keep("lab_3_4_review", R)
print(pd.DataFrame(R["contributing_factors"]).to_string(index=False))
text = json.dumps(R, ensure_ascii=False)
U.ok(blameless(text), "the review names conditions, not people")
U.ok(len(R["contributing_factors"]) >= 4, "at least four contributing factors, each with evidence")

# %% [markdown]
# ## 3 · Owned corrective actions
#
# ✏️ **Exercise** · One action per contributing factor: what changes, the owning role (not a
# person), the due date in days, and how you will know it is done (a test, a gate, a drill).

# %%
def actions() -> list[dict]:
    # BEGIN SOLUTION
    return [
        {"action": "Add Arabic tracking questions with Eastern Arabic digits to the offline set (at least 20% of it)", "owner": "answer-quality lead", "due_days": 14, "verified_by": "the regression test of step 4 runs in CI on every release"},
        {"action": "Normalise digits in the gateway, before any prompt template", "owner": "model platform engineer", "due_days": 7, "verified_by": "unit test with Eastern Arabic digits"},
        {"action": "Make the tracking lookup refuse when no exact parcel number matches", "owner": "tracking API team", "due_days": 7, "verified_by": "test: an unknown parcel number returns 'not found', never another parcel"},
        {"action": "Route every model release through the canary gate of Lab 3.3", "owner": "release engineer", "due_days": 21, "verified_by": "pipeline refuses a release without a gate verdict"},
        {"action": "Write rollback authority for on-call into the runbook", "owner": "reliability lead", "due_days": 7, "verified_by": "next game day: rollback decided by on-call within 10 minutes"},
    ]
    # END SOLUTION

# %%
try:
    A = actions()
except NotImplementedError:
    A = U.reference("lab_3_4_actions")
U.keep("lab_3_4_actions", A)
print(pd.DataFrame(A).to_string(index=False))
U.ok(all(a["owner"] and a["due_days"] and a["verified_by"] for a in A), "every action has an owner, a due date and a check")
U.ok(blameless(json.dumps(A, ensure_ascii=False)), "owners are roles, not names")

# %% [markdown]
# ## 4 · The regression test: fails before, passes after
#
# ✏️ **Exercise** · Write `check_case(answer, case)` returning a list of problems: the answer
# must name the parcel the customer asked about (compare after `U.normalise_digits`), and must
# name no other parcel number (`U.PARCEL_RE`). Then run it on every case for both versions.

# %%
def check_case(answer: str, case: dict) -> list[str]:
    # BEGIN SOLUTION
    problems = []
    a = U.normalise_digits(answer)
    asked = case["asked_parcel"]
    if asked not in a:
        problems.append(f"does not name the parcel asked about ({asked})")
    others = [p for p in U.PARCEL_RE.findall(a) if p != asked]
    if others:
        problems.append(f"names another customer's parcel ({others[0]})")
    return problems
    # END SOLUTION

# %%
try:
    results = {v: sum(1 for c in cases if not check_case(c["answers"][v], c)) for v in ("v2.4", "v2.4.1")}
except NotImplementedError:
    results = U.reference("lab_3_4_results")
U.keep("lab_3_4_results", results)
print("cases passing:", results, "of", len(cases))
U.ok(results == {"v2.4": 0, "v2.4.1": 12}, "the test fails on every case for v2.4 and passes on every case for v2.4.1")

# %% [markdown]
# **Look at** where the test lives: a regression test nobody runs is a note. In the capstone,
# show it in the release gate, failing on the old version in the pipeline log.
#
# ✱ **Stretch** · Add the test to the canary gate of Lab 3.3 as a pre-release step.

# %% [markdown]
# ## Check yourself
#
# 1. Why is "the engineer did not test Arabic" not a contributing factor?
#    <details><summary>Answer</summary>It blames a person for a gap in the process: the factor is that the evaluation set had no Arabic tracking questions, which any engineer would have missed.</details>
# 2. What makes a corrective action complete?
#    <details><summary>Answer</summary>An owning role, a due date and a check that proves it is done, such as a test in the release gate.</details>
# 3. Why must the regression test fail on v2.4?
#    <details><summary>Answer</summary>A test that passes on the broken version cannot detect the regression; failing first proves it tests the right thing.</details>
#
# **Carry forward** · The review and the test are the evidence LO4 asks for; the capstone asks for the same on the reviewed service.
