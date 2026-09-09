# NewYork_BRFSS_Health_Indicators

## 1. Import Overview

This import ingests health indicator prevalence rates across **all 62 counties** in New York State and New York City. The dataset is sourced directly from the **New York State Department of Health (NYSDOH) Behavioral Risk Factor Surveillance System (eBRFSS)**.

* **Import Directory**: `statvar_imports/us_newyork/ny_brfss_health_indicators/`
* **Import Name**: `NewYork_BRFSS_Health_Indicators`
* **Dataset Landing Page**: [https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data](https://health.data.ny.gov/Health/Behavioral-Risk-Factor-Surveillance-System-BRFSS-H/jsy7-eb4n/about_data)
* **Socrata API Endpoint**: `https://health.data.ny.gov/resource/jsy7-eb4n.json`
* **Geographic Coverage**: **All 62 NY Counties** (`geoId/36001` through `geoId/36123`) and **New York City** (`geoId/3651000`).
* **Temporal Coverage**: 2014, 2016, 2018, 2021, and 2024 survey releases.
* **Unit & Measurement Method**: Direct survey unadjusted crude prevalence percentages (`Percent`, `scalingFactor: 100`).

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
* **Canonical StatVars (12)**: Already established in the Data Commons Knowledge Graph (e.g. `Percent_Person_WithDiabetes`, `Percent_Person_WithAsthma`, `Percent_Person_WithArthritis`, `Percent_Person_WithChronicObstructivePulmonaryDisease`, `Percent_Person_WithHighBloodPressure`, `Percent_Person_WithHighCholesterol`, `Percent_Person_Obesity`, `Percent_Person_18OrMoreYears_WithDepression`, `Percent_Person_Smoking`, `Percent_Person_BingeDrinking`, `Percent_Person_18OrMoreYears_WithPoorGeneralHealth`, `Percent_Person_WithMentalHealthNotGood`, `Percent_Person_WithPhysicalHealthNotGood`).
* **Provisional StatVars (63)**: Synthesized with formal property-value graphs and emitted into `output_files/ny_brfss_health_indicators_output_stat_vars.mcf`.
* **Supporting Schema Nodes (58)**: Provisional enums, properties, and types emitted into `output_files/ny_brfss_health_indicators_output_stat_vars_schema.mcf`.

---

## 3. Directory Layout

```
statvar_imports/us_newyork/ny_brfss_health_indicators/
├── README.md                                           # Comprehensive import documentation
├── manifest.json                                       # Data Commons import automation manifest
├── validation_config.json                              # Import validation rules (historical deletion threshold)
├── ny_brfss_health_indicators_metadata.csv             # Processor configuration metadata
├── ny_brfss_health_indicators_pv_map.csv               # Property-value mapping for all 75 StatVars & 62 counties
├── schema.mcf                                          # Combined local test schema (provisional StatVars & enums)
├── download.py                                         # Multi-year Socrata downloader
├── download_test.py                                    # Downloader unit test suite
├── input_files/                                        # Multi-year source datasets from NYSDOH API
│   └── ny_brfss_health_indicators_raw.csv              # Complete raw unpivoted dataset (all 17,700 records)
├── output_files/                                       # Generated Data Commons artifacts
│   ├── ny_brfss_health_indicators_output.csv           # Cleaned StatVarObservations (13,479 rows)
│   ├── ny_brfss_health_indicators_output.tmcf          # Template MCF mapping file
│   ├── ny_brfss_health_indicators_output_stat_vars.mcf # 63 Provisional StatVar nodes
│   └── ny_brfss_health_indicators_output_stat_vars_schema.mcf # 58 Provisional schema definitions
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

### Step 3: Run Unit Tests
```bash
python3 -m unittest download_test.py
```

### Step 4: Validate with Data Commons Import Tool
```bash
java -jar ~/Downloads/import_tools_import-tool.jar lint \
  output_files/ny_brfss_health_indicators_output.csv \
  output_files/ny_brfss_health_indicators_output.tmcf \
  schema.mcf
```

---

## 5. Verification Results

* **Observations Generated**: **13,479** `StatVarObservation` records.
* **Geographies Resolved**: **63 unique entities** (all 62 NY counties `geoId/36001` - `geoId/36123` plus New York City `geoId/3651000`).
* **Non-County Regions Dropped**: **2,831 records** (sub-state DSRIP regions, Rest of State, and Statewide rows cleanly dropped by PV map).
* **Statistical Variables Generated**: **75 unique variables** (12 matched to existing canonical DCIDs, 63 provisional StatVars, 58 schema enums/properties).
* **Linter Status**: **0 fatal, 0 errors, 0 missing references** (`NumRowSuccesses: 13,479 / 13,479`).
