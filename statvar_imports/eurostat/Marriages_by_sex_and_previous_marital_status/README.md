# Eurostat Marriages by sex and previous marital status Import

## Overview
This dataset contains annual marriage statistics at the national level, sourced from Eurostat. The data tracks marital dynamics across European countries, breaking down marriage metrics by sex and the previous marital status of the individuals entering into marriage.

**type of place:** Country
**years:** Historical data to present (1960-2024) 
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/ARM, dcid:country/EST, dcid:country/BEL)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_NMSTA/?format=SDMX-CSV&compressed=false

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It originates from the "Demography, population stock and balance" database under the "Marriages" statistical framework, specifically the "Marriages by sex and previous marital status" (DEMO_NMSTA) dataset.

## Refresh Type
Automatic Refresh
The refresh is automated using the provided run.sh script, which handles both data download and processing.

## How To Run Import
To execute the complete import process (download and processing), run:
./run.sh

### Script Details:
- **Download**: Uses `curl` to fetch the latest SDMX-CSV data from Eurostat's dissemination API.
- **Processing**: Uses `stat_var_processor.py` to map raw data to Data Commons StatVarObservations using the PV map and metadata configuration.

## Key Files
- `run.sh`: Main execution script for download and processing.
- `Marriages_by_sex_and_previous_marital_status_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `Marriages_by_sex_and_previous_marital_status_metadata.csv`: Configuration parameters for the processor.
- `places_resolved.csv`: Mapping of place codes to Data Commons DCIDs.
- `Marriages_by_sex_and_previous_marital_status_output.csv`: Processed statistical observations.
- `Marriages_by_sex_and_previous_marital_status_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint Marriages_by_sex_and_previous_marital_status_output.csv Marriages_by_sex_and_previous_marital_status_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/Marriages_by_sex_and_previous_marital_status_data_raw.csv`
- Expected Output: `test_data/Marriages_by_sex_and_previous_marital_status_output.csv`
- Expected TMCF: `test_data/Marriages_by_sex_and_previous_marital_status_output.tmcf`

## Run the script for test data processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./test_data/Marriages_by_sex_and_previous_marital_status_data_raw.csv" \
  "--pv_map=./Marriages_by_sex_and_previous_marital_status_pvmap.csv" \
  "--config_file=./Marriages_by_sex_and_previous_marital_status_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=./final_output/Marriages_by_sex_and_previous_marital_status_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" 
  
## Run the script for full data processing
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./Marriages_by_sex_and_previous_marital_status_pvmap.csv" \
  "--config_file=./Marriages_by_sex_and_previous_marital_status_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor" \
  "--output_path=./final_output/Marriages_by_sex_and_previous_marital_status_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf" 