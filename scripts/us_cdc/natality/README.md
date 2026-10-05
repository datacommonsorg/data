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

---

## Directory Structure

```
scripts/us_cdc/natality/
├── download.py             # Headless Chrome downloader querying CDC WONDER directly
├── download_test.py        # Unit tests for download.py
├── process.py              # End-to-end data parsing, melting, aggregation, and TMCF generator
├── process_test.py         # Unit tests for process.py
├── manifest.json           # Import automation specification (Cloud Batch/Scheduler)
├── validation_config.json  # DuckDB freshness and validation rules
└── README.md               # Pipeline documentation
```

---

## Full Automation Architecture

1. **Automated Download (`download.py`)**:
   - **Historical Baseline**: Automatically retrieves the immutable historical baseline (1995–2022) with demographic breakdowns (Mother's Age, Race, Ethnicity, Education, etc.) from `gs://unresolved_mcf/cdc/wonder/natality/` to ensure zero historical data loss.
   - **Live Updates**: Uses Selenium with headless Google Chrome (`--headless=new`, `--no-sandbox`) to access CDC WONDER directly, bypassing CDN/WAF restrictions, accepting the Data Use Agreement in the browser DOM, selecting all years, enabling all maternal/infant health measures, and downloading the latest State and County TSV exports directly into `input_files/`.
   - **Future-Proof**: Dynamically captures newly published years without requiring code changes.

2. **Data Processing & TMCF Generation (`process.py`)**:
   - Cleans the raw TSVs by removing metadata, footers, and subtotal rows.
   - Maps raw measure columns to standardized Data Commons StatisticalVariables and schema-compliant Units (`Week`, `Gram`, `Month`, `Years`).
   - Resolves FIPS codes into Data Commons DCIDs (`geoId/XX` for State, `geoId/XXXXX` for County).
   - Merges live scraped records on top of the historical baseline (updating overlapping records and appending new years like 2023–2024).
   - Aggregates State-level counts into national Country totals (`output/country.csv`).
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