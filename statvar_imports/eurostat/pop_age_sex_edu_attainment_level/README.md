# Eurostat Population on 1 January by Age, Sex, and Educational Attainment Level Import

## Overview
This dataset contains annual population data on January 1st, broken down by age groups, sex, and highest level of education completed, sourced from Eurostat.

**type of place:** Country, NUTS Regions
**years:** 2007 to 2025
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:nuts/AT11)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/DEMO_PJANEDU/default/table?lang=en

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It is part of the "Demography and migration" database, specifically the "Population on 1 January by age, sex and educational attainment level" (DEMO_PJANEDU) dataset.

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
To process the Population on 1 January by Age, Sex, and Educational Attainment Level Import and generate statistical variables, use the following commands from your current import data directory:

Download input file

```bash
mkdir -p input_files
curl -L --retry 3 "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/DEMO_PJANEDU/?format=SDMX-CSV&compressed=false" -o ./input_files/pop_age_sex_edu_attainment_level_input.csv
```

For Test Data Run

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./test_data/pop_age_sex_edu_attainment_level_input.csv" \
  "--pv_map=./pop_age_sex_edu_attainment_level_pvmap.csv" \
  "--output_path=./test_data/pop_age_sex_edu_attainment_level_output" \
  "--config_file=./pop_age_sex_edu_attainment_level_metadata.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

For Main data processing run

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  "--input_data=./input_files/*.csv" \
  "--pv_map=./pop_age_sex_edu_attainment_level_pvmap.csv" \
  "--config_file=./pop_age_sex_edu_attainment_level_metadata.csv" \
  "--generate_statvar_name=True" \
  "--skip_constant_csv_columns=False" \
  "--output_columns=observationDate,observationAbout,variableMeasured,value,observationPeriod,unit" \
  "--output_path=./pop_age_sex_edu_attainment_level_output" \
  "--places_resolved_csv=./places_resolved.csv" \
  "--existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

## Key Files
- `run.sh`: Main execution script for download and processing.
- `pop_age_sex_edu_attainment_level_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `pop_age_sex_edu_attainment_level_metadata.csv`: Configuration parameters for the processor.
- `places_resolved.csv`: Mapping of place codes to Data Commons DCIDs.
- `pop_age_sex_edu_attainment_level_output.csv`: Processed statistical observations.
- `pop_age_sex_edu_attainment_level_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint pop_age_sex_edu_attainment_level_output.csv pop_age_sex_edu_attainment_level_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/pop_age_sex_edu_attainment_level_input.csv`
- Expected Output: `test_data/pop_age_sex_edu_attainment_level_output.csv`
- Expected TMCF: `test_data/pop_age_sex_edu_attainment_level_output.tmcf`
