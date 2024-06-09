#!/bin/bash

[ ! "$(declare -fF module)" ] && source /etc/profile.d/00-modulepath.sh && source /etc/profile.d/modules.sh && source /etc/profile.d/z01_StdEnv.sh

module load miniconda
export CONDA_ENVS_PATH=/home/pl543/workspace/conda
conda activate pytorch_env
PERFPATH=/home/pl543/project/jobperf
export PYTHONPATH=${PERFPATH}/parser
python ${PERFPATH}/controller.py
