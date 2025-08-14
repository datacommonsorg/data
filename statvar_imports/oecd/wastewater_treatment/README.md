### OECD Wastewater Treatment
**1. Import Overview**
This project processes and imports wastewater treatment data from the OECD (Organisation for Economic Co-operation and Development).

`Source URL: https://sdmx.oecd.org/public/rest/data/OECD.ENV.EPI,DSD_WATER_TREAT@DF_WATER_TREAT,/all?dimensionAtObservation=AllDimensions&format=csvfilewithlabels`

Import Type: Script-driven download via download.py (or similar script that places data in source_files).

Source Data Availability: Data is available from 1970 to the latest year, including monthly data for each year and the latest month.

Type of Place: Country, State, and Administrative Area (OECD countries).

StatVars: This set of StatVars provides a detailed breakdown of how populations manage their wastewater, including the percentage of people connected to public sewerage and the level of treatment their wastewater receives. It also accounts for the portion of the population that uses independent treatment methods, such as septic tanks.

**2. Preprocessing Steps**
Before ingestion, the following preprocessing is done:

Input files:

`oecd_wastewatertreatment_data.csv`: Raw input data (expected to be created by a download script in the input folder)

`oecd_wastewatertreatment_pvmap.csv`: Property-value mapping

`oecd_wastewatertreatment_metadata.csv`: StatVar metadata (used by stat_var_processor.py)

`oecd_wastewatertreatment_places_resolved.csv`: Geo-resolution data used by stat_var_processor.py.

### Transformation pipeline:
No transformations are performed; the raw data is used as is directly from the downloaded source.

A download script is expected to place the raw data into the source_files folder.

Data is processed using `stat_var_processor.py.`

The output files are named `oecd_wastewatertreatment.csv` and `oecd_wastewatertreatment.tmcf`.

### Data Quality Checks:
Linting is performed using the DataCommons import tool JAR.


### 3. Autorefresh Type
`Full Automation`

***Steps:***

Note: This pipeline is fully automated.

### 4. Script Execution Details

**Script 1: download.py (Download Script)**
Usage:

Bash

python3 download.py
[ASSUMPTION: This assumes a generic download.py similar to README 1. If you have a specific command/script name for downloading this data (e.g., download_util_script.pywith specific arguments as permanifest.json snippet for README 1), please provide it.]

Purpose: It downloads the latest data from the source URL.

Script 2: stat_var_processor.py (Data Processing)
Usage:

General Usage (Example adapted for this dataset):

Bash

python3 ../../../tools/statvar_importer/stat_var_processor.py \
    --input_data=source_files/oecd_wastewatertreatment_data.csv \
    --pv_map=oecd_wastewatertreatment_pvmap.csv \
    --config_file=oecd_wastewatertreatment_metadata.csv \
    --places_resolved_csv=oecd_wastewatertreatment_places_resolved.csv \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=output/oecd_wastewatertreatment
[You provided an example command. If you need examples for 'current import folder' or 'statvar_importer folder' like in README 1, they would need to be adapted similarly.]

Purpose: Generates StatVar MCF, cleans observation CSV, and TMCF.
