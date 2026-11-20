"""Fair comparison: plain RR vs WOA-DRR on the SAME number of processors.

Columns (average waiting time, raw time units; lower is better):
  RR q=1 / q=10   plain RR with a typical fixed quantum
  RR best q       plain RR with the best fixed quantum (brute force over every integer)
  WOA quantum     WOA-DRR, per-process quantum + processor assignment   (seeded)
  WOA +order      same, and WOA also chooses the ready-queue order      (seeded)
  SJF-ref         non-preemptive shortest-job-first, dealt over P processors (reference only)

Usage (from the os-scheduling-algorithms folder):
    python compare_woa.py [context_switch_cost] [csv_path] [--arrival]
  --arrival   honour the arrival_time column (default: every process ready at t=0)
"""
import sys

sys.path.append("WOA-Dynamic-Round-Robin-scheduling")
import pandas as pd
from woa_drr import baseline_rr, woa_optimize

args = [a for a in sys.argv[1:] if not a.startswith("--")]
USE_ARRIVAL = "--arrival" in sys.argv
CS = float(args[0]) if len(args) > 0 else 0.0
CSV = args[1] if len(args) > 1 else "db/data_set.csv"
SEEDS = [1, 2, 3]
POP, ITER = 40, 150

data = pd.read_csv(CSV)
bursts = data["burst_time"].tolist()
arrivals = [float(a) for a in data["arrival_time"]] if USE_ARRIVAL else None
arr = arrivals if arrivals is not None else [0.0] * len(bursts)


def sjf_reference(P):
    """Non-preemptive SJF on each of P processors (processes dealt out in index order)."""
    total = 0.0
    for p in range(P):
        procs = [(arr[i], bursts[i]) for i in range(p, len(bursts), P)]
        t, left = 0.0, sorted(procs)
        while left:
            ready = [x for x in left if x[0] <= t]
            if not ready:
                t = left[0][0]
                continue
            job = min(ready, key=lambda x: x[1])
            left.remove(job)
            total += t - job[0]
            t += job[1]
    return total / len(bursts)


print(f"{CSV} | arrival times {'ON' if USE_ARRIVAL else 'off'} | context switch = {CS} | seeds {SEEDS}", flush=True)
print(f"{'procs':<6}{'RR q=1':>11}{'RR q=10':>11}{'RR best q':>11}{'WOA quantum':>13}{'WOA +order':>12}{'SJF-ref':>10}", flush=True)
for P in (1, 2, 3):
    rr1 = baseline_rr(bursts, P, 1, CS, arrivals)["awt"]
    rr10 = baseline_rr(bursts, P, 10, CS, arrivals)["awt"]
    rrbest = min(baseline_rr(bursts, P, q, CS, arrivals)["awt"] for q in range(1, int(max(bursts)) + 1))
    w1 = [woa_optimize(bursts, P, 1, None, POP, ITER, CS, s, False, True, False, arrivals)[3] for s in SEEDS]
    w2 = [woa_optimize(bursts, P, 1, None, POP, ITER, CS, s, False, True, True, arrivals)[3] for s in SEEDS]
    print(f"{P:<6}{rr1:>11.1f}{rr10:>11.1f}{rrbest:>11.1f}{sum(w1) / len(w1):>13.1f}{sum(w2) / len(w2):>12.1f}"
          f"{sjf_reference(P):>10.1f}", flush=True)
