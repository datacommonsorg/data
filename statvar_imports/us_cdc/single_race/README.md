### This import process handles data from wonder.cdc platform.

- Description: Mortality statistics, categorized by demographic factors and specific causes of death, location, race at state level.

- Source URL: https://wonder.cdc.gov/ucd-icd10-expanded.html

- Import Type: Semi-Automated

- Data Availability: 2018 to 2023

- Release Frequency: P1Y, which means every Year.

### Preprocessing and Data Acquisition

-Download: Manual

To obtain the raw input files, data must be manually downloaded from the source. The download process involves selecting specific criteria from the dropdown menus:

	*Year
	*County
	*Sex
	*Single Race (6 categories)
	*ICD-10-113 Cause List

For each download, a specific state must be selected. The desired year range is from 2018 to 2023. After making the selections, click the "Send" button at the bottom to initiate the download.


### Data Processing

To get the input files, run the following command. The `download.sh` script will create an input_files folder and copy all the necessary files into it from the GCS :

```bash

	sh download.sh
```
After the files are downloaded, the data is processed using the stat_var_processor.py script. The 	  script uses various command-line arguments to specify the input data, pvmap, configuration file, and  output path.


```bash

	python3 stat_var_processor.py --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --input_data=../../statvar_imports/us_cdc/single_race/input_files/*.csv --pv_map=../../statvar_imports/us_cdc/single_race/single_race_pvmap.csv --config_file=../../statvar_imports/us_cdc/single_race/single_race_metadata.csv --output_path=../../statvar_imports/us_cdc/single_race/output/underlyingcauseofdeath2018_2023singlerace
```

### Automation

This import pipeline is configured to run Semi-automatic on a monthly schedule.

- Cron Expression: 30 08 * * 6

