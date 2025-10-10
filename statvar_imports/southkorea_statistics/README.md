### South Korea Statistics Import
This project is designed to process and import various statistics from South Korea.

1. Import Overview
This project imports data from the National Statistical Office of South Korea (KOSIS).

`Source URL:` https://www.google.com/search?q=https://kosis.kr/eng/index/indexList.do

`Import Type:` Manual Download.

`Source Data Availability:` Varies by dataset. Data is collected from various years and is updated regularly.

`Type of Place:` Provinces, cities, and other administrative divisions of South Korea.

`StatVars:` Varies by dataset. This project may include statistics on population, economy, society and education.

2. Preprocessing Steps
This section will detail the specific preprocessing steps required for the chosen dataset.

**Input files:**

raw_data.csv: Raw data downloaded from the source.

pv_map.csv: Property-value mapping file.

metadata.csv: StatVar metadata file.

places_resolved.csv: Place resolution file.

Transformation pipeline:
A manual download of the raw data is required.

The data is processed using the stat_var_processor.py script, which is the same process used for the OECD template, to transform it into the final CSV and TMCF formats.

3. Autorefresh Type
This project is semi - automated.
The files are downloaded manually and uploaded in the Google Cloud Bucket and run.sh script downloads it.
The downloaded files are then processed to get the desired output.

4. Script Execution Details

Script 1:
../run.sh gs://<bucket name>/<folder path>/

example:
../run.sh gs://unresolved_mcf/country/southkorea/demographics/source_files/

Make sure to run from respective folder paths.

Script 2: stat_var_processor.py (Data Processing)
Usage:

python3 stat_var_processor.py --input_data=source_files/raw_data.csv --pv_map=pvmap.csv --config_file=metadata.csv --output_path=output/

## Education Data

For processing education data use the below format (Place resolver is a seperate pvmap as we are using #Header in it, below example shows how to run from the present working directory)

python3 ../../tools/statvar_importer/statvar_processor.py --input_data=education/input_file --pv_map='education/dataset_pvmap.csv,education.places_resolved.csv' --config_file=education/dataset_metadata.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output_directory_path

**Note: For each import (e.g., demographics, health, education, and employment), be sure to use the corresponding data, pvmap, and metadata files located in their respective folders.**

Purpose: Generates the cleaned CSV and TMCF files for ingestion.
