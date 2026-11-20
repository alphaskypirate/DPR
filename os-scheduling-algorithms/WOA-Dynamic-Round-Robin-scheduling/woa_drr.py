"""WOA-optimized Dynamic Round Robin (per-process time quantum).

Each whale is a continuous position vector:
    x[0:n]    -> processor of each process   (floor, in [0, P))
    x[n:2n]   -> log of each process' quantum (round(exp(x)), in [q_min, q_max])
    x[2n:3n]  -> ready-queue priority key of each process (only if optimize_order=True);
                 inside a processor the queue is sorted by this key (random-key encoding)
Positions are moved with the standard Whale Optimization Algorithm (Mirjalili & Lewis, 2016):
shrinking encirclement, spiral bubble-net attack, and random-whale exploration.

With use_arrival / arrivals the simulation honours arrival times (see simulate_drr).
Fitness = average waiting time + response_weight * average response time over ALL processes
(plus optional context-switch cost), so it works the same for 1 or P processors and compares
directly against plain RR. response_weight=0 optimizes waiting time only (the optimizer then
lets most processes run to completion, which wrecks response time); larger values keep
quantums small enough that processes get the CPU quickly, the reason to use RR at all.

Seeding (seed_population=True): part of the initial population is filled with the best
plain-RR solutions (fixed quantum scanned over every integer value, round-robin or
load-balanced assignment). Because elitism keeps the best whale, WOA-DRR is therefore never
worse than the best fixed-quantum RR; what it finds beyond that is the real improvement.
"""
from collections import deque

import numpy as np

from cpu_time_unit import get_cpu_time_unit


def simulate_drr(bursts, quantums, context_switch=0.0, arrivals=None, keys=None):
    """Round Robin on ONE processor where every process has its own quantum.

    arrivals: arrival time of each process (default: all 0).
    keys:     priority keys; processes that become ready in the same scheduling event
              (e.g. everything at t=0, or everything that arrived during the last slice)
              enter the ready queue in ascending key order (default: list order).
    A preempted process re-enters the queue behind the processes that arrived while it ran.
    The CPU idles when nothing is ready. Returns (waiting, turnaround, response, makespan),
    where waiting = finish - arrival - burst and response = first start - arrival.
    """
    n = len(bursts)
    arrivals = [0.0] * n if arrivals is None else arrivals
    keys = list(range(n)) if keys is None else keys
    remaining = list(bursts)
    waiting, turnaround, response = [0.0] * n, [0.0] * n, [0.0] * n
    started = [False] * n
    pending = sorted(range(n), key=lambda i: (arrivals[i], keys[i]))
    nxt = 0
    ready = deque()
    t = 0.0
    done = 0
    ran_before = False

    def admit():
        nonlocal nxt
        batch = []
        while nxt < n and arrivals[pending[nxt]] <= t:
            batch.append(pending[nxt])
            nxt += 1
        batch.sort(key=lambda i: keys[i])
        ready.extend(batch)

    while done < n:
        admit()
        idle = False
        if not ready:                       # CPU idle until the next arrival
            t = arrivals[pending[nxt]]
            idle = True
            admit()
        i = ready.popleft()
        if ran_before and not idle:
            t += context_switch
            admit()
        ran_before = True
        if not started[i]:
            response[i] = t - arrivals[i]
            started[i] = True
        run = min(quantums[i], remaining[i])
        t += run
        remaining[i] -= run
        admit()
        if remaining[i] > 0:
            ready.append(i)
        else:
            turnaround[i] = t - arrivals[i]
            waiting[i] = turnaround[i] - bursts[i]
            done += 1
    return waiting, turnaround, response, t


def evaluate(assignment, quantums, bursts, num_processors, context_switch=0.0, order=None, arrivals=None):
    """Simulate every processor queue. Returns a dict of raw (unscaled) metrics.

    order:    optional per-process priority keys (see simulate_drr).
    arrivals: optional arrival times; None means every process is ready at t=0.
    """
    n = len(bursts)
    wait = tat = resp = 0.0
    makespans = []
    for p in range(num_processors):
        idx = [i for i in range(n) if assignment[i] == p]
        if not idx:
            makespans.append(0.0)
            continue
        w, tt, r, mk = simulate_drr(
            [bursts[i] for i in idx], [quantums[i] for i in idx], context_switch,
            None if arrivals is None else [arrivals[i] for i in idx],
            None if order is None else [order[i] for i in idx])
        wait += sum(w)
        tat += sum(tt)
        resp += sum(r)
        makespans.append(mk)
    return {"awt": wait / n, "att": tat / n, "art": resp / n, "makespan": max(makespans),
            "total_burst": float(sum(bursts))}


def _decode(x, n, num_processors, q_min, q_max, optimize_order):
    assignment = np.minimum(np.floor(x[:n]).astype(int), num_processors - 1).tolist()
    quantums = np.clip(np.rint(np.exp(x[n:2 * n])), q_min, q_max).astype(int).tolist()
    order = x[2 * n:3 * n].tolist() if optimize_order else None
    return assignment, quantums, order


def _encode(assignment, quantums, order, n, optimize_order):
    parts = [np.asarray(assignment, float) + 0.5, np.log(np.asarray(quantums, float))]
    if optimize_order:
        parts.append(np.asarray(order if order is not None else np.arange(n) / n, float))
    return np.concatenate(parts)


def _seeds(bursts, num_processors, q_min, q_max, context_switch, optimize_order, arrivals=None,
           response_weight=1.0, top_k=5):
    """Best plain-RR solutions as starting whales (scan every integer quantum)."""
    n = len(bursts)
    dealt = [i % num_processors for i in range(n)]
    # longest-processing-time load balancing (only differs from `dealt` when P > 1)
    loads, balanced = [0.0] * num_processors, [0] * n
    for i in sorted(range(n), key=lambda i: -bursts[i]):
        p = loads.index(min(loads))
        balanced[i] = p
        loads[p] += bursts[i]
    candidates = []
    for name, assign in (("dealt", dealt), ("balanced", balanced)):
        if name == "balanced" and num_processors == 1:
            continue
        for q in range(q_min, q_max + 1):
            m = evaluate(assign, [q] * n, bursts, num_processors, context_switch, None, arrivals)
            candidates.append((m["awt"] + response_weight * m["art"], assign, q))
    candidates.sort(key=lambda c: c[0])
    return [_encode(a, [q] * n, None, n, optimize_order) for _, a, q in candidates[:top_k]]


def woa_optimize(bursts, num_processors=1, q_min=1, q_max=None, population_size=40,
                 max_iter=150, context_switch=0.0, random_seed=None, verbose=False,
                 seed_population=True, optimize_order=False, arrivals=None, response_weight=1.0):
    """Run WOA. Returns (assignment, quantums, order, best_fitness, progress)."""
    bursts = [float(b) for b in bursts]
    n = len(bursts)
    q_max = int(q_max if q_max is not None else max(bursts))
    rng = np.random.default_rng(random_seed)
    dims = 3 * n if optimize_order else 2 * n

    lb = [np.zeros(n), np.full(n, np.log(q_min))]
    ub = [np.full(n, num_processors - 1e-9), np.full(n, np.log(q_max))]
    if optimize_order:
        lb.append(np.zeros(n))
        ub.append(np.ones(n))
    lb, ub = np.concatenate(lb), np.concatenate(ub)

    def cost(x):
        a, q, o = _decode(x, n, num_processors, q_min, q_max, optimize_order)
        m = evaluate(a, q, bursts, num_processors, context_switch, o, arrivals)
        return m["awt"] + response_weight * m["art"]

    X = lb + rng.random((population_size, dims)) * (ub - lb)
    if seed_population:
        for k, s in enumerate(_seeds(bursts, num_processors, q_min, q_max, context_switch,
                                     optimize_order, arrivals, response_weight)[:population_size]):
            X[k] = np.clip(s, lb, ub)
    fit = np.array([cost(x) for x in X])
    best_i = int(fit.argmin())
    best_x, best_f = X[best_i].copy(), float(fit[best_i])
    progress = [best_f]

    for t in range(max_iter):
        a = 2.0 - 2.0 * t / max_iter          # linearly 2 -> 0
        for i in range(population_size):
            A = 2 * a * rng.random() - a
            C = 2 * rng.random()
            l = rng.uniform(-1, 1)
            if rng.random() < 0.5:
                if abs(A) < 1:                 # encircle the best whale (exploitation)
                    X[i] = best_x - A * np.abs(C * best_x - X[i])
                else:                          # search around a random whale (exploration)
                    xr = X[rng.integers(population_size)]
                    X[i] = xr - A * np.abs(C * xr - X[i])
            else:                              # spiral bubble-net attack (b = 1)
                X[i] = np.abs(best_x - X[i]) * np.exp(l) * np.cos(2 * np.pi * l) + best_x
            X[i] = np.clip(X[i], lb, ub)
            fit[i] = cost(X[i])
            if fit[i] < best_f:
                best_x, best_f = X[i].copy(), float(fit[i])
        progress.append(best_f)
        if verbose and t % 10 == 0:
            print(f"Iteration {t}: best fitness (awt + w*art) = {best_f:.4f}")

    assignment, quantums, order = _decode(best_x, n, num_processors, q_min, q_max, optimize_order)
    return assignment, quantums, order, best_f, progress


def run_woa_drr(data, num_processors=1, q_min=1, q_max=None, population_size=40, max_iter=150,
                context_switch=0.0, random_seed=42, verbose=False,
                seed_population=True, optimize_order=False, use_arrival=False, response_weight=1.0):
    """Optimize, then report combined metrics in the same format as the other simulators."""
    bursts = data["burst_time"].tolist()
    n = len(bursts)
    arrivals = [float(a) for a in data["arrival_time"]] if use_arrival else None
    assignment, quantums, order, _, progress = woa_optimize(
        bursts, num_processors, q_min, q_max, population_size, max_iter,
        context_switch, random_seed, False, seed_population, optimize_order, arrivals,
        response_weight)
    m = evaluate(assignment, quantums, [float(b) for b in bursts], num_processors, context_switch, order, arrivals)
    u = get_cpu_time_unit()
    busy = m["makespan"] * num_processors
    result = {
        "n": str(n),
        "throughput": "%.4f" % (n / (m["makespan"] * u)),
        "cpu_util": "%.2f" % (m["total_burst"] / busy),
        "awt": "%.4f" % (m["awt"] * u),
        "att": "%.4f" % (m["att"] * u),
        "art": "%.4f" % (m["art"] * u),
        "assignment": assignment, "quantums": quantums, "order": order, "progress": progress,
    }
    if verbose:
        print(f"WOA-DRR ({num_processors} processor(s)) results:")
        print("Average waiting time = %s\nAverage turn around time = %s\nAverage response time = %s\n"
              % (result["awt"], result["att"], result["art"]))
    return result


def baseline_rr(bursts, num_processors=1, q=1, context_switch=0.0, arrivals=None):
    """Plain RR with ONE fixed quantum; processes dealt out to processors in turn."""
    n = len(bursts)
    assignment = [i % num_processors for i in range(n)]
    return evaluate(assignment, [q] * n, [float(b) for b in bursts], num_processors, context_switch,
                    None, arrivals)
