### OECD Regional Education

### 1. Import Overview
This project processes and imports regional educational attainment statistics from the OECD (Organisation for Economic Co-operation and Development) via the OECD SDMX REST API (Dataflow 2.5: `OECD.CFE.EDS:DSD_REG_EDU@DF_ATTAIN(2.5)`).

- **Source URL**: `https://stats.oecd.org/Index.aspx?DataSetCode=REGION_EDUCAT`
- **SDMX API Endpoint**: `https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_EDU@DF_ATTAIN,/A.........?dimensionAtObservation=AllDimensions&format=csvfilewithlabels`
- **Import Type**: Automated download via `download_util_script.py` followed by preprocessing in `preprocess.py` and StatVar processing via `stat_var_processor.py`.
- **Source Data Availability**: Annual regional data from 2000 to the latest available year.
- **Type of Place**: Country, State, and NUTS / OECD Territorial Level regions (`TL2` / `TL3`).
- **StatVars**: Educational attainment by age group (`25 to 34 years` and `25 to 64 years`), sex (`Male`, `Female`, and `Total`), and ISCED-2011 education level.

### 2. Preprocessing & Transformation Pipeline

**Input and configuration files:**
- `gcs_output/source_files/A.........`: Raw CSV downloaded from the OECD SDMX API by `download_util_script.py`.
- `oecd_regional_education_places_resolved.csv`: Mapping of OECD `REF_AREA` codes (including Eurostat NUTS 2024 regions) to Data Commons `dcid`s.
- `oecd_regional_education_pvmap.csv`: Property-value mapping for `stat_var_processor.py`.
- `oecd_regional_education_metadata.csv`: Configuration metadata for `stat_var_processor.py`.
- `validation_config.json`: Validation rules, including a 5% deleted records threshold (`DELETED_RECORDS_PERCENT`) to accommodate OECD Dataflow 2.5 NUTS 2024 regional boundary restructuring (e.g., retirement of obsolete NUTS 2021 codes `PT16`, `PT17`, `NL31`, `NL33` and replacement with `PT19`–`PT1D`, `NL35`, `NL36`), `MAX_DATE_CONSISTENT`, freshness lag checks, and StatVar coverage checks.

**Transformation steps (`preprocess.py`):**
1. Loads resolved region mappings (`REF_AREA` -> `dcid`) from `oecd_regional_education_places_resolved.csv` in memory.
2. Reads the raw downloaded OECD SDMX CSV (`A.........`) from `gcs_output/source_files/` while preserving the original downloaded file for provenance.
3. Filters out rows with empty `OBS_VALUE` or standard error rows (`STATISTICAL_OPERATION == 'SE'`).
4. Pre-resolves `REF_AREA` codes to `dcid:` values, extracts the required columns (`REF_AREA`, `TIME_PERIOD`, `UNIT_MULT`, `SEX`, `Education level`, `AGE`, `OBS_VALUE`), and writes the cleaned dataset to `gcs_output/source_files/oecd_regional_education_data.csv`.
5. Logs any unmapped `REF_AREA` codes to `counters/unresolved_places.csv` for observability.

### 3. Autorefresh Schedule

- **Schedule**: Runs automatically every two weeks at 10:00 AM UTC on the 1st and 15th of each month (`0 10 1,15 * *`).
- **Pipeline sequence** (configured in `manifest.json`):
  1. `download_util_script.py`: Downloads the raw SDMX CSV into `gcs_output/source_files/`.
  2. `preprocess.py`: Filters rows and resolves regional place codes into `gcs_output/source_files/oecd_regional_education_data.csv`.
  3. `stat_var_processor.py`: Generates `output/oecd_regional_education.csv`, `output/oecd_regional_education.tmcf`, and StatVar MCFs (`output/*.mcf`), plus counters in `counters/oecd_regional_education_counters.csv`.

### 4. Script Execution Details

All pipeline commands below should be executed from the dataset directory:
```bash
cd statvar_imports/oecd/regional_education
```

**Step 1: Download raw data**
```bash
python3 ../../../util/download_util_script.py \
  --download_url='https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_EDU@DF_ATTAIN,/A.........?dimensionAtObservation=AllDimensions&format=csvfilewithlabels' \
  --output_folder=gcs_output/source_files
```

**Step 2: Run preprocessing**
```bash
python3 preprocess.py
```

**Step 3: Process StatVars and observations**
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=gcs_output/source_files/oecd_regional_education_data.csv \
  --pv_map=oecd_regional_education_pvmap.csv \
  --config_file=oecd_regional_education_metadata.csv \
  --places_resolved_csv=oecd_regional_education_places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output/oecd_regional_education \
  --output_counters=counters/oecd_regional_education_counters.csv
```

### 5. Running Unit Tests

Run the unit test suite from this directory:
```bash
python3 -m unittest preprocess_test.py
```

Or from the root of the repository:
```bash
python3 -m unittest statvar_imports/oecd/regional_education/preprocess_test.py
```

