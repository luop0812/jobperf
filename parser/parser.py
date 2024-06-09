''' parser.py '''

"""
This module provides utilites to parse text into a dictionary.
"""

import yaml
import json
import uuid
import subprocess
import sys
import os
import re

import constant as const
import block_parser as bp

class Parser:

    """
    cmd: a string for a commandline
    filename: a string for a file name
    ttpye: text type - block, json, yaml, xml
    keys: a list of keywords to retrieve the values from the output
    """
    def __init__(self, cmd, filename="", ttype="block", scheduler=""):

        self._cmd = cmd
        self._filename = filename
        self._ttype = ttype
        self._maps = const.KEYWORDS[scheduler]
        self._keys = self._maps.values()
        self._records = {}
        self._tmp_filename = "/tmp/" + str(uuid.uuid4())

    """
    
    """
    def _run_cmd(self):
        if self._cmd:
            cmd_list = self._cmd.split()
            text = subprocess.run(cmd_list, capture_output=True, text=True, check=True).stdout

            f = open(self._tmp_filename, "w")
            f.write(text)
            f.close()

    """

    """
    def _get_processed_records(self):
        mylist = []
        if self._cmd:
            self._run_cmd()
            filename = self._tmp_filename
        else:
            filename = self._filename

        if self._ttype == "block":
            #print(self._keys)
            #print(filename)
            parser = bp.BlockParser(filename, self._keys)
            mylist = parser.get_processed_blocks() 
        else:
            print("{0} has not been implemented.".format(self._ttype))
            sys.exit(1)

        return mylist

    """

    """
    def _remove_tmp_file(self):
        if os.path.isfile(self._tmp_filename):
            os.remove(self._tmp_filename)
#       print("{0} is removed.".format(self._tmp_filename))

class JobParser(Parser):

    """
    records{
        jobid:{
            "gpus"    :[nodename:[{"type":gpu_type, "id":gpu_id}]], 
            "nodelist":[nodename],
            "userid"  :userid,
            "partition":partition
        }
    }
    """
    def __init__(self, *args, scheduler="SLURMJOB", **kwargs):
        super().__init__(*args, scheduler="SLURMJOB", **kwargs)

    """
    0,3,5-7
    """
    def _get_idx(self, s):
        idx = []
        if s == '':
            return idx

        _ = s.split(",")
        for i in range(len(_)):
            if "-" in _[i]:
                start = int(_[i].split("-")[0])
                end   = int(_[i].split("-")[1]) + 1
                for j in range(start, end):
                    idx.append(j)
            else:
                idx.append(int(_[i]))
        return idx

    """
    gpu:a40:4(IDX:0-3)
    gpu:a40:2(IDX:0,3)
    gpu:a100.MIG.20gb:1(IDX:0)
    gpu:a100.MIG.10gb:2(IDX:8,9)
    gpu:a100.MIG.20gb:5(IDX:0,3,5-7)
    """
    def _process_gpu_gres(self, gres):
        gpu_device_list = []

        _ = gres.split(":")
        gpu_type = _[1]
        num_devices = int(_[2].split('(')[0])
        
        if num_devices == 0:
            return gpu_device_list

        ids = []
        result = re.search(r"\(IDX:(.*)\)", gres)
        if result:
            ids = self._get_idx(result.group(1))

        assert len(ids) == num_devices
        for i in range(len(ids)):
            gpu_device_list.append({"type":gpu_type, "idx":ids[i]})

        return gpu_device_list

    def _get_greses(self, s):
        greses = []
        begin = 0
        if s:
            for i in range(len(s)-1):
                if s[i] == ')' and s[i+1] == ',':
                    greses.append(s[begin:i+1])
                    i = i+2
                    begin = i
            greses.append(s[begin:i+2])
    
        return greses

    """
    Process associative keys and values for gpus
    Examples:
    'assoc1_key': ['r817u09n05'], 'assoc1_val': ['']
    'assoc1_key': ['r4516u05n01,r4516u09n01'], 'assoc1_val': ['gpu:a40:4(IDX:0-3)']
    'assoc1_key': ['r4516u01n01', 'r4516u01n02'], 'assoc1_val': ['gpu:a40:1(IDX:0)', 'gpu:a40:1(IDX:1)']
    'assoc1_key': ['r4519u01n01'], 'assoc1_val': ['gpu:a100.MIG.20gb:1(IDX:0),gpu:a100.MIG.10gb:0(IDX:)']
    'assoc1_key': ['r106u35n01,r107u27n01,r107u35n01','r109u12n01'], 'assoc1_val': ['gpu:a5000:4(IDX:0-3)','gpu:rtx3090:4(IDX:0-3)']
    'assoc1_key': ['r4519u01n01'], 'assoc1_val': ['gpu:a100.MIG.10gb:1(IDX:8),gpu:a100.MIG.20gb:1(IDX:0)']
    'assoc1_key': ['r4519u01n01'], 'assoc1_val': ['gpu:a100.MIG.20gb:5(IDX:0,3,5-7)']
    """
    def _process_gpus(self, assoc1_key, assoc1_val):
        
        assert len(assoc1_key) == len(assoc1_val)
        ng_dict = {}
        
        for index in range(len(assoc1_key)):
            nodes = assoc1_key[index].split(",")
            greses = self._get_greses(assoc1_val[index])

            if len(greses) == 1:
                if greses[0] == '':
                    for node in nodes:
                        ng_dict[node] = []
                else:
                    _ = self._process_gpu_gres(greses[0])
                    for node in nodes:
                        ng_dict[node] = _
            else:
                assert len(nodes) == 1
                node = nodes[0]
                gpu_list = []
                for gres in greses:
                    _ = self._process_gpu_gres(gres)
                    if _:
                        gpu_list = gpu_list + _
                ng_dict[node] = gpu_list

        return ng_dict

    """
    dfl32(21944) => dfl32
    """
    def _process_userid(self, userid):
        return userid.split('(')[0]


    """
    return a dictionary of running job records
    """
    def get_records(self):

        mylist = self._get_processed_records()
        #print(mylist)

        job_record = {}
        for ml in mylist:
            # we are only interested in running jobs
            if any("RUNNING" in s for s in ml):
                assoc1_key = []
                assoc1_val = []
                for mll in ml:
                    _ = mll.split("=")
                    if _[0] == self._maps["assoc1_key"]:
                        assoc1_key.append(_[1])
                    elif _[0] == self._maps["assoc1_val"]:
                        assoc1_val.append(_[1])
                    else:
                        key = list(self._maps.keys())[list(self._maps.values()).index(_[0])]
                        job_record[key] = _[1]
                assert len(assoc1_key) == len(assoc1_val)
                job_record["assoc1_key"] = assoc1_key
                job_record["assoc1_val"] = assoc1_val
                #print(job_record)

                node_gpu_dict = self._process_gpus(job_record["assoc1_key"], job_record["assoc1_val"])
                userid = self._process_userid(job_record["userid"])
                jobid = job_record["jobid"]
                self._records[jobid] = {}
                self._records[jobid]["userid"] = userid
                self._records[jobid]["jobname"] = job_record["jobname"]
                self._records[jobid]["nodelist"] = job_record["nodelist"].split(",")
                self._records[jobid]["partition"] = job_record["partition"]
                self._records[jobid]["gpus"] = node_gpu_dict
                assert len(self._records[jobid]["nodelist"]) == len(node_gpu_dict.keys())

        #print(self._records)
        #print(self._records.keys())
        # cleanup
        self._remove_tmp_file()

    """
    output the job records to a file or files in path. 
    if filename is empty, records will be stored in separate files with the name jobid.nodename
    else all records will be stored in filename.
    """
    def dump_records(self, path, filename="", fmt="yaml"):
        # check if the path exists
        if not os.path.exists(path):
            os.makedirs(path)

        if filename:
            if fmt == "yaml":
                f = open(path+"/"+filename, "w")
                f.write(yaml.dump(self._records))
                f.close()
            else:
                print("Output format {0} has not been implemented.".format(fmt))
                sys.exit(1)
        else:
            for jobid in self._records.keys():
                for node in self._records[jobid]["nodelist"]:
                    f = open(path+"/"+jobid+"."+node, "w")
                    f.write(yaml.dump(self._records[jobid]))
                    f.close()
            
class NodeParser(Parser):

    def __init__(self, *args, scheduler="SLURMNODE", **kwargs):
        super().__init__(*args, scheduler="SLURMNODE", **kwargs)

# test
#parser = JobParser("scontrol show job -d")
#parser = JobParser("", "./test.txt", scheduler="SLURMJOB")
#parser = JobParser("", "./test.txt")
#parser.get_records()
#parser.dump_records("/home/pl543/workspace/jobprofile/implementation/individual","")
#parser.dump_records(".","output.yml")
