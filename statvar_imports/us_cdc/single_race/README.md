### This import process handles data from wonder.cdc platform.

- Description: Mortality statistics, categorized by demographic factors and specific causes of death, location, race at county level.

- Source URL: https://wonder.cdc.gov/ucd-icd10-expanded.html

- Import Type: Automated

- Data Availability: 2018 onwards

- Release Frequency: P1Y, which means every Year.

### Preprocessing and Data Acquisition

- Download: Automated live downloader (`download.py`)

The script connects directly to the CDC WONDER platform (`https://wonder.cdc.gov/ucd-icd10-expanded.html`), automates the session agreement, and downloads county-level mortality datasets across:
	* Year (2018 onwards)
	* County
	* Sex (Male, Female)
	* Single Race (6 categories)
	* ICD-10-113 Cause List

The script automatically partitions queries state by state, dynamically splits high-population states into 2-year chunks to respect CDC's 75,000 row export limit, and batches downloads in sessions with automatic renewal and cooldown to avoid rate limits.

To run the live download:
```bash
# Execute via shell wrapper:
sh download.sh

# Or directly with python:
python3 download.py

# Download specific states or years:
python3 download.py --states=02,48 --years=2018-2024
```

### Data Processing

After downloading, input files will be placed into the `input_files/` directory. The data is processed using the `stat_var_processor.py` script:

```bash
python3 ../../../tools/statvar_importer/stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=input_files/*.csv --pv_map=single_race_pvmap.csv --config_file=single_race_metadata.csv --output_path=output/underlyingcauseofdeath_singlerace --output_counters=counters/underlyingcauseofdeath_singlerace.csv
```

### Automation

This import pipeline is configured to run automatically on the second Saturday of every month schedule.

- Cron Expression: 30 08 8-14 * 6

