# NZ_International_Migration

## Overview
Imports New Zealand international migration estimates (citizenship by visa by country of last permanent residence) published by Stats NZ.

- **Source URL**: https://www.stats.govt.nz/large-datasets/csv-files-for-download/
- **Direct CSV URL**: https://www.stats.govt.nz/assets/Uploads/International-migration/International-migration-August-2026/Download-data/international-migration-august-2026-citizenship-by-visa-by-country-of-last-permanent-residence.csv
- **License**: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)
- **Place Coverage**: New Zealand (`country/NZL`)
- **Release Frequency**: Weekly

## Important Files
- `manifest.json`: Import automation specification.
- `pvmap.csv`: Property-value mappings for columns in the source CSV.
- `metadata.csv`: Configuration parameters for `stat_var_processor.py`.
- `places_resolved.csv`: Place name to Data Commons DCID mapping.
- `testdata/`: Sample input CSV (`test_input.csv`) and expected processor outputs (`.csv`, `.tmcf`, `_stat_vars.mcf`).

## How to Run

From `statvar_imports/statistics_new_zealand/international_migration`:

### 1. Download Data
```bash
python3 ../../../util/download_util_script.py \
  --download_url=https://www.stats.govt.nz/assets/Uploads/International-migration/International-migration-August-2026/Download-data/international-migration-august-2026-citizenship-by-visa-by-country-of-last-permanent-residence.csv \
  --output_folder=input_files
```

### 2. Process Data
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=input_files/international-migration-august-2026-citizenship-by-visa-by-country-of-last-permanent-residence.csv \
  --pv_map=pvmap.csv \
  --config_file=metadata.csv \
  --places_resolved_csv=places_resolved.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
  --output_path=output_files/nz_international_migration \
  --output_counters=counters/nz_international_migration_counters.csv \
  --log_level=-2 \
  --log_every_n=1000
```

### 3. Run Test on Sample Data
```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
  --input_data=testdata/test_input.csv \
  --pv_map=pvmap.csv \
  --config_file=metadata.csv \
  --places_resolved_csv=places_resolved.csv \
  --output_path=testdata/nz_international_migration
```