import os
import sys

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(BASE_DIR, "Round-Robin-scheduling"))
sys.path.append(os.path.join(BASE_DIR, "WOA-Dynamic-Round-Robin-scheduling"))
sys.path.append(BASE_DIR)

from RR import simulate_rr_algorithm
from Hybrid_RR import simulate_hrr_algorithm
from RRSJF import simulate_rrsjf_algorithm
from woa_drr import run_woa_drr

if __name__ == "__main__":
    data = pd.read_csv(os.path.join(BASE_DIR, "db", "data_set.csv"))

    # round robin (fixed quantum)
    simulate_rr_algorithm(data, 10)

    # hybrid round robin
    simulate_hrr_algorithm(data)

    # round robin + SJF
    simulate_rrsjf_algorithm(data)

    # WOA-optimized dynamic RR (per-process quantum), 1 processor like the others
    run_woa_drr(data, num_processors=1, use_arrival=True, verbose=True)
