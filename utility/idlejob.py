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
 
def main():
    # path to idle files
    idle_job_path = config["idle_job_path"]
    
    # sampling frequency
    freq = config["sample_frequency"]
    
    # time of now
    ts = time.time()
    
    idle_jobs = []
    tolerance = 5 
    
    ndays = 0
    
    parser = argparse.ArgumentParser(description='List idle jobs.')
    parser.add_argument('-n', '--ndays', type=int, help="List idle jobs that started running within the last n days.")
    args = parser.parse_args()
    if args.ndays != None:
        ndays = int(args.ndays)
    
    sec_in_days = ndays * 86400
    
    # if ndyas is 0, then we only check idle files that were updated during the last sampling cycle
    if ndays == 0:
        for fn in os.listdir(idle_job_path):
            fm_t = os.path.getmtime(idle_job_path+"/"+fn)
            if ts - fm_t <= freq + tolerance:
                idle_jobs.append(fn)
    else:
        for fn in os.listdir(idle_job_path):
            with open(idle_job_path+"/"+fn, "r") as idlefile:
                start_ts = yaml.safe_load(idlefile)["start_timestamp"]
            if ts - start_ts <= sec_in_days:
                idle_jobs.append(fn)
    
    #print(idle_jobs)
    
    # find out files with consecutive timestamps that differ between sample_frequency +/- tolerance seconds
    # for files with non-consecutive idle timestamps, list the percentage of time that is idle
    for fn in idle_jobs:
        with open(idle_job_path+"/"+fn, "r") as idlefile:
            idle = True
            idlefile_dict = yaml.safe_load(idlefile)
            timestamps = idlefile_dict["metrics"]
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
    
            if idle == False:
                # retrieve the beginning timestamp
                b_ts = idlefile_dict["start_timestamp"]
                percent = (len(timestamps)*freq)/(ts-b_ts) * 100
                if percent >= 75:
                    print(start.strftime("%c"), end=": ")
                    print(fn+":", end=" ")
                    print("{:0.2f}".format(percent), end="")
                    print("% of time is idle.", end=" ")
                    print("Idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))
                elif percent >= 20:
                    print(start.strftime("%c"), end=": ")
                    print(fn+":", end=" ")
                    print("{:0.2f}".format(percent), end="")
                    print("% of time is idle.")
    
            else:
                print(start.strftime("%c"), end=": ")
                print(fn+": idle for {} minutes.".format(int((float(timestamps[-1])-float(timestamps[0]))/60)))

if __name__ == "__main__":
    main()
