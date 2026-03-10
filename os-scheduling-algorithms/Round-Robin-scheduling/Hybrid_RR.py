from cpu_time_unit import get_cpu_time_unit
from collections import deque

idle_time = 0


def simulate_hrr_algorithm(data):
    global idle_time
    idle_time = 0
    processes = data['process_id'].tolist()
    burst_times = data['burst_time'].tolist()
    n = len(processes)
    
    # Initialize remaining burst times
    remaining_bt = burst_times.copy()
    completion_time = [0] * n
    waiting_time = [0] * n
    turnaround_time = [0] * n
    response_time = [0] * n
    
    # Ready queue as list of indices
    ready_queue = deque(range(n))
    time = 0
    first_response = [False] * n
    
    while ready_queue:
        # Sort ready queue by remaining burst time ascending
        ready_queue = deque(sorted(ready_queue, key=lambda i: remaining_bt[i]))
        
        # Set quantum to remaining burst time of first process
        if ready_queue:
            quantum = remaining_bt[ready_queue[0]]
        else:
            break
        
        # Temp queue for this cycle
        temp_queue = ready_queue.copy()
        ready_queue.clear()
        
        while temp_queue:
            i = temp_queue.popleft()
            
            # Response time for first execution
            if not first_response[i]:
                response_time[i] = time - 0  # assuming arrival 0
                first_response[i] = True
            
            # Allocate CPU
            executed = min(quantum, remaining_bt[i])
            time += executed
            remaining_bt[i] -= executed
            
            if remaining_bt[i] == 0:
                # Process completed
                completion_time[i] = time
                turnaround_time[i] = completion_time[i] - 0  # arrival 0
                waiting_time[i] = turnaround_time[i] - burst_times[i]
            else:
                # Put back to ready queue
                ready_queue.append(i)
    
    # Calculate averages
    total_waiting = sum(waiting_time)
    total_turnaround = sum(turnaround_time)
    total_burst = sum(burst_times)
    total_response = sum(response_time)
    
    cpu_utilization = total_burst / (total_burst + idle_time) if total_burst + idle_time > 0 else 0
    throughput = n / ((total_burst + idle_time) * get_cpu_time_unit()) if total_burst + idle_time > 0 else 0
    average_waiting_time = (total_waiting * get_cpu_time_unit()) / n
    average_turnaround_time = (total_turnaround * get_cpu_time_unit()) / n
    average_response_time = (total_response * get_cpu_time_unit()) / n
    
    print('Hybrid Round Robin algorithm results:')
    print("Throughput = %.4f" % throughput)
    print("CPU utilization = %.2f" % cpu_utilization)
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
