from collections import deque

from cpu_time_unit import get_cpu_time_unit


def simulate_rr_algorithm(data, quantum, verbose=True):
    """Arrival-aware Round Robin on one CPU.

    - A process joins the ready queue at its arrival time (ties: process order).
    - A preempted process goes behind the processes that arrived while it was running.
    - The CPU idles when no process is ready.
    - waiting = completion - arrival - burst, turnaround = completion - arrival,
      response = first CPU time - arrival.
    If `data` has no `arrival_time` column, every process is assumed to arrive at t=0.
    """
    burst = data['burst_time'].tolist()
    n = len(burst)
    arrival = data['arrival_time'].tolist() if 'arrival_time' in data.columns else [0] * n

    remaining = burst.copy()
    first_run = [None] * n
    completion = [0] * n

    pending = sorted(range(n), key=lambda i: (arrival[i], i))  # not yet arrived
    nxt = 0
    ready = deque()
    t = 0
    idle_time = 0
    done = 0

    def admit(now):
        nonlocal nxt
        while nxt < n and arrival[pending[nxt]] <= now:
            ready.append(pending[nxt])
            nxt += 1

    while done < n:
        admit(t)
        if not ready:
            # CPU idle until the next process arrives
            idle_time += arrival[pending[nxt]] - t
            t = arrival[pending[nxt]]
            admit(t)

        i = ready.popleft()
        if first_run[i] is None:
            first_run[i] = t

        run = min(quantum, remaining[i])
        t += run
        remaining[i] -= run
        admit(t)  # arrivals during this slice queue ahead of the preempted process

        if remaining[i] > 0:
            ready.append(i)
        else:
            completion[i] = t
            done += 1

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
        print('RR preemptive algorithm results: ')
        print("Average waiting time = %.4f " % average_waiting_time)
        print("Average turn around time = %.4f " % average_turnaround_time)
        print("Average response time = %.4f \n" % average_response_time)

    return {
        'n': str(n),
        'throughput': "%.4f" % throughput,
        'cpu_util': "%.2f" % cpu_utilization,
        'awt': "%.4f" % average_waiting_time,
        'att': "%.4f" % average_turnaround_time,
        'art': "%.4f" % average_response_time
    }
