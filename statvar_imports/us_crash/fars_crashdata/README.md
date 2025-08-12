# FARS_CrashData Import

This script downloads and processes the FARS_CrashData dataset, covering years from 2021 up to the latest release.

- **Source**: [National Highway Traffic Safety Administration](https://www.nhtsa.gov/file-downloads?p=nhtsa/downloads/FARS/)
- **Place Types**: Country, State, County
- **Statvars**: Demographics
- **Years**: 2021 to 2023 (Note: Data from 1975-2020 is preserved as historical data).

---

## How to Use

### 1. Download Data

The `download_script.py` script downloads data from the source website and places it into the specified output folder.

**Command:**
```bash
python3 download_script.py
```


### 2. Process Data

After downloading, use the `run.sh` script to process the raw data. It contains and triggers the stat_var_processor command.

**Generic Command:**
```bash
sh run.sh
```
OR
```bash
python3 stat_var_processor.py --input_data=<input_file>.csv --pv_map=<pvmap_file>.csv --config_file=<metadata_file>.csv --output_path=<output_path>
```

**Example:**
```bash
python3 stat_var_processor.py \
        --input_data=gcs_output/input_files/*.csv \
        --pv_map=fars_crash_pvmap.csv \
        --config_file=fars_crash_metadata.csv \
        --output_path=gcs_output/output/fars_crash
```
### 3. Import Type : Fully autorefresh

It's a fully automated import, with autorefresh enabled.

---

