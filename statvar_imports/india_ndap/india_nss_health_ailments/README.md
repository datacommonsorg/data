# India NSS Health Ailments

## 1. Import Overview

This project processes and imports health ailment data from the **National Sample Survey (NSS) Report No. 556 on Health in India**. The dataset provides a profile of ailments, healthcare facility usage, and expenditures based on a survey.

* **Source URL**: [https://ndap.niti.gov.in/dataset/7300](https://ndap.niti.gov.in/dataset/7300)
* **Import Type**: Semi-Automated
* **Source Data Availability**: Released by NDAP (NITI Aayog) based on periodic NSS survey rounds. Not updated on a regular cadence.
* **Release Frequency**: Ad-hoc (typically once every 5 years); updated manually by team when a new round is published
* **Notes**: The dataset includes metrics on various ailments as reported during NSS rounds. Each row represents health-related observations per ailment per state per year.

---

## 2. Preprocessing Steps

Before ingestion, the following preprocessing is done:

* **Input files**:

  * `india_nss_health_ailments.csv`: Raw input data
  * `india_nss_health_ailments_pvmap.csv`: Property-value mapping
  * `india_nss_health_ailments_place_resolved.csv`: Geo resolution data for Indian states/UTs
  * `india_nss_health_ailments_metadata.csv`: StatVar metadata (used by `stat_var_processor.py`)
* **Transformation pipeline**:

  * Columns are cleaned and standardized to match StatVar expectations.
  * StatVars are generated using `stat_var_processor.py`.
  * Output is written to `output/IndiaNSS_HealthAilments_output.csv` and corresponding `output/IndiaNSS_HealthAilments_output.tmcf`.
* **Data Quality Checks**:

  * Linting is performed using the DataCommons import tool JAR
  * Known warnings:

    * Missing values in `unit` and `scalingFactor` columns for rows 2–31. These must be validated and fixed manually.

---

## 3. Autorefresh Type

**Autorefresh**

* **Steps**:

  1. Monitor [NDAP Dataset 7300](https://ndap.niti.gov.in/dataset/7300) for new survey releases
  2. Download raw data using `download_script.py`
  3. Preprocess using `stat_var_processor.py` with updated CSV and mapping files
  4. Run linting and validation
  5. Upload final files to:

     * `gs://datcom-imports/india_ndap/NDAP_NSS_Health/latest/`
  6. Trigger `run_import.sh` manually for test/prod ingestion
* **Note**: This pipeline is semi-automated using a scheduled cron and GCS-staged credential configuration.

---

## 4. Script Execution Details

### Script 1: `download_script.py`

**Usage**:

```bash
python3 download_script.py
```

**Output**: `india_nss_health_ailments.csv`

**Purpose**: Downloads the raw data from the NDAP API and saves it as `india_nss_health_ailments.csv`. It retrieves query URL and credentials from GCS.

---

### Script 2: `stat_var_processor.py`

**Usage**:

```bash
python3 stat_var_processor.py \
  --input_data='india_nss_health_ailments.csv' \
  --pv_map='india_nss_health_ailments_pvmap.csv' \
  --places_resolved_csv='india_nss_health_ailments_place_resolved.csv' \
  --config_file='india_nss_health_ailments_metadata.csv' \
  --output_path=output/IndiaNSS_HealthAilments_output \
  --output_counters=counters/IndiaNSS_HealthAilments_counters.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

**Purpose**: Generates StatVar MCF and cleaned observation CSV (`output/IndiaNSS_HealthAilments_output.csv`, `output/IndiaNSS_HealthAilments_output.tmcf`)

---

### Script 3: Java Linting Tool

**Usage**:

```bash
java -jar '/path/to/datacommons-import-tool.jar' lint \
  'output/IndiaNSS_HealthAilments_output.csv' \
  'output/IndiaNSS_HealthAilments_output.tmcf'
```

**Purpose**: Validates final CSV+TMCF for formatting and semantic consistency before ingestion

---

## 5. Configuration & Troubleshooting

### GCS Configuration Location

`download_script.py` fetches the NDAP query URL and API credentials from Google Cloud Storage:
* **GCS Path**: `gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json`

**Expected JSON Structure**:
```json
{
  "url": "<NDAP_API_QUERY_URL_WITH_CREDENTIALS>",
  "input_files": [
    "india_nss_health_ailments.csv"
  ]
}
```

### Troubleshooting NDAP API Key / Token Expiry

If the download script fails or logs HTTP `401 Unauthorized` / `403 Forbidden` errors:

1. **Obtain Fresh API Query/Key**:
   * Navigate to [NDAP Dataset 7300](https://ndap.niti.gov.in/dataset/7300).
   * Generate or copy the updated API query URL containing the valid access token / API key.
2. **Update GCS Configuration**:
   * Create or update the local `download_config.json` with the new query URL.
   * Upload the updated configuration file to GCS:
     ```bash
     gcloud storage cp download_config.json gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json
     # or
     gsutil cp download_config.json gs://unresolved_mcf/india_ndap/NDAP_NSS_Health/latest/download_config.json
     ```
3. **Verify Download**:
   * Re-run `python3 download_script.py` and verify `india_nss_health_ailments.csv` downloads successfully.
