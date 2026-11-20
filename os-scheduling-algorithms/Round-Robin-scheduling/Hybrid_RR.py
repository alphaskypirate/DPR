from cpu_time_unit import get_cpu_time_unit


def simulate_hrr_algorithm(data, verbose=True):
    """Arrival-aware Hybrid Round Robin on one CPU.

    Work proceeds in cycles. At the start of a cycle every process that has arrived and is
    unfinished is sorted by remaining burst (shortest first) and the quantum is set to the
    smallest remaining burst. Each process then runs once for min(quantum, remaining).
    Processes that arrive during a cycle join at the start of the next cycle. The CPU idles
    when nothing is ready. waiting = completion - arrival - burst, turnaround = completion -
    arrival, response = first CPU time - arrival. Without an `arrival_time` column every
    process is assumed to arrive at t=0.
    """
    burst = data['burst_time'].tolist()
    n = len(burst)
    arrival = data['arrival_time'].tolist() if 'arrival_time' in data.columns else [0] * n

    remaining = burst.copy()
    first_run = [None] * n
    completion = [0] * n

    pending = sorted(range(n), key=lambda i: (arrival[i], i))
    nxt = 0
    ready = []
    t = 0
    idle_time = 0
    done = 0

    while done < n:
        while nxt < n and arrival[pending[nxt]] <= t:
            ready.append(pending[nxt])
            nxt += 1

        if not ready:
            # CPU idle until the next process arrives
            idle_time += arrival[pending[nxt]] - t
            t = arrival[pending[nxt]]
            continue

        # one cycle: shortest remaining first, quantum = smallest remaining burst
        ready.sort(key=lambda i: (remaining[i], i))
        quantum = remaining[ready[0]]
        cycle, ready = ready, []

        for i in cycle:
            if first_run[i] is None:
                first_run[i] = t
            run = min(quantum, remaining[i])
            t += run
            remaining[i] -= run
            if remaining[i] == 0:
                completion[i] = t
                done += 1
            else:
                ready.append(i)

    turnaround = [completion[i] - arrival[i] for i in range(n)]
    waiting = [turnaround[i] - burst[i] for i in range(n)]
    response = [first_run[i] - arrival[i] for i in range(n)]

    unit = get_cpu_time_unit()
    total_burst = sum(burst)
    busy_window = total_burst + idle_time
    cpu_utilization = total_burst / busy_window if busy_window > 0 else 0
    throughput = n / (busy_window * unit) if busy_window > 0 else 0
    average_waiting_time = sum(waiting) * unit / n
    average_turnaround_time = sum(turnaround) * unit / n
    average_response_time = sum(response) * unit / n

    if verbose:
        print('Hybrid Round Robin algorithm results:')
        print("Average waiting time = %.4f" % average_waiting_time)
        print("Average turn around time = %.4f" % average_turnaround_time)
        print("Average response time = %.4f" % average_response_time)
        print()

    return {
        'n': str(n),
        'throughput': "%.4f" % throughput,
        'cpu_util': "%.2f" % cpu_utilization,
        'awt': "%.4f" % average_waiting_time,
        'att': "%.4f" % average_turnaround_time,
        'art': "%.4f" % average_response_time
    }
