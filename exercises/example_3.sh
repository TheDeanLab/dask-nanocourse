#!/bin/bash
#SBATCH --job-name dask-seg
#SBATCH -p 512GB
#SBATCH -N 6
#SBATCH --mem 501760
#SBATCH -t 0-0:30:00
#SBATCH -o /home2/kdean/portal_jobs/job_%j.out
#SBATCH -e /home2/kdean/portal_jobs/job_%j.err
#SBATCH --mail-type ALL
#SBATCH --mail-user kevin.dean@UTSouthwestern.edu

# Non-Standard miniconda path
export PATH="/project/bioinformatics/Danuser_lab/Dean/dean/miniconda3/bin:$PATH"

# Load updated PATH
eval "$(/project/bioinformatics/Danuser_lab/Dean/dean/miniconda3/bin/conda shell.bash hook)"

# Confirm that conda is available
conda --version

# Activate the environment with Dask and other dependencies
source activate dask-nanocourse

# Launch the Python script using Dask with 5 workers
srun -n 5 \
   python /archive/bioinformatics/Danuser_lab/Dean/dean/git/dask-nanocourse/exercises/example_3.py \
   --job-id "${SLURM_JOB_ID}"
exit 0
