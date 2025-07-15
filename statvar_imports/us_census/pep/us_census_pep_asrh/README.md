# USCensusPEP_AgeSexRaceHispanicOrigin Import

This script downloads and processes the USCensusPEP_AgeSexRaceHispanicOrigin dataset, covering years from 2020 up to the latest release.

- **Source**: [U.S. Census Bureau](https://www.census.gov/)
- **Place Types**: Country, State, County
- **Statvars**: Demographics
- **Years**: 2020 to 2024 (Note: Data from 1980-2019 is preserved as historical data, as the source now only provides data from 2020 onwards).

---

## How to Use

### 1. Download Data

The `pep_asrh_download_script.py` script downloads data from the source website and places it into the specified output folder.

**Command:**
```bash
python3 pep_asrh_download_script.py --start_year=2030 --url_path_base_year=2020 --input_path=input_files
```

**Arguments:**
-   `--input_path`: Directory to store downloaded files (default: `input_files`).
-   `--start_year`: The first year to search for data (inclusive, default: `2030`).
-   `--url_path_base_year`: The base year used in the source URL path structure (e.g., '2020' in '.../2020-{YEAR}/...').

### 2. Process Data

After downloading, use the `stat_var_processor.py` script to process the raw data.

**Generic Command:**
```bash
python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pvmap_file>.csv --config=<metadata_file>.csv --output_path=<output_path>
```

**Example (County Level):**
```bash
python3 stat_var_processor.py \
    --input_data=input_files/county/*.csv \
    --pv_map=pep_asrh_county_pvmap.csv \
    --config=pep_asrh_county_metadata.csv \
    --output_path=output/county/pep_asrh
```
*Note: The config and pvmap files for other geographic levels are available in the same folder. Adjust the command accordingly.*

---

## Future Improvements & TODOs : b/431970934

-   **Make Shard Count Configurable**: The file shard count is currently hardcoded (e.g., as 11). This should be converted to a configurable parameter to accommodate potential changes in the source data structure.
-   **Dynamic End Year**: The end year for the download should be made configurable or derived automatically from the current date rather than being hardcoded. This would make the script more robust over time.
-   **Remove Statvar Remapping**: The script currently uses `pep_asrh_remap.csv` to remap statvar DCIDs. This step should be removed once the underlying schema cleanup is complete.
-   **Remove Statvar Remapping**: The variable "YEAR" is used in captial letter need to make it small letter