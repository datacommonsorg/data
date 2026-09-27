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
  pip install pandas absl-py
  ```

---

## Running the Automated Pipeline

### 1. Download Input Data
```bash
./scripts/us_cdc/natality/download.sh
```
This downloads preprocessed input files from the latest version folder in `gs://unresolved_mcf/cdc/wonder/natality/` into `scripts/us_cdc/natality/input_files/`.

### 2. Process and Generate Output Files
```bash
python3 scripts/us_cdc/natality/process.py
```
This cleans, consolidates, and formats the output data into `output/`:
- `output/country.csv` & `output/country.tmcf`
- `output/state.csv` & `output/state.tmcf`
- `output/county.csv` & `output/county.tmcf`

---

## Manual Preprocessing & Staging Workflow (For Dataset Updates)

When CDC releases a new Natality dataset bracket on [CDC WONDER](https://wonder.cdc.gov/natality.html):
1. **Export Data**: Export TSV data from the CDC WONDER online query tool.
2. **Clean Raw Exports**:
   ```bash
   python3 scripts/us_cdc/natality/clean_cdc_data.py --input_path=<raw_tsv_dir> --output_path=<cleaned_tsv_dir>
   ```
3. **Preprocess State/County Data**:
   ```bash
   python3 scripts/us_cdc/natality/preprocess.py --input_path=<cleaned_tsv_dir> --config_path=scripts/us_cdc/natality/state/<config.json> --output_path=<output_dir>
   ```
4. **Aggregate Country Level Data**:
   ```bash
   python3 scripts/us_cdc/natality/aggregate.py --input_path=<state_csv_path> --output_path=<country_csv_path>
   ```
5. **Stage to GCS**:
   Upload the preprocessed CSV files to a new dated snapshot directory under `gs://unresolved_mcf/cdc/wonder/natality/{country,states,county}/<YYYYMMDD>/`. The automated pipeline will pick up the latest dated folder on its next run.

---

## Running Tests

Run the test suite via the repository test runner or unittest:
```bash
# Using repository test runner
./run_tests.sh -p scripts/us_cdc/natality

# Using Python unittest
python3 -m unittest scripts/us_cdc/natality/preprocess_test.py scripts/us_cdc/natality/process_test.py
```