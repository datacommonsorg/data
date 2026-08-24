# Commerce_EDA_Poverty (Persistent Poverty Counties)

This importer fetches and processes U.S. Treasury CDFI Fund datasets detailing the list of U.S. counties classified as Persistent Poverty Counties (PPCs).

- **Source**: [CDFI Fund Geographic Reports](https://www.cdfifund.gov/documents/geographic-reports)
- **Place Type**: U.S. Counties and County Equivalents (`County`)
- **Time Coverage**: 1990, 2000, 2021 (based on 1990 Decennial Census, 2000 Decennial Census, and 2016-2020 American Community Survey)
- **Import Type**: Automated download and preprocess
- **Release Frequency**: Decadal / Periodic

## Pipeline Steps

### 1. Preprocessing (`process_poverty.py`)
Run the python script to copy the original Poverty CSV dataset from GCS (`gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv`), clean the columns, format GEOID/FIPS codes, and structure it into a clean format:
```bash
python3 process_poverty.py
```
This writes the formatted data to `output/Poverty_cleaned.csv`.

### 2. Statistical Variable Processing
Run the Data Commons `stat_var_processor.py` to generate the final MCF and CSV files for import:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/Poverty_cleaned.csv \
  --pv_map=Povertypvmap.csv \
  --config_file=Povertymetadata.csv \
  --output_path=output/Poverty_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_counters=counters/Poverty_counters.csv
```

## Future Updates
- The preprocessing script (`process_poverty.py`) copies the source file from GCS. In future release cycles, if the source file in `gs://unresolved_mcf/us_eda/latest/input_files/Poverty.csv` is updated, running the script will automatically process the updated data. If the source portal structure or URL changes, the script may need to be updated to fetch directly from the website.
