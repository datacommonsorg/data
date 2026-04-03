# WHO Tuberculosis Estimated Incidence Rate Import

## Overview
This dataset contains national-level statistics for the Estimated Tuberculosis Incidence Rate (per 100,000 population).
Specifically, it provides incidence rates for two categories:
- Overall TB incidence
- HIV-positive TB incidence

The generated statistical variables capture the incidence rate for these conditions.
Examples of the statvars generated:
- `dcid:Count_MedicalConditionIncident_ConditionTuberculosis_AsAFractionOf_Count_Person`
- `dcid:Count_MedicalConditionIncident_ConditionTuberculosisAndHIV_AsAFractionOf_Count_Person`

**type of place:** Country, Region (M49 codes), WHO Regions, Overseas Territory, Special Administrative Regions
**years:** 2000 to 2024
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:country/IND)

## Data Source
**Source URL:**
https://data.who.int/indicators/i/EB68992/2674B39

**Provenance Description:**
The data comes from the World Health Organization (WHO) master database and the public API. It tracks the estimated TB incidence rate globally (Indicator ID: `EB689922674B39`).

## Refresh Type
Automatic Refresh

For refresh of the data, the import includes a Python script (`tb_data_download.py`) to automatically fetch the data from the WHO API, join it with ISO3 geographic identifiers, and save the formatted CSV.

## Data Publish Frequency
Release Frequency = Annual

## How To Download Input Data
To download the data, run the provided script:
```bash
python3 tb_data_download.py
```
This will fetch the latest full dataset, process the ISO3 codes, and save it locally as `input_files/Estimated_incidence_rate_per_100_000_population.csv` making it available for stat var processing.

## Processing Instructions
To process the WHO Tuberculosis Incidence Rate data and generate statistical variables, use the following command from the import directory:

**For Data Run**
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=input_files/* \
    --pv_map=tuberculosis_estimated_incidence_rate_pvmap.csv \
    --output_path=tuberculosis_estimated_incidence_rate_output \
    --config_file=tuberculosis_estimated_incidence_rate_metadata.csv
```

This generates the following output files:
- tuberculosis_estimated_incidence_rate_output.csv
- tuberculosis_estimated_incidence_rate_output_stat_vars_schema.mcf
- tuberculosis_estimated_incidence_rate_output_stat_vars.mcf
- tuberculosis_estimated_incidence_rate_output.tmcf

**For Data Quality Checks and validation**
Validation of the data is done using the lint flag in the DataCommons import tool.

```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar lint tuberculosis_estimated_incidence_rate_output_stat_vars_schema.mcf tuberculosis_estimated_incidence_rate_output.csv tuberculosis_estimated_incidence_rate_output.tmcf tuberculosis_estimated_incidence_rate_output_stat_vars.mcf
```

This generates the following output files:
- report.json
- summary_report.csv
- summary_report.html

The report files can be analyzed to check for errors and warnings. Further, linting is performed on the generated output files using the DataCommons import tool.

## Testing
Testing is performed using the provided `test_data` directory:
- Input: `test_data/tuberculosis_estimated_incidence_rate_input.csv`
- Output (expected): `test_data/tuberculosis_estimated_incidence_rate_output.csv`
- MCF (expected): `test_data/tuberculosis_estimated_incidence_rate_output.tmcf`
