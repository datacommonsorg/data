# Feeding America Map the Meal Gap Import (`FeedingAmerica_MapMealGap`)

This directory contains the automated Data Commons import pipeline for **Feeding America's Map the Meal Gap (MMG)** dataset (`FeedingAmerica_MapMealGap`), covering annual food insecurity statistics across US states (`geoId/01`–`geoId/56`), counties (5-digit FIPS `geoId/`), and congressional districts (`geoId/0101`, etc.).

## 1. Overview & Data Sources

- **Source Organization**: [Feeding America](https://www.feedingamerica.org/research/map-the-meal-gap)
- **Import Name**: `FeedingAmerica_MapMealGap`
- **Provenance URL**: `https://www.feedingamerica.org/research/map-the-meal-gap/by-county`
- **Geography Coverage**: US States (`51`), US Counties (`3,142`–`3,143`), and US Congressional Districts (`436`, 2018)
- **Temporal Coverage**: `2018`–`2021` (`P1Y` observation period)
- **GCS Staging Bucket**: `gs://unresolved_mcf/feeding_america/map_meal_gap/latest/`
  - Historical baseline (`2018`–`2019` state, county, and congressional district rows): `gs://unresolved_mcf/feeding_america/map_meal_gap/latest/table/FeedingAmerica_MMG.csv`
  - Multi-year release workbooks (`2019`–`2021` state and county data): `gs://unresolved_mcf/feeding_america/map_meal_gap/latest/MMG2023_2019-2021_Data_ToShare_Google.xlsx` (and exported CSV sheets `feeding_america_data_2019_2021_{state,county}.csv`)

## 2. Statistical Variables

This import produces 9 `StatisticalVariable` series defined in canonical Google3 schema (`//depot/google3/third_party/datacommons/schema/stat_vars/feeding_america_stat_vars.mcf`):

| Column in `FeedingAmerica_MMG.csv` | `variableMeasured` (`dcid`) | Unit | Description |
| :--- | :--- | :--- | :--- |
| `FoodInsecurePersonCount` | `dcid:Count_Person_FoodInsecure` | — | Total food-insecure population |
| `BelowPovertyLineCount` | `dcid:Count_Person_FoodInsecure_EligibleForAllFederalBenefits` | — | Food-insecure population below low SNAP/federal poverty threshold (`Count * % FI ≤ Low Threshold`) |
| `AbovePovertyLineCount` | `dcid:Count_Person_FoodInsecure_IneligibleForFederalBenefits` | — | Food-insecure population above federal nutrition threshold (`Count * % FI > High Threshold` through 2020; `Count * % FI > Low Threshold` in 2021 when single threshold is reported) |
| `BetweenThresholdsCount` | `dcid:Count_Person_FoodInsecure_EligibleForSomeFederalBenefits` | — | Food-insecure population between low and high thresholds (`Count * % FI Btwn Thresholds`; reported through 2020) |
| `FoodInsecureChildrenCount` | `dcid:Count_Child_FoodInsecure` | — | Total food-insecure children |
| `ChildrenEligibleForFederalAssistCount` | `dcid:Count_Child_FoodInsecure_EligibleForManyChildNutritionBenefits` | — | Food-insecure children with household income `<= 185% FPL` |
| `ChildrenIneligibleForFederalAssistCount` | `dcid:Count_Child_FoodInsecure_IneligibleForChildNutritionBenefits` | — | Food-insecure children with household income `> 185% FPL` |
| `CostPerMeal` | `dcid:Mean_MealCost_Person_FoodSecure` | `dcid:USDollar` | Average cost per meal |
| `AnnualFoodBudgetShortfall` | `dcid:Annual_FoodBudgetShortfall` | `dcid:USDollar` | Weighted annual food budget shortfall |

## 3. Running the Pipeline Locally

### Run Data Processing (`run.sh` or `process_mmg.py`)

```bash
./statvar_imports/feeding_america/map_meal_gap/run.sh \
  --input_dir=/path/to/local/input_dir \
  --output_dir=statvar_imports/feeding_america/map_meal_gap/output
```

Or run `./statvar_imports/feeding_america/map_meal_gap/run.sh` with no arguments if `gsutil` credentials are configured to sync from `gs://unresolved_mcf/feeding_america/map_meal_gap/latest/`.

### Run Unit Tests

```bash
./run_tests.sh -p statvar_imports/feeding_america/map_meal_gap
```

### Generate MCF, Summary Report, Golden Files, and Run Validation

```bash
java -Djava.awt.headless=true -jar import-tool.jar genmcf \
  -o statvar_imports/feeding_america/map_meal_gap/genmcf_out \
  statvar_imports/feeding_america/map_meal_gap/output/FeedingAmerica_MMG.tmcf \
  statvar_imports/feeding_america/map_meal_gap/output/FeedingAmerica_MMG.csv

python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=statvar_imports/feeding_america/map_meal_gap/genmcf_out/summary_report.csv \
  --generate_goldens=statvar_imports/feeding_america/map_meal_gap/golden_data/golden_summary_report.csv \
  --generate_goldens_property_sets="StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods"

python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=statvar_imports/feeding_america/map_meal_gap/output/FeedingAmerica_MMG.csv \
  --generate_goldens=statvar_imports/feeding_america/map_meal_gap/golden_data/golden_observations.csv \
  --goldens_sample_rows=100 \
  --goldens_must_include="observationAbout:top_100k_places.csv" \
  --generate_goldens_property_sets="observationAbout"

python3 -m tools.import_validation.runner \
  --validation_config=statvar_imports/feeding_america/map_meal_gap/validation_config.json \
  --stats_summary=statvar_imports/feeding_america/map_meal_gap/genmcf_out/summary_report.csv \
  --lint_report=statvar_imports/feeding_america/map_meal_gap/genmcf_out/report.json \
  --validation_output=statvar_imports/feeding_america/map_meal_gap/genmcf_out/validation_output.csv
```
