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
1. **Download raw CSVs and shard wide CSVs for `stat_var_processor.py`:**
   ```bash
   python3 download.py
   ```
2. **Run `stat_var_processor.py` to generate final MCF, TMCF, CSVs, and counters:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="input_files/*_cleaned.csv" \
     --pv_map=pvmap.csv \
     --config_file=metadata.csv \
     --output_path=output/output \
     --output_counters=counters/output_counters.csv \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```
