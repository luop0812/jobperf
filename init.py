#!/bin/env python

import os
import glob
from config import config

# set up the directories
job_info_path = config["job_info_path"]
perf_path_prefix = config["perf_path_prefix"]
idle_job_path = config["idle_job_path"]
small_job_path = config["small_job_path"]
paths = [job_info_path, perf_path_prefix, idle_job_path, small_job_path]
for path in paths:
    print(path)
    os.makedirs(path, exist_ok=True)

