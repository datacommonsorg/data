# IPEDS Student to Faculty Ratio
**Import Overview**
This project processes and imports the Student to Faculty Ratio data from the Integrated Postsecondary Education Data System (IPEDS). IPEDS is the primary federal source of data on U.S. colleges, universities, and technical/vocational institutions.

# Import Name: IPEDS_StudentToFacultyRatio

Source URL: ``https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx?gotoReportId=7&fromIpeds=true&sid=859539d0-db09-4d03-a36a-eabf93d07355&rtid=7`

Provenance Description: Integrated Postsecondary Education Data System (IPEDS) is the official online home for the primary federal source of data on U.S. colleges, universities, and technical/vocational institutions. This import focuses on Student to Faculty Ratio data.

# Import Type: Automated

# Notes: This import focuses exclusively on the Student to Faculty Ratio.

**Preprocessing Steps**
The import process is divided into two main stages: downloading the raw data, preprocessing and then processing it to generate the final artifacts for ingestion.

# Input files: `download.py`: Downloads, unzips the raw data.

`preprocess.py`: Further cleans the downloaded data (rename the input files and adds a year column)

# Source Data: Files in `input_files/*.csv`

Transformation pipeline:

download.py downloads the yearly data releases, unzips them, filters for relevant files, renames them, and saves them as CSV files in the input_files/ directory.

preprocess.py is executed for additional cleaning/transformation.

After the download is complete, the stat_var_processor.py tool is run on the cleaned CSV files in the input_files directory using the shell script run.sh.

The processor uses `metadata and pv_map` files (not explicitly named for IPEDS here) to generate the final .csv and .tmcf files, placing them in the processed_output/ directory.

# Output Files:

`processed_output/student_faculty_ratio_data_2009.tmcf (Template MCF)`

`processed_output/*.csv (Cleaned CSV data files)`

# Data Quality Checks:

Linting is performed on the generated output files using the DataCommons import tool.

# Autorefresh 
This import is designed to be autorefreshed via a Cloud Scheduler job.

# Scripts Executed: `download.py, preprocess.py, run.sh`

Schedule: 0 0 15 7 * (Runs at 00:00 on day 15 of July, i.e., annually on July 15th).

Resource Limits: CPU: 32, Memory: 256, Disk: 1000

## Steps:

The Cloud Scheduler job executes `download.py` to automatically download the latest data release.

`preprocess.py` is executed to clean the downloaded data.

The shell script run.sh then runs the `stat_var_processor.py` tool to process the yearly files and generate the final artifacts.

The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

# pre   Script Execution Details
To run the import manually, follow these steps in order.

**Step 1:** Download and Preprocess Raw Data
This script downloads all available data files, unzips them, filters for relevant files, renames them, and adds 'year'.

# Usage:

```Bash

python3 download.py

The processed source files will be located in input_files/.
```

**Step 2:** 
# Process the Data
This script processes all cleaned input files to generate the final CSV and TMCF files.

The shell script run.sh runs the stat_var_processor.py tool on all the files in the input_files folder (on every year-wise data file) and executes them in parallel.

### For example:
# Usage:

```Bash

sh run.sh
```

A generic command for the processor looks like:

```Bash

python3 ../../../../tools/statvar_importer/stat_var_processor.py --input_data="input/student_faculty_ratio_data_<year>.csv" --pv_map="student_faculty_ratio_pvmap.csv" --config_file="student_faculty_ratio_metadata.csv" --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path="output/student_to_faculty_ratio_<year>"
```

**Step 3:** 
# Validate the Output Files
This command validates the generated files for formatting and semantic consistency before ingestion.

# Usage:

```Bash

java -jar /path/to/datacommons-import-tool.jar lint -d 'output/'
```

This step ensures that the generated artifacts are ready for ingestion into Data Commons.