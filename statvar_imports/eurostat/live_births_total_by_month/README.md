# Eurostat Live Births Total By Month Import

## Overview
This dataset contains monthly live births data at national and regional levels, sourced from Eurostat. The data tracks the total number of live births per month across various European countries and regions.

**type of place:** Country, NUTS Regions (Level 0-3)
**years:** Historical data to present (1960-2025) 
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:nuts/AT113)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/DEMO_FMONTH__custom_270818/default/table?lang=en

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It is part of the "Demography and migration" database, specifically the "Live births by month" (DEMO_FMONTH) dataset.

## Refresh Type
Automatic Refresh

The refresh is automated using the provided `run.sh` script, which handles both data download and processing.

## How To Run Import
To execute the complete import process (download and processing), run:
```bash
./run.sh
```

### Script Details:
- **Download**: Uses `curl` to fetch the latest SDMX-CSV data from Eurostat's dissemination API.
- **Processing**: Uses `stat_var_processor.py` to map raw data to Data Commons StatVarObservations using the PV map and metadata configuration.

## Processing Instructions
To process the Eurostat Live Births data and generate statistical variables, use the following commands from your current import data directory:

Download input file

```bash
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_FMONTH/?format=SDMX-CSV&compressed=false" -o input_files/live_births_total_by_month_data_input.csv
```

For Test Data Run

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./test_data/live_births_total_by_month_data_input.csv" \
  "--pv_map=./live_births_total_by_month_pvmap.csv" \
  "--output_path=./test_data/live_births_total_by_month_output" \
  "--config_file=./live_births_total_by_month_metadata.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

For Main data processing run

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./live_births_total_by_month_pvmap.csv" \
  "--config_file=./live_births_total_by_month_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=output_files/live_births_total_by_month_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

## Key Files
- `run.sh`: Main execution script for download and processing.
- `live_births_total_by_month_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `live_births_total_by_month_metadata.csv`: Configuration parameters for the processor.
- `places_resolved.csv`: Mapping of place codes to Data Commons DCIDs.
- `output_files/live_births_total_by_month_output.csv`: Processed statistical observations.
- `output_files/live_births_total_by_month_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint output_files/live_births_total_by_month_output.csv output_files/live_births_total_by_month_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/live_births_total_by_month_data_input.csv`
- Expected Output: `test_data/live_births_total_by_month_output.csv`
- Expected TMCF: `test_data/live_births_total_by_month_output.tmcf`
