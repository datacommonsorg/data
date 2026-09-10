# Post-Mortem: Commerce EDA Persistent Poverty Import (`Commerce_EDA_Poverty`)

**Target Path:** [`statvar_imports/commerce_eda_poverty/`](file:///usr/local/google/home/shvngisingh/data_new/data/statvar_imports/commerce_eda_poverty/)  
**Pull Request:** [datacommonsorg/data#2178](https://github.com/datacommonsorg/data/pull/2178)  
**Author:** Shivangi Singh (@shvngisingh)  
**Date:** September 10, 2026  
**Status:** Resolved & Verified

---

## 1. Executive Summary & Impact

* **Incident Description:** In commit `a6f21ffe` of PR #2178, an intentional 100-row sampling step (`df = df.head(100)`) was placed directly into the production ETL preprocessing script (`preprocess_poverty()` in `process_poverty.py`).
* **Impact:** 
  - **Severe Data Loss:** 3,132 of 3,232 U.S. counties and island territories (~96.9% of the country) across 48 states were silently discarded prior to Data Commons ingestion. The generated output observation file shrank from 9,689 rows down to only 295 rows (restricted to Alabama, Alaska, and 3 Arizona counties).
  - **Validation Defeat:** To force the 100-row sample to pass automated validation, the county place count validator `check_num_places_county_count` (`NUM_PLACES_COUNT`, expecting 3,100 to 3,250 counties) was removed from `validation_config.json` and replaced with `minimum_observations_per_statvar` (`minimum: 1`), dismantling the import's geographic completeness verification.

---

## 2. Root Cause Analysis

1. **Conflation of Test Fixtures and Production Outputs:**
   Repository guidelines recommend keeping golden verification files compact (~50–200 rows) under `golden_data/` to prevent repository bloat. The author mistakenly implemented this sampling recommendation directly in the production preprocessing script (`process_poverty.py:116`) rather than in an isolated golden generation utility (`validator_goldens.py`).
2. **Cascading Validation Downgrade:**
   When `process_poverty.py` truncated the dataset, the existing validation rule `check_num_places_county_count` failed because only 100 places were observed. Instead of investigating the unexpected place count drop, the author replaced the rule with `minimum_observations_per_statvar` (`minimum: 1`), removing the safeguard that was specifically designed to catch dataset truncation.
3. **Fragile Network Handling:**
   `download_from_gcs()` invoked `file_util.file_copy()` without a retry loop or backoff, leaving Cloud Batch jobs vulnerable to transient Cloud Storage timeouts.
4. **Style and POSIX Non-Compliance:**
   `manifest.json` lacked a terminating newline, and several lines in `process_poverty.py` and `process_poverty_test.py` exceeded the PEP 8 100-character limit.

---

## 3. Debugging Trail & Evidence

1. **Initial Discovery:**
   During the automated code review of PR #2178, diff inspection of commit `a6f21ffe` surfaced the hardcoded truncation:
   ```python
   # Save only 100 rows for the checked-in dataset
   df = df.head(100)
   ```
2. **Telemetry & Counter Confirmation:**
   Inspection of `counters/Poverty_counters.csv` verified the truncation:
   ```csv
   "output-svobs-unique-observationAbout",100
   "output-svobs-csv-rows",295
   ```
   Instead of the expected 3,232 counties and 9,689 observations, the pipeline recorded only 100 counties.
3. **Validator Diff Archaeology:**
   Git log analysis confirmed `validation_config.json` had its place count rule modified in the same commit:
   ```diff
   -      "rule_id": "check_num_places_county_count",
   -      "validator": "NUM_PLACES_COUNT",
   -      "params": {
   -        "minimum": 3100,
   -        "maximum": 3250
   -      }
   +      "rule_id": "minimum_observations_per_statvar",
   +      "validator": "NUM_OBSERVATIONS_CHECK",
   +      "params": {
   +        "minimum": 1
   +      }
   ```
4. **Test Suite Audit:**
   The unit test in `process_poverty_test.py` utilized a 9-row synthetic fixture that filtered to 5 rows. Because 5 < 100, `df = df.head(100)` was a no-op during unit testing, allowing the truncation defect to pass CI with zero warnings.

---

## 4. CI/CD & Testing Gap Analysis

* **Why Unit Tests Did Not Catch It:**
  The unit test fixture was smaller than the truncation threshold. No assertion verified that a dataset with $>100$ rows retained 100% of its records.
* **Why Validation Did Not Catch It:**
  The validation rule that would have failed the Cloud Batch run (`NUM_PLACES_COUNT`) was modified in tandem with the code change, exposing a key review risk: PRs modifying both pipeline logic and validation rules can silently weaken quality gates.

---

## 5. Fix Applied & Verification

### Code Remediations:
1. **Removed Dataset Truncation:**
   Deleted `df = df.head(100)` from `process_poverty.py`. The pipeline now processes all 3,232 counties and island territories.
2. **Restored Place Count Validation:**
   Restored `check_num_places_county_count` with `minimum: 3100, maximum: 3250` in `validation_config.json`, and added clear `description` strings to all 7 rules.
3. **Hardened GCS Downloads:**
   Added a 3-attempt retry loop with exponential backoff (`backoff_factor: 1.5`) and non-empty file size verification (`os.path.getsize(dst_path) > 0`).
4. **Clean Wide Format Preserved:**
   Preserved the normalized wide format mapping in `Povertypvmap.csv` (`poverty_rate_1990`, `poverty_rate_2000`, `poverty_rate_recent`).
5. **Fixed PEP 8 & POSIX Issues:**
   Wrapped all lines $>100$ characters and added a trailing newline to `manifest.json`.
6. **Regenerated Output Artifacts:**
   Regenerated `output/Poverty_cleaned.csv` (3,232 rows), `output/Poverty_output.csv` (9,689 observations), and `counters/Poverty_counters.csv`.

### Verification Results:
* **Unit Tests:**
  `python3 -m unittest statvar_imports.commerce_eda_poverty.process_poverty_test`
  Result: **OK (All tests pass in 0.014s)**.
* **Output Coverage Audit:**
  - `output-svobs-unique-observationAbout`: **3,232 counties** (all 50 states, DC, PR, VI, GU, AS, MP).
  - `output-svobs-csv-rows`: **9,689 observations** across 1990, 2000, and 2021.
  - Value range: **0.0% to 83.3%** (all within expected range 0.0% to 100.0%).
* **Validation Config:**
  - `check_num_places_county_count` (3,232 places in 3100–3250): **PASS**
  - `check_percent_min_value` (min >= 0.0%): **PASS**
  - `check_percent_max_value` (max <= 100.0%): **PASS**
  - `check_date_span_sql` (1990 to 2021): **PASS**
  - `check_deleted_records_percent` (0.1% threshold): **PASS**
* **Lint Cleanliness:**
  - `git diff --check`: **0 errors**.
  - PEP 8: **0 lines > 100 characters**.

---

## 6. Long-Term Prevention & Recommendations

### Short-Term Actions:
* Push commit `e9bd6517` to update PR #2178 on GitHub.

### Systemic / Architectural Recommendations:
1. **Automated Linter Rule Against Head Truncation:**
   Add a pre-commit or CI check flagging `.head(`, `[:N]`, or `LIMIT` in ETL processing scripts under `statvar_imports/**` and `scripts/**`.
2. **Review Scrutiny on Validation Relaxations:**
   Flag pull requests for mandatory second-reviewer sign-off whenever a validation threshold in `validation_config.json` is relaxed (e.g. reducing place counts or deleting rules).
3. **Enforce Test Fixture Scale Checks:**
   Require unit tests for ETL preprocessing to include fixtures larger than typical batching/sampling boundaries (e.g. $>100$ rows) to guarantee that filter functions preserve valid records.
