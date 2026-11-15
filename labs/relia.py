"""Shared helpers for the AE-403 labs (Rasael Post and Parcels, the Athar assistant).

Everything here runs on a laptop CPU. The self-hosted inference engine is a deterministic
simulator (`Engine`), calibrated to behave like a continuous-batching server with a limited
key-value cache; answers are recorded and graded by code. `live_answer` optionally asks a free
hosted open-weight model and falls back to the recording.

    import relia as U
    U.QUICK                      # True when RELIA_QUICK=1
    U.load("telemetry_week")     # a data file as a DataFrame
    U.reference("lab_1_1")       # the safety-net result of an exercise
"""

from __future__ import annotations

import base64
import collections
import hashlib
import heapq
import json
import math
import os
import random
import re
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

LABS = Path(__file__).resolve().parent
DATA = LABS / "data"
REF = DATA / "reference"
ARTIFACTS = LABS / "artifacts"
QUICK = os.environ.get("RELIA_QUICK", "0") == "1"
SEED = 403

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 20)


def pick(full, quick):
    """The full value, or the small one in quick mode (RELIA_QUICK=1)."""
    return quick if QUICK else full


def workdir(lab: str) -> Path:
    """A fresh folder for one lab's outputs: labs/artifacts/<lab>/ (delete artifacts/ before `academy check`)."""
    d = ARTIFACTS / lab
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    return d


# ---------------------------------------------------------------- data files

_FILES = {
    "telemetry_week": "telemetry_week.csv",
    "probe_week": "probe_week.csv",
    "requests_day": "requests_day.csv",
    "telemetry_month": "telemetry_month.csv",
    "release_requests": "release_requests.csv",
    "traffic_hourly": "traffic_hourly.csv",
    "overload_trace": "overload_trace.csv",
    "replay_day": "replay_day.csv",
    "deploy_log": "deploy_log.csv",
    "questions": "questions.jsonl",
    "answers": "answers.jsonl",
    "answer_cache": "answer_cache.jsonl",
    "articles": "help_articles.jsonl",
    "sessions": "redelivery_sessions.jsonl",
    "taqdir_checklist": "taqdir/checklist.csv",
    "taqdir_evidence": "taqdir/evidence.json",
}


def load(name: str):
    """Load a data file by its short name (see labs/README.md)."""
    path = DATA / _FILES.get(name, name)
    if path.suffix == ".csv":
        return pd.read_csv(path)
    if path.suffix == ".jsonl":
        with path.open(encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        return pd.DataFrame(rows) if name not in ("sessions",) else rows
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    raise ValueError(f"unknown data file {name}")


def reference(name: str):
    """The reference result of an exercise, for the safety-net cells."""
    obj = json.loads((REF / f"{name}.json").read_text(encoding="utf-8"))
    if isinstance(obj, dict) and obj.get("__frame__"):
        return pd.DataFrame(obj["rows"], columns=obj["columns"])
    return obj


def keep(name: str, value):
    """Write a reference result (only when RELIA_WRITE_REF=1, from a solution run)."""
    if os.environ.get("RELIA_WRITE_REF") != "1":
        return value
    REF.mkdir(parents=True, exist_ok=True)
    if isinstance(value, pd.DataFrame):
        obj = {"__frame__": True, "columns": list(value.columns),
               "rows": json.loads(value.to_json(orient="values"))}
    else:
        obj = json.loads(json.dumps(value, default=_jsonable))
    (REF / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return value


def _jsonable(x):
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, (set, tuple)):
        return list(x)
    raise TypeError(type(x))


def ok(cond: bool, msg: str):
    """Print a self-check. With RELIA_STRICT=1 (the course's solution runs) a failed check raises."""
    print(("✅ " if cond else "❌ ") + msg)
    if not cond and os.environ.get("RELIA_STRICT") == "1":
        raise AssertionError(msg)
    return cond


def wilson(passed: int, n: int, z: float = 1.96):
    """95% Wilson interval of a pass rate: (low, high)."""
    if n == 0:
        return (0.0, 1.0)
    p = passed / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


def runs(mask, gap: int = 0):
    """Consecutive runs of True in a boolean sequence, joining runs separated by <= gap Falses.
    Returns a list of (start_index, end_index_inclusive)."""
    out, start, last = [], None, None
    for i, v in enumerate(list(mask)):
        if v:
            if start is None:
                start = i
            elif i - last - 1 > gap:
                out.append((start, last))
                start = i
            last = i
    if start is not None:
        out.append((start, last))
    return out


# ---------------------------------------------------------------- the simulated engine

OBJ_TTFT_MS = 1500   # Athar's first-token objective threshold
OBJ_TPOT_MS = 100    # per-output-token threshold


class Engine:
    """A deterministic simulator of one replica of a continuous-batching inference engine.

    Each iteration decodes one token for every running request and prefills up to
    `prefill_chunk` prompt tokens. Iteration time = base + per_seq * running + per_tok * prefill.
    A request holds key-value cache for its prompt and its generated tokens; when the cache is
    full the newest request is preempted and must prefill again (recomputation).
    """

    def __init__(self, kv_tokens=40000, base_ms=14.0, per_seq_ms=0.9, per_tok_ms=0.05,
                 prefill_chunk=2048, max_seqs=128, seed=SEED):
        self.kv_tokens, self.base_ms, self.per_seq_ms = kv_tokens, base_ms, per_seq_ms
        self.per_tok_ms, self.prefill_chunk, self.max_seqs = per_tok_ms, prefill_chunk, max_seqs
        self.seed = seed

    # one request's lengths: retrieval-augmented prompts are long, answers short
    @staticmethod
    def lengths(rng, cls="P2", lang="en", long_prompts=False):
        tax = 1.35 if lang == "ar" else 1.0
        if cls == "P3":
            prompt, out = rng.randint(2500, 4000), rng.randint(300, 500)
        else:
            prompt, out = rng.randint(900, 2100), rng.randint(60, 260)
        if long_prompts:
            prompt *= 3
        return int(prompt * tax), int(out * tax)

    def _sim(self, source, duration_s, gateway=None, drain_s=60.0):
        """source: object with next_arrivals(t) -> list of requests, on_done(req, t)."""
        t = 0.0
        waiting = collections.deque()   # inside the engine (FIFO), already admitted by the gateway
        running = []
        done = []
        kv_used = 0
        end = duration_s + drain_s
        while t < end:
            for r in source.next_arrivals(t):
                if t >= duration_s:
                    continue
                if gateway is None:
                    waiting.append(r)
                else:
                    gateway.offer(r, t)
            if gateway is not None:
                inflight = len(waiting) + len(running)
                by_cls = collections.Counter(r["cls"] for r in waiting)
                by_cls.update(r["cls"] for r in running)
                for r in gateway.release(t, inflight, by_cls):
                    waiting.append(r)
                for r in gateway.expired(t):
                    done.append(r)
            # admit into the batch while cache and slots allow
            while waiting and len(running) < self.max_seqs:
                r = waiting[0]
                need = r["prompt"] + 16
                if kv_used + need > self.kv_tokens and running:
                    break
                waiting.popleft()
                r.setdefault("admitted", t)
                r["prefilled"] = 0
                r["generated"] = 0
                running.append(r)
                kv_used += need
            if not running:
                if gateway is None and not waiting and t >= duration_s:
                    break
                t += 0.005
                continue
            budget = self.prefill_chunk
            prefill_tokens = 0
            decoders = []
            for r in running:
                if r["prefilled"] < r["prompt"]:
                    if budget > 0:
                        take = min(budget, r["prompt"] - r["prefilled"])
                        r["prefilled"] += take
                        budget -= take
                        prefill_tokens += take
                else:
                    decoders.append(r)
            dt = (self.base_ms + self.per_seq_ms * len(running) + self.per_tok_ms * prefill_tokens) / 1000.0
            t += dt
            finished = []
            for r in running:
                if r["prefilled"] >= r["prompt"] and r not in decoders and r.get("first") is None:
                    r["first"] = t          # prefill completed this iteration: first token out
                    r["generated"] = 1
                    kv_used += 1
                elif r in decoders:
                    r["generated"] += 1
                    kv_used += 1
                if r["generated"] >= r["out"]:
                    finished.append(r)
            for r in finished:
                running.remove(r)
                kv_used -= r["prompt"] + 16 + r["generated"]
                r["done"] = t
                r["status"] = 200
                done.append(r)
                source.on_done(r, t)
            # cache overflow: preempt the newest running request (recompute later)
            while kv_used > self.kv_tokens and len(running) > 1:
                v = running.pop()
                kv_used -= v["prompt"] + 16 + v["generated"]
                v["preempted"] = v.get("preempted", 0) + 1
                v["first"] = v.get("first")  # tokens already streamed stay streamed
                waiting.appendleft(v)
        for r in list(waiting) + running:
            r["status"] = 504
            done.append(r)
        if gateway is not None:
            done.extend(gateway.leftover())
        return _frame(done)

    def closed_loop(self, concurrency: int, duration_s: float = 120.0, warmup_s: float = 20.0,
                    long_prompts=False, lang_mix=0.6):
        """`concurrency` virtual users, each sending its next request as soon as one finishes."""
        rng = random.Random(self.seed * 1000 + concurrency)
        eng = self

        class Src:
            def __init__(self):
                self.pending = [0.0] * concurrency
                self.n = 0

            def next_arrivals(self, t):
                out = []
                while self.pending and self.pending[0] <= t:
                    a = self.pending.pop(0)
                    lang = "ar" if rng.random() < lang_mix else "en"
                    p, o = eng.lengths(rng, "P2", lang, long_prompts)
                    self.n += 1
                    out.append({"id": self.n, "arrive": a, "cls": "P2", "lang": lang, "prompt": p, "out": o})
                return out

            def on_done(self, r, t):
                self.pending.append(t)
                self.pending.sort()

        df = self._sim(Src(), duration_s, drain_s=0.0)
        return df[(df.arrive >= warmup_s)].reset_index(drop=True)

    def replay(self, trace: pd.DataFrame, gateway=None, retries=None, faults=None):
        """Open-loop replay of a per-second trace with columns second, P1, P2, P3 (requests per second)."""
        rng = random.Random(self.seed + 7)
        eng = self
        arrivals = []
        n = 0
        for row in trace.itertuples(index=False):
            for cls in ("P1", "P2", "P3"):
                lam = getattr(row, cls)
                k = _poisson(rng, lam)
                for _ in range(k):
                    n += 1
                    lang = "ar" if rng.random() < 0.6 else "en"
                    p, o = eng.lengths(rng, cls, lang)
                    arrivals.append({"id": n, "arrive": row.second + rng.random(), "cls": cls,
                                     "lang": lang, "prompt": p, "out": o})
        arrivals.sort(key=lambda r: r["arrive"])

        class Src:
            def __init__(self):
                self.heap = [(r["arrive"], r["id"], r) for r in arrivals]
                heapq.heapify(self.heap)

            def next_arrivals(self, t):
                out = []
                while self.heap and self.heap[0][0] <= t:
                    out.append(heapq.heappop(self.heap)[2])
                return out

            def on_done(self, r, t):
                pass

        duration = float(trace.second.max() + 1)
        return self._sim(Src(), duration, gateway=gateway)


def _poisson(rng, lam):
    if lam <= 0:
        return 0
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= L:
            return k
        k += 1


def _frame(done):
    rows = []
    for r in done:
        first = r.get("first")
        fin = r.get("done")
        status = r.get("status", 504)
        ttft = (first - r["arrive"]) * 1000 if first is not None and status == 200 else np.nan
        tpot = ((fin - first) * 1000 / max(r["out"] - 1, 1)) if (fin and first is not None and status == 200) else np.nan
        rows.append({"id": r["id"], "cls": r["cls"], "lang": r["lang"], "arrive": round(r["arrive"], 3),
                     "status": status, "prompt": r["prompt"], "out": r["out"],
                     "ttft_ms": round(ttft, 1) if ttft == ttft else np.nan,
                     "tpot_ms": round(tpot, 2) if tpot == tpot else np.nan,
                     "done": round(fin, 3) if fin else np.nan, "preempted": r.get("preempted", 0)})
    return pd.DataFrame(rows).sort_values("id").reset_index(drop=True)


def goodput(df: pd.DataFrame, seconds: float, ttft_ms=OBJ_TTFT_MS, tpot_ms=OBJ_TPOT_MS) -> float:
    """Requests per second that finished and met both latency objectives."""
    good = df[(df.status == 200) & (df.ttft_ms <= ttft_ms) & (df.tpot_ms <= tpot_ms)]
    return round(len(good) / seconds, 3)


# ---------------------------------------------------------------- the gateway (Lab 2.2, 2.4)

class Gateway:
    """Admission in front of the engine: a cap on requests in flight, an optional cap per class
    (`class_caps`), one bounded queue per priority class and an optional queueing deadline per class. A request that finds its queue full is shed at once (503). Requests are released highest priority first (P1, then P2, then P3)."""

    def __init__(self, cap: int, queue_limits: dict, order=("P1", "P2", "P3"), deadline_s: dict | None = None,
                 class_caps: dict | None = None):
        self.cap, self.limits, self.order = cap, queue_limits, order
        self.class_caps = class_caps or {}
        self.deadline = deadline_s or {}
        self.queues = {c: collections.deque() for c in order}
        self.shed = []
        self.timed_out = []

    def offer(self, r, t):
        q = self.queues[r["cls"]]
        if len(q) >= self.limits.get(r["cls"], 0):
            r["status"] = 503
            self.shed.append(r)
        else:
            q.append(r)

    def release(self, t, inflight, by_cls=None):
        out = []
        used = collections.Counter(by_cls or {})
        while inflight + len(out) < self.cap:
            for c in self.order:
                if self.queues[c] and used[c] < self.class_caps.get(c, self.cap):
                    out.append(self.queues[c].popleft())
                    used[c] += 1
                    break
            else:
                break
        return out

    def expired(self, t):
        out = []
        for c, q in self.queues.items():
            d = self.deadline.get(c)
            if d is None:
                continue
            while q and t - q[0]["arrive"] > d:
                r = q.popleft()
                r["status"] = 503
                self.timed_out.append(r)
                out.append(r)
        return out

    def leftover(self):
        rest = []
        for q in self.queues.values():
            for r in q:
                r["status"] = 504
                rest.append(r)
        return self.shed + rest


def class_report(df: pd.DataFrame, objectives: dict) -> pd.DataFrame:
    """Per class: offered, served, shed, share of offered requests that met the class's TTFT objective."""
    rows = []
    for cls, lim in objectives.items():
        d = df[df.cls == cls]
        met = ((d.status == 200) & (d.ttft_ms <= lim)).sum()
        rows.append({"cls": cls, "offered": len(d), "served": int((d.status == 200).sum()),
                     "shed": int((d.status == 503).sum()), "ttft_p95_ms": round(float(d.ttft_ms.quantile(0.95)), 0) if d.ttft_ms.notna().any() else np.nan,
                     "met_objective": round(met / max(len(d), 1), 3), "objective_ms": lim})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- answers and grading (Lab 2.3)

def grade(answer: str, facts: list[str]) -> bool:
    """An answer passes when it states every required fact (code grader, recorded answers)."""
    a = normalise_digits(answer or "")
    return all(normalise_digits(f) in a for f in facts)


_EASTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


def normalise_digits(s: str) -> str:
    """Eastern Arabic digits to Western digits."""
    return s.translate(_EASTERN)


PARCEL_RE = re.compile(r"\bRP\d{9}SA\b")


def live_answer(question: str, mode: str = "full", recorded: str = "") -> tuple[str, str]:
    """Ask a free hosted open-weight model, if OPENROUTER_API_KEY is set; otherwise, or on any
    error, return the recorded answer. Returns (answer, source)."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        return recorded, "recorded"
    import urllib.request
    model = os.environ.get("RELIA_MODEL" if mode == "full" else "RELIA_SMALL_MODEL",
                           "google/gemma-4-31b-it:free" if mode == "full" else "google/gemma-4-26b-a4b-it:free")
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": "You are Athar, the help assistant of a postal operator. Answer in the language of the question, briefly."},
        {"role": "user", "content": question}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out = json.loads(resp.read())
        return out["choices"][0]["message"]["content"], model
    except Exception as e:  # a busy free model, a bad key, no network
        return recorded, f"recorded ({type(e).__name__})"


DISCLOSURE = {
    "fallback": {"en": "Athar is running in reduced mode: this answer may be less complete than usual.",
                 "ar": "يعمل أثر حاليًا بوضع مخفَّض، وقد تكون هذه الإجابة أقل اكتمالًا من المعتاد."},
    "cache": {"en": "Athar is answering from saved answers: details may not reflect the latest updates.",
              "ar": "يجيب أثر حاليًا من إجابات محفوظة، وقد لا تعكس التفاصيل آخر التحديثات."},
}


# ---------------------------------------------------------------- the service under chaos (Lab 2.4)

class Service:
    """Athar as a request path: gateway, retrieval, model provider (with a fallback model) and the
    tracking API. Faults are switched on per experiment. Latencies in milliseconds."""

    def __init__(self, seed=SEED, timeout_ms=3000, fallback=True, cache=True, retry_budget=None,
                 backoff=False):
        self.rng = random.Random(seed)
        self.timeout_ms, self.fallback, self.cache = timeout_ms, fallback, cache
        self.retry_budget, self.backoff = retry_budget, backoff
        self.faults = set()

    def handle(self, kind: str, lang: str, load: float = 1.0):
        """One request: returns (mode, latency_ms, ok). kind is 'tracking' or 'help'."""
        rng = self.rng
        lat = rng.uniform(20, 40)   # gateway
        mode = "full"
        retrieval_ok = "retrieval_outage" not in self.faults
        if kind == "help":
            if retrieval_ok:
                lat += rng.uniform(60, 120)
            else:
                lat += 2000 if "retrieval_slow" in self.faults else rng.uniform(5, 10)  # fast failure
                if self.cache and rng.random() < 0.64:
                    return "cache", lat + rng.uniform(10, 30), True
                if not self.cache:
                    return "error", lat, False
                return "unanswered", lat, False
        else:
            lat += rng.uniform(40, 90)   # tracking API, not retrieval
        provider_slow = "provider_timeout" in self.faults
        base = rng.uniform(600, 1300) * (1 + max(load - 1.0, 0) * 2.5)
        if provider_slow:
            lat += self.timeout_ms
            if self.fallback:
                return "fallback", lat + rng.uniform(400, 800), True
            return "error", lat, False
        if base > self.timeout_ms:
            return "error", lat + self.timeout_ms, False
        return mode, lat + base, True


def retry_storm(base_rps: float, capacity_rps: float, seconds: int, fault_window: tuple,
                max_retries: int = 3, retry_budget: float | None = None, backoff: bool = False, seed=SEED):
    """A fluid model of client retries. During the fault window every request fails; failed
    requests are retried (immediately, or with exponential backoff and jitter), each retry adds
    load. Over capacity goodput collapses, as in Lab 2.1, so the excess drags the served rate down. `retry_budget` caps retries at a share of first
    attempts. Returns a per-second frame: offered, served, failed, retries."""
    rng = random.Random(seed)
    pending = collections.defaultdict(float)  # second -> retries scheduled
    rows = []
    a, b = fault_window
    for s in range(seconds):
        first = base_rps
        retries = pending.pop(s, 0.0)
        if retry_budget is not None:
            retries = min(retries, retry_budget * first)
        offered = first + retries
        if a <= s < b:
            served = 0.0
        elif offered <= capacity_rps:
            served = offered
        else:  # past the knee goodput collapses (Lab 2.1): requests time out after using capacity
            served = capacity_rps * max(0.15, 1 - 1.2 * (offered / capacity_rps - 1))
        failed = offered - served
        # each failed request is retried until max_retries; approximate the attempt mix
        share_retryable = 1.0 - (1.0 / (max_retries + 1)) if retries else 1.0
        to_retry = failed * share_retryable if max_retries > 0 else 0.0
        if to_retry > 0:
            if backoff:
                for k in (1, 2, 4):
                    delay = k + rng.random() * k
                    pending[s + int(math.ceil(delay))] += to_retry / 3
            else:
                pending[s + 1] += to_retry
        rows.append({"second": s, "offered": round(offered, 2), "served": round(served, 2),
                     "failed": round(failed, 2), "retries": round(retries, 2)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- burn rates (Lab 3.1)

def burn_rate(bad: pd.Series, total: pd.Series, objective: float, window: int) -> pd.Series:
    """Burn rate over a rolling window of `window` rows: (bad / total) / (1 - objective)."""
    b = bad.rolling(window, min_periods=1).sum()
    n = total.rolling(window, min_periods=1).sum()
    return (b / n.replace(0, np.nan)) / (1 - objective)


# ---------------------------------------------------------------- the game day (Lab 3.2)

ACTIONS = {
    "declare": "Declare an incident and open the decision log",
    "assign_roles": "Assign incident lead, operator and scribe",
    "status_update": "Post a status update to customer services",
    "rollback_model": "Roll the model back to the last good version",
    "arabic_to_fallback": "Route Arabic traffic to the fallback model",
    "disable_cache": "Turn off the cached-answer mode",
    "page_dpo": "Page the data protection officer",
    "preserve_evidence": "Preserve logs and the affected responses",
    "assess_breach": "Assess the breach: data, people affected, likely harm",
    "notify_sdaia": "Notify SDAIA through the national platform",
    "notify_customers": "Notify the affected customers",
    "root_cause": "Start root-cause analysis",
    "wait": "Wait and watch the dashboards",
}


class GameDay:
    """The scripted game day of Lab 3.2. A model update at T+0 makes Arabic tracking answers wrong
    and, for parcel numbers written in Eastern Arabic digits, puts another customer's parcel record
    into the answer. Minutes are counted from the page (T+0)."""

    PAGE = ("T+0 page: the Arabic quality burn-rate alert fired on Athar. English is normal. "
            "Model v2.4 was released 40 minutes before the page.")
    EVENTS = {
        4: "Customer services: three Arabic customers say Athar gives the wrong parcel status.",
        9: "Customer services: a customer received another person's delivery address in Athar's answer.",
        15: "Operator: 2.1% of Arabic answers since the release contain a parcel number the customer did not ask about.",
    }

    def __init__(self):
        self.wrong_per_min = 38.0      # wrong Arabic answers per minute while v2.4 serves Arabic
        self.leak_per_min = 0.8        # answers per minute with another customer's record

    def run(self, plan: list[dict], horizon: int = 90):
        """plan: [{"minute": int, "role": str, "action": key of ACTIONS, "reason": str}]"""
        acts = sorted(plan, key=lambda p: p["minute"])
        log, wrong, leaks = [], 0.0, 0.0
        state = {"declared": None, "mitigated": None, "leak_stopped": None, "dpo": None,
                 "assessed": None, "sdaia": None, "customers": None, "preserved": None, "roles": None}
        unknown = [p["action"] for p in acts if p["action"] not in ACTIONS]
        if unknown:
            raise ValueError(f"unknown actions: {unknown}; choose from {list(ACTIONS)}")
        i = 0
        for m in range(horizon + 1):
            while i < len(acts) and acts[i]["minute"] <= m:
                p = acts[i]
                a = p["action"]
                key = {"declare": "declared", "rollback_model": "mitigated", "page_dpo": "dpo",
                       "assess_breach": "assessed", "notify_sdaia": "sdaia", "notify_customers": "customers",
                       "preserve_evidence": "preserved", "assign_roles": "roles"}.get(a)
                if key and state[key] is None:
                    state[key] = m
                if a == "rollback_model":
                    state["leak_stopped"] = state["leak_stopped"] if state["leak_stopped"] is not None else m
                if a == "arabic_to_fallback":
                    state["mitigated"] = state["mitigated"] if state["mitigated"] is not None else m
                    state["leak_stopped"] = state["leak_stopped"] if state["leak_stopped"] is not None else m
                log.append({"minute": p["minute"], "role": p.get("role", ""), "action": a,
                            "what": ACTIONS[a], "reason": p.get("reason", "")})
                i += 1
            if state["mitigated"] is None:
                wrong += self.wrong_per_min
            if state["leak_stopped"] is None:
                leaks += self.leak_per_min
        # the release ran 40 minutes before the page
        wrong += 40 * self.wrong_per_min
        leaks += 40 * self.leak_per_min
        report = {"time_to_declare": state["declared"], "time_to_mitigate": state["mitigated"],
                  "wrong_arabic_answers": int(wrong), "answers_with_other_customers_data": int(leaks),
                  "dpo_paged_at": state["dpo"], "breach_assessed_at": state["assessed"],
                  "evidence_preserved_at": state["preserved"], "sdaia_notified_at": state["sdaia"],
                  "customers_notified_at": state["customers"], "roles_assigned_at": state["roles"],
                  "log_entries": len(log), "entries_without_reason": sum(1 for e in log if not e["reason"].strip())}
        return pd.DataFrame(log), report


# ---------------------------------------------------------------- the canary (Lab 3.3)

CANDIDATES = {
    # quality pass rate by language, first-token p95 factor relative to the stable version
    "stable": {"en": 0.975, "ar": 0.970, "ttft_factor": 1.00},
    "v2.6": {"en": 0.976, "ar": 0.968, "ttft_factor": 0.97},
    "v2.6-int4": {"en": 0.972, "ar": 0.905, "ttft_factor": 0.82},
}

CANARY_STEPS = [(5, 10), (25, 20), (50, 20), (100, 0)]  # (traffic percent, minutes of analysis)


def canary_window(candidate: str, percent: int, minutes: int, step: int, seed=SEED,
                  rps: float = 3.0, graded_share: float = 0.05):
    """Simulated observations of one canary step: graded samples and first-token times for the
    canary and the stable version over the same minutes."""
    rng = np.random.default_rng(seed * 10 + step * 3 + len(candidate))
    out = {}
    for who, share in (("canary", percent / 100), ("stable", 1 - percent / 100 if percent < 100 else 0.0)):
        name = candidate if who == "canary" else "stable"
        q = CANDIDATES[name]
        n_req = int(rps * 60 * minutes * share)
        res = {}
        for lang, mix in (("ar", 0.6), ("en", 0.4)):
            n = int(rng.binomial(max(int(n_req * mix), 0), graded_share)) if n_req else 0
            res[f"graded_{lang}"] = n
            res[f"passed_{lang}"] = int(rng.binomial(n, q[lang])) if n else 0
        lat = rng.lognormal(mean=math.log(700 * q["ttft_factor"]), sigma=0.45, size=max(n_req, 1))
        res["ttft_p95_ms"] = round(float(np.quantile(lat, 0.95)), 1) if n_req else float("nan")
        res["requests"] = n_req
        out[who] = res
    return out


# ---------------------------------------------------------------- model artefacts (Day 4)

MODELS = DATA / "models"


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def model_files(folder) -> list[str]:
    folder = Path(folder)
    return sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file())


def copy_model(name: str, lab: str) -> Path:
    """A working copy of a supplied model artefact under artifacts/<lab>/."""
    src = MODELS / name
    dst = workdir(lab) / name
    shutil.copytree(src, dst)
    return dst


def dsse_statement(sig_path) -> dict:
    """The in-toto statement inside a model-signing bundle (the signed payload)."""
    bundle = json.loads(Path(sig_path).read_text(encoding="utf-8"))
    env = bundle["dsseEnvelope"]
    return json.loads(base64.b64decode(env["payload"]))


# ---------------------------------------------------------------- plotting outside a notebook
try:
    get_ipython  # type: ignore[name-defined]  # noqa: B018
except NameError:  # running as a script: draw to files, never open a window
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt

    _plt.show = lambda *a, **k: None
