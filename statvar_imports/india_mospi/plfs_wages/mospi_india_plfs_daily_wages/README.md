### MOSPI_IndiaPLFS_DailyWages

- Description: Daily wages at the country and state level.

- Source URL: https://esankhyiki.mospi.gov.in/macroindicators?product=plf

- Import Type: Manual Refresh

- Data Availability: 2017-05 to 2024-02

- Release Frequency: P3Y

### Preprocessing and Data Acquisition

To download the raw input files:
- Use the link to download the data. Select "Average wage earnings (Rs. 0.00) per day from casual labour work other than public works". Selected all years, gender, quarter, sector and state.

### Data Processing

After the files are downloaded, the data is processed using the stat_var_processor.py script. Each stage handles a specific data category. The script uses various command-line arguments to specify the input data, pvmap, configuration file, and output path for each category.

```bash

    python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data='../../statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/{InputFile}.csv' --pv_map='../../statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/daily_wages_pvmap.csv' --config_file='../../statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/daily_wages_metadata.csv' --output_path='../../statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/output/daily_wages' --places_resolved_csv='../../statvar_imports/india_mospi/plfs_wages/mospi_india_plfs_daily_wages/daily_wages_places.csv'
```
