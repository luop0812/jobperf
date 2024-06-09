import time
import os
import yaml
from config import config

# path to idle files
idle_job_path = config["idle_job_path"]

# sampling frequency
freq = config["sample_frequency"]

# time of now
ts = time.time()

idle_jobs = []
tolerance = 5 
# find all files whose timestamp is within sampling frequency amount of time of now
for fn in os.listdir(idle_job_path):
    fm_t = os.path.getmtime(idle_job_path+"/"+fn)
    if ts - fm_t <= freq + tolerance:
        idle_jobs.append(fn)

print(idle_jobs)

# find out files with consecutive timestamps that differ between sample_frequency +/- tolerance seconds
# for files with non-consecutive idle timestamps, list the percentage of time that is idle
for fn in idle_jobs:
    with open(idle_job_path+"/"+fn, "r") as file:
        idle = True
        timestamps = file.read().strip().split("\n")
        pre_ts = float(timestamps[0])
        i = 1
        while i < len(timestamps):
            ts = float(timestamps[i])
            diff = ts - pre_ts
            if diff > freq + tolerance:
                idle = False
            pre_ts = ts
            i = i + 1

        if idle == False:
            # retrieve the beginning timestamp
            fn_splits = fn.split(".")
            perf_fn = config["perf_path_prefix"]+"/"+fn_splits[0]+"/"+fn_splits[1]+"."+fn_splits[2]
            with open(perf_fn, "r") as file:
                b_ts = float(yaml.safe_load(file)["metrics"][0].split(":")[0])
            percent = (len(timestamps)*freq)/(ts-b_ts) * 100
            print(fn+":", end=" ")
            print("{:0.2f}".format(percent), end="")
            print("% of time is idle.")
        else:
            print(fn+": idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))
