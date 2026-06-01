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
- `output_pvmap_cleaned.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `output_metadata.csv`: Configuration parameters for the processor.
- `places_resolved_runtime.csv`: Mapping of place codes to Data Commons DCIDs.
- `output.csv`: Processed statistical observations.
- `output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint output.csv output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/Marriages_by_sex_and_previous_marital_status_data_raw.csv`
- Expected Output: `test_data/output.csv`
- Expected TMCF: `test_data/output.tmcf`
