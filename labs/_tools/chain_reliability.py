"""Numbers for the slides on a chain of dependent steps (Day 1, Session 4) and for the
practice question on the pickup-request flow.

    uv run python _tools/chain_reliability.py      (from labs/; standard library only)

A flow whose steps run one after the other, each needing the one before it, succeeds only when
every step succeeds: the success rates multiply (when failures are independent). Its time is the
sum of the step times: means add, percentiles do not, so the end-to-end p95 comes from a
simulation (or from traces), never from adding the steps' p95s.
"""

from __future__ import annotations

import math
import random

SEED = 403
N = 200_000


def joint(rates: list[float]) -> float:
    return math.prod(rates)


def lognormal_mu(mean: float, sigma: float) -> float:
    return math.log(mean) - sigma * sigma / 2


def p95(xs: list[float]) -> float:
    ys = sorted(xs)
    return ys[int(0.95 * (len(ys) - 1))]


def simulate(steps: list[dict], seed: int = SEED, n: int = N, retry: str | None = None) -> dict:
    """End-to-end time of the sessions that complete, and the completion rate, by simulation.
    `retry` names one step that is retried once after a failure (an independent second try)."""
    r = random.Random(seed)
    totals, done = [], 0
    step_times = {s["step"]: [] for s in steps}
    for _ in range(n):
        t, ok = 0.0, True
        for s in steps:
            tries = 2 if s["step"] == retry else 1
            for k in range(tries):
                d = r.lognormvariate(lognormal_mu(s["mean_s"], s["sigma"]), s["sigma"])
                t += d
                step_times[s["step"]].append(d)
                passed = r.random() < s["success"]
                if passed:
                    break
            if not passed:
                ok = False
                break
        if ok:
            done += 1
            totals.append(t)
    return {"completion": done / n, "mean_s": sum(totals) / len(totals), "p95_s": p95(totals),
            "sum_of_step_p95_s": sum(p95(v) for v in step_times.values())}


def report(name: str, steps: list[dict], objective: dict, whatifs: list[tuple[str, list[dict], str | None]]):
    print(f"\n== {name} ==")
    print(f"{'step':<16}{'success':>9}{'mean s':>8}{'share of time':>15}")
    total_mean = sum(s["mean_s"] for s in steps)
    for s in steps:
        print(f"{s['step']:<16}{s['success']:>9.1%}{s['mean_s']:>8.1f}{s['mean_s'] / total_mean:>15.0%}")
    j = joint([s["success"] for s in steps])
    print(f"joint success (product): {j:.4f}  ({j:.1%});  lowest step: {min(s['success'] for s in steps):.1%}")
    print(f"end-to-end mean (sum of means): {total_mean:.1f} s")
    sim = simulate(steps)
    print(f"simulated: completion {sim['completion']:.4f}, mean {sim['mean_s']:.2f} s, "
          f"end-to-end p95 {sim['p95_s']:.2f} s, sum of step p95s {sim['sum_of_step_p95_s']:.2f} s")
    print(f"objective: {objective}")
    for label, alt, retry in whatifs:
        ja = joint([s["success"] for s in alt]) if retry is None else None
        sa = simulate(alt, retry=retry)
        if ja is None:
            ja = joint([1 - (1 - s["success"]) ** 2 if s["step"] == retry else s["success"] for s in alt])
        ma = sum(s["mean_s"] for s in alt) + sum((1 - s["success"]) * s["mean_s"] for s in alt if s["step"] == retry)
        print(f"  what if {label:<38} joint {ja:.4f} ({ja:.1%}), gain {100 * (ja - j):+.1f} points, "
              f"mean {ma:.2f} s, sim p95 {sa['p95_s']:.2f} s")


def with_(steps: list[dict], step: str, **kw) -> list[dict]:
    return [dict(s, **kw) if s["step"] == step else dict(s) for s in steps]


# The address-change flow of Athar (the slides' example): five steps in a row.
ADDRESS = [
    {"step": "verify_caller", "success": 0.996, "mean_s": 0.8, "sigma": 0.4},
    {"step": "find_parcel", "success": 0.998, "mean_s": 0.4, "sigma": 0.3},
    {"step": "check_address", "success": 0.960, "mean_s": 1.2, "sigma": 0.5},
    {"step": "reroute", "success": 0.992, "mean_s": 2.9, "sigma": 0.45},
    {"step": "confirm_change", "success": 0.995, "mean_s": 0.6, "sigma": 0.3},
]

# The pickup-request flow (the practice question): four steps in a row.
PICKUP = [
    {"step": "check_area", "success": 0.995, "mean_s": 0.5, "sigma": 0.3},
    {"step": "price_quote", "success": 0.990, "mean_s": 1.8, "sigma": 0.4},
    {"step": "book_courier", "success": 0.975, "mean_s": 1.0, "sigma": 0.4},
    {"step": "send_receipt", "success": 0.997, "mean_s": 0.4, "sigma": 0.3},
]

if __name__ == "__main__":
    report("Address change", ADDRESS, {"completion": ">= 95%", "p95 end to end": "<= 8 s"}, [
        ("check_address 96% -> 99%", with_(ADDRESS, "check_address", success=0.99), None),
        ("check_address retried once", ADDRESS, "check_address"),
        ("find_parcel 99.8% -> 100%", with_(ADDRESS, "find_parcel", success=1.0), None),
        ("reroute 2.9 s -> 1.5 s", with_(ADDRESS, "reroute", mean_s=1.5), None),
    ])
    report("Pickup request", PICKUP, {"completion": ">= 97%"}, [
        ("book_courier 97.5% -> 99.5%", with_(PICKUP, "book_courier", success=0.995), None),
        ("send_receipt 99.7% -> 100%", with_(PICKUP, "send_receipt", success=1.0), None),
        ("price_quote 1.8 s -> 0.9 s", with_(PICKUP, "price_quote", mean_s=0.9), None),
    ])
