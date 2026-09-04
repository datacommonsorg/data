# Commerce_EDA (USASpending Source)

This importer fetches and processes U.S. Economic Development Administration (EDA) investment datasets dynamically from USASpending.gov.

- **Source**: [USASpending.gov API](https://api.usaspending.gov/)
- **Place Type**: U.S. States and Territories (`AdministrativeArea1`)
- **Time Coverage**: FY 2012 to Present (dynamically fetched up to current year + 1)
- **Import Type**: Automated API-based import
- **Release Frequency**: Continuous / On-demand

## Pipeline Steps

### 1. Preprocessing (`process.py`)
Run the python script to dynamically download all awards from USAspending.gov and pivot/structure them into a clean tall format:
```bash
python3 process.py
```
This writes the formatted data to `output/Investment_cleaned.csv` with columns:
`Place,State or Territory / EDA Program,Year,Value`

### 2. Statistical Variable Processing
Run the Data Commons `stat_var_processor.py` to generate the final MCF and CSV files for import:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/Investment_cleaned.csv \
  --pv_map=Investmentpvmap.csv \
  --config_file=Investmentmetadata.csv \
  --output_path=output/Investment_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_counters=counters/Investment_counters.csv
```

## Generic Updates for Coming Years
- The preprocessing script (`process.py`) dynamically queries the USASpending.gov API up to the current fiscal year + 1.
- `Investmentpvmap.csv` is configured in tall format to resolve years and values generically using `{Number}` and `{Place}` wildcard templates.
- Start and end dates are commented out in `Investmentmetadata.csv` to ensure the importer remains entirely year-agnostic and never needs manual updates as new year records become available.
