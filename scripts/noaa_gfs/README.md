# NOAA: Global Forecast System Dataset
## Overview
The NOAA-GFS 0.25 Atmos dataset provides high-resolution global atmospheric and land-surface data on a 0.25-degree (~28km) grid. It includes a wide range of meteorological variables, such as temperature, wind, humidity, precipitation, and soil moisture, generated four times daily with forecasts extending up to 16 days (384 hours).
The dataset provides a standardized global output on a 0.25-degree (~28km) equidistant cylindrical grid, covering the entire Earth's surface and up to 127 vertical atmospheric layers. It is distributed in GRIB2 (Gridded Binary Edition 2) format via the NOAA Operational Model Archive and Distribution System (NOMADS) and is categorized as a public domain product of the United States Government.
This pipeline automates the ingestion, format conversion, and standardized mapping of GFS GRIB2 files into Data Commons-compatible StatVar observations.

## Data Source & Provenance
* **Source URL:** [NOMADS NCEP GFS Production](https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/)
* **Provider:** National Centers for Environmental Prediction (NCEP / NOAA).
* **Update Frequency:** 4 times daily (00z, 06z, 12z, 18z).
* **Variable Inventory:** [NCO Product Description](https://www.nco.ncep.noaa.gov/pmb/products/gfs/gfs.t00z.pgrb2.0p25.anl.shtml)


## Automated Pipeline Logic
The pipeline is a Python-driven architecture managed via a `manifest.json` import specification.

### 1. Data Ingestion (`download_noaa_gfs_grib.py`)
* **Stateful Tracking:** The script retrieves its last successful run checkpoint from `gs://{bucket}/state.json`.
* **Chronological Integrity:** It identifies missing 6-hour slots (00z, 06z, 12z, 18z) and performs memory-efficient streamed downloads of GRIB2 files into local `input_files/` directories.

### 2. Transformation & Mapping (`grib_statvar_processor.py`)
This stage converts binary meteorological data into structured CSVs using the `pygrib` library.
* **Parallel Processing:** Utilizes `multiprocessing.Pool` to process GRIB messages across available CPU cores.
* **Coordinate Normalization:** Longitudes are transformed from the 0–360 range to the -180 to 180 range.
* **StatVar Mapping:**
    * **DCID Construction:** Maps GRIB short codes (e.g., `TMP`, `UGRD`) and vertical levels to formal Data Commons identifiers like `dcid:Temperature_Place_850Millibar`.
    * **Unit Scaling:** Automatically scales variables such as Land and Ice cover.
* **GCS Streaming:** Processed CSVs are merged and uploaded directly to the GCS output prefix.

### 3. BigQuery Ingestion (`dc_bq_ingest.py`)
* **Staging Pattern:** Bulk loads raw CSVs from GCS into a staging table (`Observation_Staging`).
* **SQL Transformation:** Executes an `INSERT INTO` query to map staging data to the final production schema, handling type casting and attaching the provenance ID (`dc/base/NOAA_GlobalForecastSystem`).

---

## Pipeline Configuration (`manifest.json`)
The pipeline is governed by specific resource requirements for high-concurrency GRIB decompression:
* **Cron Schedule:** `30 04,10,16,22 * * *` (Runs 30 minutes after GFS cycle releases).
* **Resource Limits:** 64 CPUs | 256GB RAM | 4GB Disk.
* **Timeout:** 1 hour (`3600s`).

---

## Usage Instructions

### Prerequisites
* **Python Libraries:** `pygrib`, `numpy`, `google-cloud-storage`, `google-cloud-bigquery`, `absl-py`.
* **System Requirements:** Requires `libgrib-api` or `eccodes` installed on the host system.

### Manual Execution
While designed for automated execution, stages can be run manually for debugging:

```bash
# 1. Download missing data
python3 download_noaa_gfs_grib.py --project_id=YOUR_PROJECT_ID

# 2. Process GRIB to CSV and upload to GCS
python3 grib_statvar_processor.py --input=./input_files

# 3. Ingest from GCS to BigQuery
python3 dc_bq_ingest.py --project_id=YOUR_PROJECT_ID --dataset_id=YOUR_DATASET
