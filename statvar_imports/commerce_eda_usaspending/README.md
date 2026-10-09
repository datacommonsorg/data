# Commerce_EDA_USAspending

This importer fetches and processes U.S. Economic Development Administration (EDA) investment datasets dynamically from USAspending.gov.

- **Source**: [USAspending.gov](https://www.usaspending.gov/) ([API Endpoint](https://api.usaspending.gov/api/v2/search/spending_by_award/))
- **Place Type**: U.S. States and Territories (`AdministrativeArea1`)
- **Time Coverage**: FY 2012 to Present (dynamically fetched by federal fiscal year)
- **Import Type**: Automated API-based import
- **Release Frequency**: Weekly (Mondays 05:30 UTC, `30 05 * * 1`)

## Prerequisites

- Python 3.10+ with `pandas`, `requests`, `urllib3`, and `absl-py` installed (see repository `.env` or `requirements.txt`).
- Outbound HTTPS access to `https://api.usaspending.gov/api/v2/search/spending_by_award/`.

## Important Files

- `manifest.json`: Import automation specification, script sequence, input/output artifact paths (`node_mcf` configured with `investment_schema.mcf` and `output/*.mcf`), and weekly cron schedule (`30 05 * * 1`).
- `process.py`: Fetches EDA award obligations from the USAspending REST API partitioned by fiscal year, deduplicates cross-FY award amendments, excludes net negative de-obligations, and outputs `input_files/investment_cleaned.csv`.
- `process_test.py`: Hermetic unit test suite covering pagination, deduplication, de-obligations, fiscal year calculation, sample fixtures, and error handling.
- `test_data/`: Hermetic sample input (`sample_awards.json`) and expected output (`sample_output.csv`) fixtures for unit testing.
- `investment_pvmap.csv`: Property-value mappings converting state/territory codes, years, and EDA program names into Data Commons schema observations.
- `investment_metadata.csv`: Configuration parameters for `stat_var_processor.py`.
- `investment_schema.mcf`: Schema definitions for new `InvestmentProgramEnum` instances.
- `validation_config.json`: Validation rules (`check_deleted_records_percent`, `active_programs_freshness`, `non_negative_investment_amounts`).

## Pipeline Steps

### 1. Run Tests
Verify unit tests pass from the repository root:
```bash
./run_tests.sh -p statvar_imports/commerce_eda_usaspending
```

### 2. Preprocessing (`process.py`)
Run the Python script from `statvar_imports/commerce_eda_usaspending/` to download all awards from USAspending.gov partitioned by fiscal year and aggregate them into clean tall format:
```bash
python3 statvar_imports/commerce_eda_usaspending/process.py
```
Outputs produced:
- `input_files/raw_usaspending_eda_awards.json`: Raw award JSON payloads from the API.
- `input_files/investment_cleaned.csv`: Aggregated tall format with columns `Place,State or Territory / EDA Program,Year,Value`.

### 3. Statistical Variable Processing
Run Data Commons `stat_var_processor.py` from `statvar_imports/commerce_eda_usaspending/` to generate the final MCF and CSV files for import:
```bash
python3 ../../tools/statvar_importer/stat_var_processor.py \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --input_data=input_files/investment_cleaned.csv \
  --pv_map=investment_pvmap.csv \
  --config_file=investment_metadata.csv \
  --existing_schema_mcf=investment_schema.mcf \
  --output_path=output/investment_output \
  --output_counters=counters/investment_counters.csv
```
Outputs produced:
- `output/investment_output.csv`: Cleaned CSV mapped to Data Commons schema.
- `output/investment_output.tmcf`: Template MCF mapping observation properties.
- `output/investment_output_stat_vars.mcf`: Node MCF for new `StatisticalVariable` entities.
- `counters/investment_counters.csv`: Processing counters and diff statistics.

### 4. Refresh & Validation Procedure
Validate generated outputs against `validation_config.json` from the repository root:
```bash
python3 -m tools.import_validation.runner \
  --validation_config=statvar_imports/commerce_eda_usaspending/validation_config.json \
  --stats_summary=statvar_imports/commerce_eda_usaspending/output/summary_report.csv \
  --lint_report=statvar_imports/commerce_eda_usaspending/output/report.json \
  --differ_output=statvar_imports/commerce_eda_usaspending/output/differ_summary.json \
  --validation_output=statvar_imports/commerce_eda_usaspending/output/validation_output.csv
```

## Data Processing & Methodology
- **Cumulative Award Inception Semantics**: `process.py` queries the USAspending `/api/v2/search/spending_by_award/` endpoint and groups awards by the federal fiscal year of each award's `Start Date` (where October–December maps to `year + 1`), summing the total `Award Amount`. Consequently, multi-year grants and subsequent obligation modifications/amendments are attributed as cumulative lifetime award obligations to the fiscal year of award inception rather than individual annual outlay transactions.
- **Year Partitioning**: API queries are partitioned fiscal-year by fiscal-year up to the current federal fiscal year to prevent USAspending's 10,000-record pagination ceiling.
- **De-obligations**: Award adjustments resulting in net non-positive annual funding for a program in a state are excluded, ensuring State Totals are mathematically consistent with the sum of reported components.
- **Coverage**: Covers all historical and modern EDA programs including CHIPS Act Tech Hubs (11.039), Recompete Pilot (11.040), Science and Research Park Development Grants (11.030), and STEM Talent Challenge (11.023).

