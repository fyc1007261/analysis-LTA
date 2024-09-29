import numpy as np
import scipy.stats as ss



def n_k_analysis_window(arr, n, k):
    tot = len(arr) - n + 1
    hit = 0
    result_arr = []
    for i in range(tot):
        if np.sum(arr[i:i+n]) >= k:
            hit += 1
            result_arr.append(1)
        else:
            result_arr.append(0)
    return hit / tot, result_arr


"""
We wish to sample from a discretized Gaussian distribution centered on 
computation times to construct a trajetory. Later we will extend this to sample varying release times too. Hence 
we start with a generic discretization procedure.

We specify an interval (specified as a percentage)  centered on the mean of a 
Guassian distribution, divide it into an equally spaced number of points, and then 
assign probabilities to these points by computing 
the cdfs of small intervals around these points. To compute the cdfs we also need 
to specify the how many standard deviations we are going to use.  
"""

def disc_prob(mu, sigma=0.2, perc=20, nop=10, brd=0.1):
    # return (np.array([0.8 * mu, 1.2 * mu]), [0.5,0.5])
    P = np.linspace(mu-(mu*perc/100), mu+(mu*perc/100), nop).tolist()
    PU = [x+brd for x in P]
    PL = [x-brd for x in P]
    probU = [ss.norm.cdf(x,mu,sigma*mu) for x in PU]
    probL = [ss.norm.cdf(x,mu,sigma*mu) for x in PL]
    prob = []
    for i in range(len(probU)):
        prob.append(probU[i]-probL[i])
    prob = prob/sum(prob)
    return(np.array(P), prob)


def disc_prob_two(mu, sigma=0.2, perc=20, nop=10, brd=0.1):
    return (np.array([0.8 * mu, 1.2 * mu]), [0.5,0.5])

def disc_prob_two_abnormal(mu):
    return (np.array([95/99 * mu, 5 * mu]), [0.99,0.01])

def get_hyper_period(tasks: list) -> int:
    max_period = -1
    for task in tasks:
        max_period = max(max_period, task.period)
    for task in tasks:
        assert max_period % task.period == 0
    return round(max_period)

def generate_combinations(num_probs, num_jobs):
    num_allocs = num_probs ** num_jobs
    ret = []
    for i in range(num_allocs):
        cur_alloc = []
        for j in range(num_jobs):
            cur_alloc.append(i % num_probs)
            i = int(i/num_probs)
        ret.append(cur_alloc)
    return np.array(ret)

"""
---------Parameters-----------
num_situs: A list of integers. 
Each is the number of possible allocations for each task.
"""
def generate_combinations_all_tasks(num_situs: list):
    cur_num_situ = num_situs[0]
    if len(num_situs) == 1:
        tails = [[i] for i in range(cur_num_situ)]
        return tails
    tails = generate_combinations_all_tasks(num_situs[1:]) 
    results = []       
    for i in range(len(tails)):
        for j in range(cur_num_situ):
            results.append([j]+ tails[i])
    return results



def get_job_arrivals(tasks: list):
    hp = get_hyper_period(tasks)
    arrivals = dict()
    for task in tasks:
        for time in range(0, round(hp), round(task.period)):
            if time not in arrivals.keys():
                arrivals[time] = [task]
            else:
                arrivals[time].append(task)
    return arrivals

def distance(arr1, arr2):
    return np.sqrt(np.sum(np.square(arr1 - arr2)))