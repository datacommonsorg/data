# CDC Wonder Natality Import

## About the Dataset
This directory imports [CDC Wonder Natality data](https://wonder.cdc.gov/natality.html) into Data Commons. It provides comprehensive birth statistics and maternal and infant health metrics across three geographic resolutions: National (US country level), State, and County levels.

The dataset includes measures such as:
- Total Live Births (`Count_BirthEvent_LiveBirth`) across demographic breakdowns (Mother's Age, Race, Hispanic Origin, Education)
- Birth Weight metrics (`Mean_BirthWeight_BirthEvent_LiveBirth`)
- Gestational Age metrics (Obstetric Estimate and Last Menstrual Period)
- Maternal Health Metrics (Pre-pregnancy BMI, Prenatal Visits, Inter-pregnancy intervals)

### Geographic Coverage
- **Country**: Aggregated national totals across the United States.
- **State**: All 50 US States and the District of Columbia.
- **County**: US counties with populations of 100,000 or higher.

### Temporal Coverage and Data Brackets
Data is categorized into four year brackets according to CDC reporting revisions:
- **1995–2002**: Initial reporting bracket (8 race classifications).
- **2003–2006**: Intermediate revision bracket (4 bridged race classifications).
- **2007–2020**: Standard revision bracket.
- **2016–2020 / Expanded**: Expanded natality metrics (15 race classifications and extended maternal health metrics).

---

## Import Automation & Directory Structure

```
scripts/us_cdc/natality/
├── manifest.json              # Import automation specification (Cloud Batch/Scheduler)
├── validation_config.json     # Import validation framework configuration
├── download.sh                # Automated data download script from GCS repository
├── process.py                 # End-to-end data consolidation and processing pipeline
├── process_test.py            # Unit test for process.py pipeline
├── preprocess.py              # Core preprocessing utility
├── preprocess_test.py         # Unit test for preprocess.py
├── clean_cdc_data.py          # CDC raw file cleaning script
├── aggregate.py               # National-level aggregation utility
├── country/                   # National level configuration and output.tmcf
├── state/                     # State level bracket configs and output.tmcf
├── county/                    # County level bracket configs and output.tmcf
├── testdata/                  # Test sample fixtures and expected outputs
└── output/                    # Generated output directory
    ├── country.csv
    ├── country.tmcf
    ├── state.csv
    ├── state.tmcf
    ├── county.csv
    └── county.tmcf
```

### Automation Cadence
- **Dataset Release Frequency**: Annual (`P1Y`).
- **Cloud Batch Cron Schedule**: Annual on June 1 (`0 0 1 6 *`) in `manifest.json`.
- **Google3 Ingestion**: Polled weekly (`auto1w`) to detect new versions published to GCS.

---

## Prerequisites

- **Google Cloud SDK (`gcloud`)**: Configured with credentials to access GCS buckets.
- **Python Dependencies**:
  ```bash
  pip install pandas absl-py requests
  ```

---

## Running the Import

### 1. Download Input Data
```bash
./scripts/us_cdc/natality/download.sh
```
This downloads preprocessed and raw input files into `scripts/us_cdc/natality/input_files/`.

### 2. Process and Generate Output Files
```bash
python3 scripts/us_cdc/natality/process.py
```
This cleans, consolidates, and formats the output data into `output/`:
- `output/country.csv` & `output/country.tmcf`
- `output/state.csv` & `output/state.tmcf`
- `output/county.csv` & `output/county.tmcf`

---

## Running Tests

Run the unit tests:
```bash
python3 -m unittest scripts/us_cdc/natality/preprocess_test.py
python3 -m unittest scripts/us_cdc/natality/process_test.py
```