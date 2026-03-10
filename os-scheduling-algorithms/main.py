import os
import sys

import pandas as pd

sys.path.append(os.path.relpath("First-Come-First-Serve-scheduling"))
sys.path.append(os.path.relpath("Priority-Scheduling"))
sys.path.append(os.path.relpath("Round-Robin-scheduling"))
sys.path.append(os.path.relpath("Shortest-Job-First-scheduling"))
sys.path.append(os.path.relpath("WOA-Dynamic-Round-Robin-scheduling"))

from FCFS import simulate_fcfs_algorithm
from SJF_np import simulate_sjf_np_algorithm
from SJF_p import simulate_sjf_p_algorithm
from RR import simulate_rr_algorithm
from priority_p import simulate_priority_p_algorithm
from priority_np import simulate_priority_np_algorithm
from WOADRR import woa_optimize_assignment_quantum

if __name__ == "__main__":
    # read data
    data = pd.read_csv("db/data_set.csv")

    # fcfs algorithm
    simulate_fcfs_algorithm(data)

    # sjf non preemptive algorithm
    simulate_sjf_np_algorithm(data)

    # sjf preemptive algorithm
    simulate_sjf_p_algorithm(data)

    # round robin preemptive algorithm
    quantum = 1
    simulate_rr_algorithm(data, quantum)

    # WOA-optimized RR algorithm
    import numpy as np
    tasks = [{"pid": row["process_id"], "burst_time": row["burst_time"]} for _, row in data.iterrows()]
    num_processors = 2
    quantum_min = 1
    quantum_max = 5
    population_size = 10
    max_iter = 30
    from WOADRR import simulate_rr_algorithm
    best_whale, best_fitness, progress = woa_optimize_assignment_quantum(
        tasks, num_processors=num_processors, quantum_min=quantum_min, quantum_max=quantum_max,
        population_size=population_size, max_iter=max_iter, random_seed=42, verbose=False
    )
    assignment, quantums = best_whale
    processor_queues = [[] for _ in range(num_processors)]
    for i, proc in enumerate(assignment):
        processor_queues[proc].append(tasks[i])
    for idx, queue in enumerate(processor_queues):
        # Create a DataFrame for this processor's queue
        if queue:
            queue_df = pd.DataFrame({
                'process_id': [t['pid'] for t in queue],
                'burst_time': [t['burst_time'] for t in queue]
            })
            simulate_rr_algorithm(queue_df, quantums[idx], verbose=True, woa_label=True)

    # priority non preemptive algorithm
    simulate_priority_np_algorithm(data)

    # priority preemptive algorithm
    simulate_priority_p_algorithm(data)
