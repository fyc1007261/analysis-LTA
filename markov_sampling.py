import pandas as pd
import os
import sys
import time
import copy
import json
import arviz as az

from task import Task
from utils import *
from state import *


def simu_one_hp(tasks, arrivals, sorted_arrival_times, edf):
    hp = get_hyper_period(tasks)
    times = []
    for task in tasks:
        job_time = task.sample_one(hp).tolist()
        times.append(job_time)
    if edf:
        return simulate_one_step_edf(tasks, times, arrivals, copy.deepcopy(sorted_arrival_times))
    else:
        return simulate_one_step(tasks, times, arrivals, copy.deepcopy(sorted_arrival_times))


def simulate_nh(tasks, iters, state_duration,
                nk_dict, edf, burn=2, chains=4):
    state_duration *= 1000
    prev_dlms = dict()  # task -> chain -> dlms
    n_k_requirements = dict()
    n_k_requirements_total = dict()
    per_hp_rates = dict()
    issused_tasks_all_chains = [dict() for i in range(chains)]
    for tau in tasks:
        prev_dlms[tau.id] = [[] for i in range(chains)]
        n_k_requirements[tau.id] = [[] for i in range(chains)]
        n_k_requirements_total[tau.id] = [[] for i in range(chains)]
        per_hp_rates[tau.id] = [[] for i in range(chains)]

    stable = False

    t_stab = round(1000 * 30000 / state_duration)

    for i in range(iters + burn):
        if i % 500 == 0:
            print(f"{sys.argv[1]}: Step {i} out of {iters}")
        for c in range(chains):
            times = []
            start_time = i * state_duration
            arrivals = dict()
            end_time = start_time + state_duration
            # Generate
            for tau in tasks:
                job_time = tau.sample_time_range(
                    start_time, end_time, arrivals).tolist()
                times.append(job_time)
            # print(times)
            sorted_arrival_times = sorted(arrivals.keys())
            sorted_arrival_times.append(end_time)
            dlms = None
            if edf:
                dlms, issused_tasks_all_chains[c] = \
                simulate_non_harmonic_edf(
                    tasks, times, arrivals,
                    sorted_arrival_times,
                    issused_tasks_all_chains[c],
                    start_time,
                    state_duration)

            else:
                dlms, issused_tasks_all_chains[c] = simulate_non_harmonic(
                    tasks, times, arrivals,
                    sorted_arrival_times,
                    issused_tasks_all_chains[c],
                    start_time,
                    state_duration)
            assert len(dlms) == len(tasks)
            for tauid in range(len(dlms)):
                prev_dlms[tauid][c] += dlms[tauid]
                n = nk_dict['n'][str(tauid)]
                k = nk_dict['k'][str(tauid)]
                state_arr = prev_dlms[tauid][c]
                if len(state_arr) < n:
                    continue
                rate, result_arr = n_k_analysis_window(state_arr[:], n, k)

                # n_k_requirements[tauid][c].append(rate)
                n_k_requirements[tauid][c].extend(result_arr)
                if n > 1:
                    prev_dlms[tauid][c] = prev_dlms[tauid][c][-n+1:]
                else:
                    prev_dlms[tauid][c] = []

        
        if i % t_stab == 0 and i > 0:
            good = True
            for tau in tasks:
                least_finished = None
                to_rhat = [[] for c in range(chains)]
                for c in range(chains):
                    if least_finished is None or len(n_k_requirements[tau.id][c]) < least_finished:
                        least_finished = len(n_k_requirements[tau.id][c])
                for c in range(chains):
                    to_rhat[c] = n_k_requirements[tau.id][c][:least_finished]
                chain_az = az.convert_to_dataset(
                    np.array(to_rhat))
                rhat_val = az.rhat(chain_az, method='rank')
                score = float(rhat_val['x'])
                if np.max(score) > 1.0002:
                    print(f"Not good, found {np.max(score)}")
                    good = False
                    break
            if stable and good:
                print(f"Converge in {i} steps")
                break
            else:
                stable = good

    results = []
    for tau in tasks:
        least_finished = None
        to_mean = [[] for c in range(chains)]
        for c in range(chains):
            if least_finished is None or len(n_k_requirements[tau.id][c]) < least_finished:
                least_finished = len(n_k_requirements[tau.id][c])
        for c in range(chains):
            to_mean[c] = n_k_requirements[tau.id][c][:least_finished]

        results.append(np.mean(to_mean))
    return results


def main():
    if len(sys.argv) < 9:
        print(
            f"python {sys.argv[0]} <task_xml> <m_k_json> <chain> <chain_length> <state_length> <edf?>  <uniform?> <suffix>")
        exit(1)

    filename = sys.argv[1]
    task_df = None
    try:
        tasks_df = pd.read_xml(filename)
    except Exception as e:
        print(e)
        exit(1)
    n_k_file = sys.argv[2]
    chains = int(sys.argv[3])
    length = int(sys.argv[4])
    state_duration = int(sys.argv[5])
    edf = int(sys.argv[6])
    uniform = int(sys.argv[7])
    suffix = sys.argv[8]

    Tasks = []
    id = 0
    for task in tasks_df.to_numpy():
        period = task[0]
        exec_mu = task[1]
        prio = task[2]
        exec_time, prob = None, None
        if uniform == 1:
            exec_time, prob = disc_prob_two(exec_mu)
        elif uniform == 0:
            exec_time, prob = disc_prob_two_abnormal(exec_mu)
        elif uniform > 1:
            exec_time, prob = disc_prob(exec_mu, uniform)
        else:
            assert 0
        Tasks.append(Task(id, exec_time, prob, period, prio))
        id += 1

    nk_dict = json.load(open(n_k_file, 'r'))

    start_time = time.time()

    req = simulate_nh(Tasks, length, state_duration,
                      nk_dict, edf, chains=chains)

    print(req)
    end_time = time.time()
    with open(f"{filename[:-4]}-sampling-{suffix}.txt", 'w') as f:
        f.write(f"{end_time-start_time} s\n")
        f.write(f"{req}\n")
    print(f"Wrote to {filename[:-4]}-sampling-{suffix}.txt")


if __name__ == "__main__":
    main()
