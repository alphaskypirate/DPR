from cpu_time_unit import get_cpu_time_unit

idle_time = 0


def simulate_rrsjf_algorithm(data):
    global idle_time
    idle_time = 0
    
    processes = []
    for _, row in data.iterrows():
        processes.append({
            'id': row['process_id'],
            'arrival': row['arrival_time'],
            'burst': row['burst_time'],
            'remaining': row['burst_time'],
            'completion': 0,
            'waiting': 0,
            'turnaround': 0,
            'response': -1  # first response time
        })
    
    t = 0
    completed = 0
    n = len(processes)
    
    while completed < n:
        # Get arrived processes with remaining > 0
        arrived = [p for p in processes if p['arrival'] <= t and p['remaining'] > 0]
        
        if not arrived:
            t += 1
            idle_time += 1
            continue
        
        # Calculate qtime = average remaining burst of arrived
        total_remaining = sum(p['remaining'] for p in arrived)
        qtime = total_remaining / len(arrived)
        
        # Sort arrived by remaining burst ascending
        arrived.sort(key=lambda p: p['remaining'])
        
        # Execute each in order
        for p in arrived:
            if p['remaining'] <= 0:
                continue
            
            # First response
            if p['response'] == -1:
                p['response'] = t - p['arrival']
            
            execute = min(p['remaining'], qtime)
            t += execute
            p['remaining'] -= execute
            
            if p['remaining'] == 0:
                p['completion'] = t
                p['turnaround'] = p['completion'] - p['arrival']
                p['waiting'] = p['turnaround'] - p['burst']
                completed += 1
    
    # Calculate averages
    total_waiting = sum(p['waiting'] for p in processes)
    total_turnaround = sum(p['turnaround'] for p in processes)
    total_burst = sum(p['burst'] for p in processes)
    total_response = sum(p['response'] for p in processes)
    
    cpu_utilization = total_burst / (total_burst + idle_time) if total_burst + idle_time > 0 else 0
    throughput = n / ((total_burst + idle_time) * get_cpu_time_unit()) if total_burst + idle_time > 0 else 0
    average_waiting_time = (total_waiting * get_cpu_time_unit()) / n
    average_turnaround_time = (total_turnaround * get_cpu_time_unit()) / n
    average_response_time = (total_response * get_cpu_time_unit()) / n
    
    print('Round Robin SJF algorithm results:')
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
