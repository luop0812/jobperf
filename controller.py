#!/bin/env python

import os
import glob
from parser import parser
from config import config

# set up the directories
job_info_path = config["job_info_path"]

# clean up the files generated from the previous run
files = glob.glob(job_info_path+"/*")
for f in files:
    os.remove(f)

myparser = parser.JobParser("/opt/slurm/current/bin/scontrol show job -d")
myparser.get_records()
myparser.dump_records(job_info_path,"")
