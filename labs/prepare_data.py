# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Write the synthetic case-study data of AE-403 (Rasael Post and Parcels, the Athar assistant).

    uv run prepare_data.py

Standard library only, seed 403: the same bytes on every run. Time is counted in minute or slot
indexes from the start of a period, never as clock times. Everything is synthetic: the people,
the parcels, the addresses, the telemetry, the answers and the model files (random bytes, not a
model). The planted problems and the expected numbers are in solutions/answer_key.md.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SEED = 403


def rng(tag: str) -> random.Random:
    return random.Random(f"{SEED}-{tag}")


def write_csv(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def binom(r: random.Random, n: int, p: float) -> int:
    if n <= 0:
        return 0
    if n < 60:
        return sum(1 for _ in range(n) if r.random() < p)
    mu, sd = n * p, math.sqrt(n * p * (1 - p))
    return max(0, min(n, int(round(r.gauss(mu, sd)))))


def poisson(r: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam > 50:
        return max(0, int(round(r.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= r.random()
        if p <= L:
            return k
        k += 1


def diurnal(minute_of_day: int) -> float:
    """Relative demand over a day: low at night, a late-morning and an evening peak."""
    h = minute_of_day / 60.0
    return 0.18 + 0.55 * math.exp(-((h - 11.0) ** 2) / 6.0) + 0.82 * math.exp(-((h - 21.0) ** 2) / 4.0)


# ---------------------------------------------------------------- help articles and questions

SERVICES = [
    ("domestic parcel", "طرد محلي"), ("express parcel", "طرد سريع"), ("registered letter", "رسالة مسجلة"),
    ("post office box", "صندوق بريد"), ("customs clearance", "التخليص الجمركي"), ("cash on delivery", "الدفع عند الاستلام"),
    ("parcel locker", "خزانة الطرود"), ("returns", "الإرجاع"), ("redelivery", "إعادة التوصيل"),
    ("address change", "تغيير العنوان"), ("lost item claim", "مطالبة بمفقود"), ("prohibited items", "المواد المحظورة"),
    ("packaging", "التغليف"), ("pickup request", "طلب الاستلام من الموقع"), ("international shipping", "الشحن الدولي"),
]
ASPECTS = [
    ("fee", "الرسوم", "The fee is SAR {n}.", "الرسوم {n} ريالًا."),
    ("delivery time", "مدة التوصيل", "Delivery takes {d} working days.", "يستغرق التوصيل {d} أيام عمل."),
    ("weight limit", "حد الوزن", "The weight limit is {k} kg.", "حد الوزن {k} كجم."),
    ("documents", "المستندات", "Bring form {f}.", "أحضر النموذج {f}."),
    ("opening period", "مدة الحفظ", "Items are held for {d} days.", "تُحفظ المواد مدة {d} أيام."),
    ("tracking", "التتبع", "Tracking updates every {d} hours.", "يُحدَّث التتبع كل {d} ساعات."),
    ("refund", "الاسترداد", "Refunds are paid within {d} days.", "يُصرف الاسترداد خلال {d} أيام."),
    ("eligibility", "الأهلية", "Form {f} is required for eligibility.", "يلزم النموذج {f} للأهلية."),
    ("complaints", "الشكاوى", "Complaints are answered within {d} days.", "يُرد على الشكاوى خلال {d} أيام."),
    ("insurance", "التأمين", "Insurance covers up to SAR {n}.", "يغطي التأمين حتى {n} ريال."),
]
REGIONS = [("Riyadh", "الرياض"), ("Jeddah", "جدة"), ("Dammam", "الدمام"), ("Makkah", "مكة المكرمة"), ("Madinah", "المدينة المنورة"),
           ("Abha", "أبها"), ("Tabuk", "تبوك"), ("Hail", "حائل"), ("Jazan", "جازان"), ("Buraydah", "بريدة")]


def fact_values(r, aspect):
    return {"n": r.choice([15, 20, 25, 30, 35, 45, 60, 80, 120, 500, 1000, 2000]), "d": r.choice([2, 3, 4, 5, 7, 10, 14]),
            "k": r.choice([5, 10, 20, 30]), "f": f"RP-{r.randint(10, 99)}"}


def fact_of(aspect_i, vals):
    key = {0: "n", 1: "d", 2: "k", 3: "f", 4: "d", 5: "d", 6: "d", 7: "f", 8: "d", 9: "n"}[aspect_i]
    return str(vals[key])


def articles():
    r = rng("articles")
    out = []
    i = 0
    for si, (se, sa) in enumerate(SERVICES):
        for ai, (ae, aa, te, ta) in enumerate(ASPECTS):
            for ri, (re_, ra) in enumerate(REGIONS):
                vals = fact_values(r, ai)
                day = r.randint(1, 30)
                fact = fact_of(ai, vals)
                for lang in ("en", "ar"):
                    i += 1
                    if lang == "en":
                        title = f"{se.capitalize()} in {re_}: {ae}"
                        body = (f"This article explains the {ae} for {se} at Rasael branches in {re_}. " + te.format(**vals) +
                                " Rules can change; the article date shows the last update.")
                    else:
                        title = f"{sa} في {ra}: {aa}"
                        body = (f"توضح هذه المقالة {aa} لخدمة {sa} في فروع رسائل في {ra}. " + ta.format(**vals) +
                                " قد تتغير القواعد، ويبين تاريخ المقالة آخر تحديث.")
                    out.append({"id": f"HA-{i:04d}", "lang": lang, "topic": f"{si:02d}-{ai}-{ri}", "title": title,
                                "body": body, "facts": [fact], "updated_day": day})
    return out


def parcel_id(r):
    return f"RP{r.randint(100000000, 999999999)}SA"


AR_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
NAMES = ["Noor A.", "Hassan K.", "Reem S.", "Fahd M.", "Dalal T.", "Sami R.", "Hind Q.", "Yousef B.", "Maha J."]
STREETS = ["Al-Orouba Road", "King Fahd Road", "Al-Takhassusi Street", "Prince Sultan Road", "Al-Madinah Road"]


def questions_and_answers(arts):
    r = rng("qa")
    help_arts = [a for a in arts if a["topic"].endswith("-0") or a["topic"].endswith("-1")]
    picks = r.sample([a for a in help_arts if a["lang"] == "en"], 100) + r.sample([a for a in help_arts if a["lang"] == "ar"], 100)
    qs, ans, cache = [], [], []
    statuses_en = ["out for delivery", "at the sorting centre", "delivered to a parcel locker", "held for customs"]
    statuses_ar = ["خرج للتوصيل", "في مركز الفرز", "سُلِّم إلى خزانة الطرود", "محجوز لدى الجمارك"]
    for k, a in enumerate(picks):
        qid = f"Q{k + 1:03d}"
        if a["lang"] == "en":
            text = f"What is the {a['title'].split(': ')[1]} for {a['title'].split(' in ')[0].lower()} in {a['title'].split(' in ')[1].split(':')[0]}?"
        else:
            topic, aspect = a["title"].split(": ")
            text = f"ما {aspect} لـ{topic}؟"
        qs.append({"id": qid, "lang": a["lang"], "kind": "help", "text": text, "facts": a["facts"], "article": a["id"]})
    for k in range(40):
        lang = "en" if k < 16 else "ar"
        pid = parcel_id(r)
        st = r.randrange(4)
        qid = f"Q{201 + k:03d}"
        text = f"Where is my parcel {pid}?" if lang == "en" else f"أين طردي {pid}؟"
        fact = statuses_en[st] if lang == "en" else statuses_ar[st]
        qs.append({"id": qid, "lang": lang, "kind": "tracking", "text": text, "facts": [pid, fact], "parcel": pid})
    # recorded answers: full model and the smaller fallback model
    quality = {("full", "en"): 0.95, ("full", "ar"): 0.94, ("fallback", "en"): 0.90, ("fallback", "ar"): 0.73}
    for q in qs:
        for mode in ("full", "fallback"):
            good = r.random() < quality[(mode, q["lang"])]
            facts = q["facts"] if good else [f for f in q["facts"][:-1]] + (["unknown"] if q["lang"] == "en" else ["غير معروف"])
            if q["lang"] == "en":
                text = "According to Rasael's help articles: " + "; ".join(facts) + "."
            else:
                text = "بحسب مقالات المساعدة لدى رسائل: " + "، ".join(facts) + "."
            ans.append({"qid": q["id"], "mode": mode, "answer": text})
    # the answer cache: saved answers for frequent help questions, some stale, some personal
    by_id = {a["id"]: a for a in arts}
    helpq = [q for q in qs if q["kind"] == "help"]
    cached = r.sample(helpq, 128)
    stale = set(q["id"] for q in r.sample(cached, 7))
    for q in cached:
        art = by_id[q["article"]]
        fact = q["facts"][0]
        if q["id"] in stale:
            fact_old = str(int(fact) + 5) if fact.isdigit() else fact + "0"
            text = ("Saved answer: " if q["lang"] == "en" else "إجابة محفوظة: ") + fact_old + "."
            cached_day = max(art["updated_day"] - r.randint(2, 6), 0)
        else:
            text = ("Saved answer: " if q["lang"] == "en" else "إجابة محفوظة: ") + fact + "."
            cached_day = min(art["updated_day"] + r.randint(0, 5), 30)
        cache.append({"key": q["text"].strip().lower(), "lang": q["lang"], "intent": "help", "answer": text,
                      "cached_day": cached_day, "article": q["article"]})
    for k in range(9):
        pid = parcel_id(r)
        name, street = NAMES[k], r.choice(STREETS)
        lang = "en" if k < 4 else "ar"
        key = (f"where is my parcel {pid}?" if lang == "en" else f"أين طردي {pid}؟")
        text = (f"Your parcel {pid} for {name}, {street}, house {r.randint(3, 90)}, is out for delivery." if lang == "en"
                else f"طردك {pid} باسم {name}، {street}، منزل {r.randint(3, 90)}، خرج للتوصيل.")
        cache.append({"key": key, "lang": lang, "intent": "tracking", "answer": text, "cached_day": 29, "article": None})
    r.shuffle(cache)
    return qs, ans, cache, sorted(stale)


# ---------------------------------------------------------------- telemetry: a week (Lab 1.1)

WEEK_INCIDENTS = [
    # (day, start minute of day, minutes, kind, what the probe sees)
    (1, 1170, 95, "arabic_quality", "probe green: retrieval index refresh broke Arabic answers"),
    (2, 1230, 70, "ttft", "probe green: evening queueing, first token over 4 s"),
    (3, 600, 50, "tpot", "probe green: slow streaming after an engine setting change"),
    (4, 840, 40, "empty", "probe green: 18% of answers empty (cut at the output limit)"),
    (5, 300, 12, "outage", "probe red: the engine pods restarted"),
]


def telemetry_week():
    r = rng("week")
    rows, probe = [], []
    inc = {}
    for d, s, n, kind, _ in WEEK_INCIDENTS:
        for m in range(s, s + n):
            inc[d * 1440 + m] = kind
    for minute in range(7 * 1440):
        day, mod = divmod(minute, 1440)
        kind = inc.get(minute)
        for lang, share in (("ar", 0.6), ("en", 0.4)):
            lam = 200 * share * diurnal(mod)
            req = poisson(r, lam)
            err = binom(r, req, 0.002)
            ttft = r.gauss(820, 90) * (1 + 0.25 * diurnal(mod))
            tpot = r.gauss(42, 4)
            empty = binom(r, req, 0.004)
            p_pass = 0.975 if lang == "en" else 0.972
            if kind == "arabic_quality" and lang == "ar":
                p_pass = 0.70
            if kind == "ttft":
                ttft = r.gauss(4800, 400)
            if kind == "tpot":
                tpot = r.gauss(210, 15)
            if kind == "empty":
                empty = binom(r, req, 0.18)
            if kind == "outage":
                err = req
            graded = binom(r, req - err, 0.05)
            passed = binom(r, graded, p_pass)   # empty answers are not sent to grading
            rows.append({"minute": minute, "day": day, "lang": lang, "requests": req, "errors": err,
                         "ttft_p95_ms": round(ttft) if req > err else "", "tpot_p95_ms": round(tpot, 1) if req > err else "",
                         "empty_answers": empty if req > err else 0, "graded": graded, "passed": passed})
        probe_ok = 0 if kind == "outage" else 1
        probe.append({"minute": minute, "probe_ok": probe_ok, "probe_ms": round(r.gauss(310, 30)) if probe_ok else ""})
    write_csv(DATA / "telemetry_week.csv", rows)
    write_csv(DATA / "probe_week.csv", probe)


# ---------------------------------------------------------------- a day of request logs (Lab 1.2)

def requests_day():
    r = rng("day")
    rows = []
    rid = 0
    for minute in range(1440):
        lam = 22 * diurnal(minute)
        for _ in range(poisson(r, lam)):
            rid += 1
            lang = "ar" if r.random() < 0.6 else "en"
            client = "web" if r.random() < 0.35 else "app"
            u = r.random()
            if u < 0.031:
                status = 499     # the user closed the chat before the answer: a client cancel
            elif u < 0.035:
                status = 429     # rate limited by the gateway
            elif u < 0.0395:
                status = 500
            elif u < 0.041:
                status = 503
            else:
                status = 200
            served = status == 200
            ttft = round(r.lognormvariate(math.log(780), 0.42)) if served else ""
            tpot = round(r.lognormvariate(math.log(45), 0.35), 1) if served else ""
            out = r.randint(40, 320) if served else 0
            graded = 1 if served and r.random() < 0.06 else 0
            p_pass = 0.975 if lang == "en" else 0.955
            passed = (1 if r.random() < p_pass else 0) if graded else ""
            rows.append({"request_id": f"R{rid:06d}", "minute": minute, "client": client, "lang": lang, "status": status,
                         "ttft_ms": ttft, "tpot_ms": tpot, "output_tokens": out, "graded": graded, "passed": passed})
        # the synthetic probe: one tiny prompt a minute, always fast, always English
        rid += 1
        rows.append({"request_id": f"R{rid:06d}", "minute": minute, "client": "probe", "lang": "en", "status": 200,
                     "ttft_ms": round(r.gauss(140, 15)), "tpot_ms": round(r.gauss(30, 2), 1), "output_tokens": 4,
                     "graded": 0, "passed": ""})
    write_csv(DATA / "requests_day.csv", rows)


# ---------------------------------------------------------------- a month in five-minute slots (Lab 1.3)

def telemetry_month():
    r = rng("month")
    rows = []
    for day in range(1, 31):
        for slot in range(288):
            mod = slot * 5
            outage = day == 9 and 102 <= slot < 111                   # 45 minutes
            slow = day in (17, 18) and 216 <= slot < 288               # six evening hours
            ar_drop = (day == 20 and slot >= 144) or day == 21 or (day == 22 and slot < 144)   # 48 hours
            for lang, share in (("ar", 0.6), ("en", 0.4)):
                valid = poisson(r, 1000 * share * diurnal(mod))
                ok = 0 if outage else valid - binom(r, valid, 0.0006)
                ttft_good = binom(r, ok, 0.70 if slow else 0.985)
                graded = binom(r, ok, 0.05)
                p = 0.978 if lang == "en" else 0.972
                if ar_drop and lang == "ar":
                    p = 0.80
                passed = binom(r, graded, p)
                rows.append({"day": day, "slot": slot, "lang": lang, "valid": valid, "ok": ok,
                             "ttft_good": ttft_good, "graded": graded, "passed": passed})
    write_csv(DATA / "telemetry_month.csv", rows)
    write_csv(DATA / "release_requests.csv", [
        {"id": "RR-1", "change": "New model version v2.5 for all languages", "touches": "quality_ar quality_en ttft", "kind": "feature"},
        {"id": "RR-2", "change": "Shorter English system prompt", "touches": "quality_en", "kind": "feature"},
        {"id": "RR-3", "change": "Raise the engine's batch size", "touches": "ttft availability", "kind": "feature"},
        {"id": "RR-4", "change": "Gateway security patch", "touches": "availability", "kind": "security"},
        {"id": "RR-5", "change": "Refresh the Arabic help index", "touches": "quality_ar", "kind": "feature"},
    ])


# ---------------------------------------------------------------- the redelivery flow (Lab 1.4)

def sessions():
    r = rng("sessions")
    out = []
    steps = ["identify_parcel", "check_eligibility", "offer_slots", "confirm_booking"]
    for k in range(2000):
        lang = "ar" if r.random() < 0.6 else "en"
        calls, outcome = [], "completed"
        looping = r.random() < 0.05
        for si, st in enumerate(steps):
            attempts = 1
            while r.random() < 0.012:     # a tool error, retried by the assistant: the call log shows a failure
                calls.append({"step": st, "ok": False, "tokens": r.randint(900, 1600)})
                attempts += 1
            n_ok = 1
            if st == "offer_slots" and looping:
                n_ok = r.randint(6, 12)    # the customer rejects slot after slot; the assistant re-offers
            for _ in range(n_ok):
                calls.append({"step": st, "ok": True, "tokens": r.randint(900, 1600)})
            if st == "check_eligibility" and r.random() < 0.085:
                outcome = "escalated"      # not eligible online, handed to an agent
                break
            if st == "offer_slots" and (looping and r.random() < 0.7 or r.random() < 0.06):
                outcome = "abandoned"
                break
            if st == "confirm_booking" and r.random() < 0.035:
                outcome = "abandoned"      # the confirmation message timed out on the customer's side
        out.append({"session": f"S{k + 1:05d}", "lang": lang, "calls": calls, "outcome": outcome})
    write_jsonl(DATA / "redelivery_sessions.jsonl", out)


# ---------------------------------------------------------------- traffic (Labs 2.1, 2.2)

def traffic():
    r = rng("traffic")
    rows = []
    for day in range(1, 31):
        boost = 1.55 if day == 27 else (1.15 if day in (25, 26, 28) else 1.0)   # the national sale day
        for hour in range(24):
            rps = 5.1 * diurnal(hour * 60 + 30) * boost * r.uniform(0.95, 1.05)
            rows.append({"day": day, "hour": hour, "rps": round(rps, 2)})
    write_csv(DATA / "traffic_hourly.csv", rows)
    trace = []
    for s in range(1200):
        spike = 300 <= s < 900
        trace.append({"second": s, "P1": 1.0 if spike else 0.55, "P2": 1.7 if spike else 0.95, "P3": 0.45 if spike else 0.25})
    write_csv(DATA / "overload_trace.csv", trace)


# ---------------------------------------------------------------- the replayed day (Lab 3.1)

def replay_day():
    r = rng("replay")
    rows = []
    for slot in range(288):
        for lang, share in (("ar", 0.6), ("en", 0.4)):
            req = poisson(r, 1000 * share * max(diurnal(slot * 5), 0.45))
            graded = binom(r, req, 0.05)
            p = 0.978 if lang == "en" else 0.972
            if lang == "ar" and slot >= 130:
                p = 0.62
            rows.append({"slot": slot, "lang": lang, "requests": req, "graded": graded, "passed": binom(r, graded, p)})
    write_csv(DATA / "replay_day.csv", rows)
    write_csv(DATA / "deploy_log.csv", [
        {"slot": 40, "change": "help index refresh (English)", "version": "index-2026-44"},
        {"slot": 130, "change": "model update", "version": "athar-v2.4"},
        {"slot": 210, "change": "gateway configuration", "version": "gw-118"},
    ])


# ---------------------------------------------------------------- the incident record (Lab 3.4)

def incident():
    r = rng("incident")
    timeline = [
        (-35, "release", "Model v2.4 released to all traffic after the offline evaluation passed (English set only)."),
        (0, "alert", "Arabic quality burn-rate alert pages the on-call engineer."),
        (4, "report", "Customer services report wrong parcel statuses from Arabic customers."),
        (7, "decision", "Incident declared; Thabit Al-Junaibi takes the incident lead role."),
        (9, "report", "A customer reports another person's delivery address in an answer."),
        (11, "decision", "Data protection officer paged."),
        (14, "mitigation", "Model rolled back to v2.3; Arabic answers recover within five minutes."),
        (15, "finding", "2.1% of Arabic answers since the release named a parcel the customer did not ask about."),
        (32, "finding", "Parcel numbers written in Eastern Arabic digits were not normalised by the v2.4 prompt template; the tracking lookup fell back to the nearest match."),
        (55, "decision", "Breach assessed: 40 answers exposed another customer's name and address; harm is likely; SDAIA to be notified and the customers told."),
        (180, "decision", "Notification sent to SDAIA through the national platform; customers informed by text message."),
    ]
    rec = {
        "id": "INC-0412", "service": "Athar", "severity": "SEV-2",
        "summary": "After the v2.4 model update, Arabic tracking questions with Eastern Arabic digits returned other customers' parcel records.",
        "timeline": [{"minute": m, "kind": k, "event": e} for m, k, e in timeline],
        "chat": [
            {"minute": 2, "who": "on-call", "text": "English quality fine, Arabic burning. v2.4 went out 35 min before the page."},
            {"minute": 6, "who": "on-call", "text": "Should I roll back or wait for the evaluation team?"},
            {"minute": 13, "who": "incident lead", "text": "Roll back now, diagnose after."},
            {"minute": 30, "who": "release engineer", "text": "Our offline set has no Eastern Arabic digits at all."},
            {"minute": 41, "who": "model platform", "text": "The template change in v2.4 dropped the digit normalisation step."},
        ],
        "facts": {"answers_exposing_data": 40, "customers_affected": 37, "wrong_arabic_answers": 1900,
                  "minutes_from_release_to_rollback": 49, "evaluation_set_arabic_share": 0.0},
    }
    write_json(DATA / "incident" / "INC-0412.json", rec)
    cases = []
    for k in range(12):
        asked = parcel_id(r)
        other = parcel_id(r)
        q = f"أين طردي {asked.translate(AR_DIGITS)}؟"
        cases.append({"case": f"C{k + 1:02d}", "question": q, "asked_parcel": asked,
                      "answers": {"v2.4": f"طردك {other} خرج للتوصيل إلى {r.choice(STREETS)}.",
                                  "v2.4.1": f"طردك {asked} {r.choice(['في مركز الفرز', 'خرج للتوصيل', 'سُلِّم إلى خزانة الطرود'])}."}})
    write_jsonl(DATA / "incident" / "cases.jsonl", cases)


# ---------------------------------------------------------------- model artefacts (Day 4)

def model_files(name: str, seed_tag: str, licence: str):
    r = rng(seed_tag)
    files = {
        "config.json": json.dumps({"model_type": "athar-small", "hidden_size": 512, "num_layers": 8, "vocab_size": 32000}, indent=1) + "\n",
        "generation_config.json": json.dumps({"max_new_tokens": 320, "temperature": 0.2}, indent=1) + "\n",
        "tokenizer.json": json.dumps({"version": "1.0", "model": {"type": "BPE", "vocab_size": 32000}}, indent=1) + "\n",
        "LICENSE": licence + "\n",
        "README.md": f"# {name}\n\nSynthetic model card for the AE-403 labs. The weight files are random bytes, not a model.\n\nLicence: {licence.splitlines()[0]}\n",
    }
    blobs = {f"model-0000{i}-of-00002.safetensors": bytes(r.getrandbits(8) for _ in range(24576)) for i in (1, 2)}
    return files, blobs


def models():
    root = DATA / "models"
    specs = [
        ("athar-small-v1", "small", "Apache-2.0\nLicensed under the Apache License, Version 2.0."),
        ("athar-small-v1-mirror", "small", "Apache-2.0\nLicensed under the Apache License, Version 2.0."),
        ("athar-tiny-q4", "tiny", "LicenseRef-Research-Only\nResearch use only. Commercial use and redistribution are not permitted."),
    ]
    provenance = []
    for name, tag, lic in specs:
        files, blobs = model_files(name.replace("-mirror", ""), tag, lic)
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        for fn, text in files.items():
            (d / fn).write_text(text, encoding="utf-8", newline="\n")
        publisher = {}
        for fn, b in blobs.items():
            publisher[fn] = hashlib.sha256(b).hexdigest()
            if name.endswith("mirror") and fn.startswith("model-00002"):
                b = bytearray(b)
                for i in range(4096, 4160):
                    b[i] ^= 0x5A           # 64 changed bytes in the second shard
                b = bytes(b)
            (d / fn).write_bytes(b)
        for fn, text in files.items():
            publisher[fn] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        provenance.append({
            "artefact": name,
            "publisher": "Rasael ML platform team" if tag == "small" else "an external research group",
            "source": "models.rasael.example/athar-small" if tag == "small" else "research.example/athar-tiny",
            "revision": hashlib.sha1(f"{SEED}{tag}".encode()).hexdigest(),
            "obtained_from": "a third-party mirror" if name.endswith("mirror") else "the publisher",
            "licence": lic.splitlines()[0],
            "publisher_sha256": dict(sorted(publisher.items())),
        })
    write_json(root / "provenance.json", provenance)


# ---------------------------------------------------------------- Taqdir, the reviewed service (Lab 4.4)

def taqdir():
    items = [
        ("O1", "objectives", "Objectives for availability and first-token time", "objectives.latency", 3, 4),
        ("O2", "objectives", "An answer-quality objective sliced by language", "objectives.quality_by_language", 4, 5),
        ("O3", "objectives", "Burn-rate alerts on each objective", "alerts.burn_rate", 4, 4),
        ("C1", "capacity", "Load test up to the busiest hour with headroom", "capacity.busiest_hour", 4, 4),
        ("C2", "capacity", "Admission limit and shedding priorities", "capacity.admission", 3, 4),
        ("D1", "degradation", "Fallback mode tested under a provider failure", "degradation.fallback_tested", 3, 4),
        ("D2", "degradation", "Degraded answers disclosed to users", "degradation.disclosure", 3, 3),
        ("I1", "incidents", "Runbook with incident roles and a decision log", "incidents.runbook", 3, 3),
        ("I2", "incidents", "Breach procedure linked, data protection officer named", "incidents.breach_procedure", 2, 5),
        ("R1", "release", "Canary with an automated quality and latency gate", "release.canary_gate", 3, 4),
        ("R2", "release", "Rollback tested in the last 30 days", "release.rollback_tested", 2, 4),
        ("S1", "integrity", "Model signature verified at admission", "integrity.signature", 3, 5),
        ("S2", "integrity", "Bill of materials with licences", "integrity.bom", 2, 3),
    ]
    write_csv(DATA / "taqdir" / "checklist.csv", [
        {"id": i, "area": a, "item": t, "evidence": e, "likelihood": l, "impact": m} for i, a, t, e, l, m in items])
    evidence = {
        "service": "Taqdir, the delivery-estimate assistant of the cross-border parcels team",
        "objectives.latency": {"status": "met", "note": "99.5% availability and 95% under 2 s to first token, 30 days"},
        "objectives.quality_by_language": {"status": "partial", "note": "quality objective of 92%, measured on English samples only"},
        "alerts.burn_rate": {"status": "partial", "note": "burn-rate alert on availability; quality has a static threshold on the daily average"},
        "capacity.busiest_hour": {"status": "missing", "note": "load test at the average hour (2.1 requests a second); the busiest hour was 6.4"},
        "capacity.admission": {"status": "met", "note": "concurrency cap of 12 per replica, two priority classes"},
        "degradation.fallback_tested": {"status": "partial", "note": "fallback model configured; never exercised with a provider failure"},
        "degradation.disclosure": {"status": "met", "note": "reduced-mode banner in Arabic and English"},
        "incidents.runbook": {"status": "missing", "note": "runbook lists commands, no roles, no decision log"},
        "incidents.breach_procedure": {"status": "met", "note": "linked; data protection officer named"},
        "release.canary_gate": {"status": "partial", "note": "canary at 10% for 30 minutes, latency gate only"},
        "release.rollback_tested": {"status": "met", "note": "rollback drill 12 days before the review"},
        "integrity.signature": {"status": "missing", "note": "weights pulled from a third-party mirror; no signature"},
        "integrity.bom": {"status": "met", "note": "CycloneDX ML-BOM with the licence of each component"},
    }
    write_json(DATA / "taqdir" / "evidence.json", evidence)


def main():
    arts = articles()
    write_jsonl(DATA / "help_articles.jsonl", arts)
    qs, ans, cache, stale = questions_and_answers(arts)
    write_jsonl(DATA / "questions.jsonl", qs)
    write_jsonl(DATA / "answers.jsonl", ans)
    write_jsonl(DATA / "answer_cache.jsonl", cache)
    telemetry_week()
    requests_day()
    telemetry_month()
    sessions()
    traffic()
    replay_day()
    incident()
    models()
    taqdir()
    print(f"wrote {sum(1 for _ in DATA.rglob('*') if _.is_file())} files under data/; stale cached answers: {', '.join(stale)}")


if __name__ == "__main__":
    main()
