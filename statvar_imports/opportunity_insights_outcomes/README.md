# Opportunity Insights: The Opportunity Atlas Outcomes (`OpportunityInsightsOutcomes`)

This import migrates the legacy `google3` Borg import (`//depot/google3/datacommons/mcf/oi_v3/opportunity_atlas_outcomes_v2.py`) to `stat_var_processor.py`.

## Source Data
* **Provider:** Opportunity Insights (https://opportunityinsights.org/data/)
* **CNS Raw Files:** `/cns/jv-d/home/datcom/opportunity_insights/opportunity_atlas/`
  * `commuting_zone_outcomes.csv` (`geoId/cz{cz:05d}`)
  * `county_outcomes.csv` (`geoId/{state:02d}{county:03d}`)
  * `tract_outcomes.csv` (`geoId/{state:02d}{county:03d}{tract:06d}`)

## Pipeline Steps
1. **Preprocess wide CSV files into normalized observation rows:**
   ```bash
   python3 preprocess.py --input_dir=raw_data --output_dir=input_files
   ```
2. **Run `stat_var_processor.py`:**
   ```bash
   python3 ../../tools/statvar_importer/stat_var_processor.py \
     --input_data="input_files/*_outcomes_cleaned.csv" \
     --pv_map=pv_map/opportunity_insights_outcomes_pvmap.csv \
     --config_file=pv_map/opportunity_insights_outcomes_metadata.csv \
     --output_path=output_files/opportunity_insights_outcomes \
     --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```
