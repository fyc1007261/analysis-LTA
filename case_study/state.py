
from utils import *

def simulate_one_step(tasks: list, job_exec_times: list, arrivals: dict, sorted_arrival_times: list) -> list:
    """
    Given the sampled job execution times, calculate the deadline misses and hits

    Returns
    ----------
    A list of tuples. A tuple should consist boolean values.
    True means ddl hit, False means ddl miss.

    Parameter
    ----------
    tasks : A list of Task objects
    job_exec_times: The return value of `Sampler::extend_samples_to_steps()`
    arrivals: A dictionary of job arrival times
    sorted_arrival_times: Sorted dictionary keys
    """
    hit_misses = []
    for i in range(len(tasks)):
        hit_misses.append([])
    sim_time = sorted_arrival_times.pop(0)
    assert sim_time == 0
    issued_tasks = dict()  # dict: task_id -> [issue_time, remaining, ddl]
    for task in arrivals[sim_time]:
        issued_tasks[task.id] = [
            sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
        assert issued_tasks[task.id][1] >= 0
    hp = get_hyper_period(tasks)
    while sim_time < hp:
        if len(issued_tasks.keys()) == 0:
            # All tasks have finished. Go to the next job-arrival time
            sim_time = sorted_arrival_times.pop(0)
            if sim_time == get_hyper_period(tasks):
                break
            for task in arrivals[sim_time]:
                issued_tasks[task.id] = [
                    sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                assert issued_tasks[task.id][1] >= 0
            continue
        else:
            # Execute the highest priority task
            next_issue_time = sorted_arrival_times[0]
            high_prio_id = sorted(issued_tasks.keys())[0]
            (_, remain, ddl) = issued_tasks[high_prio_id]
            if ddl <= sim_time:
                print(issued_tasks[high_prio_id], high_prio_id, sim_time)
                # Should not go there
                assert 0
            elif next_issue_time - sim_time >= remain:
                # Enough time to finish
                hit_misses[high_prio_id].append(1)
                sim_time += remain
                issued_tasks.pop(high_prio_id)
                continue
            else:
                # Not enough time to finish,
                # execute until the next issue time
                issued_tasks[high_prio_id][1] -= (next_issue_time - sim_time)
                sim_time = sorted_arrival_times.pop(0)
                assert sim_time == next_issue_time
                if sim_time == hp:
                    for unfinished in issued_tasks.keys():
                        hit_misses[unfinished].append(0)
                    break
                # Issue the new jobs
                for task in arrivals[sim_time]:
                    if task.id in issued_tasks.keys():
                        # Deadline miss
                        hit_misses[task.id].append(0)
                    issued_tasks[task.id] = [
                        sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                    assert issued_tasks[task.id][1] >= 0
    return hit_misses


def simulate_one_step_edf(tasks: list, job_exec_times: list, arrivals: dict, sorted_arrival_times: list) -> list:
    hit_misses = []
    for i in range(len(tasks)):
        hit_misses.append([])
    sim_time = sorted_arrival_times.pop(0)
    assert sim_time == 0
    issued_tasks = dict()  # dict: task_id -> [issue_time, remaining, ddl]
    for task in arrivals[sim_time]:
        issued_tasks[task.id] = [
            sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
        assert issued_tasks[task.id][1] >= 0
    hp = get_hyper_period(tasks)
    while sim_time < hp:
        if len(issued_tasks.keys()) == 0:
            # All tasks have finished. Go to the next issue time
            sim_time = sorted_arrival_times.pop(0)
            if sim_time == get_hyper_period(tasks):
                break
            for task in arrivals[sim_time]:
                issued_tasks[task.id] = [
                    sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                assert issued_tasks[task.id][1] >= 0
            continue
        else:
            # Execute the task with earliest ddl
            next_issue_time = sorted_arrival_times[0]
            # Search the earliest ddl
            earliest_ddl = hp
            task_ed = -1
            ddl = None
            for task_id in sorted(issued_tasks.keys()):
                ddl = issued_tasks[task_id][2]
                if ddl <= earliest_ddl:
                    task_ed = task_id
                    earliest_ddl = ddl
            assert task_ed >= 0
            remain = issued_tasks[task_ed][1]

            if ddl <= sim_time:
                assert 0
            elif next_issue_time - sim_time >= remain:
                # Enough time to finish
                hit_misses[task_ed].append(1)
                sim_time += remain
                issued_tasks.pop(task_ed)
                continue
            else:
                # Not enough time to finish,
                # execute util the next issue time
                issued_tasks[task_ed][1] -= (next_issue_time - sim_time)
                sim_time = sorted_arrival_times.pop(0)
                assert sim_time == next_issue_time
                if sim_time == hp:
                    for unfinished in issued_tasks.keys():
                        hit_misses[unfinished].append(0)
                    break
                # Issue the new jobs
                for task in arrivals[sim_time]:
                    if task.id in issued_tasks.keys():
                        # Deadline miss
                        hit_misses[task.id].append(0)
                    issued_tasks[task.id] = [
                        sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                    assert issued_tasks[task.id][1] >= 0
    return hit_misses


def simulate_non_harmonic_edf(tasks: list,
                              job_exec_times: list,
                              arrivals: dict,
                              sorted_arrival_times: list,
                              issued_tasks: dict,
                              time_offset: int,
                              duration: int) -> tuple:
    """
    Parameter
    ----------
    time_offset: The starting time of that "period", unlike harmonic tasks 
    where we can assume this to be zero.

    job_exec_times, arrivals, sorted_arrival_times: need to add the offset.

    issued_tasks: the list returned by the last state. dict: task_id -> [issue_time, remaining, ddl]

    """
    hit_misses = []
    for i in range(len(tasks)):
        hit_misses.append([])
    sim_time = time_offset
    finish_time = sim_time + duration

    while sim_time < finish_time:
        if len(issued_tasks.keys()) == 0:
            # All tasks have finished. Go to the next job-arrival time
            sim_time = sorted_arrival_times.pop(0)
            if sim_time == finish_time:
                break
            for task in arrivals[sim_time]:
                assert task.id not in issued_tasks.keys()
                issued_tasks[task.id] = [
                    sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                assert issued_tasks[task.id][1] >= 0
            continue
        else:
            # Execute the task with earliest ddl
            next_issue_time = sorted_arrival_times[0]
            # Search the earliest ddl
            earliest_ddl = None
            task_ed = None
            ddl = None
            for task_id in sorted(issued_tasks.keys()):
                ddl = issued_tasks[task_id][2]
                if earliest_ddl is None or ddl <= earliest_ddl:
                    task_ed = task_id
                    earliest_ddl = ddl
            assert task_ed is not None
            remain = issued_tasks[task_ed][1]

            if earliest_ddl < sim_time:
                assert 0
            elif next_issue_time - sim_time >= remain:
                # Enough time to finish
                hit_misses[task_ed].append(1)
                sim_time += remain
                issued_tasks.pop(task_ed)
                continue
            else:
                # Not enough time to finish,
                # execute until the next issue time
                issued_tasks[task_ed][1] -= (next_issue_time - sim_time)
                old_sim = sim_time
                sim_time = sorted_arrival_times.pop(0)
                assert sim_time == next_issue_time
                if sim_time == finish_time:
                    to_pop = []
                    for unfinished in issued_tasks.keys():
                        if issued_tasks[unfinished][2] <= finish_time:
                            hit_misses[unfinished].append(0)
                            to_pop.append(unfinished)
                    for unfinished in to_pop:
                        issued_tasks.pop(unfinished)
                    break
                # Issue new jobs
                for task in arrivals[sim_time]:
                    if task.id in issued_tasks.keys():
                        # Deadline miss
                        hit_misses[task.id].append(0)
                    issued_tasks[task.id] = [
                        sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                    assert issued_tasks[task.id][1] >= 0
    return hit_misses, issued_tasks





def simulate_non_harmonic(tasks: list,
                              job_exec_times: list,
                              arrivals: dict,
                              sorted_arrival_times: list,
                              issued_tasks: dict,
                              time_offset: int,
                              duration: int) -> tuple:
    """
    Parameter
    ----------
    time_offset: The starting time of that "period", unlike harmonic tasks 
    where we can assume this to be zero.

    job_exec_times, arrivals, sorted_arrival_times: need to add the offset.

    issued_tasks: the list returned by the last state. dict: task_id -> [issue_time, remaining, ddl]

    """
    hit_misses = []
    for i in range(len(tasks)):
        hit_misses.append([])
    sim_time = time_offset
    finish_time = sim_time + duration

    while sim_time < finish_time:
        if len(issued_tasks.keys()) == 0:
            # All tasks have finished. Go to the next job-arrival time
            sim_time = sorted_arrival_times.pop(0)
            if sim_time == finish_time:
                break
            for task in arrivals[sim_time]:
                assert task.id not in issued_tasks.keys()
                issued_tasks[task.id] = [
                    sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                assert issued_tasks[task.id][1] >= 0
            continue
        else:
            next_issue_time = sorted_arrival_times[0]
            ddl = None
            high_prio_id = sorted(issued_tasks.keys())[0]
            (_, remain, ddl) = issued_tasks[high_prio_id]

            if ddl < sim_time:
                assert 0
            elif next_issue_time - sim_time >= remain:
                # Enough time to finish
                hit_misses[high_prio_id].append(1)
                sim_time += remain
                issued_tasks.pop(high_prio_id)
                continue
            else:
                # Not enough time to finish,
                # execute until the next issue time
                issued_tasks[high_prio_id][1] -= (next_issue_time - sim_time)
                old_sim = sim_time
                sim_time = sorted_arrival_times.pop(0)
                assert sim_time == next_issue_time
                if sim_time == finish_time:
                    to_pop = []
                    for unfinished in issued_tasks.keys():
                        if issued_tasks[unfinished][2] <= finish_time:
                            hit_misses[unfinished].append(0)
                            to_pop.append(unfinished)
                    for unfinished in to_pop:
                        issued_tasks.pop(unfinished)
                    break
                # Issue new jobs
                for task in arrivals[sim_time]:
                    if task.id in issued_tasks.keys():
                        # Deadline miss
                        hit_misses[task.id].append(0)
                    issued_tasks[task.id] = [
                        sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                    assert issued_tasks[task.id][1] >= 0
    return hit_misses, issued_tasks



def simulate_non_harmonic_non_preempt(tasks: list,
                              job_exec_times: list,
                              arrivals: dict,
                              sorted_arrival_times: list,
                              issued_tasks: dict,
                              time_offset: int,
                              duration: int,
                              last_running) -> tuple:
    """
    Parameter
    ----------
    time_offset: The starting time of that "period", unlike harmonic tasks 
    where we can assume this to be zero.

    job_exec_times, arrivals, sorted_arrival_times: need to add the offset.

    issued_tasks: the list returned by the last state. dict: task_id -> [issue_time, remaining, ddl]

    """
    hit_misses = []
    for i in range(len(tasks)):
        hit_misses.append([])
    sim_time = time_offset

    finish_time = sim_time + duration

    while sim_time < finish_time:
        if len(issued_tasks.keys()) == 0:
            # All tasks have finished. Go to the next job-arrival time
            sim_time = sorted_arrival_times.pop(0)
            if sim_time == finish_time:
                break
            for task in arrivals[sim_time]:
                assert task.id not in issued_tasks.keys()
                issued_tasks[task.id] = [
                    sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                assert issued_tasks[task.id][1] >= 0
            continue
        else:
            next_issue_time = sorted_arrival_times[0]
            ddl = None
           
            if last_running:
                high_prio_id = last_running
            else:
                high_prio_id = sorted(issued_tasks.keys())[0]
                last_running = high_prio_id
            (_, remain, ddl) = issued_tasks[high_prio_id]

            if ddl < sim_time:
                assert 0
            elif next_issue_time - sim_time >= remain:
                # Enough time to finish
                hit_misses[high_prio_id].append(1)
                sim_time += remain
                issued_tasks.pop(high_prio_id)
                last_running = None
                continue
            else:
                # Not enough time to finish,
                # execute until the next issue time
                issued_tasks[high_prio_id][1] -= (next_issue_time - sim_time)
                old_sim = sim_time
                sim_time = sorted_arrival_times.pop(0)
                assert sim_time == next_issue_time
                if sim_time == finish_time:
                    to_pop = []
                    for unfinished in issued_tasks.keys():
                        if issued_tasks[unfinished][2] <= finish_time:
                            hit_misses[unfinished].append(0)
                            to_pop.append(unfinished)
                            if unfinished == last_running:
                                last_running = None
                    for unfinished in to_pop:
                        issued_tasks.pop(unfinished)
                    break
                # Issue new jobs
                for task in arrivals[sim_time]:
                    if task.id in issued_tasks.keys():
                        # Deadline miss
                        hit_misses[task.id].append(0)
                    issued_tasks[task.id] = [
                        sim_time, job_exec_times[task.id].pop(0), sim_time + task.period]
                    assert issued_tasks[task.id][1] >= 0
    return hit_misses, issued_tasks, last_running