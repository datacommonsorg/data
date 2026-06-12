# Eurostat Unemployment by sex and age - monthly data Import

## Overview
The data is provided by Eurostat, the statistical office of the European Union. It belongs to the Labour market database under the Employment and unemployment (Labour force survey) statistical theme, specifically the Unemployment by sex and age - monthly data (UNE_RT_M) dataset.

**type of place:** Country, NUTS Regions
**years:** 1983-01 - 2026-05
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:nuts/AT11)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/une_rt_m/default/table?lang=en

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It belongs to the "Labour market" database under the "Employment and unemployment (Labour force survey)" statistical theme, specifically the "Unemployment by sex and age - monthly data" (UNE_RT_M) dataset.

## Refresh Type
Automatic Refresh

The refresh is automated using the provided `run.sh` script, which handles both data download and processing.

## How To Run Import
To execute the complete import process (download and processing), run:
./run.sh

### Script Details:
- **Download**: Uses `curl` to fetch the latest SDMX-CSV data from Eurostat's dissemination API.
- **Processing**: Uses `stat_var_processor.py` to map raw data to Data Commons StatVarObservations using the PV map and metadata configuration.

## Key Files
- `run.sh`: Main execution script for download and processing.
- `unemployment_by_sex_and_age_monthly_data_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `unemployment_by_sex_and_age_monthly_data_metadata.csv`: Configuration parameters for the processor.
- `places_resolved.csv`: Mapping of place codes to Data Commons DCIDs.
- `unemployment_by_sex_and_age_monthly_data_output.csv`: Processed statistical observations.
- `unemployment_by_sex_and_age_monthly_data_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint unemployment_by_sex_and_age_monthly_data_output.csv unemployment_by_sex_and_age_monthly_data_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/unemployment_by_sex_and_age_monthly_data_data_raw.csv`
- Expected Output: `test_data/unemployment_by_sex_and_age_monthly_data_output.csv`
- Expected TMCF: `test_data/unemployment_by_sex_and_age_monthly_data_output.tmcf`

## Run to Process the test data
python3 tools/statvar_importer/stat_var_processor.py \
  "--input_data=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/test_data/unemployment_by_sex_and_age_monthly_data_data_raw.csv" \
  "--pv_map=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/unemployment_by_sex_and_age_monthly_data_pvmap.csv" \
  "--config_file=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/unemployment_by_sex_and_age_monthly_data_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit,scalingFactor" \
  "--output_path=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/final_output/unemployment_by_sex_and_age_monthly_data_output" \
  "--places_resolved_csv=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"

## Run to Process the full data
python3 tools/statvar_importer/stat_var_processor.py \
  "--input_data=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/unemployment_by_sex_and_age_monthly_data_data_raw.csv" \
  "--pv_map=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/unemployment_by_sex_and_age_monthly_data_pvmap.csv" \
  "--config_file=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/unemployment_by_sex_and_age_monthly_data_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit,scalingFactor" \
  "--output_path=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/final_output/unemployment_by_sex_and_age_monthly_data_output" \
  "--places_resolved_csv=statvar_imports/eurostat/unemployment_by_sex_and_age_monthly_data/places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
