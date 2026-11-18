# Feeding America: Map the Meal Gap (`FeedingAmerica_MapMealGap`)

## 1. Overview
- **Import Name:** `FeedingAmerica_MapMealGap`
- **Source:** Feeding America — Map the Meal Gap (`https://map.feedingamerica.org/`)
- **API Endpoint:** `GET https://map.feedingamerica.org/mapdata?maptype=county&year=<YYYY>&type={overall,child}`
- **Geographic Coverage:** 51 US States (including DC, `geoId/01`–`geoId/56`) and US Counties (`geoId/01001`–`geoId/56045`) — `3,204` unique places
- **Date Coverage:** `2018`–`2024` (preserves `2018–2019` historical baseline and fetches `2020+` live from the Map the Meal Gap JSON endpoint)
- **StatVars Covered (`9`):**
  - `Count_Person_FoodInsecure`
  - `Count_Person_FoodInsecure_EligibleForAllFederalBenefits`
  - `Count_Person_FoodInsecure_EligibleForSomeFederalBenefits` (`2018–2020`)
  - `Count_Person_FoodInsecure_IneligibleForFederalBenefits`
  - `Count_Child_FoodInsecure`
  - `Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits`
  - `Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits`
  - `Mean_MealCost_Person_FoodSecure`
  - `Annual_FoodBudgetShortfall`

---

## 2. Data Diffs & Refresh Summary (`differ_summary.json`)

Comparison against the legacy production `FeedingAmerica_MapMealGap` baseline (`/cns/jv-d/home/datcom/v3_mcf/feeding_america/map_meal_gap/`):

| Metric | Count | Explanation |
| :--- | :---: | :--- |
| **Previous Observations** | `55,507` | Legacy CNS baseline covering `2018–2019` across `3,193` states and counties |
| **Current Observations** | `185,217` | Refreshed `2018–2024` output across `3,204` states and counties |
| **Added Observations** | `+129,710` | New `2020–2024` observations (`2020`: `27,558`; `2021`: `25,540`; `2022`: `25,558`; `2023`: `25,508`; `2024`: `25,546`) |
| **Modified Observations** | `5,292` | `0` numerical differences (`float(new) == float(old)` for all `5,292` rows; trailing `.0` stripped on integer-valued floats by `stat_var_processor.py`) |
| **Deleted Observations** | `0` (`0.0%`) | Zero historical deletions (`DELETED_RECORDS_PERCENT == 0.0%`) |

---

## 3. Automation, Schedule & Baseline Staging

- **Manifest:** `manifest.json`
- **Cron Schedule:** `0 09 1 * *` (monthly on the 1st at 09:00 UTC)
- **Historical Baseline (`2018–2019`):** Committed at `input_files/FeedingAmerica_MMG_baseline_2018_2019.csv` (`456,391` bytes, matching the legacy CNS CSV). If absent locally, `download.py` falls back to downloading it from `gs://unresolved_mcf/feeding_america/map_meal_gap/latest/input_files/FeedingAmerica_MMG_baseline_2018_2019.csv`.
- **Schema & StatVars:** All 9 StatVars and supporting schema nodes are already defined in Data Commons canonical schema (`third_party/datacommons/schema/stat_vars/feeding_america_stat_vars.mcf` and `third_party/datacommons/schema/core/food_security_schema.mcf`) and indexed in `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`. `manifest.json` uses `"node_mcf": "output/*.mcf"` so existing schema is not re-ingested.

---

## 4. How to Run

1. **Download and merge data (`2018–2019` baseline + `2020+` live API):**
   ```bash
   cd statvar_imports/feeding_america/map_meal_gap
   ../../../.env/bin/python download.py
   ```

2. **Run `stat_var_processor.py`:**
   ```bash
   ../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
     --input_data=input_files/feedingamerica_mapmealgap_input.csv \
     --pv_map=feedingamerica_mapmealgap_pvmap.csv \
     --config_file=feedingamerica_mapmealgap_metadata.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=output/feedingamerica_mapmealgap_output \
     --output_counters=counters/feedingamerica_mapmealgap_counters.csv
   ```

3. **Verify `test_data/` fixtures against `stat_var_processor.py`:**
   ```bash
   ../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
     --input_data=test_data/feedingamerica_mapmealgap_input.csv \
     --pv_map=feedingamerica_mapmealgap_pvmap.csv \
     --config_file=feedingamerica_mapmealgap_metadata.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
     --output_path=/tmp/feedingamerica_test_output
   diff -u test_data/feedingamerica_mapmealgap_output.tmcf /tmp/feedingamerica_test_output.tmcf
   diff -u <(sort test_data/feedingamerica_mapmealgap_output.csv) <(sort /tmp/feedingamerica_test_output.csv)
   ```

4. **Run unit tests and Python lint/format checks (from repo root):**
   ```bash
   ./run_tests.sh -p statvar_imports/feeding_america/map_meal_gap
   .env/bin/ruff check statvar_imports/feeding_america
   .env/bin/yapf -r --diff -p --style=google statvar_imports/feeding_america
   ```

5. **Run `dc-import lint` on generated outputs:**
   ```bash
   ../../../import-automation/executor/scripts/run_import_tool.sh lint \
     output/feedingamerica_mapmealgap_output.tmcf \
     output/feedingamerica_mapmealgap_output.csv
   ```

