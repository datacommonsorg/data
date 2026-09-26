# Opportunity Insights: The Opportunity Atlas Outcomes (`OpportunityInsightsOutcomes`)

This import migrates the legacy `google3` Borg import (`//depot/google3/datacommons/mcf/oi_v3/opportunity_atlas_outcomes_v2.py`) to `stat_var_processor.py`.

## Source Data
* **Provider:** Opportunity Insights (https://opportunityinsights.org/data/)
* **Source Files (`raw_data/`):**
  * `commuting_zone_outcomes.csv` (`geoId/cz{cz:05d}`)
  * `county_outcomes.csv` (`geoId/{state:02d}{county:03d}`)
  * `tract_outcomes.csv` (`geoId/{state:02d}{county:03d}{tract:06d}`, including the 72 `kfi_*` and `kii_*` dollar-level income columns)
  * `tract_outcomes_late_simple.csv` (1984–1989 cohort refresh)
  * `county_by_cohort_outcomes.csv` (1978–1992 annual birth cohorts)
  * `cz_by_cohort_outcomes.csv` (1978–1992 annual birth cohorts)

## Pipeline Steps
1. **Download and extract raw CSVs into `raw_data/`:**
   ```bash
   python3 download.py
   ```
2. **Resolve headers and prepare sharded CSV inputs (`input_files/` and `output/output_part_*.csv`):**
   ```bash
   python3 preprocess.py
   ```
3. **Run `stat_var_processor.py` to generate final MCF, TMCF, CSVs, and counters:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="input_files/*_cleaned.csv" \
     --pv_map=pvmap.csv \
     --config_file=metadata.csv \
     --output_path=output/output \
     --output_counters=counters/output_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

## Testing & Generating Expected Test Outputs

Sample raw inputs (100 rows per file) are located under `test_data/raw_data/`, mirroring the regular directory layout (`test_data/raw_data/`, `test_data/input_files/`, `test_data/output/`, `test_data/counters/`).

Run all commands below from `data/statvar_imports/opportunity_insights_outcomes/`:

1. **Run `preprocess.py` on `test_data/raw_data` to generate `test_data/input_files/*_cleaned.csv` and `test_data/output/output_part_*.csv`:**
   ```bash
   python3 preprocess.py \
     --input_dir=test_data/raw_data \
     --shard_dir=test_data/input_files \
     --sv_output_prefix=test_data/output/output \
     --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
   ```

2. **Run `stat_var_processor.py` to generate `test_data/output/output.csv`, `test_data/output/output.tmcf`, `test_data/output/output_stat_vars.mcf`, and `test_data/counters/output_counters.csv`:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="test_data/input_files/*_cleaned.csv" \
     --pv_map=pvmap.csv \
     --config_file=metadata.csv \
     --output_path=test_data/output/output \
     --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
   ```

3. **Run unit and integration tests:**
   ```bash
   python3 download_test.py
   ```

