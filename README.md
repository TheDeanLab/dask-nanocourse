# Scalable Data Analysis with Dask
## Lyda Hill Department of Bioinformatics
### University of Texas Southwestern Medical Center

-------------------------

## Course Information
**Dates:** 8/6/2025
**Instructors:** Kevin Dean, Ph.D. and Conor McFadden  
**Credit Hours:** 0.5 
**Room:** G9.102  
**Class Size:** 10  

-------------------------

## Course Description
This one-day advanced Python course introduces graduate students and postdoctoral scientists to parallel and distributed computing using Dask, with a focus on large-scale biomedical data analysis. Participants will learn how to process and analyze 2D/3D image data and sequencing datasets using Dask Arrays and DataFrames, including out-of-core computation and storage with Zarr. The course covers local parallelism, distributed computing on SLURM clusters, and best practices for performance profiling and optimization. Through lectures, hands-on exercises, and real-world examples, attendees will gain the skills to scale their existing NumPy, Pandas, and scikit-image workflows to handle large datasets efficiently and reproducibly.

-------------------------

## Course Objectives
By the end of this course, participants will be able to:
- Understand the need for parallel and distributed computing in handling large biomedical datasets.
- Learn what Dask is and how it enables parallel processing by dividing work into tasks.
- Familiarize with Dask’s core concepts (task graphs, schedulers, lazy evaluation) and how it integrates with Python’s scientific stack.

------

## Installation of Dependencies
### Using venv
```bash
python -m venv .venv
pip install --upgrade pip
pip install -e .
```

### Using Conda on BioHPC
```bash
module load python/latest-3.12.x-anaconda
(base) conda create -n dask-nanocourse python=3.10
(base) conda activate dask-nanocourse
(dask-nanocourse) pip install --upgrade pip setuptools wheel
(dask-nanocourse) conda install -c conda-forge pyzmq
(dask-nanocourse) pip install -e . --no-cache-dir

```

## Add the kernel to your iPython environment and launch a Jupyter Notebook
Install the IPython kernel inside the activated virtual environment, then register it with Jupyter:

## Using venv
```bash
python -m ipykernel install --user --name .venv --display-name "Dask Nanocourse"
```

## Using Conda
```bash
python -m ipykernel install --user --name dask-nanocourse --display-name "Dask Nanocourse"
```


## Install Jupyter Lab Extensions
```bash
conda install nodejs
jupyter labextension install dask-labextension
```

## Launch Jupyter Lab
```bash
jupyter-lab
```

