# US Census Surface Area Import (`USCensusGeos_SurfaceArea`)

## Overview

- **Import Type**: Automated (Scheduled)
- **Variable Measured**: `dcs:SurfaceArea`
- **Unit**: `dcs:SquareMile`
- **Formula**:
  $$\text{SurfaceArea} = \text{round}\left(\frac{\text{ALAND} + \text{AWATER}}{2589988.11}, 4\right)$$
  (Converts square meters to square miles, rounded to 4 decimal places).

Historically, this dataset was generated via a manual Google3 internal BigQuery script (`//depot/google3/datacommons/import/mcf/manifest/us_census/USCensusGeos_SurfaceArea.textproto`). This automated pipeline migrates and automates the process to directly fetch public U.S. Census Gazetteer files and State Area Measurements, compute the total surface area (land area + water area), and produce production-ready Data Commons CSV and TMCF files across all available years (2018–2025+).

## Data Sources

1. **U.S. Census Bureau Gazetteer Files**:
   - Base URL: `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/`
   - Files utilized per annual release:
     - `counties`: `*Gaz_counties_national.zip`
     - `congressional_districts`: `*Gaz_*CDs_national.zip` (e.g. 116CDs, 119CDs)
     - `cbsa`: `*Gaz_cbsa_national.zip`
     - `place`: `*Gaz_place_national.zip`
     - `cousubs`: `*Gaz_cousubs_national.zip`
     - `unsd`: `*Gaz_unsd_national.zip` (Unified School Districts)
     - `elsd`: `*Gaz_elsd_national.zip` (Elementary School Districts)
     - `scsd`: `*Gaz_scsd_national.zip` (Secondary School Districts)
     - `tracts`: `*Gaz_tracts_national.zip`
     - `state`: `*Gaz_state_national.zip` (for releases >= 2024)

2. **U.S. Census Bureau State Area Measurements**:
   - URL: `https://www.census.gov/geographies/reference-files/2010/geo/state-area.html`
   - Used for baseline 50 U.S. States, District of Columbia, and Puerto Rico.

## Geographic Entities & Coverage

| Entity Type | DCID Prefix | Example DCID | 2018 Baseline Count |
|---|---|---|---|
| States | `geoId/` | `geoId/01` (Alabama) | 52 |
| Counties | `geoId/` | `geoId/01001` (Autauga County) | 3,220 |
| Congressional Districts | `geoId/` | `geoId/0101` (AL CD 1) | 440 |
| Core Based Statistical Areas (CBSA) | `geoId/C` | `geoId/C10100` | 945 |
| Places | `geoId/` | `geoId/0100124` | 29,574 |
| County Subdivisions (MCDs) | `geoId/` | `geoId/0100190000` | 36,630 |
| Unified School Districts | `geoId/sch` | `geoId/sch0100005` | 10,887 |
| Elementary School Districts | `geoId/sch` | `geoId/sch0100001` | 1,958 |
| Secondary School Districts | `geoId/sch` | `geoId/sch0400004` | 486 |
| Census Tracts | `geoId/` | `geoId/01001020100` | 74,001 |
| **Total** | | | **158,193** |

## Directory Structure

```
surface_area/
├── README.md               # Pipeline documentation and operational guidelines
├── manifest.json           # Import automation manifest specification
├── validation_config.json  # Data validation threshold configuration
├── preprocess.py           # Download and preprocessing script
├── preprocess_test.py      # Hermetic unit tests
├── golden_data/            # Non-volatile golden summary reports
│   └── golden_summary_report.csv
├── input_files/            # Downloaded raw input files
├── output_files/           # Generated cleaned CSV and TMCF
└── test_data/              # Sample fixtures and expected test outputs
```

## Running the Pipeline

### Dynamic Year Discovery & Full Automation
By default, `--years` is set to `auto`. When executed (e.g. via scheduled monthly cron), the pipeline dynamically queries `https://www2.census.gov/geo/docs/maps-data/data/gazetteer/`, detects all available annual release directories starting from 2018 up to the latest published year (e.g. 2018–2026+), downloads any newly released files, and processes all years. No manual code updates or year bumps are needed for future releases.

### Download Mode
Fetches the raw gazetteer and reference files from census.gov (skipping already-downloaded historical files):
```bash
# Automatically discovers and downloads all available years >= 2018:
python3 preprocess.py --mode=download

# Or specify a targeted year / range:
python3 preprocess.py --mode=download --year=latest
python3 preprocess.py --mode=download --years=2018-2025
```

### Process Mode
Processes downloaded raw files into `output_files/surface_area.csv` and `output_files/surface_area.tmcf`:
```bash
python3 preprocess.py --mode=process
```

### End-to-End Execution
Downloads any new/missing files and processes all available years in a single step:
```bash
python3 preprocess.py --mode=all
```

## Validation & Verification

### 1. Unit Tests
Run unit tests hermetically:
```bash
python3 -m unittest preprocess_test.py
```

### 2. Validation Configuration & Threshold Justifications

The import configuration in `validation_config.json` enforces 4 critical validation rules:

1. **`check_deleted_records_percent` (`DELETED_RECORDS_PERCENT`: 0.1%)**:
   - **Justification**: A strict 0.1% threshold is maintained because Census geographic boundaries (e.g. Census Designated Places, School Districts, and Tracts) occasionally undergo rare dissolutions, annexations, or boundary consolidations across annual national releases. This threshold accommodates legitimate administrative changes while catching unintended data drops.
2. **`check_max_date_consistent` (`MAX_DATE_CONSISTENT`)**:
   - **Justification**: All entities measured for `dcs:SurfaceArea` share the identical latest release date (e.g. 2025).
3. **`check_max_date_freshness` (`SQL_VALIDATOR`)**:
   - **Justification**: Uses DuckDB SQL condition `max_year >= (EXTRACT(YEAR FROM CURRENT_DATE) - 2)` to verify freshness within allowable annual release latency without prematurely failing on calendar year rollovers before the Census Bureau releases the new year's Gazetteer files.
4. **`check_goldens_summary_report` (`GOLDENS_CHECK`)**:
   - **Justification**: Validates non-volatile StatVar schema properties (`StatVar`, `NumPlaces`, `MinDate`, `Units`, `MeasurementMethods`, `ScalingFactors`, `observationPeriods`) against `golden_data/golden_summary_report.csv`. Volatile fields (`MaxDate`, `NumObservations`, `MaxValue`, `MinValue`) are excluded so future multi-year additions pass goldens cleanly. Raw observation goldens are intentionally omitted due to the granular nature of school district and tract entities.

Run the import validator locally:
```bash
python3 tools/import_validation/runner.py \
  --stats_summary=scripts/us_census/surface_area/output_files/dc_generated/summary_report.csv \
  --lint_report=scripts/us_census/surface_area/output_files/dc_generated/report.json \
  --differ_output=scripts/us_census/surface_area/diff \
  --validation_config=scripts/us_census/surface_area/validation_config.json \
  --validation_output=/tmp/validation_output.csv
```

### 3. Differ Comparison against Production Baseline

To verify backwards compatibility with legacy production data:
```bash
python3 tools/import_differ/import_differ.py \
  --current_data=scripts/us_census/surface_area/output_files/dc_generated/table_mcf_nodes_surface_area.mcf \
  --previous_data=scripts/us_census/surface_area/output_files/prod.mcf \
  --output_location=scripts/us_census/surface_area/diff \
  --file_format=mcf \
  --runner_mode=native
```

Result for 2018 baseline comparison:
- **Deleted Observations**: **0** (100% legacy entity coverage)
- **Modified Observations**: **0** (Exact numerical agreement)
- **Added Observations**: New observations covering years 2019 through 2025.

## Troubleshooting

- **HTTP 404 on Future Years**:
  If `--years` includes an unreleased future year, `preprocess.py` logs a clear warning and stops year discovery early without failing the pipeline.
- **Corrupted or Truncated Downloads**:
  Downloads write to temporary files in `input_files/` and atomically replace existing files only after checking that the file is non-empty (`os.path.getsize > 0`). If a download is interrupted, retry with `python3 preprocess.py --mode=download`.
- **Validation Path Resolution**:
  Relative paths in `validation_config.json` resolve relative to the configuration file itself (`golden_data/golden_summary_report.csv`).
