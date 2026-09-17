# World Bank Datasets (`WorldBankDatasets`)

This import ingests data across multiple World Bank databases (including World Development Indicators, Jobs, and Education Statistics) from the [World Bank DataBank](https://databank.worldbank.org/source/world-development-indicators).

## Workflow

1. **Download (`download.py`)**: Downloads bulk CSV archives from the World Bank API/DataBank into `gcs_output/input_files/`.
2. **Process (`process.py`)**:
   - Transforms raw World Bank CSV files into `gcs_output/output/transformed_data_for_all_final.csv`, mapping countries via `places.csv` and units via `statvars.csv`.
   - Merges and deduplicates previously deleted historical observations from GCS (`--historical_gcs_path`, defaulting to `gs://unresolved_mcf/world_bank/datasets/deleted_historical_data_06_2026.csv`), prioritizing fresh observations (`keep='first'`) when composite keys (`indicatorcode, statvar, measurementmethod, observationabout, observationdate, unit`) match.
   - Copies retained historical BigQuery exports (`bq-results-20250423.csv`) into `gcs_output/output/`.
3. **Validation (`validation_config.json`)**:
   - Enforces a maximum `0.1%` deleted records threshold (`DELETED_RECORDS_PERCENT`).
   - Validates data freshness (`check_max_date_freshness`) via `SQL_VALIDATOR` to verify non-projected WDI series include recent observations (`MaxDate >= 2024`).

## Running Tests

```bash
python3 -m unittest scripts/world_bank/datasets/process_test.py
```
