import os
from pathlib import Path
import numpy as np
import pandas as pd


def generate_process():
    print('---Process Generator---')
    n = int(input('Please insert the number of precesses: '))

    burst_time = np.random.randint(low=1, high=50, size=n)
    burst_time = np.ceil(burst_time).astype(int)
    # Arrival time configuration
    print('Arrival time mode:')
    print('  1) Fixed step (start + gap)')
    print('  2) Random uniform range')
    mode = input('Choose mode (1/2, default 1): ').strip() or '1'

    if mode == '2':
        low = int(input('Enter minimum arrival time (e.g., 0): ').strip() or '0')
        high = int(input('Enter maximum arrival time (exclusive, e.g., 50): ').strip() or '50')
        arrival_time = np.random.randint(low=low, high=high, size=n)
        arrival_time = np.sort(arrival_time)  # keep non-decreasing arrival order
    else:
        start = int(input('Enter start time (default 0): ').strip() or '0')
        gap = int(input('Enter fixed gap between arrivals (default 2): ').strip() or '2')
        arrival_time = np.arange(start, start + gap * n, gap)
    process_id = np.arange(1, n + 1)
    priority = process_id.copy()
    np.random.shuffle(priority)

    csv_data = np.stack(
        (process_id, arrival_time, priority, burst_time), axis=0)

    data_csv = pd.DataFrame(csv_data).T.set_axis(
        ["process_id", "arrival_time", "priority", "burst_time"], axis="columns"
    )
    # Ensure the target directory exists relative to this script's folder
    script_dir = Path(__file__).resolve().parent  # os-scheduling-algorithms
    db_dir = script_dir / "db"
    os.makedirs(db_dir, exist_ok=True)

    output_csv = db_dir / "data_set.csv"
    try:
        # attempt to write, handle permission issues
        data_csv.to_csv(output_csv, index=False)
    except PermissionError as e:
        # try to change file permissions and retry
        print(f"PermissionError writing {output_csv}: {e}")
        try:
            os.chmod(output_csv, 0o666)
            data_csv.to_csv(output_csv, index=False)
        except Exception as ex:
            print(f"Failed to write even after chmod: {ex}")
            raise
    print(f'{n} process generated in csv file successfully!')


if __name__ == '__main__':
    generate_process()
