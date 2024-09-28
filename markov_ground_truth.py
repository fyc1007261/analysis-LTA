import pandas as pd
import sys
import time

from task import Task
from utils import *
from state import *


def get_dlm_all_iterative(tasks: list, num_probs: list, edf: bool):
    dict_dlm_prob = dict()
    tot_comb = 1
    for prob in num_probs:
        tot_comb *= prob
    print(f"Total {tot_comb}")
    if tot_comb > 2 ** 29:
        print("killed")
        return None, None
    arrivals = get_job_arrivals(tasks)
    sorted_arrival_times = sorted(arrivals.keys())
    sorted_arrival_times.append(round(get_hyper_period(tasks)))

    dlm_init = None
    for idx in range(tot_comb):
        if idx % 100000 == 0:
            print(f"processing {idx} / {tot_comb}: {sys.argv}")
        comb = []
        for tau in range(len(tasks)):
            subidx = idx % num_probs[tau]
            comb.append(subidx)
            idx = int(idx / num_probs[tau])
        prob = 1
        exec_times = []
        for i in range(len(comb)):
            prob *= tasks[i].all_prob_list[comb[i]]
            exec_times.append(tasks[i].all_time_list[comb[i]])
        dlm = None
        if edf:
            dlm = simulate_one_step_edf(tasks, copy.deepcopy(exec_times), 
                                        arrivals, copy.deepcopy(sorted_arrival_times))
        else:
            dlm = simulate_one_step(tasks, copy.deepcopy(exec_times), 
                                    arrivals, copy.deepcopy(sorted_arrival_times))
        if str(dlm) in dict_dlm_prob.keys():
            dict_dlm_prob[str(dlm)] += prob
        else:
            dict_dlm_prob[str(dlm)] = prob
        if dlm_init is None:
            dlm_init = dlm
    return dict_dlm_prob, dlm_init

def get_dict_per_task(tasks: list, dict_dlm_prob: dict): 
    dicts = []
    for i in range(len(tasks)):
        dicts.append(dict())
    for key in sorted(dict_dlm_prob.keys()):
        for tau in range(len(tasks)):
            keytau = eval(key)[tau]
            if str(keytau) in dicts[tau].keys():
                dicts[tau][str(keytau)] += dict_dlm_prob[key]
            else:
                dicts[tau][str(keytau)] = dict_dlm_prob[key]
    return dicts

def merge_2_dicts(dict_tau: dict):
    results = dict()
    sorted_keys = sorted(dict_tau.keys())
    for k1 in sorted_keys:
        k1_list = eval(k1)
        for k2 in sorted_keys:
            k2_list = eval(k2)
            results[str(k1_list + k2_list)] = dict_tau[k1] * dict_tau[k2]
    return results


def get_n_k_per_task(dict_tau, n, k):
    results = 0
    sorted_keys = sorted(dict_tau.keys())
    for i, key1 in enumerate(sorted_keys):
        key1_list = eval(key1)
        for j, key2 in enumerate(sorted_keys):
            key2_list = eval(key2)
            prob = dict_tau[key1] * dict_tau[key2]
            prev_dlms = key1_list
            dlms = key2_list
            state_arr = prev_dlms[-(n-1):] + dlms
            rate, _ = n_k_analysis_window(state_arr, n, k)
            results += prob * rate
    return results


def get_hit_rate_each_hp(tasks: list, dict_dlm_prob: dict):
    results = np.zeros((len(tasks), ))
    for key in dict_dlm_prob.keys():
        prob = dict_dlm_prob[key]
        key_list = eval(key)
        for i in range(len(key_list)):
            rate = np.mean(key_list[i])
            results[i] += rate * prob
    return results


def main():
    if len(sys.argv) < 5:
        print(f"python {sys.argv[0]} <task_xml> <edf> <uniform> <suffix> ")
        exit(1)
    
    filename = sys.argv[1]
    edf = int(sys.argv[2])
    uniform = int(sys.argv[3])
    suffix = sys.argv[4]

    tasks_df = None
    try:
        tasks_df = pd.read_xml(filename)
    except Exception as e:
        print("Error reading", filename, e)
        exit(1)

    Tasks = []
    id = 0
    for task in tasks_df.to_numpy():
        period = task[0]
        exec_mu = task[1]
        prio = task[2]
        if uniform:
            exec_time, prob = disc_prob_two(exec_mu)
            Tasks.append(Task(id, exec_time, prob, period, prio))
        else:
            exec_time, prob = disc_prob_two_abnormal(exec_mu)
            Tasks.append(Task(id, exec_time, prob, period, prio))
        id += 1

    start_time = time.time()

    hp = get_hyper_period(Tasks)
    num_probs = []
    for task in Tasks:
        num_prob = task.enumerate_allocations(hp)
        num_probs.append(num_prob)

    print("Intra-task enumeration done")

    dict_dlm_prob, dlm_init = get_dlm_all_iterative(Tasks, num_probs, edf)
    if dict_dlm_prob is None:
        with open(f"{filename[:-4]}-ground-truth-{suffix}.txt", 'w') as f:
            f.write("killed")
        exit(1)
    end_time_enum = time.time()
    
    n_ks = get_hit_rate_each_hp(Tasks, dict_dlm_prob)
    end_time_ratio = time.time()

    dicts = get_dict_per_task(Tasks, dict_dlm_prob)
    dicts = [merge_2_dicts(dicts[i]) for i in range(len(dicts))]


    n_ks43 = []
    for tau in Tasks:
        n_ks43.append(get_n_k_per_task(dicts[tau.id], 4, 3))
    n_ks43 = np.array(n_ks43)
    end_time_nk = time.time()

    diff_time_ratio = end_time_ratio - start_time
    diff_time_nk = end_time_nk - end_time_ratio + end_time_enum - start_time

    print("deadline hit ratio", n_ks)
    print("(m,k)=(3,4)", n_ks43, diff_time_nk)


    with open(f"{filename[:-4]}-ground-truth-{suffix}.txt", 'w') as f:
        f.write(str(n_ks43.tolist()))
        f.write("\n")
        f.write(str(n_ks.tolist()))
        f.write("\n")
        f.write(f"{diff_time_nk} s")
        f.write("\n")
        f.write(f"{diff_time_ratio} s")
        f.write("\n")


if __name__ == "__main__":
    main()
