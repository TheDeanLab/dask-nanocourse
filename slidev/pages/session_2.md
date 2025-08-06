---
layout: cover

---
## Dask Arrays for Big Image Data 
### Session 2: 10:15 - 11:00 AM


---

## The Problem with Tiff Files

**Logical Structure:** TIFF files can store single or multi-page images. Multi-page TIFF include multiple images within a single file, typically sequentially.

**On-Disk Representation:**
- Image planes typically stored as contiguous blocks or sequential slices in one large file. 
- 3D regions of interest must be read from non-contiguous slices, which is inefficient.
- Metadata (e.g., image dimensions, data type) stored in headers as XML.

**Parallel Read/Write:**
- Reading TIFF files in parallel is challenging due to sequential data layout; often requires reading headers to locate slices.
- Limited parallel I/O, leading to bottlenecks for large images.

---

## Dask Array Storage

**Logical Structure:** Dask arrays themselves are an abstraction without a built-in storage format. Instead, they use external chunked storage backends like Zarr or HDF5 for persistent storage.

**On-Disk Representation (Zarr):**
- Each chunk is stored as an individual compressed binary file within a hierarchical directory structure (e.g., /array_name/0.0.0, /array_name/0.0.1, etc.). 
- A JSON metadata file describes array shape, chunk size, data type, compression.

**Parallel Read/Write:**
- Each chunk can be accessed independently, facilitating highly parallel I/O.
- Excellent performance in distributed environments or cloud storage.
- Compression of each chunk performed independently, reducing storage footprint.

---

## Alternatives to Dask Arrays
**Xarray:** Built on top of NumPy and Dask, Xarray adds labeled dimensions and coordinates to arrays, making it ideal for multidimensional scientific data. Especially popular in atmospheric, oceanographic, and environmental sciences.

**N5/Zarr:** A storage format designed for chunked, compressed, and parallel data access. Often used alongside Dask and Xarray for storing and handling large datasets efficiently. Zarr enables efficient reading and writing of large-scale datasets, particularly beneficial in cloud and HPC environments.

**HDF5:** A widely used file format for storing large amounts of numerical data. HDF5 supports chunking and compression, making it suitable for large datasets. It is often used in scientific computing and data analysis.

**OME-NGFF:** A format specifically designed for biological imaging data, providing a standardized way to store and share image metadata. OME-NGFF is built on top of Zarr and HDF5, and is optimized for cloud computing environments.

_Xarray, Zarr, and OME-NGFF have metadata specifications that accommodate data types associated with image analysis. Outputs, such as segmentation labels, can be saved in a common data structure with the original pixel data and metadata, providing provenance._
---

## Object Storage vs. Traditional File Systems

**Cloud Object Storage:**
- Small objects distributed across multiple servers
- Entire binary objects read as monolithic blocks
- Higher latency but greater parallelization potential
- No random access within files - must read complete objects

**Local HPC Environments:**
- Traditional file systems with random access capabilities
- Lower latency, direct memory mapping possible
- Limited by single-node I/O bandwidth
- Can seek to specific byte ranges within large files

<!--
**Implications for Image Data:**
- Cloud: Favors chunked formats (Zarr/NGFF) with small, independent objects
- HPC: Can efficiently handle large monolithic files (TIFF/HDF5)
- Chunked storage becomes essential for cloud-native workflows
-->

---
layout: image-right
image: pages/images/ngff.png
backgroundSize: 90%
---

## Converting Image Formats

**Universal Metadata Standard**
- Open Microscopy Environment XML schema provides standardized metadata for biological imaging
- Describes image dimensions, acquisition parameters, experimental conditions
- Same OME-XML can be used across different storage backends

<!--
**Benefits of Standardization:**

- Convert between formats while preserving complete metadata
- Tools can read any format using same OME-XML parser
- Future-proof data storage and analysis workflows
-->

---

## Converting Image Formats


**Bio-Formats (Java/Python):** Reads 150+ proprietary formats, writes OME-TIFF, OME-NGFF, etc.
- `bioformats2raw`: Proprietary → OME-NGFF/Zarr
- `raw2ometiff`: OME-NGFF → OME-TIFF
- `python-bioformats`: Python wrapper for Bio-Formats

**Python Ecosystem:**
- `tifffile`: TIFF ↔ NumPy arrays with metadata
- `zarr-python`: Create/read Zarr arrays
- `ome-zarr-py`: OME-NGFF specific operations
- `h5py`: HDF5 file I/O


````bash 
# Proprietary → OME-TIFF
bfconvert input.lsm output.ome.tiff

# OME-TIFF → OME-NGFF
bioformats2raw input.lsm output.zarr
````

---
layout: image-right
image: pages/images/pyramidal.png
backgroundSize: 90%
---

# Multi-Resolution Image Pyramids

- Store same image at multiple resolution levels (scales)
- Full resolution at level 0, each subsequent level downsampled by factor of 2
- Load only the resolution needed for current viewing/analysis task

**Advantages:**
- Quick overview at low resolution, zoom to full detail on demand
- Avoid loading massive full-resolution data for overview tasks

--- 

## Optimizing Chunk Sizes
### Critical for performance in Dask Arrays and Zarr storage

**Chunk Size Trade-offs**. 
- **Too Small:** Task scheduling overhead (~1ms per task) dominates runtime
- **Too Large:** Memory overflow and reduced parallelism
- **Sweet Spot:** 10MB - 1GB chunks, tasks taking >100ms each

**Multi-Dimensional Chunking Strategies**
- **Spatial Chunking (X,Y,Z):** Best for pixel-wise operations
- **Temporal Chunking (T):** Efficient for time-series analysis
- **Hybrid Chunking:** Balance multiple dimensions

```bash
# Generate multi-resolution pyramid with custom chunk size
bioformats2raw --resolutions 5 --tile_width 512 --tile_height 512 --chunk_depth 1 input.czi output.zarr

# Specify custom downsampling factors with optimized chunks
bioformats2raw --resolutions 4 --downsample-type AREA --tile_width 1024 --tile_height 1024 input.lsm pyramid.zarr
````

--- 

## Optimizing Chunk Sizes
### Critical for performance in Dask Arrays and Zarr storage

**Matching Chunks to Analytical Operations**
- **Feature Detection:** Chunks should be 3-5× larger than the largest feature you're detecting
- **Convolution/Filtering:** Include padding equal to filter kernel size. Prevents edge effects
- **2D Operations on 3D Data:** Use thin Z-chunks (1-3 planes) with larger XY dimensions
- **Time Series Analysis:** Chunk along time dimension for operations across timepoints


---

## Lazy Loading of Large Image Data
### Loading Zarr as Dask Array

```python
import dask.array as da

# Load Zarr dataset as Dask array
arr = da.from_zarr('data.zarr')

# Or specify specific array within Zarr group, such as the resolution level. 
# e.g., arr = da.from_zarr('data.zarr', component='0') 

# Inspecting Array Structure
print(f"Shape: {arr.shape}")           # (10, 65, 1024, 1024)
print(f"Chunks: {arr.chunks}")         # ((5, 5), (65,), (512, 512), (512, 512))
print(f"Dtype: {arr.dtype}")           # uint16
print(f"Size: {arr.nbytes / 1e9:.2f} GB")  # 10.22 GB

# Rechunk for different access patterns
spatial_chunks = arr.rechunk((1, 1, 512, 512))      # Spatial operations
temporal_chunks = arr.rechunk((10, -1, 256, 256))   # Time-series analysis
balanced_chunks = arr.rechunk((2, 32, 256, 256))    # Balanced approach

# Persist optimized chunks to storage
balanced_chunks.to_zarr('optimized.zarr')
````

**_exercises/session_2/exercise_2.ipynb_**

---

## Dask Array Operations
### map_blocks: Element-wise Operations

**Apply Functions to Array Chunks Independently**
- Process each chunk separately without communication between chunks
- Ideal for pixel-wise operations (filtering, thresholding, normalization)
- Maintains chunk structure and enables perfect parallelization

**Key Points**

- No overlap between chunks - perfect for independent operations
- Maintains original chunking structure
- Minimal memory 

---

## Dask Array Operations
### map_blocks: Element-wise Operations

```python
import dask.array as da
import numpy as np
from skimage import filters

arr = da.from_zarr('microscopy_data.zarr', component='0/0')

def gaussian_filter_chunk(chunk, sigma=2):
    return filters.gaussian(chunk, sigma=sigma, preserve_range=True)

# Process all chunks in parallel
filtered = da.map_blocks(
    gaussian_filter_chunk, # Function to apply
    arr, # Input Dask array
    sigma=2, 
    dtype=arr.dtype,
    meta=np.array((), dtype=arr.dtype))

result = filtered.compute()
```

---

## Dask Array Operations
### Dask map_overlap: Neighborhood Operations

**Handle Operations Requiring Neighboring Pixels**
- Automatically manages overlap between chunks for convolution-like operations
- Essential for edge detection, morphological operations, and local feature analysis
- Handles boundary conditions and chunk edge artifacts

**Key Parameters:**
- depth: Overlap size (pixels/voxels) - must accommodate operation's neighborhood
- boundary: How to handle array edges ('reflect', 'constant', 'wrap')
- Automatically trims overlap from final result

---

## Dask Array Operations
### Dask map_overlap: Neighborhood Operations

```python
import dask.array as da
import numpy as np
from skimage import morphology, feature

# Load imaging data
arr = da.from_zarr('cell_segmentation.zarr', component='0/0')

# Edge detection requires neighboring pixels
def sobel_edge_detection(chunk):
    return feature.canny(chunk, sigma=1.0)

# Apply with overlap to handle chunk boundaries
edges = da.map_overlap(
    sobel_edge_detection,
    arr,
    depth=10,          # 10-pixel overlap on all sides
    boundary='reflect', # Handle array edges
    dtype=bool,
    meta=np.array((), dtype=bool)
)

# Compute results
edge_map = edges.compute()
```

---

## Dask Array Operations
### blockwise: Advanced Multi-Array Operations

```python
import dask.array as da
import numpy as np

fluorescence = da.from_zarr('fluorescence.zarr', component='0/0')
brightfield = da.from_zarr('brightfield.zarr', component='0/0')
background = da.from_zarr('background.zarr', component='0/0')

def ratio_calculation(fluor_chunk, bright_chunk, bg_chunk):
    corrected_fluor = fluor_chunk - bg_chunk
    corrected_bright = bright_chunk - bg_chunk
    ratio = np.divide(
        corrected_fluor, corrected_bright, out=np.zeros_like(corrected_fluor), where=corrected_bright!=0)
    return ratio

ratio_image = da.blockwise(
    ratio_calculation,           # Function to apply
    'ijk',                      # Output dimensions
    fluorescence, 'ijk',        # First input array and its dimensions
    brightfield, 'ijk',         # Second input array and its dimensions
    background, 'ijk',          # Third input array and its dimensions
    dtype=np.float32,
    concatenate=False
)
result = ratio_image.compute()
```

----

## Dask Array Operations
### blockwise: Advanced Multi-Array Operations

```python
import dask.array as da
import numpy as np

# Mathematical operations with different array shapes
mask = da.from_zarr('cell_mask.zarr')  # Shape: (1024, 1024)
timeseries = da.from_zarr('timelapse.zarr')  # Shape: (100, 1024, 1024)

def apply_mask(time_chunk, mask_chunk):
    """Apply 2D mask to each timepoint"""
    return time_chunk * mask_chunk[np.newaxis, :, :]

masked_series = da.blockwise(
    apply_mask, 'tij',
    timeseries, 'tij',
    mask, 'ij',
    dtype=timeseries.dtype
)
masked_result = masked_series.compute()

```

---

## Dask Array Operations
### blockwise: Advanced Multi-Array Operations

**Element-wise Operations Across Multiple Arrays**
- Apply functions that operate on corresponding chunks from multiple arrays
- More flexible than `map_blocks` for operations involving multiple inputs
- Handles broadcasting and alignment automatically
- Perfect for mathematical operations between different datasets

**Key Features:**
- Operates on multiple Dask arrays simultaneously
- Preserves chunking structure across all inputs
- Supports custom output chunk shapes and data types
- Handles different array shapes through broadcasting

---

## Dask Array Operations

### Chaining Operations

**Build Complex Processing Pipelines**
- Chain multiple `map_blocks` operations to create computational graphs
- Only one `compute()` call triggers the entire pipeline
- Dask optimizes the task graph for efficient execution

**Advantages:**
- Minimizes memory usage - intermediate arrays stay as task graphs
- Optimized execution plan across the entire pipeline
- Easy to modify pipeline without recomputing previous steps

---

## Dask Array Operations

### Chaining Operations

```python
import dask.array as da
import numpy as np
from skimage import filters, exposure, morphology

arr = da.from_zarr('microscopy_data.zarr', component='0/0')

def gaussian_filter_chunk(chunk, sigma=2):
    return filters.gaussian(chunk, sigma=sigma, preserve_range=True)

def normalize_chunk(chunk):
    return exposure.rescale_intensity(chunk, out_range=(0, 1))

def threshold_chunk(chunk, threshold=0.5):
    return chunk > threshold

def morphology_chunk(chunk):
    return morphology.remove_small_objects(chunk, min_size=50)

# Chain operations
filtered = da.map_blocks(gaussian_filter_chunk, arr, sigma=1.5, dtype=arr.dtype)
normalized = da.map_blocks(normalize_chunk, filtered, dtype=np.float32)
binary = da.map_blocks(threshold_chunk, normalized, threshold=0.3, dtype=bool)
cleaned = da.map_blocks(morphology_chunk, binary, dtype=bool)
result = cleaned.compute()
```

---
## Other Dask Array Operations
### Useful Operations

**da.stack and da.concatenate**
- Combining multiple arrays along new or existing dimensions

**da.reduction operations** 
- sum(), mean(), max(), std() across dimensions. Tree reduction patterns for efficient parallel computation 

**da.apply_gufunc** 
- Generalized universal functions for more complex array operations, handles operations that require custom broadcasting or shape manipulation

**da.overlap module** 
- overlap_internal for custom neighborhood operations, more control than map_overlap for advanced use cases