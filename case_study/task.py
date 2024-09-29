import numpy as np


from utils import *

class Task:    
    def __init__(self, id: int, exec_time: np.ndarray, probs: np.ndarray, period: int, priority: int) -> None:
        self.id = id
        self.exec_time = [1000 * i  for i in exec_time]
        self.probs = probs
        self.period = round(1000 * period)
        self.priority = priority
        self._format_check()

    
    def _format_check(self) -> bool:
        self.exec_time = np.array(self.exec_time, dtype=float)
        self.probs = np.array(self.probs, dtype=float)
        
        assert self.exec_time.shape[0] > 0
        assert self.exec_time.shape == self.probs.shape
        assert np.sum(self.probs) > 0.9999 and np.sum(self.probs) < 1.0001

        self._format_check = True 

    """
    ------------Return-----------
    A list of tuples of job execution times
    A list of probabilities
    
    """
    def enumerate_allocations(self, hp):
        num_jobs = round(hp / self.period)
        num_probs = self.exec_time.shape[0]
        combinations = generate_combinations(num_probs, num_jobs)
        all_time_list = []
        all_prob_list = []
        for comb in combinations:
            prob = 1
            exec_times = []
            for idx in comb:
                prob *= self.probs[idx]
                # use a list in order to be compatible with multi-chain code
                exec_times.append(self.exec_time[idx]) 
            all_time_list.append(exec_times)
            all_prob_list.append(prob)
        self.all_time_list = all_time_list
        self.all_prob_list = all_prob_list
        return len(all_prob_list)

    def sample_one(self, hp):
        num = round(hp / self.period)
        return np.random.choice(self.exec_time, num, p=self.probs)
        
    def sample_time_range(self, start, end, arrivals: dict):
        """
        Return an arrays of execution times. Update the arrivals.
        """
        t = int(start / self.period) * self.period
        if t != start:
            t += self.period
        num = 0
        while t < end:
            if t not in arrivals.keys():
                arrivals[t] = [self]
            else:
                arrivals[t].append(self)
            num += 1
            t += self.period

        return np.random.choice(self.exec_time, num, p=self.probs)



    def __repr__(self) -> str:
        ret = ""
        ret += "-----------------task---------------\n"
        ret += "exec_time:\t" + str(self.exec_time) + "\n"
        ret += "probability:\t" + str(self.probs) + "\n"
        ret += "period:\t" + str(self.period) + "\n"
        ret += "priority:\t" + str(self.priority) + "\n"
        ret += "-------------end task---------------\n"
        return ret