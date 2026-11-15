# %% [markdown]
# @header
#
# AI policy: AI-tutor. An assistant may explain the data; which modes exist, when they switch on and what users are told are your decisions.

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
# ## 1 · Grade the full mode on the question set
#
# `questions.jsonl`: 240 questions, 200 help questions (half Arabic, half English) and 40
# tracking questions about a customer's own parcel. Each has the `facts` a correct answer must
# state. `answers.jsonl` holds the recorded answers of the full model and of the smaller fallback
# model; `U.grade(answer, facts)` is the code grader.
#
# The answers are recordings, so every participant grades the same text. `U.live_answer` can ask a
# free hosted open-weight model instead when `OPENROUTER_API_KEY` is set (stretch only).

# %%
qs = U.load("questions")
ans = U.load("answers")
recorded = {(r.qid, r.mode): r.answer for r in ans.itertuples()}
print(qs.groupby(["kind", "lang"]).size())


def quality(qs, answer_of) -> pd.DataFrame:
    rows = []
    for q in qs.itertuples():
        a = answer_of(q)
        rows.append({"lang": q.lang, "kind": q.kind, "answered": a is not None,
                     "passed": a is not None and U.grade(a, q.facts)})
    df = pd.DataFrame(rows)
    return (df.groupby("lang").agg(questions=("passed", "size"), answered=("answered", "mean"),
                                   pass_rate=("passed", "mean")).round(3).reset_index())


full = quality(qs, lambda q: recorded[(q.id, "full")])
print(full)

# %% [markdown]
# ## 2 · Grade the fallback model by language
#
# ✏️ **Exercise** · Grade the fallback model's answers and return the same table. Then decide
# whether it keeps the minimum service: a pass rate of at least 85% **in each language**.

# %%
def fallback_quality(qs):
    # BEGIN SOLUTION
    return quality(qs, lambda q: recorded[(q.id, "fallback")])
    # END SOLUTION

# %%
try:
    fb = fallback_quality(qs)
except NotImplementedError:
    fb = U.reference("lab_2_3_fallback")
U.keep("lab_2_3_fallback", fb)
print(fb)
fb_ok = dict(zip(fb.lang, fb.pass_rate >= 0.85))
U.ok(fb_ok["en"] and not fb_ok["ar"], "the smaller model keeps English (87%) and fails Arabic (73%): only the per-language view says which users lose the minimum service")
print("both languages together:", round(float((fb.pass_rate * fb.questions).sum() / fb.questions.sum()), 3))

# %% [markdown]
# ## 3 · Build the cached-answer mode and its refusal rule
#
# `answer_cache.jsonl` holds saved answers for frequent questions, keyed by the question's text
# in lower case. ✏️ **Exercise** · Write `cached_answer(q)` that returns a saved answer or `None`.
# It must refuse:
# - any tracking question, and any saved answer that contains a parcel number (`U.PARCEL_RE`):
#   a saved answer about one customer's parcel must never reach another customer;
# - a saved answer older than the help article it came from (`cached_day` before the article's `updated_day`).

# %%
cache = U.load("answer_cache")
articles = U.load("articles").set_index("id")
by_key = {r.key: r for r in cache.itertuples()}
print("saved answers:", len(cache), "· of which tracking:", int((cache.intent == "tracking").sum()))


def cached_answer(q):
    # BEGIN SOLUTION
    if q.kind == "tracking":
        return None
    hit = by_key.get(q.text.strip().lower())
    if hit is None or hit.intent != "help" or U.PARCEL_RE.search(hit.answer):
        return None
    if articles.loc[hit.article, "updated_day"] > hit.cached_day:
        return None
    return hit.answer
    # END SOLUTION

# %%
try:
    cq = quality(qs[qs.kind == "help"], cached_answer)
    leaked = sum(1 for q in qs.itertuples() if (a := cached_answer(q)) and U.PARCEL_RE.search(a))
    hits = [q for q in qs[qs.kind == "help"].itertuples() if cached_answer(q) is not None]
    on_hits = round(sum(U.grade(cached_answer(q), q.facts) for q in hits) / len(hits), 3)
except NotImplementedError:
    ref = U.reference("lab_2_3_cache")
    cq, leaked, on_hits = pd.DataFrame(ref["table"]), 0, ref["on_hits"]
U.keep("lab_2_3_cache", {"table": cq.to_dict("records"), "on_hits": on_hits})
print(cq)
print("pass rate on cache hits:", on_hits)
U.ok(leaked == 0, "no saved answer with a parcel number is ever served")
U.ok(on_hits >= 0.98, "stale answers refused: what the cache serves is right")

# %% [markdown]
# ## 4 · Route by health signals and disclose the mode
#
# ✏️ **Exercise** · Write `route(health, q)` returning `(mode, text)` where mode is `full`,
# `fallback`, `cache`, `tracking_template` or `unavailable`. Health has `engine_ok`,
# `retrieval_ok`, `fallback_ok`. Rules to implement:
# - full when the engine and retrieval are healthy;
# - tracking questions need the tracking API, not retrieval: when the engine is down, answer
#   them with a fixed template from the API (`tracking_template`), with no model;
# - an English help question goes to the fallback model; an **Arabic** one goes to the cache first,
#   because the fallback fails Arabic, and to the fallback only on a cache miss;
# - every degraded answer starts with the disclosure in the question's language (`U.DISCLOSURE`).

# %%
def route(health: dict, q):
    # BEGIN SOLUTION
    if health["engine_ok"] and health["retrieval_ok"]:
        return "full", recorded[(q.id, "full")]
    if q.kind == "tracking":
        return "tracking_template", U.DISCLOSURE["fallback"][q.lang] + " " + " ".join(q.facts)
    order = ["cache", "fallback"] if q.lang == "ar" else ["fallback", "cache"]
    for mode in order:
        if mode == "fallback" and health["fallback_ok"] and health["retrieval_ok"]:
            return "fallback", U.DISCLOSURE["fallback"][q.lang] + " " + recorded[(q.id, "fallback")]
        if mode == "cache" and (a := cached_answer(q)):
            return "cache", U.DISCLOSURE["cache"][q.lang] + " " + a
    return "unavailable", None
    # END SOLUTION

# %%
SCENARIOS = {"healthy": dict(engine_ok=True, retrieval_ok=True, fallback_ok=True),
             "engine down": dict(engine_ok=False, retrieval_ok=True, fallback_ok=True),
             "retrieval down": dict(engine_ok=True, retrieval_ok=False, fallback_ok=True)}
try:
    rows = []
    for name, h in SCENARIOS.items():
        for q in qs.itertuples():
            mode, text = route(h, q)
            disclosed = mode in ("full", "unavailable") or (text or "").startswith(tuple(d[q.lang] for d in U.DISCLOSURE.values()))
            rows.append({"scenario": name, "lang": q.lang, "mode": mode, "disclosed": disclosed,
                         "passed": text is not None and U.grade(text, q.facts)})
    routed = pd.DataFrame(rows)
    table = (routed.groupby(["scenario", "lang"]).agg(pass_rate=("passed", "mean"), answered=("mode", lambda m: (m != "unavailable").mean()),
                                                      disclosed=("disclosed", "mean")).round(3).reset_index())
except NotImplementedError:
    table = U.reference("lab_2_3_routes")
U.keep("lab_2_3_routes", table)
print(table.to_string(index=False))
U.ok(bool((table.disclosed == 1.0).all()), "every degraded answer tells the user, in the user's language")
eng_down = table[table.scenario == "engine down"].set_index("lang")
U.ok(eng_down.loc["ar", "pass_rate"] > fb.set_index("lang").loc["ar", "pass_rate"], "routing Arabic to the cache first beats the fallback alone")

# %% [markdown]
# **Look at** "retrieval down": the fallback model needs retrieval too, so only the cache and
# the tracking template are left. That is a minimum service, measured and disclosed, not a
# full one; Lab 2.4 checks it holds under injected faults.
#
# ✱ **Stretch** · Set the cache freshness limit from how often help articles change (`articles.updated_day`).

# %% [markdown]
# ## Check yourself
#
# 1. The fallback passes 81% of questions overall. Why is that not a pass?
#    <details><summary>Answer</summary>It passes 90% in English and 73% in Arabic; the minimum service is per language, and Arabic users would get a failing service.</details>
# 2. Why must a tracking answer never come from the cache?
#    <details><summary>Answer</summary>It holds one customer's parcel, name and address; serving it to another customer is a personal data breach.</details>
# 3. What does a user see in a degraded mode?
#    <details><summary>Answer</summary>A plain sentence in their language saying the answer is reduced or saved, before the answer itself.</details>
#
# **Carry forward** · The routing rules (`data/reference/lab_2_3_routes.json`) are the design Lab 2.4 tests under faults.
