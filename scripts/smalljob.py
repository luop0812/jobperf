"""
By default, we only list jobs that have no running processes from the last sampling action.
-n|--ndays n_days: list idle jobs from the previouse n_days.
-a|--all: list all idle jobs stored in the data directory.
-b|--begin: 
-e|--end:
"""
import time
from datetime import datetime
import os
import yaml
import argparse

from config import config
 
# path to idle files
small_job_path = config["small_job_path"]

# sampling frequency
freq = config["sample_frequency"]

# time of now
ts = time.time()

small_jobs = []
tolerance = 5 


ndays = 0

parser = argparse.ArgumentParser(description='List small jobs.')
parser.add_argument('-n', '--ndays', type=int, help="List small jobs from the last n days.")
args = parser.parse_args()
if args.ndays != None:
    ndays = int(args.ndays)

sec_in_days = ndays * 86400

for fn in os.listdir(small_job_path):
    fm_t = os.path.getmtime(small_job_path+"/"+fn)
    if ts - fm_t <= sec_in_days + freq + tolerance:
        small_jobs.append(fn)

#print(small_jobs)

# find out files with consecutive timestamps that differ between sample_frequency +/- tolerance seconds
# for files with non-consecutive small timestamps, list the percentage of time that is small
for fn in small_jobs:
    with open(small_job_path+"/"+fn, "r") as file:
        small = True
        timestamps = file.read().strip().split("\n")
        pre_ts = float(timestamps[0])
        i = 1
        while i < len(timestamps):
            ts = float(timestamps[i])
            diff = ts - pre_ts
            if diff > freq + tolerance:
                small = False
            pre_ts = ts
            i = i + 1

        if int((float(timestamps[-1])-float(timestamps[0]))/60) == 0:
            continue

        # print the date
        start = datetime.fromtimestamp(float(timestamps[0]))
        print(start.strftime("%c"), end=": ")

        if small == False:
            # retrieve the beginning timestamp
            fn_splits = fn.split(".")
            perf_fn = config["perf_path_prefix"]+"/"+fn_splits[0]+"/"+fn_splits[1]+"."+fn_splits[2]
            with open(perf_fn, "r") as file:
                b_ts = float(yaml.safe_load(file)["metrics"][0].split(":")[0])
            percent = (len(timestamps)*freq)/(ts-b_ts) * 100
            print(fn+":", end=" ")
            if percent >= 98:
                print("{:0.2f}".format(percent), end="")
                print("% of time is small.", end=" ")
                print("Idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))
            else:
                print("{:0.2f}".format(percent), end="")
                print("% of time is small.")

        else:
            print(fn+": small for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))
