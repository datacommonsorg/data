### EPA US Air Pollutant Emission Trends (County)

- Description: US Environmental Protection Agency (EPA) National Emissions Inventory (NEI) County Tier 1 Summary Data, measuring annual air pollutant emissions (such as Carbon Monoxide, Ammonia, Nitrogen Oxides, PM10, PM2.5, Sulfur Dioxide, and Volatile Organic Compounds) by emission source category at the county level.

- Source URL: https://www.epa.gov/air-emissions-inventories/air-pollutant-emissions-trends-data

- Data FTP URL: https://gaftp.epa.gov/air/nei

- Import Type: Automated

- Data Availability: 2008 onwards (every 3-year NEI cycle: 2008, 2011, 2014, 2017, 2020, etc.)

- Release Frequency: P3Y (every 3 years)

- Type of Place: County (resolved via state and county FIPS code)

### Preprocessing and Data Acquisition

- Download: Automated (`download_preprocess.py`)

The `download_preprocess.py` script automatically:
1. Checks EPA NEI directories (`https://gaftp.epa.gov/air/nei/<year>/tier_summaries/`) for 3-year NEI cycles starting from 2008 up to the current year.
2. Downloads the latest version of the Tier 1 summary archive/database (`.zip`, `.accdb`, or `.mdb`).
3. Extracts the Microsoft Access database files and exports tables to CSV using `mdb-tables` and `mdb-export`, prepending the `year` column (and normalizing 2014 Tribal state FIPS codes to `88`).
4. Moves all county-level CSV files into `input_files/county_input_file/`.

Note: `mdbtools` (`mdb-tables` and `mdb-export`) must be installed in the environment to export the `.mdb`/`.accdb` database files.

### Data Processing

To download and preprocess the raw input files, run:

```bash
python3 download_preprocess.py
```

After the county input CSV files are generated in `input_files/county_input_file/`, the data is processed using `stat_var_processor.py` in two steps (individual Tier 1 categories and aggregated source categories):

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=input_files/county_input_file/*.csv \
    --pv_map=pvmap.csv \
    --config_file=metadata.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=output_files/county_tier1

python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=input_files/county_input_file/*.csv \
    --pv_map=aggregate_pvmap.csv \
    --config_file=aggregate_metadata.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=output_files/county_tier1_aggregate
```

### Automation

This import pipeline is configured to run automatically on a weekly schedule (every Tuesday at 07:00 UTC) as defined in `manifest.json`.

- Cron Expression: `0 07 * * 2`
