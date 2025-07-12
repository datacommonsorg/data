---

```markdown
# Standardized Precipitation Evapotranspiration Index (SPEI) - CDC Import

## Overview

This repository manages the ingestion of the **Standardized Precipitation Evapotranspiration Index (SPEI)** dataset from the [Centers for Disease Control and Prevention (CDC)](https://data.cdc.gov). The goal is to structure this dataset for inclusion in the [Data Commons Knowledge Graph](https://datacommons.org), enabling better accessibility and analysis of environmental health data.

---

## Dataset Summary

- **Source:** CDC - National Environmental Public Health Tracking Network  
- **URL:** [CDC SPEI Dataset](https://data.cdc.gov/resource/6nbv-ifib.csv)
- **Refresh Status:** Static dataset with auto-refresh framework prepared.
- **Variable:** Standardized Precipitation Evapotranspiration Index (SPEI)
- **Geography:** County-level (USA)
- **Time Coverage:** Varies by county, primary issue with year ranges being addressed.

---

## Import Pipeline Stages

1. **Download**
   - Utilizes `requests` to fetch data via CDC API endpoint.
   - Input file saved as: `CDC_StandardizedPrecipitationEvapotranspirationIndex_input.csv`

2. **Parsing**
   - `parse_precipitation_index.py` processes the raw input.
   - Output file: `CDC_StandardizedPrecipitationEvapotranspirationIndex_output.csv`
   - Handles normalization, year formatting, and identifier resolution.

3. **TMCF Mapping**
   - Template MCF defined in `StandardizedPrecipitationEvapotranspirationIndex.tmcf`
   - Maps fields to DC schema (e.g., `observationDate`, `observationAbout`, `value`)

4. **Linting**
   - The import is linted using `datacommons-import-tool`.
   - **Current Issue:** `lint` reports a failure related to missing or invalid year range in the dataset. This is under investigation and similar to a previously known issue.

5. **Cloud Deployment**
   - Uses `run_import.sh` to deploy to Cloud Run with Docker support.
   - Cloud project: `datcom prod imports`
   - Docker artifact registry: `us-central1-docker.pkg.dev/datcom prod imports/...`
   - Validation skipping supported via `INVOKE_IMPORT_VALIDATION=false`

---

## Testing

To run parsing locally:

```bash
python3 parse_precipitation_index.py \
  CDC_StandardizedPrecipitationEvapotranspirationIndex_input.csv \
  output/CDC_StandardizedPrecipitationEvapotranspirationIndex_output.csv
````

To deploy import job (with validation disabled):

```bash
./run_import.sh \
  -p datcom-infosys-dev \
  -d dc-test-executor-$USER \
  -cloud \
  -e "INVOKE_IMPORT_VALIDATION=false" \
  -a us-central1-docker.pkg.dev/datcom-infosys-dev/datcom-infosys-dev-artifacts \
  ../../scripts/us_cdc/environmental/manifest.json
```


## References

* [CDC Dataset Portal](https://data.cdc.gov)

---

