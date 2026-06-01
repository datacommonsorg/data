# Eurostat Marriage Indicators Import

## Overview
This dataset contains annual marriage indicators at the national level, sourced from Eurostat. The data tracks various metrics including total marriages, crude marriage rates, mean age at first marriage, and total first marriage rates across various European countries.

**type of place:** Country
**years:** Historical data to present (1960-2024) 
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/ARM, dcid:country/EST)

## Data Source
**Source URL:**
https://ec.europa.eu/eurostat/databrowser/view/DEMO_NIND/default/table?lang=en

**Provenance Description:**
The data is provided by Eurostat, the statistical office of the European Union. It is part of the "Demography and migration" database, specifically the "Marriage indicators" (DEMO_NIND) dataset.

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
- `marriage_indicators_pvmap.csv`: Property-Value mapping for StatVar definitions and dimensions.
- `marriage_indicators_metadata.csv`: Configuration parameters for the processor.
- `places_resolved_runtime.csv`: Mapping of place codes to Data Commons DCIDs.
- `marriage_indicators_output.csv`: Processed statistical observations.
- `marriage_indicators_output.tmcf`: Template MCF mapping the CSV columns to Data Commons schema.


## Validation
To validate the generated data, use the Data Commons import tool (lint mode). Note that you must include the StatVar MCF files to resolve schema references:
```bash
java -jar datacommons-import-tool.jar lint marriage_indicators_output.csv marriage_indicators_output.tmcf
```
The resulting reports (`report.json`, `summary_report.html`) in `dc_generated/` provide detailed insights into data quality and validation status.

## Testing
Testing is performed using the `test_data` directory:
- Expected Output: `marriage_indicators_output.csv`
- Expected TMCF: `marriage_indicators_output.tmcf`
