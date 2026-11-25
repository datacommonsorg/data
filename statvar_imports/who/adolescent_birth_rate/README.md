# WHO Adolescent Birth Rate Import

## Overview
This dataset contains national and regional-level statistics for the Adolescent Birth Rate (per 1,000 women).
Specifically, it provides data for two distinct age groups:
- 10-14 years (Y10T14)
- 15-19 years (Y15T19)

**type of place:** Country, Region (M49 codes), WHO Regions, Overseas Territory, Special Administrative Regions
**years:** 2000 to 2024
**place_resolution:** Resolved to DCIDs (e.g., dcid:country/FRA, dcid:europe, dcid:LatinAmericaAndCaribbean)

## Data Source
**Source URL:**
https://data.who.int/indicators/i/24C65FE/27D371A

**Provenance Description:**
The data comes from the World Health Organization (WHO). It specifically tracks Sustainable Development Goal (SDG) Indicator 3.7.2, measuring the adolescent birth rate (per 1,000 women aged 10–14 and 15–19) globally across different geographic classifications.

## Refresh Type
Automatic Refresh

For refresh of the data, the import includes a Python script (`data_download.py`) to automatically download the complete historical dataset directly from the WHO's backend Azure Blob storage endpoint (`requests.Session` with `urllib3.util.retry.Retry` exponential backoff on transient HTTP `429`/`5xx` and network/stream errors, failing immediately on permanent `4xx` responses).

## Data Publish Frequency
Release Frequency = Annual

## How To Download Input Data
To download the data, run the provided script from the `adolescent_birth_rate` directory:
```bash
python3 data_download.py
```

This fetches the latest full dataset, validates UTF-8 encoding and CSV structure, normalizes integer-mantissa scientific-notation values in `RATE_PER_1000_N` (for example, `4e-09` → `4.0e-09`) so `stat_var_processor.py` (`mcf_file_util.get_numeric_value`) parses them as floating-point values instead of misinterpreting those rows as section headers, and writes the result atomically to `input_files/adolescent_birth_rate_input.csv`.

### Optional CLI Flags
- `--indicator_id`: WHO indicator ID used to build the default Azure Blob CSV URL (default: `27D371A`).
- `--input_url`: Explicit source CSV URL override; takes precedence over `--indicator_id` when set (default: `""`).
- `--output_dir`: Directory where `adolescent_birth_rate_input.csv` is written (default: `input_files`).

## Processing Instructions
To process the WHO Adolescent Birth Rate data and generate statistical variables, use the following command from the `adolescent_birth_rate` directory:

**For Data Run**
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=input_files/* \
    --pv_map=adolescent_birth_rate_pvmap.csv \
    --output_path=adolescent_birth_rate_output \
    --config_file=adolescent_birth_rate_metadata.csv
```

This generates the following output files:
- adolescent_birth_rate_output.csv
- adolescent_birth_rate_output_stat_vars_schema.mcf
- adolescent_birth_rate_output_stat_vars.mcf
- adolescent_birth_rate_output.tmcf

**For Data Quality Checks and validation**
Validation of the data is done using the lint flag in the DataCommons import tool
```bash
java -jar datacommons-import-tool-0.1-jar-with-dependencies.jar lint adolescent_birth_rate_output_stat_vars_schema.mcf adolescent_birth_rate_output.csv adolescent_birth_rate_output.tmcf adolescent_birth_rate_output_stat_vars.mcf
```

This generates the following output files:
- report.json
- summary_report.csv
- summary_report.html

The report files can be analyzed to check for errors and warnings. Further, linting is performed on the generated output files using the DataCommons import tool.

## Testing
To run the download unit tests (`data_download_test.py`) from the repository root:
```bash
./run_tests.sh -p statvar_imports/who/adolescent_birth_rate/
```
*(Repo-wide discovery via `./run_tests.sh -p statvar_imports` also runs this suite.)*

End-to-end processor fixtures are provided in the `test_data` directory:
- Input: `test_data/adolescent_birth_rate_input.csv`
- Output (expected): `test_data/adolescent_birth_rate_output.csv`
- MCF (expected): `test_data/adolescent_birth_rate_output.tmcf`
