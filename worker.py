"""
input file:   jobid.nodename
output files: jobid.perf, jobid.idle, jobid.small
jobid.perf: timestamp:gpu_type:idx:uuid: 
  - process_id, gpu_id, gpu_type, gpu_utilizaiton, vram_total, vram_usage, vram_utilization
  - process_id ....
"""

import platform
import os
import sys
import yaml
import time
from pynvml import * 
from datetime import datetime
from pathlib import Path

from config import uuids, config, ids

def handle_error(err):
    if (err.value == NVML_ERROR_NOT_SUPPORTED):
        return "N/A"
    else:
        return err.__str__()

"""
input: idx, uuid
    idx: GPU device number
    uuid: GPU device uuid. It is empty for non-MIG device. It is the MIG instance UUID if MIG is enabled on the device.
output: a dictionary with the following structure:
    {"gpu_util":gpu_util, "mem_total":mem_total, "mem_used":mem_used, "mem_free":mem_free, 
     "temperature":temperature, "num_procs":num_procs, "procs":[{"name":proc_name,"mem":proc_mem}]}
    gpu_util is empty for MIG-enabled devices. 
"""
def _get_gpu_usage(id, uuid):
#   print("call get_gpu_usage")
    ret_metrics = {}

    nvmlInit()
    # MIG-enabled GPU doesn't support GPU utiliztion function. 
    if uuid == "":
        handle = nvmlDeviceGetHandleByIndex(id)
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_util = util.gpu
#       print(gpu_util)
        ret_metrics["gpu_util"] = str(gpu_util)
    else:
        handle = nvmlDeviceGetHandleByUUID(uuid)
        ret_metrics["gpu_util"] = ""

    try:
        procs = nvmlDeviceGetComputeRunningProcesses(handle)
        ret_metrics["num_procs"] = len(procs)
        ret_metrics["procs"] = []

        for p in procs:
            try:
                name = str(nvmlSystemGetProcessName(p.pid))
            except NVMLError as err:
                name = handle_error(err)

            if (p.usedGpuMemory == None):
                mem = ""
            else:
                mem = str(p.usedGpuMemory / 1024 / 1024)

#           print(name)
#           print(mem)
            ret_metrics["procs"].append({"name":name, "mem":mem})

        memInfo = nvmlDeviceGetMemoryInfo(handle)
        mem_total = str(memInfo.total / 1024 / 1024)
        mem_used = str(memInfo.used / 1024 / 1024)
        mem_free = str(memInfo.total / 1024 / 1024 - memInfo.used / 1024 / 1024)
        ret_metrics["mem_total"] = mem_total
        ret_metrics["mem_used"] = mem_used
        ret_metrics["mem_free"] = mem_free

    except NVMLError as err:
        print(handle_error(err))

    # MIG doesn't support the following functions. 
    # For MIG-enabled device, we can get temperature from the device handle
    handle = nvmlDeviceGetHandleByIndex(id)
    try:
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)) 
    except NVMLError as err:
        temp = handle_error(err)
    ret_metrics["temp"] = temp

#   print(mem_total)
#   print(mem_used)
#   print(mem_free)
#   print(temp)

    return ret_metrics


def _convert_to_mib(size_str):
    _ = size_str.split(' ')
    size = float(_[0])
    unit = _[1]
    if unit in "GiB|GB|G|gib|gb|g":
        return size * 1024
    elif unit == "MiB|MB|M|mib|mb|m":
        return size
    elif unit == "KiB|KB|K|kib|kb|k":
        return size / 1024
    else:
        sys.exit("Fatal error: size unit is not recognized")

host = platform.node().split(".")[0]

jobhost = []
for fn in os.listdir(config["job_info_path"]):
    if host in fn:
       jobhost.append(fn)

#print(jobhost)

for fn in jobhost:
    jobid = fn.split(".")[0]
#   print(jobid)
    with open(config["job_info_path"]+"/"+fn, 'r') as file:
        jobinfo = yaml.safe_load(file)

    # Create a performance file for the job if it doesn't exist
    # and write meta data to the file
    perf_path = config["perf_path_prefix"]+"/"+jobid
    if not os.path.exists(perf_path):
        os.makedirs(perf_path)
    gpus = jobinfo["gpus"][host]

    for gpu in gpus:
        idx = gpu["idx"]
 
        perf_fn = perf_path+"/"+host+"."+str(idx)
        if not os.path.isfile(perf_fn): 
            with open(perf_fn, "w") as perfile:
                # print metrics format
                perfile.write("# timestamp:mm-dd-yyy:gpu_type:idx:uuid:mem_total:mem_used:gpu_util:temperature:num_procs:proc_name:mem:proc_name:mem...\n")
                perfile.write("# mem size is in MiB; temperature is in Celsius.\n")
                perfile.write("---\n")
    
                # print meta data
                perfile.write("jobid: "+jobid+"\n")
                perfile.write("userid: "+jobinfo["userid"]+"\n")
                perfile.write("jobname: "+jobinfo["jobname"]+"\n")
                perfile.write("nodename: "+host+"\n")
                perfile.write("metrics:"+"\n")
    
                # create a symlink, pointing to perfile     
                perf_user_path = config["perf_user_prefix"]+"/"+jobinfo["userid"]
                if not os.path.exists(perf_user_path):
                    os.makedirs(perf_user_path)
                os.symlink(perf_fn, perf_user_path+"/"+jobid+"."+host+"."+str(idx))
    
        # Append performance metrics to the file
        perfile = open(perf_fn, "a")

        uuid = ""
        if "MIG" in gpu["type"]:
            uuid = uuids[host][idx]  
            id = ids[host][idx]
        else:
            id = idx

#       print(uuid)

        perf_metrics = _get_gpu_usage(id, uuid)
        perf_metrics["jobid"] = jobid
        perf_metrics["userid"] = jobinfo["userid"]
        perf_metrics["jobname"] = jobinfo["jobname"]
#       print(perf_metrics)
        perfstr = "  - "
        ts = time.time()
        perfstr = perfstr + str(ts)
        dt = datetime.fromtimestamp(ts)
        str_dt = dt.strftime("%m-%d-%Y")
        perfstr = perfstr + ":" + str_dt
        perfstr = perfstr + ":" + gpu["type"]
        perfstr = perfstr + ":" + str(idx)
        perfstr = perfstr + ":" + uuid
        perfstr = perfstr + ":" + perf_metrics["mem_total"]
        perfstr = perfstr + ":" + perf_metrics["mem_used"]
        perfstr = perfstr + ":" + perf_metrics["gpu_util"]
        perfstr = perfstr + ":" + perf_metrics["temp"]
        num_procs = perf_metrics["num_procs"]
        perfstr = perfstr + ":" + str(num_procs)
        for i in range(num_procs):
            perfstr = perfstr + ":" + perf_metrics["procs"][i]["name"]
            perfstr = perfstr + ":" + str(perf_metrics["procs"][i]["mem"])

        perfile.write(perfstr+"\n")

        # check if the GPU device is idle
        if num_procs == 0:
            idle_fn = config["idle_job_path"]+"/"+jobid+"."+host+"."+str(idx)
            if not os.path.isfile(idle_fn):
                Path(idle_fn).touch()

            with open(idle_fn, "a") as idlefile:
                idlefile.write(str(ts)+"\n")

        else:
            # check if the memory size is smaller than the small job threshold
            sm_threshold = _convert_to_mib(config["small_job_threshold"])
            if float(perf_metrics["mem_used"]) < sm_threshold:
                small_fn = config["small_job_path"]+"/"+jobid+"."+host+"."+str(idx)
                if not os.path.isfile(small_fn):
                    Path(small_fn).touch()
    
                with open(small_fn, "a") as smallfile:
                    smallfile.write(str(ts)+":"+perf_metrics["mem_total"]+":"+perf_metrics["mem_used"]+"\n")

        perfile.close()


