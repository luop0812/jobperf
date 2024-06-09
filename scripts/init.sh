#!/bin/bash

module load miniconda
export CONDA_ENVS_PATH=/home/pl543/workspace/conda
conda activate pytorch_env
PERFPATH=/home/pl543/project/jobperf
export PYTHONPATH=${PERFPATH}/parser
python ${PERFPATH}/init.py
