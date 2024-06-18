#!/bin/env python

import os
import glob
from schedparser import parser
from config import config

def main():
    # set up the directories
    job_info_path = config["job_info_path"]
    
    # clean up the files generated from the previous run
    files = glob.glob(job_info_path+"/*")
    for f in files:
        os.remove(f)
    
    myparser = parser.JobParser("/opt/slurm/current/bin/scontrol show job -d")
    myparser.get_records()
    myparser.dump_records(job_info_path,"")

if __name__ == '__main__':
    main()
