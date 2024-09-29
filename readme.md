# Analysis of the Long-Term Average Properties of Probabilistic Task Systems

## 1. Introduction
This repo includes the artifacts of the paper "Analysis of the Long-Term Average Properties of Probabilistic Task Systems" published in [RTNS '24](https://cister-labs.pt/rtns24/). 

## 2. Requirements
Python 3.x is required. We tested the code with Python 3.10.9.

To install the required packages, run 
```shell
$ pip install -r requirements.txt
```

## 3. Task Set Generation
The task sets can be generated using `task_gen.py`. The usage is as follows.
```bash
$ python task_gen.py <total_util> <num_tasks> <num_sets> <max_period> <out_dir>
```
The parameters:
- `total_util`: (float) The total utilzaition of each task set.
- `num_tasks`: (int) The number of tasks in each task set.
- `num_sets`: (int) The number of task sets for each combination of configurations.
- `max_period`: (int) The maximum period among all tasks in each task set. 
- `out_dir`: (str) The name of the output directory.

Example:
```bash
$ python task_gen.py 1.0 4 5 4 1.0u_4tasks_4max
```

With the script, a new directory with the name `out_dir` will be created, with `num_sets` xml files inside.

## 4. Ground Truth Computation
The ground truth can be computed with `markov_ground_truth.py`. The usage is as follows:
```bash
$ python markov_ground_truth.py <task_xml> <edf> <uniform> <suffix>
```

The parameters:
- `task_xml`: (str) The path to the xml file (generated by `task_gen.py`).
- `edf`: (0 or 1) 1 for using EDF policy, and 0 for using static-prioirty policy.
- `uniform`: (0 or 1) 1 for a uniform distribution, and 0 for a "likely-unlikely" distribution (defined in the paper).
- `suffix`: (str) The suffix of the output file name (usually to help differentiate the outputs of different configurations)

Example:
```bash
$ python markov_ground_truth.py 1.0u_4tasks_4max/1.xml 1 1 edf-uniform
```

The output will be stored in a file in the same directory as the xml file. There will be four lines in the output.
- Line #1: The satisfication rate of (m,k)=(3,4) for each task
- Line #2: The deadline hit ratio for each task
- Line #3: The time it takes to compute the weakly-hard constraints
- Line #4: The time it takes to compute the deadline hit ratio

Note:
- The computation may be extremely slow for larger task set. Please check the paper to find out what is doable.
- The source code might use a different notation of weakly-hard constraints (using (k,n) instead of (m,k)).


## 5. Sampling
The sampling is performed using `markov_sampling.py`. The usage is as follows:
```bash
$ python markov_sampling.py <task_xml> <m_k_json> <chain> <chain_length> <state_length> <edf?>  <uniform?> <suffix>
```
The parameters:
- `task_xml`: (str) The path to the xml file (generated by `task_gen.py`).
- `m_k_json`: (str) The path to the (m,k) configuration file (jsons provided).
- `chain`: (int) The number of chains to sample. We fix the number to be 4 in the paper.
- `chain_length`: (int) The maximum number of length of the chain, even if the convergence criteria is not met. The sampling will be stopped once the criteria ($\hat{R}$ score and $T_{stab}$) are met.
- `state_length`: (int) The value of $\Delta$ in the paper.
- `edf`: (0 or 1) 1 for using EDF policy, and 0 for using static-prioirty policy.
- `uniform`: (0 or 1) 1 for a uniform distribution, and 0 for a "likely-unlikely" distribution (defined in the paper).
- `suffix`: (str) The suffix of the output file name (usually to help differentiate the outputs of different configurations)

Example:
```bash
$ python markov_sampling.py 1.0u_4tasks_4max/1.xml m3k4.json 4 50000 1000 1 1 edf-uniform-sl1000-m3k4
```

## 6. Case Study
The code for the case study is in the `case_study/` directory. The sampling method is modified to match the non-preemptive scheduling policy. The `case_study/tasks/` directory includes the execution time that has been profiled from the ArduPilot execution. Usage:
```bash
$ cd case_study/
$ python markov_sampling_case.py <m_k_json> <chain> <chain_length> <state_length> <output-file>
```

Parameters:
- `m_k_json`: (str) The path to the (m,k) configuration file (provided `m1k1.json` and `m3k4.json`).
- `chain`: (int) The number of chains to sample. We fix the number to be 4 in the paper.
- `chain_length`: (int) The maximum number of length of the chain, even if the convergence criteria is not met. The sampling will be stopped once the criteria ($\hat{R}$ score and $T_{stab}$) are met.
- `state_length`: (int) The value of $\Delta$ in the paper.
- `output-file`: (str) The file name of the output.

Output:
- A file with two columns: the first column is the task id, and the second column is the violation rate.
- Mapping from task id to task names can be found [here](https://github.com/ArduPilot/ardupilot/blob/413452aa1aa6a178c13ba365f12776ec4f1a147f/Rover/Rover.cpp#L69). The priority of the task in this link is used as the task id.

Example:
```bash
$ python markov_sampling_case.py ../m3k4.json 4 500000 200000 results-m3k4
```

Note: 
- The process may be slow since the number of tasks is large for the case study.
