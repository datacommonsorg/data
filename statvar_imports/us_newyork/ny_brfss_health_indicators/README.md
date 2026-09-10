# NewYork_BRFSS_Health_Indicators

## 1. Import Overview

This import ingests health indicator prevalence rates across **all 62 counties** in New York State and New York City. The dataset is sourced directly from the **New York State Department of Health (NYSDOH) Behavioral Risk Factor Surveillance System (eBRFSS)**.

* **Import Directory**: `statvar_imports/us_newyork/ny_brfss_health_indicators/`
* **Import Name**: `NewYork_BRFSS_Health_Indicators`
* **Dataset Landing Page**: [https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data](https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data)
* **Socrata API Endpoint**: `https://health.data.ny.gov/resource/jsy7-eb4n.json`
* **Geographic Coverage**: **All 62 NY Counties** (`geoId/36001` through `geoId/36123`) and **New York City** (`geoId/3651000`).
* **Temporal Coverage**: 2014, 2016, 2018, 2021, and 2024 survey releases.
* **Unit & Measurement Method**: Direct survey unadjusted crude prevalence percentages (`Percent`).

---

## 2. Health Indicators & Statistical Variables

The import supports **all 75 health indicators** in the NYSDOH dataset across 6 primary health domains:

| Health Domain | Indicators | Key Topics Covered |
|---|:---:|---|
| **Prevent Chronic Diseases** | 42 | Arthritis, Asthma, Cardiovascular Disease, COPD, Diabetes, High Blood Pressure, Obesity, Overweight, Current Smoking (all age/income/disability subsets), e-Cigarettes, Breast/Cervical/Colorectal/PSA Screenings, Physical Activity, Fast Food, Sugary Drinks, Fruits/Vegetables |
| **Improve Health Status & Reduce Disparities** | 13 | Disability (6-question ACA standard), Limitation Status, Health Care Coverage, Personal Health Care Provider, Annual Checkup, Dental Visit, Medical Care Cost Barrier, Poor General & Physical Health, Food Insecurity, Food Security, Housing Insecurity |
| **Promote Mental Health & Substance Abuse** | 9 | Depressive Disorder, Poor Mental Health ($\ge 14$ days), Binge Drinking, Heavy Drinking, DWI, Cannabis Use, Medical Cannabis Use, Smoking with Poor Mental Health, Adverse Childhood Experiences (ACEs) |
| **Prevent HIV/STDs, Vaccine-Preventable Diseases & HAIs** | 5 | Influenza Immunization (Ages 18+, Ages 65+), Pneumococcal Immunization (Ages 65+), Hepatitis C (HCV) Testing (All Adults, Ages 47-68) |
| **Promote Healthy Women, Infants, and Children** | 5 | Female Health Care Coverage (18-64), Female Routine Checkups (18-44, 18-64), Female Dental Visits (18-44), Health Care Provider Discussed Healthy Pregnancy |
| **Promote a Healthy and Safe Environment** | 1 | Walkable Neighborhoods Suitable for Physical Activity |
| **Total** | **75** | **13,479 Observations** |

### Statistical Variable Resolution
* **Canonical StatVars (20)**: Reused directly from the Data Commons Knowledge Graph (e.g. `Percent_Person_WithDiabetes`, `Percent_Person_WithAsthma`, `Percent_Person_WithArthritis`, `Percent_Person_WithChronicObstructivePulmonaryDisease`, `Percent_Person_WithHighBloodPressure`, `Percent_Person_WithHighCholesterol`, `Percent_Person_Obesity`, `Percent_Person_18OrMoreYears_WithDepression`, `Percent_Person_Smoking`, `Percent_Person_BingeDrinking`, `Percent_Person_18OrMoreYears_WithPoorGeneralHealth`, `Percent_Person_WithMentalHealthNotGood`, `Percent_Person_WithPhysicalHealthNotGood`, `Percent_Person_18OrMoreYears_WithAnyDisability`, `Percent_Person_ReceivedDentalVisit`, `Percent_Person_ReceivedCholesterolScreening`, `Percent_Person_50To74Years_Female_ReceivedMammography`, `Percent_Person_21To65Years_Female_ReceivedCervicalCancerScreening`, `Percent_Person_50To75Years_ReceivedColorectalCancerScreening`, `Percent_Person_18OrMoreYears_WithHighBloodPressure_ReceivedTakingBloodPressureMedication`).
* **Provisional StatVars (55)**: Synthesized with formal property-value graphs and emitted into `output_files/ny_brfss_health_indicators_output_stat_vars.mcf`.
* **Supporting Schema Nodes (56)**: Provisional enums, properties, and types emitted into `output_files/ny_brfss_health_indicators_output_stat_vars_schema.mcf`.

---

## 3. Directory Layout

```
statvar_imports/us_newyork/ny_brfss_health_indicators/
├── README.md                                           # Comprehensive import documentation
├── manifest.json                                       # Data Commons import automation manifest
├── validation_config.json                              # Import validation rules (historical deletion and date freshness)
├── ny_brfss_health_indicators_metadata.csv             # Processor configuration metadata
├── ny_brfss_health_indicators_pv_map.csv               # Property-value mapping for all 75 StatVars & 62 counties
├── download.py                                         # Multi-year Socrata downloader
├── test_data/                                          # Sample fixtures for integration testing
│   ├── sample_input.csv                                # Representative raw slice of API data (21 rows)
│   ├── sample_expected_output.csv                      # Expected golden observations
│   ├── sample_expected_output.tmcf                     # Expected golden TMCF
│   ├── sample_expected_output_stat_vars.mcf            # Expected generated StatVars
│   └── sample_expected_output_stat_vars_schema.mcf     # Expected generated schema
├── input_files/                                        # Multi-year source datasets from NYSDOH API
│   └── ny_brfss_health_indicators_raw.csv              # Complete raw unpivoted dataset (all 17,700 records)
├── output_files/                                       # Generated Data Commons artifacts
│   ├── ny_brfss_health_indicators_output.csv           # Cleaned StatVarObservations (13,479 rows)
│   ├── ny_brfss_health_indicators_output.tmcf          # Template MCF mapping file
│   ├── ny_brfss_health_indicators_output_stat_vars.mcf # 55 Provisional StatVar nodes
│   └── ny_brfss_health_indicators_output_stat_vars_schema.mcf # 56 Provisional schema definitions
└── counters/                                           # Processor execution statistics
    └── ny_brfss_health_indicators_counters.csv
```

---

## 4. Execution Workflow

### Step 1: Download Raw Health Data
To fetch the full historical survey data:
```bash
python3 download.py
```
This queries the NYSDOH Socrata API for all 17,700 records across all 75 indicators and 5 survey waves, writing directly to `input_files/ny_brfss_health_indicators_raw.csv`.

### Step 2: Generate StatVar Observations & TMCF
Run `stat_var_processor.py` directly on the raw dataset from within the import directory:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="input_files/ny_brfss_health_indicators_raw.csv" \
  --pv_map=ny_brfss_health_indicators_pv_map.csv \
  --config_file=ny_brfss_health_indicators_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/ny_brfss_health_indicators_output \
  --output_counters=counters/ny_brfss_health_indicators_counters.csv
```

### Step 3: Run Sample Integration Test
Verify property-value mapping against the sample test fixtures:
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data="test_data/sample_input.csv" \
  --pv_map=ny_brfss_health_indicators_pv_map.csv \
  --config_file=ny_brfss_health_indicators_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=test_data/sample_expected_output
```

### Validation Configuration

Validation is configured in `validation_config.json`:
* `check_deleted_records_percent`: Strictly enforces a historical deletion average threshold of `0.1%`. Note that on the initial import run, this rule expectedly reports missing differ summary because there is no prior version in prod GCS to diff against; it is configured to safeguard future recurring refreshes. Per consensus on initial imports, golden regression files are omitted from initial submission.
* `check_max_date_freshness`: Enforces date freshness (`CAST(MaxDate AS INTEGER) >= 2024`) across active recurring health indicator StatVars (e.g. Diabetes, Obesity, Smoking, Asthma, Hypertension, Cardiovascular Disease, Depression, Dental Visits, Routine Checkups) to ensure the latest published survey wave is always captured.
* `check_import_max_date_freshness`: Enforces that the overall import contains observations through at least 2024 (`CAST(max_date AS INTEGER) >= 2024`).

---

## 5. Summary Results

* **Observations Generated**: **13,479** `StatVarObservation` records.
* **Geographies Resolved**: **63 unique entities** (all 62 NY counties `geoId/36001` - `geoId/36123` plus New York City `geoId/3651000`).
* **Non-County Regions Dropped**: **3,081 records** (sub-state DSRIP regions, Rest of State, and Statewide rows cleanly dropped by PV map).
* **Statistical Variables Generated**: **75 unique variables** (20 matched to existing canonical DCIDs, 55 provisional StatVars, 56 schema enums/properties).

