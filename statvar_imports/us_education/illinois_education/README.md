# Illinois State Board of Education (ISBE) Report Card Data

## Import Overview

This project processes and imports the Illinois School Report Card data from the Illinois State Board of Education (ISBE). The dataset provides annual school level data on various metrics including student demographics and assessment results.

* **Source URL**: [https://www.isbe.net/Pages/Illinois-State-Report-Card-Data.aspx](https://www.isbe.net/Pages/Illinois-State-Report-Card-Data.aspx)  
* **Import Type**: Semi Automated  
* **Source Data Availability**: Annual releases from the Illinois State Board of Education.  
* **Release Frequency**: Annual  
* **Notes**: This dataset provides annual school Each row represents a specific demographic breakdown for a given school.

---

## Preprocessing Steps

The import process is divided into two main stages: downloading the raw data and then processing it to generate the final artifacts for ingestion.

* **Input files**:  
    
  * `download_script.py`: Downloads and performs initial cleaning of the raw data.  
  * `metadata.csv`: Configuration file for the data processing script.  
  * `pvmap.csv`: Property-value mapping file used by the processor.  
  * `schema.mcf`: Statistical variable definitions.


* **Transformation pipeline**:  
    
  1. `download_script.py` downloads the annual data releases for all years from 2018 to the current year. It downloads xls files and split the each sheet to a csv file, saving the results in the `input_files/` directory.  
  2. After the download is complete, the `stat_var_processor.py` tool is run on all cleaned CSV files.  
  3. The processor uses the `metadata.csv` and `pvmap.csv` files to generate the final `output.csv` and `output.tmcf` files, placing them in the `output_files/` directory.


* **Data Quality Checks**:  
    
  * Linting is performed on the generated output files using the DataCommons import tool.  
  * There are no known warnings or errors.

---

## Autorefresh

This import is considered semi-automated because the data source URLs are not stable and require manual updates for new releases. To refresh the data, you will need to:

* Check for New Data: Visit the ISBE Report Card Data website to check for new data releases.   
* Update Configuration: If new data is available, update the import\_configs.json file with the new URLs and corresponding year information.   
* Run Scripts: Execute the download script as outlined below.

* **Steps**:  
  1. A Cloud Scheduler job, defined in `manifest.json`, runs annually at 00:00 on December 15th.  
  2. Download the Data: Execute the download\_script.py script to fetch the raw data files from the URLs specified in import\_configs.json. Then it will split each xlsx sheet to csv sheet.These files will be saved in the input\_files directory.  
  3. It then runs the `stat_var_processor.py` tool, which processes all the yearly files and generates the final artifacts.  
  4. The final, validated output files are uploaded to a GCS bucket for ingestion into the Data Commons Knowledge Graph.

---

## Script Execution Details

To run the import manually, follow these steps in order.

### Step 1: Download Data

This script downloads all available annual data files and split them

**Usage**:

```shell
python3 download_script.py
```

The cleaned source files will be located in `input_files/`.

---

### Step 2: Process the Data

This script processes all cleaned input files to generate the final `output.csv` and `output.tmcf`.

**Usage**:

```shell
python3 ../../tools/statvar_importer/stat_var_processor.py --input_data=input_files/trenddata_data.csv --pv_map=configs/trenddata_pvmap.csv --config_file=trenddata_metadata.csv --places_resolved_csv=placeresolver.csv --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf --output_path=output_files/trenddata_output'
```

---

### Step 3: Validate the Output Files

This command validates the generated files for formatting and semantic consistency before ingestion.

**Usage**:

```shell
java -jar /path/to/datacommons-import-tool.jar lint -d 'output_files/'
```

This step ensures that the generated artifacts are ready for ingestion into Data Commons.

---

