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
The dataset is processed via an automated Bash pipeline (run.sh) designed for containerized environments. The pipeline performs the following steps:

### 1. Environment Bootstrap
* **Build Dependencies:** Installs `build-essential`, `gfortran`, `cmake`, and `libaec-dev`.
* **Toolchain Setup:** Performs a shallow clone of the [NOAA-EMC/wgrib2](https://github.com/NOAA-EMC/wgrib2.git) repository and compiles the binary at runtime using `cmake` and `make install`.

### 2. Data Ingestion
* **Dynamic Targeting:** Automatically calculates the current date and constructs the URL for the specified GFS cycle (default: `00z`).
* **Reliable Download:** Uses `curl -L` to fetch the binary GRIB2 forecast file (e.g., `gfs.t00z.pgrb2.0p25.f000`).

### 3. Transformation & Mapping
The pipeline pivots the data from binary to a structured StatVar CSV via two layers:
1.  **Format Conversion:** `wgrib2` converts the `.pgrb2` binary into a raw `.csv` file.
2.  **StatVar Mapping (`custom_statvar_processor.py`):** * **DCID Construction:** Short codes (e.g., `TMP`, `UGRD`) and levels (e.g., `2 m above ground`) are mapped to formal DCIDs like `dcid:Temperature_Place_2Meter`.
    * **Cleaning:** Standardizes vertical levels and measurement methods (e.g., `GroundLevel`).
    * **Streaming Upload:** Uses `google-cloud-storage` with a 64MB chunked buffer to stream processed rows directly to the GCS bucket in batches of 1,000 to manage memory footprint.

---

## Usage Instructions

### Running the Pipeline
The script can be executed directly. Ensure your environment has Google Cloud credentials configured if running outside of GCP.

```bash
# Make the script executable
chmod +x run.sh

# Run with default settings (Today's 00z data)
./run.sh
