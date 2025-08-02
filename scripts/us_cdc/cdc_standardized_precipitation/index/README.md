# Standardized Precipitation Index (SPI) - CDC Import

## Automation and Import Pipeline
The data ingestion process is fully (Auto Refresh) automated using a serverless architecture on Google Cloud.

## Overview
This repository manages the automated ingestion of the **Standardized Precipitation Index (SPI)** dataset from the [Centers for Disease Control and Prevention (CDC)](https://data.cdc.gov). The pipeline is designed for full, unattended auto-refreshes to ensure the data is consistently updated for the [Data Commons Knowledge Graph](https://datacommons.org).

## Dataset Summary
- **Source:** CDC - National Environmental Public Health Tracking Network
- **URL:** [CDC SPI Dataset](https://data.cdc.gov/resource/xbk2-5i4e.csv)
- **Refresh Status:** Fully automated periodic refreshes.
- **Variable:** Standardized Precipitation Index (SPI)
- **Geography:** County-level (USA)
- **Time Coverage:** Varies by county.


1.  **Scheduled Execution**: A Google Cloud Scheduler job triggers the import on a regular, predefined schedule, ensuring that the data remains current without manual intervention.
2.  **Containerized Processing**: The trigger invokes a Cloud Run job, which executes the import logic within a Docker container. This environment is defined by the `Dockerfile` and configured via `manifest.json`.
3.  **Data Download**: The `download_script.py <import name>` script runs first, fetching the latest dataset from the CDC's API endpoint.
4.  **Data Parsing**: Next, `parse_precipitation_index.py` processes the raw downloaded data, cleanses and transforms it into the required format, and resolves geographic identifiers.
5.  **Schema Mapping**: The transformed data is mapped to the Data Commons schema using the `StandardizedPrecipitationIndex.tmcf` template.
6.  **Validation and Import**: The `datacommons-import-tool` lints the processed files and imports the final data into the Data Commons Knowledge Graph. The entire process is managed by the `run_import.sh` script.

This end-to-end automation ensures a reliable and hands-off approach to maintaining the dataset's freshness and accuracy.

## Data Download
To download the data:
```bash
python3 download_script.py --import_name=CDC_StandardizedPrecipitationIndex \
    --config_file=import_configs.json
```
## Testing
To run the parsing logic locally for development or testing:
```bash
python3 parse_precipitation_index.py \
  CDC_StandardizedPrecipitationIndex_input.csv \
  output/CDC_StandardizedPrecipitationIndex_output.csv


To manually trigger a cloud deployment of the import job:
```bash
./run_import.sh \
  -p <gcp-project-id> \
  -d <instance-name> \
  -cloud \
  -a <artifact-registry-path> \
  scripts/us_cdc/cdc_standardized_precipitation/index/manifest.json
```

## References
- [CDC Dataset Portal](https://data.cdc.gov)