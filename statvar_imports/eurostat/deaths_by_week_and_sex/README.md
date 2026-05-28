# Eurostat Deaths By Week And Sex Import

## Overview
This dataset contains weekly death indicators at national and regional levels, sourced from Eurostat. The data tracks the total number of deaths broken down by sex and week across various European countries and regions.

**type of place:** Country, NUTS Regions (Level 0-3)
**years:** Historical data to present (2000-present, recorded weekly e.g., 2000-W01) 
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:nuts/AT113)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/demo_r_mwk_ts/default/table?lang=en

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It belongs to the "Demography, population stock and balance" database under the "Deaths by week - special data collection" statistical theme, specifically the "Deaths by week and sex" (DEMO_R_MWK_TS) dataset.

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
- `deaths_by_week_and_sex_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `deaths_by_week_and_sex_metadata.csv`: Configuration parameters for the processor.
- `places_resolved_runtime.csv`: Mapping of place codes to Data Commons DCIDs.
- `deaths_by_week_and_sex_output.csv`: Processed statistical observations.
- `deaths_by_week_and_sex_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.

## Validation
To validate the generated data, use the Data Commons import tool (lint mode):
```bash
java -jar datacommons-import-tool.jar lint deaths_by_week_and_sex_output.csv deaths_by_week_and_sex_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Raw Input: `test_data/deaths_by_week_and_sex_data_raw.csv`
- Expected Output: `test_data/deaths_by_week_and_sex_output.csv`
- Expected TMCF: `test_data/deaths_by_week_and_sex_output.tmcf`
