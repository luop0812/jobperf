import os
import yaml
import numpy
import matplotlib

from config import config

perf_path_prefix = config["perf_path_prefix"]

memused_ary = []
for jobid in os.listdir(perf_path_prefix):
    for fn in os.listdir(perf_path_prefix+"/"+jobid):
        fullname = perf_path_prefix+"/"+jobid+"/"+fn

        with open(fullname, "r") as f:
            jobperf = yaml.safe_load(f)

            perflist = jobperf["metrics"]

            # find the largest memory used
            maxmem = 0
            for i in range(len(perflist)):
                memused = float(perflist[i].split(":")[6])
                if memused > maxmem:
                    maxmem = memused

        memused_ary.append(maxmem/1024)

print(memused_ary)

buckets = [5, 10, 20, 48, 80]



buckets = [6, 12, 24, 48, 80]
