from drs import drs
import xml
import os
import sys
import numpy as np

def random_period(max_period):
    return np.random.randint(1, max_period + 1) 

def main():
    if len(sys.argv) != 6:
        print(f"Usage: python {sys.argv[0]} <total_util> <num_tasks> <num_sets> <max_period> <out_dir>")
        sys.exit(1)
    total_util = float(sys.argv[1])
    num_tasks = int(sys.argv[2])
    num_sets = int(sys.argv[3])
    max_period = int(sys.argv[4])
    out_dir = sys.argv[5]
    os.mkdir(out_dir)

    for i in range(num_sets):
        with open(f"{out_dir}/{i}.xml", 'w') as f:
            # To be consistent with the previous xml format
            f.write("<system>\n")
            utils = drs(num_tasks, total_util)
            seen_max = -1
            for tau in range(num_tasks):
                period = random_period(max_period)
                seen_max = max(period, seen_max)
                if seen_max != max_period and tau == num_tasks - 1:
                    period = max_period
                util = utils[tau]
                exec_time = period * util
                f.write(f"\t<task p=\"{period}\" e=\"{exec_time}\" u=\"{util}\" prio=\"{tau}\"/>\n")
            f.write("</system>")
            





if __name__ == "__main__":
    main()