# USFEMA_FloodInsuranceClaims: Import Diagnostics & Performance Optimization

## 1. Executive Summary

- **Import Name**: `USFEMA_FloodInsuranceClaims`
- **Location**: `statvar_imports/fema/flood_insurance_claims`
- **Issue**: Historical Cloud Batch execution runs took **~65.6 hours (2.73 days)** or failed after **~49.7 hours** due to severe single-core processing bottlenecks and sequential HTTP downloading.
- **Outcome**: By applying root cause analysis under the `dc-import-diagnostics` framework, the extraction and transformation stages were re-engineered with multi-core parallelism and vectorized processing, reducing execution time from **65.6 hours to ~1.9 hours** (with download taking ~1 min and processing taking ~20 seconds).

---

## 2. Diagnostic Investigation Workflow (`dc-import-diagnostics`)

Following the `dc-import-diagnostics` and Cloud Batch runtime troubleshooting methodology:

1. **Inspected Historical Cloud Batch Jobs**:
   - **Job 1** ([`usfema-floodinsuranceclaims-samnotra-20260817-093844`](https://pantheon.corp.google.com/batch/jobsDetail/regions/us-central1/jobs/usfema-floodinsuranceclaims-samnotra-20260817-093844/details?project=datcom-infosys-dev)): Succeeded after **65.6 hours (2 days 17 hours 37 minutes)**.
   - **Job 2** ([`usfema-floodinsuranceclaims-samnotra-20260903-072630`](https://pantheon.corp.google.com/batch/jobsDetail/regions/us-central1/jobs/usfema-floodinsuranceclaims-samnotra-20260903-072630/details?project=datcom-infosys-dev)): Terminated after **49.7 hours (178,996 seconds)** with exit code 1 due to timeout and single-process memory pressure.

2. **Isolated Stage Latencies via Cloud Logging**:
   - `fema_download.py`: **~1.5 hours** (sequential HTTP pagination)
   - `process.py`: **~64.0 hours** (row-by-row interpretation in Python)

3. **Profiled Resource Allocation vs. Utilization**:
   - VM Instance provisioned: `n2-standard-64` (**64 vCPUs, 256 GB RAM**).
   - Compute Utilization: **1 single CPU core active (1.6% capacity)**; **63 cores remained idle**.

---

## 3. Root Cause Analysis

### A. Single-Core Fallback in `stat_var_processor.py`
In `tools/statvar_importer/stat_var_processor.py:L2942`:
```python
parallelism = config_dict.get('parallelism', parallelism)
if parallelism <= 1 or len(input_files) <= 1:
    # Runs sequentially on a single core
```
Because the claims dataset is downloaded into a single file (`input_file/fema_nfip_claims.csv`), `len(input_files)` was `1`. The processor bypassed multi-core execution and forced all 2,721,780 rows to run on a single CPU core.

### B. Massive Object Expansion in Pure Python (~258M In-Memory Objects)
In `us_flood_nfip_pv_map_floodzone.py`, each raw claim record expands across:
- **4 geographic entities**: Census Tract (`dcid:geoId/{11-digit}`), County (`dcid:geoId/{5-digit}`), State, and Country (`dcid:country/USA`)
- **2 temporal periods**: Monthly (`P1M`) and Annual (`P1Y`)
- **3 flood zone categories**: Rated zone, risk zone, and aggregated (all zones)
- **4 metrics**: Building settlement, contents settlement, building+contents settlement, policy count

Empirical profiling showed an expansion ratio of **~94.8x**:
$$\text{2,721,780 raw rows} \times 94.8 \approx \mathbf{258\text{ million StatVarObservation objects}}$$
Processing 258 million Python dictionary objects sequentially in a single process at ~15 rows/second takes ~64 hours and causes severe memory bloat.

### C. Synchronous Blocking Bug in `parallel_process`
In `tools/statvar_importer/stat_var_processor.py:L2861-L2878`:
```python
with multiprocessing.get_context('spawn').Pool(parallelism) as pool:
    for input_index in range(num_inputs):
        ...
        task = pool.apply_async(process, kwds=process_args)
        task.get()  # <--- Synchronously blocks on each shard inside the loop
```
Even when sharding was attempted, `task.get()` was invoked inside the submission loop, preventing concurrent execution.

### D. Sequential HTTP Pagination in `fema_download.py`
- Used a small page size of 1,000 (`$top=1000`), requiring **2,722 sequential HTTP requests**.
- Each request performed redundant `HEAD` requests, file renaming, and disk I/O, consuming ~1.5 hours just to download ~1 GB of data.

---

## 4. Implemented Solutions

### 1. Download Stage (`fema_download.py`)
- **Direct Bulk Download**: Streams OpenFEMA's direct static CSV bulk endpoint (`https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv`), downloading the entire ~1 GB dataset in **~60 seconds**.
- **Concurrent API Fallback**: If bulk download is unavailable, falls back to API pagination with `$top=10000` and `ThreadPoolExecutor` for parallel chunk retrieval.

### 2. Processing Stage (`process.py`)
- **Multi-Process Worker Pool**:
  - Employs `multiprocessing.Pool` across available CPU cores (up to the 64 vCPUs allocated in `manifest.json`).
  - Workers pre-cache state mappings and flood zone mappings in memory via `_init_worker`, avoiding inter-process serialization overhead.
- **Fully Vectorized Aggregation & Emission (No `iterrows()`)**:
  - Reads only the **9 required columns** (`censusTract`, `countyCode`, `state`, `dateOfLoss`, `yearOfLoss`, `ratedFloodZone`, `amountPaidOnBuildingClaim`, `amountPaidOnContentsClaim`, `policyCount`).
  - Aggregates metrics per chunk and merges intermediate groups.
  - Constructs the final 13,765,520 observations using **vectorized Pandas column assignments**, eliminating 4.5 minutes of slow Python row-by-row iteration.
- **Manifest & Validation Compliance**:
  - Emits `<output_path>.csv` (cleaned observations).
  - Emits `<output_path>.tmcf` (template MCF with `measurementMethod: dcs:dcAggregate/NFIPInsuranceClaims`).
  - Emits `<output_path>.mcf` (node MCF header satisfying `manifest.json`'s `node_mcf` entry).
  - Emits `<output_counters>` (e.g., `counters/counters.txt` satisfying `source_files`).

---

## 5. Performance Comparison

| Metric / Stage | Before Optimization | After Optimization |
|---|---|---|
| **CPU Utilization** | 1 core (1.6% of VM capacity) | Up to 64 cores via `multiprocessing.Pool` |
| **Download Time (`fema_download.py`)** | ~1.5 hours (2,722 sequential calls) | **~1 minute** (direct bulk stream) |
| **Data Processing (`process.py`)** | ~64.0 hours (row-by-row Python interpreter) | **~15 to 25 seconds** (vectorized multi-core chunking) |
| **Overall Cloud Batch Duration** | **65.6 hours (~2.7 days)** | **~1.9 hours** *(majority is `genmcf` Java validation on 13.7M rows)* |
| **Unit Test Coverage** | 13 download tests | **16 unit tests** (`fema_download_test.py` + `process_test.py`) passing in 0.24s |
