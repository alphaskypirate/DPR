"""Synthetic process dataset generator.

The four workload scenarios follow Chapter 3 (Test Case Generation) of the thesis:

    burst time    low  = short CPU bursts, 1 - 50 time units
                  high = long CPU bursts, 200 - 500 time units
    arrival time  low  = dense arrivals concentrated early in the timeline, 0 - 20 time units
                  high = arrivals dispersed over a long horizon, 1 - 100 time units

Usage (from this folder):
    python process_generator.py                   interactive menu
    python process_generator.py --all             write all 4 scenarios to db/scenarios/
    python process_generator.py --all --seeds 1 2 3 -n 100
    python process_generator.py --scenario high_burst_low_arrival -n 100 --seed 7 --out db/data_set.csv

The output CSV has the columns process_id, arrival_time, priority, burst_time. Process ids follow
arrival order. Use --seed to make a dataset reproducible.
"""
import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd

BURST_RANGES = {"low": (1, 50), "high": (200, 500)}      # inclusive, Chapter 3
ARRIVAL_RANGES = {"low": (0, 20), "high": (1, 100)}      # inclusive, Chapter 3

SCENARIOS = {
    "low_burst_high_arrival": ("low", "high"),
    "high_burst_high_arrival": ("high", "high"),
    "low_burst_low_arrival": ("low", "low"),
    "high_burst_low_arrival": ("high", "low"),
}
SCENARIO_LABELS = {
    "low_burst_high_arrival": "Low burst time, high arrival time",
    "high_burst_high_arrival": "High burst time, high arrival time",
    "low_burst_low_arrival": "Low burst time, low arrival time",
    "high_burst_low_arrival": "High burst time, low arrival time",
}

SCRIPT_DIR = Path(__file__).resolve().parent
DB_DIR = SCRIPT_DIR / "db"
SCENARIO_DIR = DB_DIR / "scenarios"


def make_dataset(n, burst_range, arrival_range, seed=None):
    """Return a DataFrame with n processes (ranges are inclusive)."""
    rng = np.random.default_rng(seed)
    burst = rng.integers(burst_range[0], burst_range[1] + 1, size=n)
    arrival = np.sort(rng.integers(arrival_range[0], arrival_range[1] + 1, size=n))
    process_id = np.arange(1, n + 1)
    priority = rng.permutation(process_id)
    return pd.DataFrame({"process_id": process_id, "arrival_time": arrival,
                         "priority": priority, "burst_time": burst})


def make_scenario(name, n=100, seed=None):
    burst_level, arrival_level = SCENARIOS[name]
    return make_dataset(n, BURST_RANGES[burst_level], ARRIVAL_RANGES[arrival_level], seed)


def save_csv(df, path):
    path = Path(path)
    os.makedirs(path.parent, exist_ok=True)
    try:
        df.to_csv(path, index=False)
    except PermissionError as exc:
        print(f"PermissionError writing {path}: {exc}")
        os.chmod(path, 0o666)
        df.to_csv(path, index=False)
    return path


def write_all(n=100, seeds=(1,)):
    """Write every scenario for every seed to db/scenarios/<scenario>_s<seed>.csv."""
    written = []
    for name in SCENARIOS:
        for seed in seeds:
            written.append(save_csv(make_scenario(name, n, seed), SCENARIO_DIR / f"{name}_s{seed}.csv"))
    return written


def _ask_int(prompt, default):
    raw = input(f"{prompt} (default {default}): ").strip()
    return int(raw) if raw else default


def generate_process():
    """Interactive menu (kept for backwards compatibility)."""
    print("---Process Generator---")
    print("Scenarios (Chapter 3 definitions):")
    names = list(SCENARIOS)
    for i, name in enumerate(names, 1):
        b, a = SCENARIOS[name]
        print(f"  {i}) {SCENARIO_LABELS[name]}   burst {BURST_RANGES[b]}, arrival {ARRIVAL_RANGES[a]}")
    print("  5) Custom ranges")
    choice = _ask_int("Choose scenario 1-5", 1)
    n = _ask_int("Number of processes", 100)
    seed_raw = input("Random seed (blank = random): ").strip()
    seed = int(seed_raw) if seed_raw else None

    if choice == 5:
        bl, bh = _ask_int("Minimum burst time", 1), _ask_int("Maximum burst time", 100)
        al, ah = _ask_int("Minimum arrival time", 0), _ask_int("Maximum arrival time", 50)
        df = make_dataset(n, (bl, bh), (al, ah), seed)
    else:
        df = make_scenario(names[choice - 1], n, seed)

    out = save_csv(df, DB_DIR / "data_set.csv")
    print(f"{n} processes written to {out}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic process datasets (thesis scenarios).")
    parser.add_argument("--all", action="store_true", help="write all four scenarios to db/scenarios/")
    parser.add_argument("--scenario", choices=list(SCENARIOS), help="generate one scenario")
    parser.add_argument("-n", type=int, default=100, help="number of processes (default 100)")
    parser.add_argument("--seed", type=int, default=None, help="random seed for --scenario")
    parser.add_argument("--seeds", type=int, nargs="+", default=[1], help="seeds for --all (default: 1)")
    parser.add_argument("--out", default=None, help="output CSV for --scenario (default db/data_set.csv)")
    args = parser.parse_args()

    if args.all:
        for path in write_all(args.n, args.seeds):
            print("wrote", path)
    elif args.scenario:
        out = save_csv(make_scenario(args.scenario, args.n, args.seed), args.out or DB_DIR / "data_set.csv")
        print(f"{args.n} processes ({SCENARIO_LABELS[args.scenario]}) written to {out}")
    else:
        generate_process()


if __name__ == "__main__":
    main()
