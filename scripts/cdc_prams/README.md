# US: CDC Pregnancy Risk Assessment Monitoring System (PRAMS)

## About the Dataset
This dataset provides Population Estimates and Maternal and Child Health (MCH) indicators
from the Pregnancy Risk Assessment Monitoring System (PRAMS) in the USA for the years 2016
through 2020.

The population is categorized across 14 indicator topics:
1. Nutrition (Multivitamin use)
2. Pre-Pregnancy Weight (Underweight, Overweight, Obese)
3. Substance Use (Cigarettes, E-Cigarettes, Hookah, Heavy Drinking)
4. Intimate Partner Violence (Before and during pregnancy)
5. Depression (Self-reported depression before, during, and postpartum)
6. Health Care Services (Flu shot, prenatal care, maternal checkup)
7. Pregnancy Intention (Intended, mistimed, unwanted, unsure)
8. Postpartum Family Planning (Sterilization, LARC, moderate, least effective methods)
9. Oral Health (Teeth cleaned during pregnancy)
10. Health Insurance Status One Month Before Pregnancy (Private, Medicaid, No Insurance)
11. Health Insurance Status for Prenatal Care (Private, Medicaid, No Insurance)
12. Health Insurance Status Postpartum (Private, Medicaid, No Insurance)
13. Infant Sleep Practices (Baby often laid on back to sleep)
14. Breastfeeding Practices (Ever breastfed, breastfeeding at 8 weeks)

Each indicator is measured across 4 statistical properties:
- **SampleSize_Count**: Sample count (`statType: dcs:sampleSize`, `measuredProperty: dcs:count`)
- **Percent**: Percentage fraction (`statType: dcs:measuredValue`,
  `measurementDenominator: dcs:Count_BirthEvent_LiveBirth`, `scalingFactor: 100`)
- **ConfidenceIntervalLowerLimit**: Lower CI limit (`statType: dcs:confidenceIntervalLowerLimit`,
  `scalingFactor: 100`)
- **ConfidenceIntervalUpperLimit**: Upper CI limit (`statType: dcs:confidenceIntervalUpperLimit`,
  `scalingFactor: 100`)

Total Statistical Variables: 168

### Source Download URL
The data is published at the CDC PRAMS repository:
`https://www.cdc.gov/prams/php/data-research/mch-indicators-by-site.html`

Example PDF file:
`https://www.cdc.gov/prams/prams-data/mch-indicators/states/pdf/2020/Alabama-PRAMS-MCH-Indicators-508.pdf`

---

## Import Automation & Directory Structure

```
scripts/cdc_prams/
├── manifest.json              # Import automation specification (Cloud Batch/Scheduler)
├── validation_config.json     # Import validation framework configuration
├── download.py                # Download utility with retries, timeouts, and headers
├── download_input_files.py    # Downloads all 49 state/territory/national PDFs
├── process.py                 # Extracts PDF tables with tabula-py and produces CSV/MCF/TMCF
├── process_test.py            # Unit test comparing output against expected fixtures
├── constants.py               # MCF templates and property mappings
├── statvar.py                 # Statistical variable name mappings
├── test_data/                 # Test sample fixtures (State & National PDFs and expected outputs)
└── output/                    # Generated output directory
    ├── PRAMS.csv
    ├── PRAMS.mcf
    └── PRAMS.tmcf
```

### Automation Cadence
- **Dataset Release Frequency**: Annual (`P1Y`).
- **Cloud Batch Cron Schedule**: Annual on June 1 (`0 0 1 6 *`) in `manifest.json`.
- **Google3 Ingestion**: Polled weekly (`auto1w`) to detect new versions published to GCS.

---

## Prerequisites

- **Java Runtime**: Java 8 or higher (required by `tabula-py` for PDF table parsing).
  ```bash
  java -version
  ```
- **Python Dependencies**:
  ```bash
  pip install tabula-py pandas absl-py numpy requests urllib3
  ```

---

## Running the Import

### 1. Download Input PDFs
```bash
python3 scripts/cdc_prams/download_input_files.py
```
This downloads all 49 state, NYC, DC, Puerto Rico, and national PDF files into
`scripts/cdc_prams/input_files/`.

### 2. Process and Generate Output Files
```bash
python3 scripts/cdc_prams/process.py
```
This parses the downloaded PDFs and produces:
- `output/PRAMS.csv`
- `output/PRAMS.mcf`
- `output/PRAMS.tmcf`

---

## Running Tests

### Unit Tests
```bash
python3 scripts/cdc_prams/process_test.py
```
or via unittest:
```bash
python3 -m unittest scripts/cdc_prams/process_test.py
```

---

## Two-Step Rollout & Differ Validation Procedure

When upgrading the dataset schema (e.g., adding `scalingFactor: 100` to confidence interval
limits), StatVarObservation (SVO) identity hashes change for affected observations:

1. **Step 1 (Schema Modernization & SVO Replacement)**:
   - The differ check flags deleted records (approx. 49.37%) corresponding exactly to the
     old unscaled Lower and Upper CI observations (16,380 old SVOs replaced by 16,378 new
     scaled SVOs). No Statistical Variables are deleted.
   - Run 1 establishes the modernized schema with scaled SVO identity hashes.
   - In `datcom-import-test`, promote the Run 1 output version to `latest_version.txt`.

2. **Step 2 (Baseline Verification)**:
   - Run 2 executes against the new baseline established in Step 1.
   - Differ validation passes with **0.0% deletions** against the strict `0.1%` threshold.

---

## Refresh Procedure

CDC publishes PRAMS MCH Indicator reports annually. When a new release is published:

1. **Verify Source Availability**:
   - Check the active CDC landing page at:
     [https://www.cdc.gov/prams/php/data-research/mch-indicators-by-site.html](https://www.cdc.gov/prams/php/data-research/mch-indicators-by-site.html).
   - Note on coverage: The current automated pipeline modernizes the 2016–2020 state summary
     PDF ingestion. CDC transitioned 2021+ data to consolidated Excel workbooks
     (`PRAMS-MCH-Indicators-2016-2022-508.xlsx`). A follow-up pipeline enhancement is tracked
     to parse multi-tab Excel workbooks for 2021–2022+.

2. **Download Updated Data**:
   - If updating PDF inputs:
     ```bash
     python3 scripts/cdc_prams/download_input_files.py --overwrite
     ```

3. **Process and Generate Outputs**:
   - Run the processing pipeline:
     ```bash
     python3 scripts/cdc_prams/process.py
     ```

4. **Verify and Run Tests**:
   - Run unit tests to ensure parser integrity:
     ```bash
     python3 scripts/cdc_prams/process_test.py
     ```
   - Inspect `output/PRAMS.csv`, `output/PRAMS.mcf`, and `output/PRAMS.tmcf`.

5. **Update Manifest & Provenance (if new observation years added)**:
   - Update `end_date_in_kg` in `US_CDC_PRAMS.textproto` and `latestObservationDate`
     in `US_CDC_PRAMS.mcf`.
   - Run `import_groups_test` and `manifest_checker_test` in google3.
