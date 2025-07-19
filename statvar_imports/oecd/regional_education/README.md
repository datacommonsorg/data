### OECD Regional Education
### 1. Import Overview
This project processes and imports education-related data from the OECD (Organisation for Economic Co-operation and Development), focusing on regional education statistics.

`Source URL`: https://stats.oecd.org/Index.aspx?DataSetCode=REGION_EDUCAT

`Import Type`: Script-driven download via download_script.py.

`Source Data Availability`: Data is available from 2000 to the latest year, including monthly data for each year and the latest month.

`Type of Place`: Country, State, and Administrative Area (OECD countries).

`StatVars`: Primarily related to Men, Women, and both sexes' education qualification data.

### Notes: 
The dataset primarily includes educational attainment data for two distinct age groups: 25 to 34 years and 25 to 64 years.

The data covers countries listed within the OECD member nations.

Mean value has been taken and standard deviation values are ignored.

### 2. Preprocessing Steps
Before ingestion, the following preprocessing is done:

**Input files:**

`oecd_regional_education_data.csv:` Raw input data (created by download_script.py in the input folder)

`oecd_regional_education_pvmap.csv:` Property-value mapping

`oecd_regional_education_metadata.csv:` StatVar metadata (used by stat_var_processor.py)

`oecd_regional_education_places_resolved.csv:` place_resolved.csv 

### Transformation pipeline:

The download.py creates an input folder for raw files and an output folder for processed results.

Data is processed using stat_var_processor.py.

No transformations are performed; the raw data is used as is directly from the downloaded source.

### Data Quality Checks:

Linting is performed using the DataCommons import tool JAR.

### 3. Autorefresh Type

***Full Automation***

***Steps:***

The import job runs automatically in the cloud every two weeks, specifically at 10:00 AM UTC on the 1st and 15th of each month (based on `cron schedule 0 10 1,15 * *`).

It executes the download_util_script.py to retrieve the latest data from the OECD SDMX API endpoint: https://sdmx.oecd.org/public/rest/data/OECD.CFE.EDS,DSD_REG_EDU@DF_ATTAIN,/A.........?dimensionAtObservation=AllDimensions&format=csvfilewithlabels.

Subsequently, the stat_var_processor.py is run to process the downloaded raw data, generating the final oecd_regional_education.csv and oecd_regional_education.tmcf files.

The generated **output files**: `(oecd_regional_education.csv and oecd_regional_education.tmcf)` are prepared for ingestion.

### Note: This pipeline is fully automated.


### 4. Script Execution Details
***Script 1:*** download.py (Download Script)
Usage:

```Bash

python3 download.py
Purpose: It downloads the latest data from the source.
```

***Script 2:*** stat_var_processor.py (Data Processing)
Usage:

**General Usage:**

(Processing from current import folder data/statvar_imports/oecd/regional_education):

```Bash

python3 ../../../tools/statvar_importer/stat_var_processor.py --input_data=input/oecd_regional_education_data.csv --pv_map=oecd_regional_education_pvmap.csv --config_file=oecd_regional_education_metadata.csv --output_path=output/oecd_regional_education
```
(Processing from statvar_importer folder data/tools/statvar_importer):

```Bash

python3 stat_var_processor.py --input_data=input/oecd_regional_education_data.csv --pv_map=oecd_regional_education_pvmap.csv --config_file=oecd_regional_education_metadata.csv --output_path=output/oecd_regional_education
Purpose: Generates StatVar MCF, cleans observation CSV, TMCF.

```

