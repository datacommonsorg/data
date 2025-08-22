### South Korea Statistics Import
This project is designed to process and import various statistics from South Korea.

1. Import Overview
This project imports data from the National Statistical Office of South Korea (KOSIS).

`Source URL:` https://www.google.com/search?q=https://kosis.kr/eng/index/indexList.do

`Import Type:` Manual Download.

`Source Data Availability:` Varies by dataset. Data is collected from various years and is updated regularly.

`Type of Place:` Provinces, cities, and other administrative divisions of South Korea.

`StatVars:` Varies by dataset. This project may include statistics on population, economy, and society.

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
This project is set up for manual or automated refreshes, depending on the dataset's update schedule.

4. Script Execution Details
Script 1: statvar_processor.py (Data Processing)
Usage:

python3 statvar_processor.py --input_data=input/raw_data.csv --pv_map=pvmap.csv --config_file=metadata.csv --output_path=output/

**Note: For each import (e.g., demographics, health, education, and employment), be sure to use the corresponding data, pvmap, and metadata files located in their respective folders.**

Purpose: Generates the cleaned CSV and TMCF files for ingestion.
