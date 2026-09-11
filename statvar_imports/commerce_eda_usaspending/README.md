# Commerce_EDA (USASpending Source)

This importer fetches and processes U.S. Economic Development Administration (EDA) investment datasets dynamically from USASpending.gov.

- **Source**: [USASpending.gov API](https://api.usaspending.gov/)
- **Place Type**: U.S. States and Territories (`AdministrativeArea1`)
- **Time Coverage**: FY 2012 to Present (dynamically fetched by fiscal year up to current year + 1)
- **Import Type**: Automated API-based import
- **Release Frequency**: Weekly (Mondays 05:30 UTC)

## Pipeline Steps

### 1. Run Tests
Verify unit tests pass from the repository root:
```bash
python3 -m unittest statvar_imports/commerce_eda_usaspending/process_test.py
```

### 2. Preprocessing (`process.py`)
Run the Python script from `statvar_imports/commerce_eda_usaspending/` to download all awards from USAspending.gov partitioned by fiscal year and aggregate them into clean tall format:
```bash
python3 process.py
```
Outputs produced:
- `output/raw_usaspending_eda_awards.json`: Raw award JSON payloads from the API.
- `output/Investment_cleaned.csv`: Aggregated tall format with columns `Place,State or Territory / EDA Program,Year,Value`.

### 3. Statistical Variable Processing
Run Data Commons `stat_var_processor.py` to generate the final MCF and CSV files for import:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --input_data=output/Investment_cleaned.csv \
  --pv_map=Investmentpvmap.csv \
  --config_file=Investmentmetadata.csv \
  --output_path=output/Investment_output \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_counters=counters/Investment_counters.csv
```
Outputs produced:
- `output/Investment_output.csv`: Cleaned CSV mapped to Data Commons schema.
- `output/Investment_output.tmcf`: Template MCF mapping observation properties.
- `output/Investment_output.mcf`: Node MCF for new StatisticalVariable entities.
- `counters/Investment_counters.csv`: Processing counters and diff statistics.

## Data Processing & Methodology
- **Year Partitioning**: API queries are partitioned fiscal-year by fiscal-year to prevent USAspending's 10,000-record pagination ceiling.
- **De-obligations**: Award adjustments resulting in net non-positive annual funding for a program in a state are excluded, ensuring State Totals are mathematically consistent with the sum of reported components.
- **Coverage**: Covers all historical and modern EDA programs including CHIPS Act Tech Hubs (11.039), Recompete Pilot (11.040), Good Jobs Challenge (11.030), and STEM Talent Challenge (11.023).
