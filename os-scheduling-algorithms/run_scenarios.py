"""Run the four thesis workload scenarios and compare the Round Robin family.

Scenarios (Chapter 3): low/high burst time x low/high arrival time, single processor.
For every scenario and every dataset seed the following are simulated on the same data:

    RR (q=10)             Round Robin with a fixed quantum of 10 time units
    RR (tuned q)          Round Robin with the best fixed quantum (every integer scanned)
    HRR                   Hybrid Round Robin
    RR-SJF                Round Robin with SJF ordering
    WOA-DRR               WOA optimizes a time quantum for every process
    WOA-DRR + order       same, and WOA also optimizes the ready-queue order

All times are in simulated time units. Results are written to results/scenario_results.json.

Usage (from this folder):   python run_scenarios.py [--seeds 1 2 3] [-n 100] [--workers 4]
"""
import argparse
import contextlib
import io
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
for folder in ("Round-Robin-scheduling", "WOA-Dynamic-Round-Robin-scheduling"):
    sys.path.append(str(BASE_DIR / folder))
sys.path.append(str(BASE_DIR))

import cpu_time_unit

cpu_time_unit.CPU_TIME_UNIT = 1  # report raw simulated time units instead of scaled seconds

import pandas as pd

from Hybrid_RR import simulate_hrr_algorithm
from RR import simulate_rr_algorithm
from RRSJF import simulate_rrsjf_algorithm
from process_generator import SCENARIOS, SCENARIO_LABELS, make_scenario, save_csv, SCENARIO_DIR
from woa_drr import baseline_rr, evaluate, fitness_of, woa_optimize

ALGORITHMS = ["RR (q=10)", "RR (tuned q)", "HRR", "RR-SJF", "WOA-DRR", "WOA-DRR + order"]
FIXED_QUANTUM = 10
POPULATION, ITERATIONS = 40, 150


def _metrics(d):
    return {"awt": float(d["awt"]), "att": float(d["att"]), "art": float(d["art"])}


def _quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


def run_one(job):
    name, seed, n = job
    df = make_scenario(name, n, seed)
    save_csv(df, SCENARIO_DIR / f"{name}_s{seed}.csv")
    bursts = [float(b) for b in df["burst_time"]]
    arrivals = [float(a) for a in df["arrival_time"]]
    out = {}

    out["RR (q=10)"] = _metrics(_quiet(simulate_rr_algorithm, df, FIXED_QUANTUM, False))

    best = min(range(1, int(max(bursts)) + 1),
               key=lambda q: fitness_of(baseline_rr(bursts, 1, q, 0.0, arrivals)))
    m = baseline_rr(bursts, 1, best, 0.0, arrivals)
    out["RR (tuned q)"] = {"awt": m["awt"], "att": m["att"], "art": m["art"], "quantum": best}

    out["HRR"] = _metrics(_quiet(simulate_hrr_algorithm, df, False))
    out["RR-SJF"] = _metrics(_quiet(simulate_rrsjf_algorithm, df))

    for label, order in (("WOA-DRR", False), ("WOA-DRR + order", True)):
        assign, quantums, o, _, _ = woa_optimize(bursts, 1, 1, None, POPULATION, ITERATIONS, 0.0, seed,
                                                 False, True, order, arrivals)
        m = evaluate(assign, quantums, bursts, 1, 0.0, o, arrivals)
        out[label] = {"awt": m["awt"], "att": m["att"], "art": m["art"]}

    stats = {"n": n, "total_burst": float(sum(bursts)), "mean_burst": sum(bursts) / n,
             "min_burst": min(bursts), "max_burst": max(bursts),
             "min_arrival": min(arrivals), "max_arrival": max(arrivals)}
    print(f"done {name} seed {seed}", flush=True)
    return name, seed, out, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("-n", type=int, default=100)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    jobs = [(name, seed, args.n) for name in SCENARIOS for seed in args.seeds]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run_one, jobs))

    summary = {}
    for name in SCENARIOS:
        runs = [(seed, out, stats) for nm, seed, out, stats in results if nm == name]
        mean = {alg: {k: sum(r[1][alg][k] for r in runs) / len(runs) for k in ("awt", "att", "art")}
                for alg in ALGORITHMS}
        summary[name] = {
            "label": SCENARIO_LABELS[name],
            "mean": mean,
            "per_seed": {str(seed): out for seed, out, _ in runs},
            "dataset_stats": {str(seed): stats for seed, _, stats in runs},
            "tuned_quantum": {str(seed): out["RR (tuned q)"]["quantum"] for seed, out, _ in runs},
        }

    os.makedirs(BASE_DIR / "results", exist_ok=True)
    path = BASE_DIR / "results" / "scenario_results.json"
    path.write_text(json.dumps({"n": args.n, "seeds": args.seeds, "fixed_quantum": FIXED_QUANTUM,
                                "population": POPULATION, "iterations": ITERATIONS, "scenarios": summary},
                               indent=2), encoding="utf-8")

    for name, s in summary.items():
        print(f"\n{s['label']}  (mean of {len(args.seeds)} datasets, time units)")
        print(f"{'algorithm':<18}{'AWT':>12}{'ATT':>12}{'ART':>12}")
        for alg in ALGORITHMS:
            m = s["mean"][alg]
            print(f"{alg:<18}{m['awt']:>12.2f}{m['att']:>12.2f}{m['art']:>12.2f}")
    print("\nsaved", path)


if __name__ == "__main__":
    main()
