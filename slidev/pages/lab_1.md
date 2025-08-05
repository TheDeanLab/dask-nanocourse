---
layout: cover

---
## Processing Large Image Data with Dask 
### Lab 1: 11:00 – 12:00

---

## Lab 1: Processing Large Image Data with Dask

- Load an image series into dask as a Dask array. Evaluate its shape, dtype, and chunk sizes.
- Perform reductions like max/mean projections across the image stack, and plot the results.
- Apply a Gaussian filter to each image slice using map_blocks or map_overlap.
- Rechunk the Dask array and evaluate the performance of the operation.
- Save results to Zarr: Store the large filtered Dask array (or the computed projection if space is limited) in Zarr format.
- Compare the results with a standard numpy/scikit-image workflow to see the performance difference.

Note: Can be performed on your local machine or on BioHPC.

---

## Lab 1: Key Takeaways
- **Parallel, Larger Than Memory Analysis:** Dask Array enables parallel, out-of-core computation on large images. It breaks big arrays into chunks and processes them with blocked algorithms, so you can work with datasets larger than memory.
- **Chunk wisely:** The size and shape of chunks matters. Too many tiny chunks add overhead (each task has scheduling cost ~1ms), while huge chunks won’t fit in RAM. Aim for a sweet spot in between – chunks that are as large as possible but still memory-friendly (often tens of MBs each).
- **Lazy loading and compute:** Dask integrates easily with file-based data. You can load image slices lazily and only compute what you need. Operations (slicing, projections, filtering) run per chunk and aggregate, so you never have to load the entire dataset into memory.
- **Zarr format:** a great option for storing big arrays. It keeps data chunked on disk, which pairs perfectly with Dask’s chunked processing. With Zarr, you can save intermediate results or datasets and reload them efficiently later – Dask will only read the chunks required for your analysis.