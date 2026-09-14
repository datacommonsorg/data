# US FEMA - National Flood Insurance Program Claims

This import automates the ingestion of National Flood Insurance Program (NFIP) redacted claims data from the Federal Emergency Management Agency (FEMA) into Data Commons.

- **Source**: [OpenFEMA FIMA NFIP Redacted Claims - v2](https://www.fema.gov/openfema-data-page/fima-nfip-redacted-claims-v2)
- **Geographic Coverage**: US States, Counties, and Census Tracts
- **Temporal Periods**: Monthly (`P1M`) and Annual (`P1Y`)
- **Key Metrics**:
  - Claims count (`CountOfClaims`)
  - Settlement amount on building structure (`SettlementAmount...BuildingStructure`)
  - Settlement amount on building contents (`SettlementAmount...BuildingContents`)
  - Settlement amount on combined structure and contents (`SettlementAmount...BuildingStructureAndContents`)
  - Breakdowns across FEMA flood hazard risk zones (High, Moderate, Low, and specific zones)

---

## 1. Prerequisites

- Python 3.9+
- Required packages:
  ```bash
  pip install pandas numpy requests absl-py retry
  ```

---

## 2. File & Artifact Overview

| File / Artifact | Description |
|---|---|
| `manifest.json` | Import specification, Cloud Batch resource allocations (64 cores, 256 GB RAM), and schedule. |
| `fema_download.py` | Data downloader supporting direct bulk CSV streaming with automatic API pagination fallback. |
| `process.py` | High-performance multi-process vectorized processing script transforming raw claims into Data Commons observations. |
| `validation_config.json` | Operational validation rules and thresholds for ingestion checks. |
| `test_data/flood_insurance_claims_input.csv` | Sample input claims data for local testing and continuous integration. |
| `fema_download_test.py` | Mock-isolated unit tests for the download module. |
| `process_test.py` | Unit tests for aggregation formulas, FIPS zero-padding, and error handling. |
| `output/nfip_output.csv` | Generated observations CSV. |
| `output/nfip_output.tmcf` | Template MCF mapping CSV columns to Data Commons schema properties. |
| `output/nfip_output.mcf` | Node MCF header. |
| `counters/counters.txt` | Import operational metrics (rows processed and output observations). |

---

## 3. Usage & CLI Documentation

### A. Download Data (`fema_download.py`)

Downloads the latest full NFIP claims dataset. By default, it uses high-speed direct bulk streaming (`~60s`), falling back to paginated API calls with retry logic if the bulk endpoint is unavailable.

```bash
python3 fema_download.py [FLAGS]
```

**Supported Flags:**
- `--bulk_url`: URL for the static full CSV bulk download.
  *(Default: `https://www.fema.gov/about/reports-and-data/openfema/FimaNfipClaims.csv`)*
- `--api_url`: Base OpenFEMA REST API endpoint used for fallback pagination.
  *(Default: `https://www.fema.gov/api/open/v2/FimaNfipClaims`)*
- `--output_dir`: Target directory for the downloaded file.
  *(Default: `input_file/`)*
- `--temp_dir`: Staging directory for temporary chunks during download.
  *(Default: `temp_fema_data/`)*

### B. Process Data (`process.py`)

Processes the raw claims dataset using a multi-core vectorized pipeline. It projects only the required columns, aggregates across places, dates, and flood zones in parallel chunks using `ProcessPoolExecutor` with `spawn`, and publishes outputs atomically.

```bash
python3 process.py \
    --input_data='input_file/fema_nfip_claims.csv' \
    --output_path='output/nfip_output' \
    --output_counters='counters/counters.txt'
```

**Supported Flags:**
- `--input_data`: Path to input raw claims CSV.
  *(Default: `input_file/fema_nfip_claims.csv`)*
- `--output_path`: Prefix path for output CSV and TMCF files (e.g. `output/nfip_output`).
  *(Default: `output/nfip_output`)*
- `--output_counters`: Path to write execution summary counters.
  *(Default: `counters/counters.txt`)*
- `--chunk_size`: Number of rows per chunk for batched streaming. Scaled dynamically when running across high core counts.
  *(Default: `250000`)*
- `--num_workers`: Number of parallel worker processes. Defaults to available system CPU count.
- `--pv_map`: Optional comma-separated mapping file configuration for custom overrides.

---

## 4. Testing Instructions

Execute the automated test suite across all modules from the `data/` repository root:

```bash
python3 -m unittest discover -v -s statvar_imports/fema/flood_insurance_claims -p "*_test.py"
```

Or from the import directory:

```bash
cd statvar_imports/fema/flood_insurance_claims
python3 -m unittest discover -v -p "*_test.py"
```

---

## 5. Dataset Refresh Schedule

- **Frequency**: Monthly
- **Cron Schedule**: `0 11 1 * *` (1st of every month at 11:00 UTC)
- **Execution Environment**: Cloud Batch provisioned with 64 vCPUs and 256 GB RAM.
