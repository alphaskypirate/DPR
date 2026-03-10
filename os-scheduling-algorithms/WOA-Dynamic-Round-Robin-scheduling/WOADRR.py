import numpy as np
import random
import pandas as pd
from cpu_time_unit import get_cpu_time_unit

idle_time = 0

def calculate_waiting_time(processes, n, burst_t, waiting_t, quantum):
    global idle_time
    remain_bt = burst_t.copy()
    t = 0
    while True:
        done = True
        for i in range(n):
            if remain_bt[i] > 0:
                done = False
                if remain_bt[i] > quantum:
                    t += quantum
                    remain_bt[i] -= quantum
                else:
                    t += remain_bt[i]
                    waiting_t[i] = t - burst_t[i]
                    remain_bt[i] = 0
            if waiting_t[i] < 0:
                idle_time += abs(waiting_t[i])
                waiting_t[i] = 0
        if done:
            break

def calculate_turnaround_time(processes, n, burst_t, waiting_t, turn_around_t):
    for i in range(n):
        turn_around_t[i] = burst_t[i] + waiting_t[i]

def calculate_response_time(n, burst_t, quantum):
    response_t = 0
    response_t_arr = []
    for i in range(n):
        if i == 0:
            response_t = 0
        else:
            if quantum >= burst_t[i - 1]:
                response_t += burst_t[i - 1]
            else:
                response_t += quantum
        response_t_arr.append(response_t)
    return (sum(response_t_arr) * get_cpu_time_unit()) / n

def simulate_rr_algorithm(data, quantum, verbose=True, woa_label=False):
    processes = data['process_id']
    n = len(processes)
    burst_time = data['burst_time']
    waiting_t = [0] * n
    turn_around_t = [0] * n
    calculate_waiting_time(processes, n, burst_time, waiting_t, quantum)
    calculate_turnaround_time(processes, n, burst_time, waiting_t, turn_around_t)
    total_waiting_t = sum(waiting_t)
    total_turn_around_t = sum(turn_around_t)
    total_burst_t = sum(burst_time)
    cpu_utilization = total_burst_t / (total_burst_t + idle_time)
    throughput = n / ((total_burst_t + idle_time) * get_cpu_time_unit())
    average_waiting_time = (total_waiting_t * get_cpu_time_unit()) / n
    average_turnaround_time = (total_turn_around_t * get_cpu_time_unit()) / n
    avg_response_t = calculate_response_time(n, burst_time, quantum)
    if verbose:
        if woa_label:
            print("WOA-DRR algorithm results:")
        print("Throughput = %.4f" % throughput)
        print(f"CPU utilization = {'%.2f' % cpu_utilization}")
        print("Average waiting time = %.4f " % average_waiting_time)
        print("Average turn around time = %.4f " % average_turnaround_time)
        print("Average response time = %.4f \n" % avg_response_t)
    return {
        'n': str(n),
        'throughput': "%.4f" % throughput,
        'cpu_util': "%.2f" % cpu_utilization,
        'awt': "%.4f" % average_waiting_time,
        'att': "%.4f" % average_turnaround_time,
        'art': "%.4f" % avg_response_t
    }

def rr_schedule(tasks, quantum):
    n = len(tasks)
    if n == 0:
        return 0
    burst_times = [t['burst_time'] for t in tasks]
    waiting_times = [0] * n
    remain_bt = burst_times[:]
    t = 0
    while True:
        done = True
        for i in range(n):
            if remain_bt[i] > 0:
                done = False
                if remain_bt[i] > quantum:
                    t += quantum
                    remain_bt[i] -= quantum
                else:
                    t += remain_bt[i]
                    waiting_times[i] = t - burst_times[i]
                    remain_bt[i] = 0
        if done:
            break
    avg_waiting_time = sum(waiting_times) / n
    return avg_waiting_time

def fitness_assignment(assignment, tasks, num_processors, quantums):
    processor_queues = [[] for _ in range(num_processors)]
    for i, proc in enumerate(assignment):
        processor_queues[proc].append(tasks[i])
    avg_waits = [rr_schedule(queue, quantums[idx]) for idx, queue in enumerate(processor_queues) if queue]
    return max(avg_waits) if avg_waits else float('inf')

def woa_optimize_assignment_quantum(tasks, num_processors=1, quantum_min=1, quantum_max=5, population_size=10, max_iter=10, random_seed=None, verbose=False):
    n = len(tasks)
    if random_seed is not None:
        np.random.seed(random_seed)
        random.seed(random_seed)
    whales = [(np.random.randint(0, num_processors, n).tolist(), [random.randint(quantum_min, quantum_max) for _ in range(num_processors)]) for _ in range(population_size)]
    best_whale = min(whales, key=lambda w: fitness_assignment(w[0], tasks, num_processors, w[1]))
    best_fitness = fitness_assignment(best_whale[0], tasks, num_processors, best_whale[1])
    fitness_progress = [best_fitness]
    a_decay = 2 / max_iter
    for t in range(max_iter):
        a = 2 - t * a_decay
        for i in range(population_size):
            r = random.random()
            A = 2 * a * r - a
            if abs(A) < 1:
                whales[i] = (best_whale[0][:], best_whale[1][:])
            else:
                whales[i] = (random.choice(whales)[0][:], random.choice(whales)[1][:])
            if random.random() < 0.5:
                idx = random.randint(0, n-1)
                whales[i][0][idx] = random.randint(0, num_processors-1)
            if random.random() < 0.5:
                proc_idx = random.randint(0, num_processors-1)
                whales[i][1][proc_idx] = random.randint(quantum_min, quantum_max)
        current_best = min(whales, key=lambda w: fitness_assignment(w[0], tasks, num_processors, w[1]))
        current_fitness = fitness_assignment(current_best[0], tasks, num_processors, current_best[1])
        if current_fitness < best_fitness:
            best_whale = current_best
            best_fitness = current_fitness
        fitness_progress.append(best_fitness)
        if verbose and t % 10 == 0:
            print(f"Iteration {t}: Best max avg waiting time = {best_fitness:.4f}")
    return best_whale, best_fitness, fitness_progress

def rr_metrics(tasks, quantum):
    n = len(tasks)
    if n == 0:
        return {'n': 0, 'throughput': 0, 'cpu_util': 0, 'awt': 0, 'att': 0, 'art': 0}
    burst_times = [t['burst_time'] for t in tasks]
    waiting_times = [0] * n
    remain_bt = burst_times[:]
    t = 0
    idle_time = 0
    while True:
        done = True
        for i in range(n):
            if remain_bt[i] > 0:
                done = False
                if remain_bt[i] > quantum:
                    t += quantum
                    remain_bt[i] -= quantum
                else:
                    t += remain_bt[i]
                    waiting_times[i] = t - burst_times[i]
                    remain_bt[i] = 0
            if waiting_times[i] < 0:
                idle_time += abs(waiting_times[i])
                waiting_times[i] = 0
        if done:
            break
    turn_around_times = [burst_times[i] + waiting_times[i] for i in range(n)]
    total_burst_t = sum(burst_times)
    cpu_utilization = total_burst_t / (total_burst_t + idle_time) if (total_burst_t + idle_time) > 0 else 0
    throughput = n / ((total_burst_t + idle_time)) if (total_burst_t + idle_time) > 0 else 0
    average_waiting_time = sum(waiting_times) / n
    average_turnaround_time = sum(turn_around_times) / n
    average_response_time = sum(waiting_times) / n
    return {
        'n': n,
        'throughput': throughput,
        'cpu_util': cpu_utilization,
        'awt': average_waiting_time,
        'att': average_turnaround_time,
        'art': average_response_time
    }

if __name__ == "__main__":
    data = pd.read_csv("../db/data_set.csv")
    tasks = [{"pid": row["process_id"], "burst_time": row["burst_time"]} for _, row in data.iterrows()]
    num_processors = 2
    quantum_min = 1
    quantum_max = 5
    population_size = 10
    max_iter = 30
    best_whale, best_fitness, progress = woa_optimize_assignment_quantum(
        tasks, num_processors=num_processors, quantum_min=quantum_min, quantum_max=quantum_max,
        population_size=population_size, max_iter=max_iter, random_seed=42, verbose=True
    )
    assignment, quantums = best_whale
    print("Best assignment (task to processor):", assignment)
    print("Best quantums per processor:", quantums)
    print("Best metric (max avg waiting time):", best_fitness)
    processor_queues = [[] for _ in range(num_processors)]
    for i, proc in enumerate(assignment):
        processor_queues[proc].append(tasks[i])
    for idx, queue in enumerate(processor_queues):
        print(f"Processor {idx} queue: {[t['pid'] for t in queue]}")
        metrics = rr_metrics(queue, quantums[idx])
        print(f"  Throughput: {metrics['throughput']:.4f}")
        print(f"  CPU utilization: {metrics['cpu_util']:.2f}")
        print(f"  Average waiting time: {metrics['awt']:.4f}")
        print(f"  Average turn around time: {metrics['att']:.4f}")
        print(f"  Average response time: {metrics['art']:.4f}")
