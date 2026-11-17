# Feeding America: Food Insecurity (`FeedingAmerica_FoodInsecurity`)

## 1. Overview
- **Import Name:** `FeedingAmerica_FoodInsecurity`
- **Source:** Feeding America — Map the Meal Gap (`https://map.feedingamerica.org/`)
- **API Endpoint:** `GET https://map.feedingamerica.org/mapdata?maptype={county,district}&year=<YYYY>&type={overall,child,black,hispanic,white}`
- **Geographic Coverage:** 51 US States (including DC, `geoId/01`–`geoId/56`), US Counties (`geoId/01001`–`geoId/56045`), and US Congressional Districts (`geoId/0101`–`geoId/5600`) — `3,648` unique places across `2019–2024`
- **Date Coverage:** `2019`–`2024+` (preserves `2019–2021` historical baseline verbatim and fetches `2022+` live from the Map the Meal Gap JSON endpoint, dynamically discovering newly published years from `https://map.feedingamerica.org/`)
- **Refresh Schedule:** Monthly check (`0 09 1 * *`); upstream publication cadence is annual (`P1Y`)
- **StatVars Covered (`16`):**
  - `Count_Person_FoodInsecure_AsAFractionOf_Count_Person` (`Percent`, `scalingFactor: 100`)
  - `Count_Person_FoodInsecure`
  - `Count_Person_FoodInsecure_Black_AsAFractionOf_Count_Person_Black` (`Percent`, `scalingFactor: 100`)
  - `Count_Person_HispanicOrLatino_FoodInSecure_AsAFractionOf_Count_Person_HispanicOrLatino` (`Percent`, `scalingFactor: 100`)
  - `Count_Person_NotHispanicOrLatino_FoodInSecure_White_AsAFractionOf_Count_Person_NotHispanicOrLatino_White` (`Percent`, `scalingFactor: 100`)
  - `Count_Person_FoodInsecure_HouseholdIncomeAtOrBelowStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure` (`Percent`, `scalingFactor: 100`)
  - `Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThresholdAndBelowOrEqualStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure` (`2019–2020`, `Percent`, `scalingFactor: 100`)
  - `Count_Person_FoodInsecure_HouseholdIncomeAboveStateHighThreshold_AsAFractionOf_Count_Person_FoodInsecure` (`2019–2020`, `Percent`, `scalingFactor: 100`)
  - `Count_Person_FoodInsecure_HouseholdIncomeAboveStateLowThreshold_AsAFractionOf_Count_Person_FoodInsecure` (`Percent`, `scalingFactor: 100`)
  - `Count_Child_FoodInsecure_AsAFractionOf_Count_Child` (`Percent`, `scalingFactor: 100`)
  - `Count_Child_FoodInsecure`
  - `Count_Child_FoodInsecure_HouseholdIncomeBelow185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure` (`Percent`, `scalingFactor: 100`)
  - `Count_Child_FoodInsecure_HouseholdIncomeAbove185PercentOfFederalPovertyLine_AsAFractionOf_Count_Child_FoodInsecure` (`Percent`, `scalingFactor: 100`)
  - `Mean_CostPerMeal_Person_FoodInSecure` (State & County, `USDollar`)
  - `Weekly_WeightedFoodSpendAmount_Person_FoodInSecure` (State & County, `USDollar`)
  - `Annual_WeightedBudgetShortfall_Food` (State & County, `USDollar`)

---

## 2. Files
- `download.py`: Loads `input_files/FeedingAmerica_FoodInsecurity_baseline_2019_2021.csv` verbatim, discovers available years (`>= 2022`) from `https://map.feedingamerica.org/`, fetches `county` and `district` JSON payloads across `overall`, `child`, `black`, `hispanic`, and `white` splits (using a stateless session with bounded retries and backoff), restores `0.0%` complementary bands when the API serializes `0%` as `null`, derives `Weekly_WeightedFoodSpendAmount_Person_FoodInSecure = money_needed / (population * 52 * 7 / 12)`, skips all-empty territory placeholders, and atomically writes `input_files/feedingamerica_foodinsecurity_input.csv`.
- `download_test.py`: Hermetic unit tests for `download.py`.
- `input_files/FeedingAmerica_FoodInsecurity_baseline_2019_2021.csv`: Consolidated `2019–2021` historical baseline (`10,889` rows / `150,729` observations) preserving historical geographies and the two discontinued `2019–2020` SNAP high-threshold StatVars.
- `feedingamerica_foodinsecurity_pvmap.csv`: Wide-to-long `stat_var_processor.py` PVMap for all 16 StatVars.
- `feedingamerica_foodinsecurity_metadata.csv`: `stat_var_processor.py` configuration.
- `feeding_america_stat_vars.mcf` & `food_security_schema.mcf`: Existing StatisticalVariable and schema definitions.
- `manifest.json`: Import automation manifest.
- `validation_config.json`: Import validation rules (non-negative values, `<= 100` for percent StatVars, active StatVar freshness/coverage, and `2019–2020` historical SNAP threshold coverage).

---

## 3. Local Run & Counter Audit Summary (`2019–2024`)

| Metric | Value |
| :--- | :---: |
| **Input Rows (`2019–2024`)** | `21,782` (`10,889` baseline + `3 × 3,631` live API) |
| **Generated / Output SVObs** | `289,904` (`2019`: `52,323`; `2020`: `52,169`; `2021`: `46,237`; `2022`: `46,434`; `2023`: `46,325`; `2024`: `46,416`) |
| **Unique Places (`observationAbout`)** | `3,648` |
| **Unique StatVars (`variableMeasured`)** | `16` |
| **Unique Dates (`observationDate`)** | `6` (`2019`–`2024`) |
| **`error-unresolved-place`** | `0` |
| **`dropped-svobs`** | `0` |
| **`dropped-output-statvars-mcf`** | `0` |
| **`2019–2021` Baseline Parity** | `150,729 / 150,729` (`0` missing, `0` numerical diffs) |

---

## 4. How to Run

Prerequisites: Repository Python virtual environment (`.env`) created via `./run_tests.sh -r`, and read access to `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`.

1. **Download and merge data (`2019–2021` baseline + `2022+` live API):**
   ```bash
   cd statvar_imports/feeding_america/food_insecurity
   ../../../.env/bin/python download.py
   ```

2. **Run `stat_var_processor.py`:**
   ```bash
   ../../../.env/bin/python ../../../tools/statvar_importer/stat_var_processor.py \
     --input_data=input_files/feedingamerica_foodinsecurity_input.csv \
     --pv_map=feedingamerica_foodinsecurity_pvmap.csv \
     --config_file=feedingamerica_foodinsecurity_metadata.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf,feeding_america_stat_vars.mcf \
     --output_path=output/feedingamerica_foodinsecurity_output \
     --output_counters=counters/feedingamerica_foodinsecurity_counters.csv
   ```

3. **Run unit tests and lint checks (from repository root):**
   ```bash
   ./run_tests.sh -p statvar_imports/feeding_america/food_insecurity
   ```
