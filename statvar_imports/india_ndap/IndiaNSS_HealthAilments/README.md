
# India NSS Health Ailments

## 1. Import Overview

This project processes and imports health ailment data from the **National Sample Survey (NSS)** conducted in India. The dataset provides health-related variables for individuals across Indian states and UTs, sourced from structured surveys.

* **Source URL**: [https://ndap.niti.gov.in/dataset/7300](https://ndap.niti.gov.in/dataset/7300)
* **Import Type**: Manual file-based import (CSV)
* **Source Data Availability**: Released by NDAP (NITI Aayog) based on periodic NSS survey rounds. Not updated on a regular cadence.
* **Release Frequency**: Ad-hoc (typically once every 5 years); updated manually by team when a new round is published
* **Notes**: The dataset includes metrics on various ailments as reported during NSS rounds. Each row represents health-related observations per ailment per state per year.

---

## 2. Preprocessing Steps

Before ingestion, the following preprocessing is done:

* **Input files**:

  * `india_nss_health.csv`: Raw input data
  * `pvmap.csv`: Property-value mapping
  * `place_resolved.csv`: Geo resolution data for Indian states/UTs
  * `metadata.csv`: StatVar metadata (used by `stat_var_processor.py`)
* **Transformation pipeline**:

  * Columns are cleaned and standardized to match StatVar expectations.
  * StatVars are generated using `stat_var_processor.py`.
  * Output is written to `IndiaNSS_HealthAilments.csv` and corresponding `IndiaNSS_HealthAilments.tmcf`.
* **Data Quality Checks**:
  * Linting is performed using the DataCommons import tool JAR.
  * The `stat_var_processor.py` script handles the necessary scaling of values. The original data is provided as a value per 100,000 persons, and the script converts this to a fraction.

---

## 3. Autorefresh Type

**Autorefresh**

* **Steps**:

  1. Monitor [NDAP Dataset 7300](https://ndap.niti.gov.in/dataset/7300) for new survey releases
  2. Manually download the latest data
  3. Preprocess using `stat_var_processor.py` with updated CSV and mapping files
  4. Run linting and validation
  5. Upload final files to:

     * `gs://datcom-imports/india_ndap/NDAP_NSS_Health/latest/`
  6. Trigger `run_import.sh` manually for test/prod ingestion
* **Note**: This pipeline is not fully automated due to manual file retrieval and preprocessing needs.

---

## 4. Script Execution Details

### Script 1: `stat_var_processor.py`

**Usage**:

```bash
python3 stat_var_processor.py \
  --input_data='/path/to/india_nss_health.csv' \
  --pv_map='/path/to/pvmap.csv' \
  --places_resolved_csv='/path/to/place_resolved.csv' \
  --config_file='/path/to/metadata.csv' \
  --output_path='/path/to/output/health_nss' \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

**Purpose**: Generates StatVar MCF and cleaned observation CSV (`IndiaNSS_HealthAilments.csv`, `IndiaNSS_HealthAilments.tmcf`)

---

### Script 2: Java Linting Tool

**Usage**:

```bash
java -jar '/path/to/datacommons-import-tool.jar' lint \
  '/path/to/IndiaNSS_HealthAilments.csv' \
  '/path/to/IndiaNSS_HealthAilments.tmcf'
```

**Purpose**: Validates final CSV+TMCF for formatting and semantic consistency before ingestion

---

### Script 3: `download_script.py` (if used)

**Usage**:

```bash
python3 download_script.py
```

