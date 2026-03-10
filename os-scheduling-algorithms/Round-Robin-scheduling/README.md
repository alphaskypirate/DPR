## Round Robin Algorithm

This directory contains Python implementations of Round Robin (RR), Hybrid Round Robin (HRR), and Round Robin SJF (RRSJF) algorithms for CPU scheduling. The `RR.py` file contains the implementation of the RR algorithm, the `Hybrid_RR.py` file contains the HRR algorithm, the `RRSJF.py` file contains the RRSJF algorithm, and the `cpu_time_unit.py` file contains a utility function for calculating the CPU time unit.

### Round Robin (RR)

To run the RR algorithm, you can import the `simulate_rr_algorithm()` function from the `RR.py` file and pass in a pandas DataFrame containing the process ID and burst time for each process, as well as the time quantum.

### Hybrid Round Robin (HRR)

The HRR algorithm combines features of SJF and RR with varying time quantum. It sorts the ready queue by remaining burst time and sets the quantum to the remaining burst time of the shortest process, then performs RR with that quantum.

To run the HRR algorithm, import the `simulate_hrr_algorithm()` function from the `Hybrid_RR.py` file and pass in a pandas DataFrame containing the process ID and burst time.

### Round Robin SJF (RRSJF)

The RRSJF algorithm uses a dynamic quantum based on the average remaining burst time of arrived processes, and schedules in SJF order.

To run the RRSJF algorithm, import the `simulate_rrsjf_algorithm()` function from the `RRSJF.py` file and pass in a pandas DataFrame containing the process ID, arrival time, and burst time.

```python
import pandas as pd
from RRSJF import simulate_rrsjf_algorithm

# create a pandas DataFrame with process ID, arrival time, and burst time
data = pd.DataFrame({
    'process_id': [1, 2, 3, 4],
    'arrival_time': [0, 1, 2, 3],
    'burst_time': [5, 4, 3, 2]
})

# run the RRSJF algorithm
results = simulate_rrsjf_algorithm(data)

# print the results
print(results)
```

The output will be a dictionary containing performance metrics similar to other algorithms.

# print the CPU time unit
print(cpu_time_unit)
```

The output will be the CPU time unit, which represents the amount of time it takes for the CPU to perform a single unit
of work.

### Dependencies

The RR algorithm implementation requires the `pandas` library to be installed. You can install it using pip:

```
pip install pandas
```

### Preemptive SJF Algorithm

The Preemptive SJF algorithm is a CPU scheduling algorithm that selects the process with the shortest burst time from
the ready queue and executes it. If a new process arrives with a shorter burst time than the currently executing
process, the currently executing process is preempted and added back to the ready queue. This process continues until
all processes have been completed.

The `simulate_sjf_p_algorithm()` function in `SJF.py` implements the preemptive SJF algorithm using a `PriorityQueue` to
manage the ready queue. The function calculates the completion time, turnaround time, and waiting time for each process
and returns various performance metrics for the algorithm.

### Non-Preemptive SJF Algorithm

The Non-Preemptive SJF algorithm is a CPU scheduling algorithm that selects the process with the shortest burst time
from the ready queue and executes it until completion. This process continues until all processes have been completed.

The `simulate_sjf_np_algorithm()` function in `SJF_np.py` implements the non-preemptive SJF algorithm using
a `PriorityQueue` to manage the ready queue. The function calculates the completion time, turnaround time, and waiting
time for each process and returns various performance metrics for the algorithm.

Both algorithms are designed to minimize the average waiting time of the processes, making them useful in
situationswhere minimizing the turnaround time and improving the response time is crucial. However, these algorithms can
suffer from starvation, where a process with a long burst time may be stuck waiting indefinitely behind other shorter
tasks. Nonetheless, SJF algorithms are commonly used in real-time systems and applications where response time is
critical.

### Note

This implementation of the RR algorithm assumes that the processes are preemptive and that the burst times are sorted in
ascending order. If the burst times are not sorted, you should sort them before running the algorithm.