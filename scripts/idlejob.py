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
 
def getctime(fn):
    fc_t = 0
    with open(fn, "r") as file:
        fc_t = float(yaml.safe_load(file)["metrics"][0].split(":")[0])
    return fc_t

def main():
    # path to idle files
    idle_job_path = config["idle_job_path"]
    
    # sampling frequency
    freq = config["sample_frequency"]
    
    # path to performance files
    perf_path_prefix = config["perf_path_prefix"]
    
    # time of now
    ts = time.time()
    
    idle_jobs = []
    tolerance = 5 
    
    ndays = 0
    
    parser = argparse.ArgumentParser(description='List idle jobs.')
    parser.add_argument('-n', '--ndays', type=int, help="List idle jobs from the last n days.")
    args = parser.parse_args()
    if args.ndays != None:
        ndays = int(args.ndays)
    
    sec_in_days = ndays * 86400
    
    if ndays == 0:
        for fn in os.listdir(idle_job_path):
            fm_t = os.path.getmtime(idle_job_path+"/"+fn)
            if ts - fm_t <= freq + tolerance:
                idle_jobs.append(fn)
    else:
        for fn in os.listdir(idle_job_path):
            fn_split = fn.split(".", 1)
            fc_t = getctime(perf_path_prefix+"/"+fn_split[0]+"/"+fn_split[1])
            if ts - fc_t <= sec_in_days:
                idle_jobs.append(fn)
    
    #print(idle_jobs)
    
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
    
            if int((float(timestamps[-1])-float(timestamps[0]))/60) == 0:
                continue
    
            # print the date
            start = datetime.fromtimestamp(float(timestamps[0]))
            print(start.strftime("%c"), end=": ")
    
            if idle == False:
                # retrieve the beginning timestamp
                fn_splits = fn.split(".", 1)
                perf_fn = config["perf_path_prefix"]+"/"+fn_splits[0]+"/"+fn_splits[1]
                b_ts = getctime(perf_fn)
                percent = (len(timestamps)*freq)/(ts-b_ts) * 100
                print(fn+":", end=" ")
                if percent >= 98:
                    print("{:0.2f}".format(percent), end="")
                    print("% of time is idle.", end=" ")
                    print("Idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))
                elif percent >= 20:
                    print("{:0.2f}".format(percent), end="")
                    print("% of time is idle.")
    
            else:
                print(fn+": idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))

if __name__ == "__main__":
    main()
