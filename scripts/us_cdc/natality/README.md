# CDC Wonder Natality Import

## About the Dataset
This directory provides a fully automated pipeline for importing [CDC Wonder Natality data](https://wonder.cdc.gov/natality.html) into Data Commons. It provides comprehensive birth statistics and maternal and infant health metrics across three geographic resolutions: National (US country level), State, and County levels.

The dataset includes:
- Live Birth counts (`Count_BirthEvent_LiveBirth`)
- Average Age of Mother (`Mean_MothersAge_BirthEvent_LiveBirth`)
- Average OE Gestational Age (`Mean_OeGestationalAge_BirthEvent_LiveBirth`)
- Average LMP Gestational Age (`Mean_LmpGestationalAge_BirthEvent_LiveBirth`)
- Average Birth Weight (`Mean_BirthWeight_BirthEvent_LiveBirth`)
- Average Pre-pregnancy BMI (`Mean_PrePregnancyBMI_BirthEvent_LiveBirth`)
- Average Prenatal Visits (`Mean_PrenatalVisitCount_BirthEvent_LiveBirth`)
- Average Interval Since Last Live Birth (`Mean_IntervalSinceLastBirth_BirthEvent_LiveBirth`)
- Average Interval Since Last Other Pregnancy Outcome (`Mean_IntervalSinceLastPregnancyOutcomeNotLiveBirth_BirthEvent_LiveBirth`)

### Geographic Coverage
- **Country**: Aggregated national totals across the United States.
- **State**: All 50 US States and the District of Columbia.
- **County**: US counties with populations of 100,000 or higher.

## Prerequisites
Before running the pipeline locally or in automation, ensure the following dependencies are installed:
- **Python**: Python 3.10+ with repository dependencies (`pandas`, `absl-py`, `selenium`).
- **Google Chrome**: Google Chrome or Chromium installed on the host system for headless browser operations.
- **Google Cloud SDK (`gcloud`)**: Configured with read access to `gs://unresolved_mcf/cdc/wonder/natality/` for baseline snapshots.

---

## Directory Structure

```
scripts/us_cdc/natality/
├── download.py             # Headless Chrome downloader querying CDC WONDER directly
├── download_test.py        # Unit tests for download.py
├── process.py              # End-to-end data parsing, melting, aggregation, and TMCF generator
├── process_test.py         # Unit tests for process.py
├── manifest.json           # Import automation specification (Cloud Batch/Scheduler)
├── validation_config.json  # Import validation configuration (date freshness, consistency, deleted records)
└── README.md               # Pipeline documentation
```

---

## Full Automation Architecture

1. **Automated Download (`download.py`)**:
   - **Historical Baseline**: Automatically retrieves the historical baseline (1995–2022) across all brackets (`95-02`, `03-06`, `07-20`, `16-22`) from `gs://unresolved_mcf/cdc/wonder/natality/` to preserve historical records.
   - **Live Updates (Totals + 6 Demographic Breakdowns)**: Uses Selenium with headless Google Chrome (`--headless=new`, `--no-sandbox`) to query CDC WONDER Expanded Natality (`2016–Present`) across both un-sliced totals (`B_3 = *None*`) and all 6 active demographic Group-By (`B_3`) dimensions (`Age of Mother 13`, `Mother's Single Race 15`, `Mother's Education`, `Mother's Hispanic Origin`, `Marital Status`, and `Mother's Nativity`) for State and County levels.
   - **Fail-Fast & Retry Resilience**: Verifies that all expected maternal/infant health measure checkboxes are selected and retries transient failures with exponential backoff.

2. **Data Processing & TMCF Generation (`process.py`)**:
   - Cleans raw TSV exports by removing metadata, footers, and subtotal rows, and validates that all expected measure columns are present.
   - Maps raw measure columns and demographic codes (`Age of Mother 13 Code`, `Mother's Single Race 15 Code`, `Mother's Education Code`, `Mother's Hispanic Origin Code`, `Marital Status Code`, `Mother's Nativity Code`) to canonical Data Commons StatisticalVariables and schema-compliant Units (`Week`, `Gram`, `Month`, `Year`).
   - Resolves FIPS codes into Data Commons DCIDs (`geoId/XX` for State, `geoId/XXXXX` for County) and filters invalid/unidentified placeholder codes (`geoId/99`, `geoId/99999`) as well as `0.0` placeholder rows on `"Not Available"` unknown/unstated slices.
   - Merges live records on top of the historical baseline in chronological bracket order.
   - Computes national Country totals (`output/country.csv`) directly by aggregating `Count_*` StatisticalVariables from the consolidated State dataset.
   - Automatically writes Template MCF files (`country.tmcf`, `state.tmcf`, `county.tmcf`) to `output/`.

---

## Running Locally

### 1. Download Data from Source
```bash
python3 scripts/us_cdc/natality/download.py --output_dir=scripts/us_cdc/natality/input_files
```

### 2. Process and Generate Output Files
```bash
python3 scripts/us_cdc/natality/process.py --input_path=scripts/us_cdc/natality/input_files --output_path=scripts/us_cdc/natality/output
```

Generated outputs in `output/`:
- `country.csv` & `country.tmcf`
- `state.csv` & `state.tmcf`
- `county.csv` & `county.tmcf`

---

## Running Tests

Execute the unit tests using Python `unittest`:
```bash
python3 -m unittest discover -s scripts/us_cdc/natality -p "*_test.py"
```