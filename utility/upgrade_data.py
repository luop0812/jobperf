import os
import re
import subprocess
import yaml
from config import config


def _get_groupid(userid):
    cmd = "id -gn " + userid 
    return subprocess.run(cmd.split(), capture_output=True, text=True, check=True).stdout.strip()

metadata_fields = ["jobid", "userid", "groupid", "jobname", "nodename", "start_timestamp"]

perf_path_prefix = config["perf_path_prefix"]
idle_job_path = config["idle_job_path"]
small_job_path = config["small_job_path"]

# stores metadata for each job.node.idx file
metadata_jni = {}
# upgrade performance files
for jobid in os.listdir(perf_path_prefix):
    for fn in os.listdir(perf_path_prefix+"/"+jobid):
        fullname = perf_path_prefix+"/"+jobid+"/"+fn
        #print(fullname)
        if fullname == "":
            continue

        with open(fullname, "r") as f:
            jobperf = yaml.safe_load(f)
            #print(jobperf)
            #print(jobperf["metrics"])
            #print(jobperf.keys())
            # process "groupid"
            if not "groupid" in jobperf.keys():
                jobperf["groupid"] = _get_groupid(jobperf["userid"])
                #print(jobperf["groupid"])

            # process "start_timestamp"
            if not "start_timestamp" in jobperf.keys():
                jobperf["start_timestamp"] = jobperf["metrics"][0].split(":")[0]
                #print(jobperf["start_timestamp"])

            metadata= {}
            for key in metadata_fields:
                metadata[key] = jobperf[key]
            #print(metadata)
            key = jobid+"."+fn
            #print(key)
            metadata_jni[key] = metadata

            # write jobperf into a new file
            with open(fullname+".new", "w") as newf:
                # write the comment
                newf.write("# timestamp:mm-dd-yyy:gpu_type:idx:uuid:mem_total:mem_used:gpu_util:temperature:num_procs:proc_name:mem:proc_name:mem...\n")
                newf.write("# mem size is in MiB; temperature is in Celsius.\n")
                newf.write("---\n")
                for field in metadata_fields:
                    #print(field)
                    #print(metadata[field])
                    newf.write(field+": "+str(metadata[field])+"\n")
                # write performance metrics
                newf.write("metrics:\n")
                for i in range(len(jobperf["metrics"])):
                    newf.write("  - "+jobperf["metrics"][i]+"\n")

            # replace the old perf file with the new perf file
            cmd = "mv "+fullname+".new "+fullname
            subprocess.run(cmd.split(), capture_output=True, text=True, check=True)

# upgrade idle job files
for idlefn in os.listdir(idle_job_path):
    # if the file is already in the new format, skip
    fullidlefn = idle_job_path+"/"+idlefn
    with open(fullidlefn, "r") as idlefile:
        string = idlefile.read().strip()
        if re.search("groupid", string):
            continue

    lines = string.split("\n")

    with open(fullidlefn+".new", "w") as newidlefile:
        # write comment
        newidlefile.write("# timestamp\n")
        newidlefile.write("---\n")

        for field in metadata_fields:
            newidlefile.write(field+": "+str(metadata_jni[idlefn][field])+"\n")
        newidlefile.write("metrics:\n")
        for line in lines:
            if not re.search("^  - ", line):
                newidlefile.write("  - "+line+"\n")
            else:
                newidlefile.write(line+"\n")

    cmd = "mv "+fullidlefn+".new "+fullidlefn
    subprocess.run(cmd.split(), capture_output=True, text=True, check=True)

# upgrade small job files
for smallfn in os.listdir(small_job_path):
    fullsmallfn = small_job_path+"/"+smallfn
    with open(fullsmallfn, "r") as smallfile:
        string = smallfile.read().strip()
        if re.search("groupid", string):
            continue

    lines = string.split("\n")

    with open(fullsmallfn+".new", "w") as newsmallfile:
        # write comment
        newsmallfile.write("# timestamp:total_mem:used_mem\n")
        newsmallfile.write("---\n")

        for field in metadata_fields:
            newsmallfile.write(field+": "+str(metadata_jni[smallfn][field])+"\n")
        newsmallfile.write("metrics:\n")
        for line in lines:
            if not re.search("^  - ", line):
                newsmallfile.write("  - "+line+"\n")
            else:
                newsmallfile.write(line+"\n")

    cmd = "mv "+fullsmallfn+".new "+fullsmallfn
    subprocess.run(cmd.split(), capture_output=True, text=True, check=True)
