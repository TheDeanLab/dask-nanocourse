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

# Local Imports

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
base_path = "/archive/bioinformatics/Danuser_lab/Dean/dean/2024-05-21-tiling"

# Location of the data.
data_path = os.path.join(base_path, "cell5_fused_tp_0_ch_0.zarr")
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
