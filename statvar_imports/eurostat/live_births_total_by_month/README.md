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

## Key Files
- `run.sh`: Main execution script for download and processing.
- `Live_births_total_by_month_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `Live_births_total_by_month_metadata.csv`: Configuration parameters for the processor.
- `places_resolved.csv`: Mapping of place codes to Data Commons DCIDs.
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
- Raw Input: `test_data/live_births_total_by_month_data_raw.csv`
- Expected Output: `test_data/live_births_total_by_month_output.csv`
- Expected TMCF: `test_data/live_births_total_by_month_output.tmcf`
