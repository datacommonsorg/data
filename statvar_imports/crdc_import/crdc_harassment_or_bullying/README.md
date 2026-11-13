# Civil Rights Data Collection (CRDC) — Harassment or Bullying

## 1. Import Overview

This import processes school-level **Harassment or Bullying** data from the U.S. Department of Education's Civil Rights Data Collection (CRDC) across published survey releases (`2011-12`, `2013-14`, `2017-18`, `2020-21`, `2021-22`, `2023-24`, and future `2024+` releases).

* **Import Name**: `CRDC_EducationSchool_HarassmentOrBullying`
* **Source URL**: [https://civilrightsdata.ed.gov/data](https://civilrightsdata.ed.gov/data)
* **Entity Type**: Public schools (`nces/<12-digit COMBOKEY>`)
* **Schedule**: Weekly on Friday at `06:30 UTC` (`30 6 * * 5`)

---

## 2. Pipeline Architecture & Files

| File | Purpose |
| :--- | :--- |
| `manifest.json` | Declares scripts (`download.py`, `preprocess.py`, `run.sh`), `import_inputs` (`2012`, `2014`, `2018`, `2021`, `2022`, `2024Onwards`), `source_files`, `validation_config_file`, and Cloud Batch `resource_limits`. |
| `download.py` | Downloads CRDC ZIP archives into temporary `source_files/`, deterministically discovers school-level (`SCH`) Harassment/Bullying tables mapped in `harassment_or_bullying_pvmap.csv` (excluding `LEA`, `__MACOSX`, `layout`, and unmapped `2011-12` `Reported Allegations` tables), and writes raw converted CSVs to `input_files/`. |
| `preprocess.py` | Reads `input_files/*.csv` as strings (preserving leading zeros on `COMBOKEY` and keeping empty cells blank), strips stray quotes/backticks, inserts `Year` as column 2, and writes atomically to `preprocessed_files/`. |
| `run.sh` | Verifies all required input partitions exist in `preprocessed_files/`, runs `stat_var_processor.py` in parallel to produce `processed_output/`, and verifies all `manifest.json` `.tmcf` and `.csv` outputs exist and contain data rows. |
| `harassment_or_bullying_pvmap.csv` | Property-value mappings for CRDC Harassment and Bullying school metrics. |
| `harassment_or_bullying_metadata.csv` | Configuration parameters for `stat_var_processor.py`. |
| `validation_config.json` | Import-specific validation rules (`MAX_DATE_CONSISTENT` and `2024Onwards` date freshness; the `0.1%` deleted-records threshold, empty-import, missing-refs, and lint checks are inherited from the global `tools/import_validation/validation_config.json`). |
| `download_preprocess_test.py` | Unit tests covering deterministic file discovery, retries/fail-fast download handling, string-safe preprocessing, `run.sh` pre-flight validation, and `validation_config.json` SQL checks. |

---

## 3. Running Locally

Run all commands from the `data` repository root (or from `statvar_imports/crdc_import/crdc_harassment_or_bullying/`):

```bash
# 1. Set up the repository virtual environment
./run_tests.sh -r

# 2. Download raw CRDC Harassment/Bullying CSVs into input_files/
.env/bin/python statvar_imports/crdc_import/crdc_harassment_or_bullying/download.py

# 3. Preprocess CSVs into preprocessed_files/
.env/bin/python statvar_imports/crdc_import/crdc_harassment_or_bullying/preprocess.py

# 4. Run StatVar processing into processed_output/
PYTHON_BIN="$PWD/.env/bin/python" bash statvar_imports/crdc_import/crdc_harassment_or_bullying/run.sh
```

---

## 4. Testing & Validation

Run unit tests and lint checks from the `data` repository root:

```bash
./run_tests.sh -p statvar_imports/crdc_import/crdc_harassment_or_bullying
./run_tests.sh -l
```

To lint generated MCF/TMCF/CSV artifacts with the Data Commons import tool:

```bash
java -jar /path/to/datacommons-import-tool.jar lint -o lint_report/2012 \
  processed_output/crdc_harassment_or_bullying_2012*.csv \
  processed_output/crdc_harassment_or_bullying_2012_part_01.tmcf \
  processed_output/crdc_harassment_or_bullying_2012*.mcf
for year in 2014 2018 2021 2022 2024Onwards; do
  java -jar /path/to/datacommons-import-tool.jar lint -o lint_report/$year \
    processed_output/crdc_harassment_or_bullying_${year}.csv \
    processed_output/crdc_harassment_or_bullying_${year}.tmcf \
    processed_output/crdc_harassment_or_bullying_${year}*.mcf
done
```