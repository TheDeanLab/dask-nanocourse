---
layout: cover
---

## Distributed Dask: Scaling to Clusters with SLURM

### Session 4: 2:30 – 3:15 PM

---


## Clusters versus Runners


**Clusters:** Creates new jobs for Dask workers. Scales to the number of workers needed, if available.
- Can request a fixed number of resources, or dynamically scale number of workers with project demands.
- Requires job queue permissions
- Better for interactive/adaptive workloads


**Runners:** Uses existing allocated resources to run Dask workers. Does not scale beyond the initial allocation.
- Uses existing resources without submitting new jobs.
- Sets up scheduler on head node, workers on remaining nodes

**Key Features:**
- Dask automatically discovers available nodes from SLURM environment
- Dask handles network configuration and port management


---

## Dask Cluster Types
### HPC Clusters
**Multi-Machine Parallelism**
- SLURM, PBS, LSF, SGE support
- Submit Dask workers as batch jobs
- Automatic scaling based on workload

```python
from dask_jobqueue import SLURMCluster
cluster = SLURMCluster(
    queue='normal',
    cores=24,
    memory='128GB',
    walltime='02:00:00',
    job_extra=['--constraint=haswell']
)

cluster.scale(jobs=10)  # Request 10 nodes
client = Client(cluster)
```

---


## Dask Cluster Types

### Cloud-Native Solutions


**Kubernetes Clusters**
- Container orchestration for Dask workers
- Auto-scaling based on demand
- Integration with cloud providers (AWS, GCP, Azure)

```python
from dask_kubernetes import KubeCluster
cluster = KubeCluster.from_yaml('worker-spec.yaml')
cluster.scale(20)  # 20 worker pods
client = Client(cluster)

```

**Coiled:** Managed Dask clusters with auto-scaling and easy deployment.

**Saturn Cloud:** Provides Dask clusters with Jupyter integration and easy scaling.

**AWS Fargate:** Serverless Dask clusters on AWS, automatically scaling based on workload.

---


## Leveraging BioHPC for Dask


### How to perform a multi-node SlurmRunner job on BioHPC


See **_exercises/session_4/exercise_3.sh_**


```bash {*}{maxHeight:'300px'}
#!/bin/bash
#SBATCH --job-name dask-seg # Job name
#SBATCH -p 512GB # Partition name (queue)
#SBATCH -N 6 # Number of nodes
#SBATCH --mem 501760  # Total memory per node (in MB)
#SBATCH -t 2-0:0:00 # Wall time (days-hours:minutes:seconds)
#SBATCH -o /home2/kdean/portal_jobs/job_%j.out
#SBATCH -e /home2/kdean/portal_jobs/job_%j.err
#SBATCH --mail-type ALL
#SBATCH --mail-user kevin.dean@UTSouthwestern.edu

export PATH="/project/bioinformatics/Danuser_lab/Dean/dean/miniconda3/bin:$PATH"
eval "$(/project/bioinformatics/Danuser_lab/Dean/dean/miniconda3/bin/conda shell.bash hook)"
conda --version
source activate dask-nanocourse

srun -n 5 \
   python /archive/bioinformatics/Danuser_lab/Dean/dean/git/dask-nanocourse/exercises/exercise_3.py \
   --job-id "${SLURM_JOB_ID}"
exit 0


```


---


## Leveraging BioHPC for Dask

### How to perform a multi-node SlurmRunner job on BioHPC (continued)

See **_exercises/session_4/exercise_3.py_**

```python {*}{maxHeight:'300px'}
# Standard Library Imports
import os
import argparse
import logging

# Third Party Imports
import numpy as np
from scipy import ndimage
from dask.distributed import Client
from dask_jobqueue.slurm import SLURMRunner
import dask.array as da

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--job-id", type=str, required=True, help="SLURM Job ID")
args = parser.parse_args()

# Setup logging. Job ID automatically crated by SLURM.
log_path = os.path.join("/home2/kdean/portal_jobs/", f"job_{args.job_id}.log")
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logging.getLogger().setLevel(logging.INFO)
logging.info(f"SLURM Job ID: {args.job_id}")

# Specify the location of the scheduler file according to job id
schedule_path = os.path.join("/home2/kdean/portal_jobs/", f"scheduler_{args.job_id}.json")

# Base path for saving the output Zarr file.
base_path = "/archive/shared/MIL"

# Location of the data.
data_path = os.path.join(base_path, "3d.zarr")
save_path = os.path.join(base_path, 'example_3.zarr')

with SLURMRunner(scheduler_file=schedule_path) as runner:
    with Client(runner) as client:

        # Wait for the Dask workers to be ready
        client.wait_for_workers(runner.n_workers)

        # Configure logging for the Dask client
        client.run(lambda: logging.basicConfig(level=logging.INFO))

        # Log the connection to the Dask scheduler and number of workers
        logging.info(f"Dask Client connected to the scheduler: {client}")
        logging.info(f"Number of workers: {len(client.scheduler_info()['workers'])}")

        # Load the Zarr file with Dask
        dask_data = da.from_zarr(data_path, component='0/0')
        data_shape = dask_data.shape
        logging.info(f"Loaded data: {data_path}")

        dask_data = dask_data.squeeze()
        dask_data = dask_data.rechunk((32, 64, 64))

        # Difference of Gaussian Filtering.
        high_pass_filtered = dask_data.map_overlap(
            ndimage.gaussian_filter, sigma=3, order=0, mode="nearest", depth=40)

        low_pass_filtered = dask_data.map_overlap(
            ndimage.gaussian_filter, sigma=10, order=0, mode="nearest", depth=40)

        dog_filtered = da.map_blocks(
            np.subtract, high_pass_filtered, low_pass_filtered)

        # Save the filtered data to a Zarr file
        dog_filtered.to_zarr(save_path)
        logging.info("Difference of Gaussian filtering completed.")

```


---

## Leveraging BioHPC for Dask
### How to perform a multi-node SlurmCluster job on BioHPC

**Slurm Clusters**
- Use `SLURMCluster` to create a Dask cluster that automatically submits jobs to SLURM.
- Run a single python script or Jupyter notebook that initializes the cluster and submits jobs.  
- Cluster configuration directly specified in script, or can be loaded from a YAML file.

---

## Leveraging BioHPC for Dask
### How to perform a multi-node SlurmCluster job on BioHPC

- See **_exercises/session_4/exercise_4.ipynb_**


```python {*}{maxHeight:'300px'}
# Standard Library Imports
import os
import time
import subprocess

# Third Party Imports
from dask_jobqueue import SLURMCluster
from dask.distributed import Client
from dask import array as da
import numpy as np
from scipy import ndimage

# Figure out what your default `umask` setting is.
result = subprocess.run("umask", shell=True, capture_output=True, text=True)
print("Subprocess umask:", result.stdout.strip())

# Create temporary directory and make sure that we have write privileges.
local_directory="/project/bioinformatics/Danuser_lab/Dean/dean/dask_temp"
subprocess.run(f"mkdir -p {local_directory} && chmod -R 777 {local_directory}", shell=True)

# Location of the data.
base_path = "/archive/bioinformatics/Danuser_lab/Dean/dean/2024-05-21-tiling"
data_path = os.path.join(base_path, "cell5_fused_tp_0_ch_0.zarr")
save_path = os.path.join(base_path, 'example_4.zarr')

cluster_kwargs = {
    'cores': 28, # Number of threads per worker (utilizing cores within each process)
    'processes': 1, # Number of Python processes/worker.
    'memory': '220GB', # Total memory to allocate for each worker job.
    'local_directory': local_directory, #  Path for the Dask worker’s local storage (scratch space).
    'interface': 'ib0', # Network interface identifier for Dask communications. Infiniband.
    'walltime': "01:00:00", # The wall-time limit for each job, in HH:MM:SS.
    'job_name': "nanocourse", # Name for the Slurm job, publicly visible via squeue command.
    'queue': "256GB", # Slurm partition/queue to submit the jobs to
    'death_timeout': "600s", #  Timeout (in seconds) for worker survival without a scheduler connection.
    'job_extra_directives': [
        # --nodes=1 and --ntasks=1 ensure each job runs on a single node with one task
        "--nodes=1",
        "--ntasks=1",
        "--mail-type=FAIL",
        "--mail-user=kevin.dean@utsouthwestern.edu",
        "-o job_%j.out",
        "-e job_%j.err",
    ],
    'scheduler_options': {
        # A dictionary of settings passed to the Dask scheduler.
        "dashboard_address": ":9000",       # Dashboard web interface port
        "interface": "ib0",

        # Resource management
        "idle_timeout": "3600s",            # How long workers stay alive when idle (1 hour)
        "allowed_failures": 10,             # More failures allowed before worker marked as bad
    },
}

def wait_for_cluster(client, number_of_workers, start_time, timeout=120):
    print("Waiting for workers to connect", end="", flush=True)

    prev_count = 0
    while True:
        curr_count = len(client.scheduler_info()['workers'])
        if time.time() - start_time > timeout:
            print("\nTimed out. Canceling.")
            break

        # if no workers yet, print a dot (once) and continue
        if curr_count == 0:
            print(".", end="", flush=True)
            prev_count = 0
            time.sleep(0.3)
            continue

        if curr_count != prev_count:
            print(f"{curr_count} workers are connected.", flush=True)
            prev_count = curr_count

        if curr_count >= number_of_workers:
            break

        time.sleep(0.3)

def launch_job(data_path, save_path, number_of_workers, cluster_kwargs):

    cluster = SLURMCluster(**cluster_kwargs)
    cluster.scale(number_of_workers+1)
    client = Client(cluster)

    start_time = time.time()
    wait_for_cluster(client, number_of_workers, start_time, timeout=120)
    print(f"Client dashboard available at: {client.dashboard_link}")

    # Load the Zarr file with Dask
    dask_data = da.from_zarr(data_path, component='0/0')
    data_shape = dask_data.shape

    # Eliminate singleton dimensions, and rechunk the data.
    dask_data = dask_data.squeeze()
    dask_data = dask_data.rechunk((32, 64, 64))

    # Process the data
    high_pass_filtered = dask_data.map_overlap(
        ndimage.gaussian_filter, sigma=3, order=0, mode="nearest", depth=40)

    low_pass_filtered = dask_data.map_overlap(
        ndimage.gaussian_filter, sigma=10, order=0, mode="nearest", depth=40)

    dog_filtered = da.map_blocks(
        np.subtract, high_pass_filtered, low_pass_filtered)

    dog_filtered.to_zarr(save_path, overwrite=True)

    # Close the client and cluster
    client.close()
    cluster.close()
    print("Client and cluster closed.")
    print(f"Total time to compute: {time.time() - start_time}")

number_of_workers = 4
launch_job(data_path, save_path, number_of_workers, cluster_kwargs)

```

---

## Cluster Management Best Practices
### Worker Memory vs. Chunk Size Relationships
 - **Match chunk size to worker memory:** Choose chunk sizes small enough that many chunks fit into a worker’s RAM concurrently.  Partitions larger than a few gigabytes risk exceeding memory. Very tiny partitions (e.g. <1MB) create millions of tasks, overwhelming the scheduler. 
 - **Use guidelines for chunk sizing:** As a rule of thumb, aim for chunk sizes on the order of 100MB to 1GB for HPC workloads. Chunks much smaller than 100MB often incur high overhead, whereas chunks larger than 1–2GB should only be used if a worker has ample memory per core.
 - **Ensure sufficient parallelism:** Having too few chunks can under-utilize the cluster. The number of chunks should be at least equal to (or a multiple of) the total cores in the cluster to keep all workers busy (e.g. ≥2× number of cores) ￼.
 - **Tune memory in SLURM jobs:** When using Dask-Jobqueue with SLURM, set each worker’s memory limit to match the SLURM allocation (e.g. SLURMCluster(memory="16GB", cores=4)). This ensures Dask’s scheduler is aware of real memory per job. 
---

## Cluster Management Best Practices
### Network Bandwidth Considerations

 - **Leverage high-speed interconnects:** On HPC clusters with InfiniBand or similar, instruct Dask to use the high-bandwidth interface. For example, pass --interface ib0 to dask-scheduler/dask-worker or interface='ib0' in your SLURMCluster so Dask uses InfiniBand instead of Ethernet ￼.
 - **Minimize data transfer volume:** Avoid repeatedly shipping large datasets through the scheduler or client. Instead, load data in parallel on the workers or use methods like client.scatter to distribute data once upfront. This reduces network load and prevents the scheduler from becoming a bottleneck due to large data handling.
 - **Be cautious with shuffles and broadcasts:** Operations like Dask DataFrame shuffles or broadcasting variables to all tasks can saturate network bandwidth. If possible, repartition or filter data to reduce shuffle sizes, or use algorithms that localize data. 
 - **Monitor communication in the dashboard:** The Task Stream plot highlights communication delays (e.g. red segments indicate waiting on data from peers). 

---

## Cluster Management Best Practices
### Storage Locality Optimization

 - **Avoid spilling to shared filesystems:** By default, Dask workers spill excess data to the temp directory, which on HPC systems is often a shared network filesystem (NFS, Lustre, etc.). It’s best to minimize reliance on a shared FS for intermediate data.
 - **Use node-local storage for temp data:** If compute nodes have local SSD scratch space, direct Dask to use them for spilling and scratch files. For example, launch workers with `--local-directory /local/scratch` or configure `local_directory=...` in the cluster setup.
 - **Adjust spilling behavior if needed:** On systems without any local storage, you may choose to disable disk spilling to avoid pounding the shared filesystem. Dask allows this via config: e.g., setting `distributed.worker.memory.spill`: false (and memory.target: false) will prevent spilling and instead pause tasks when memory is full ￼. In such cases, it’s crucial to fit working data in memory or increase memory per worker.
 - **Persist data to improve locality:** If a dataset will be reused across multiple computations, call `persist()` on it to keep it in distributed memory (or explicitly write to a node-local store). 

---

## Cluster Management Best Practices
### Dask Dashboard for Real-Time Monitoring

 - **Live cluster insight:** The Dask dashboard (a web UI on the scheduler, default port 8787) provides real-time visualization of your computations. It shows tasks progressing, cluster CPU utilization, memory usage per worker, network throughput, etc., helping you understand the state of your cluster at a glance ￼.
 - **Identify bottlenecks visually:** Use the dashboard’s plots to catch performance issues. For example, red for waiting on data, orange for disk I/O, etc.
 - **Build parallel intuition:** The dashboard is an excellent teacher of distributed performance; visual feedback helps develop intuition on how tasks, data, and resources interact in Dask.
 - **Accessing the dashboard on HPC:** In a SLURM cluster environment, the dashboard is typically not directly visible on your local machine. You can forward the port via SSH to view it in a browser.
    ```bash
    `ssh -N -L 44460:localhost:44460 your-cluster-login@nucleus.biohpc.swmed.edu`
    #You can then access this at `http://localhost:44460/status`
    ```
 - **Dashboard panels and usage:** Explore different tabs like Status, Workers, Task Graph, Profile, etc. The Workers tab shows per-worker CPU and memory; the Graph tab visualizes the task dependency graph (useful to spot stragglers or uneven task distribution). 

--- 

## Cluster Management Best Practices
### Performance Profiling Tools
 - **Programmatic profiling with `Client.profile()`:** In addition to the live view, you can capture profiling data in your code. The `Client.profile() `method returns the collected profile info, which you can save to disk (e.g., `client.profile(filename=\"dask-profile.html\")`). This HTML profile can be viewed later, allowing offline analysis of a run’s performance characteristics.
 - **Performance reports:** For a comprehensive performance snapshot, use `distributed.performance_report`. Wrapping your computations in with `performance_report(filename=\"dask-report.html\")`: will produce an HTML report containing major diagnostics – task timeline, worker profiles, transfer statistics, etc. This is  useful for sharing results of a performance test or debugging session with colleagues, or analyzing performance post hoc.
 - **Classic profilers vs Dask:** Traditional Python profilers (e.g. cProfile) don’t capture multi-threaded or multi-process workloads well. Dask’s built-in tools are designed for distributed execution. If needed, you can still profile a portion of your code in isolation (e.g., run a representative task function locally under cProfile). 

---
layout: cover

---
## Adapting Code for Distributed Dask 
### Lab 3: 3:30 – 4:15 PM

Spend some time adapting your existing code to run with Dask. 

Pair up, have fun, see if you can launch a multi-node Dask job on BioHPC, and share your results with the class.
