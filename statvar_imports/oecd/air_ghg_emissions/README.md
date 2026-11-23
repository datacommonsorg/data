# OECD Air and Greenhouse Gas (GHG) Emissions Data

## 1. Import Overview

This project downloads, normalizes, and imports national (`country/<ISO3>`) and global (`Earth`) air pollutant, greenhouse gas (GHG) emission, and production-based $\text{CO}_2$ productivity statistics provided by the Organisation for Economic Co-operation and Development (OECD).

*   **Source URL**: [https://data-explorer.oecd.org/](https://data-explorer.oecd.org/)
*   **SDMX API Endpoint**: `https://sdmx.oecd.org/public/rest/` (agency `OECD.ENV.EPI`)
*   **Import Type**: Automated (`OECD_Air_GHG_emissions`)
*   **Source Data Availability**:
    *   **Greenhouse Gas Emissions (`DSD_AIR_GHG@DF_AIR_GHG`)**: Annual (`1985`–present) total GHG emissions excluding LULUCF (`GHG`, `MEASURE=_T`, `T_CO2E` and `KG_CO2E_PS`).
    *   **Air Pollutant Emissions (`DSD_AIR_EMISSIONS@DF_AIR_EMISSIONS`)**: Annual (`1990`–present) total man-made emissions (`MEASURE=T_EM_MM`) of `CO`, `NOX`, `SOX`, and `NMVOC` (`T` and `KG_PS`).
    *   **Green Growth Production-Based $\text{CO}_2$ Indicators (`DSD_GG@DF_GREEN_GROWTH`)**: Annual (`1990`–present) production-based $\text{CO}_2$ emissions (`CO2_PBEM`), per-capita $\text{CO}_2$ emissions (`CO2_PBEMCAP`), and production-based $\text{CO}_2$ productivity (`CO2_PBPROD`, `USD_CO2` — real GDP per unit of energy-related $\text{CO}_2$ emissions in `USDollarPerKilogram`).
    *   **Pre-SDMX Historical Baseline (`1960`–`1989`)**: Static historical physical-mass emission observations retained from `gs://unresolved_mcf/oecd/oecd_air_and_ghg_emissions/AirandGHGEmissions-latest - processed_csv.csv` for `(place, StatVar, year)` keys not covered by the live SDMX feeds.
*   **Release Frequency**: Annual (staggered mid-year updates across the three OECD dataflows).
*   **Notes**: Covers `13` StatisticalVariables (`12` existing emission variables + `1` production-based $\text{CO}_2$ productivity variable `RealValue_Amount_EconomicActivity_GrossDomesticProduction_AsAFractionOf_Annual_Amount_Emissions_CarbonDioxide`) across `163` countries (`country/<ISO3>`) and World (`Earth`), canonicalizing World (`WLD` $\rightarrow$ `W` $\rightarrow$ `dcid:Earth`) and excluding non-country regional aggregates (`OECD`, `OECDA`, `OECDE`, `OECDSO`, `OEU`, `EU27`, `EU27_2020`).

---

## 2. Preprocessing Steps

The import pipeline downloads raw OECD SDMX-CSV v2.1 feeds (`?dimensionAtObservation=AllDimensions&format=csvfile`) and the GCS historical baseline CSV directly into `input_files/` via `download.py`, normalizes and deduplicates them into `input_files/oecd_air_ghg_emissions_input.csv` (retaining the raw CSVs for GCS archiving), and runs `stat_var_processor.py` to generate final Data Commons CSV, TMCF, and StatVar MCF artifacts.

*   **Files**:
    *   `download.py`: Downloads the three `OECD.ENV.EPI` SDMX-CSV endpoints (`?dimensionAtObservation=AllDimensions&format=csvfile`) via `requests` and the GCS historical baseline CSV directly into `input_files/` (`oecd_air_ghg_raw.csv`, `oecd_air_emissions_raw.csv`, `oecd_green_growth_co2_raw.csv`, `historical_baseline_2024.csv`), verifies all 13 expected `(SUBJECT, MEASURE)` series are populated, normalizes `UNIT_MULT` and `UNIT_MEASURE` into `(LOCATION, SUBJECT, MEASURE, FREQUENCY, TIME, Value)`, and writes `input_files/oecd_air_ghg_emissions_input.csv` atomically.
    *   `download_test.py`: Hermetic unit and integration tests covering SDMX-CSV validation and scaling, series completeness checks, transient HTTP retries, permanent HTTP fast-failure, historical deduplication, and manifest/validation/fixture config checks.
    *   `oecd_air_ghg_emissions_metadata.csv`: Configuration file for `stat_var_processor.py` specifying output columns (`observationAbout,observationDate,value,variableMeasured,unit`), header rows, mapped columns (`"2,3"`), and provenance metadata.
    *   `oecd_air_ghg_emissions_pvmap.csv`: Property-value mapping file mapping normalized OECD subjects (`CO2`, `GHG`, `CO`, `NOX`, `SOX`, `VOC`, `CO2_PBPROD`) and measures (`MLN_TONNE`, `THND_TONNECO2`, `THND_TONNE`, `TONNE_CAP`, `KG_CAP`, `USD_CO2`) to Data Commons StatisticalVariables, units (`MetricTon`, `MetricTonCO2e`, `Kilogram`, `USDollarPerKilogram`), and `#Multiply` factors.
    *   `oecd_air_ghg_emissions_places_resolved.csv`: Resolved place mapping table mapping ISO-3166-1 alpha-3 country codes to `country/<ISO3>` and canonical World (`W`) to `Earth` (with `WLD` normalized to `W` by `download.py`).
    *   `validation_config.json`: Configuration defining 3 dataflow-scoped `MAX_DATE_CONSISTENT` rules, non-negative bounds, and rolling freshness/completeness checks across all 13 StatisticalVariables (alongside global base rules).
    *   `test_data/`: Sample input data (`sample_input.csv`) and expected output (`sample_output.csv`, `sample_output.tmcf`) for integration testing.

*   **Transformation pipeline**:
    1.  `download.py` downloads all three OECD SDMX-CSV dataflows into `input_files/` using bounded socket timeouts and exponential-backoff retries on transient HTTP (`408`, `429`, `5xx`) and network errors, validating CSV headers and observation attributes.
    2.  `download.py` fetches the static 2024 baseline CSV from `gs://unresolved_mcf/oecd/oecd_air_and_ghg_emissions/AirandGHGEmissions-latest - processed_csv.csv` into `input_files/` via `google.cloud.storage.Client()`, retains non-overlapping pre-SDMX historical keys for the 12 physical-mass emission variables (preferring canonical `dcid:Earth` over legacy `country/WLD`), and writes `input_files/oecd_air_ghg_emissions_input.csv` while preserving all 4 raw CSVs in `input_files/`.
    3.  `stat_var_processor.py` resolves all 13 StatisticalVariables and 164 geographic entities against `oecd_air_ghg_emissions_pvmap.csv`, `oecd_air_ghg_emissions_metadata.csv`, `oecd_air_ghg_emissions_places_resolved.csv`, and `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`, writing `output_files/oecd_air_ghg_emissions.csv`, `output_files/oecd_air_ghg_emissions.tmcf`, `output_files/oecd_air_ghg_emissions_stat_vars.mcf` (defining the new `CO2_PBPROD` productivity StatVar), and `counters/oecd_air_ghg_emissions_counters.csv`.

*   **Data Quality Checks**:
    *   Automated validation via `tools/import_validation/runner.py` evaluates the output against `validation_config.json` (plus global rules in `tools/import_validation/validation_config.json`), enforcing:
        *   `check_deleted_records_percent`: Global historical deletion threshold `<= 0.1%`.
        *   `max_date_consistent_ghg`, `max_date_consistent_air_pollutants`, `max_date_consistent_co2_emissions`: 3 scoped `MAX_DATE_CONSISTENT` rules verifying date consistency within co-released emission series while allowing `CO2_PBPROD` GDP productivity to update independently on its National Accounts PPP release cycle.
        *   `check_non_negative_emissions`: Verifies all emission and productivity observations are `>= 0`.
        *   `check_statvar_count_places_and_freshness`: Verifies rolling `MaxDate` freshness (`MaxDate >= GREATEST(2024, current_year - 4)`, accepting all future years), `total_svs >= 13`, `total_obs >= 35000`, `NumPlaces >= 50`, `NumObservations >= 1500`, and `MinValue >= 0`.

---

## 3. Automated Import

This import is configured for automated weekly execution in `manifest.json`.

### Automated Steps
1. The automated job triggers on cron schedule `30 6 * * 2` configured in `manifest.json`.
2. `download.py` downloads the OECD SDMX-CSV v2.1 feeds and GCS historical baseline CSV directly into `input_files/` and writes `input_files/oecd_air_ghg_emissions_input.csv`.
3. `stat_var_processor.py` processes `input_files/oecd_air_ghg_emissions_input.csv` to generate `output_files/oecd_air_ghg_emissions.csv`, `output_files/oecd_air_ghg_emissions.tmcf`, `output_files/oecd_air_ghg_emissions_stat_vars.mcf`, and `counters/oecd_air_ghg_emissions_counters.csv`.
4. Validation rules in `validation_config.json` are evaluated before publication.

---

## 4. Script Execution Details

To run the import pipeline locally from `statvar_imports/oecd/air_ghg_emissions/` (with Application Default Credentials configured for read access to `gs://unresolved_mcf/`):

### Download and Stage the Data

```bash
python3 download.py
```

### Process the Data

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/oecd_air_ghg_emissions_input.csv \
  --pv_map=oecd_air_ghg_emissions_pvmap.csv \
  --config_file=oecd_air_ghg_emissions_metadata.csv \
  --places_resolved_csv=oecd_air_ghg_emissions_places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/oecd_air_ghg_emissions \
  --output_counters=counters/oecd_air_ghg_emissions_counters.csv
```

### Run Sample Integration Test

Write sample outputs to a temporary directory and verify parity against `test_data/`:

```bash
TMP_OUT="$(mktemp -d)"
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=test_data/sample_input.csv \
  --pv_map=oecd_air_ghg_emissions_pvmap.csv \
  --config_file=oecd_air_ghg_emissions_metadata.csv \
  --places_resolved_csv=oecd_air_ghg_emissions_places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path="${TMP_OUT}/sample_output"
diff -u test_data/sample_output.csv "${TMP_OUT}/sample_output.csv"
diff -u test_data/sample_output.tmcf "${TMP_OUT}/sample_output.tmcf"
rm -rf "${TMP_OUT}"
```

### Run Unit Tests and Linting

From `statvar_imports/oecd/air_ghg_emissions/`:
```bash
python3 -m unittest discover -s . -p "*_test.py" -v
```

Or from the repository root:
```bash
./run_tests.sh -p statvar_imports/oecd/air_ghg_emissions
./run_tests.sh -l
```
