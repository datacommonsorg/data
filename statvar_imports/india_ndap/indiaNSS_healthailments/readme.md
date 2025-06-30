# India NSS Health Ailments

This project processes and imports health ailment data from the National Sample Survey (NSS) in India. The dataset provides information on various health-related variables for individuals across different regions in India.

## Source link : https://ndap.niti.gov.in/dataset/7300

## How to Run

### Prerequisites

1. Install required dependencies:

   * Python 3
   * Java (for linting process)
   * Ensure the necessary Python libraries are installed.

### Steps to Process Data

1. **Run the StatVar Processor**:

   * The script `stat_var_processor.py` is used to process the data and generate the required output.

   ```bash
   python3 stat_var_processor.py --input_data='/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/india_nss_health.csv'  --pv_map='/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/pvmap.csv'  --places_resolved_csv='/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/place_resolved.csv'  --config_file='/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/metadata.csv'  --output_path='/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/health_nss' --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
   ```

   This will process the input data (`india_nss_health.csv`) with the mapping and configuration files, generating the output in the specified `output_path`.

2. **Run the Linting Process**:

   * Use Java to run the `datacommons-import-tool` for linting the processed file.

   ```bash
   java -jar '/usr/local/google/home/kvishalll/Downloads/datacommons-import-tool-0.1-alpha.1-jar-with-dependencies.jar' lint '/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/health_nss.csv' '/usr/local/google/home/kvishalll/nss_india_health_aliment/data/statvar_imports/india_ndap/indiaNSS_healthailments/input_files/health_nss.tmcf'
   ```
   
3. **Scripts python3 download_script.py**

   This will run the linting process on the generated CSV file to check for any data issues.

Here’s a more detailed explanation without including the solution or next steps:

Report Json warnings : 

## Data Quality Warning: Empty Values in `unit` and `scalingFactor` Columns

### Issue:

While processing the **`health_nss.csv`** file, several warnings were generated indicating that there are **empty values** (`''`) in the `unit` and `scalingFactor` columns. These warnings were found in rows 2 through 31 of the dataset.

Each warning message specifically points out that the columns `unit` and `scalingFactor` contain empty values in certain rows, which means that the data for those columns is missing. These empty values can be problematic for accurate data processing, as they may lead to incomplete calculations or analysis, especially when the `unit` or `scalingFactor` values are essential for further computations.

The warnings provide specific details on where the empty values occur within the dataset:

* **Column `unit`** and **column `scalingFactor`** are the two affected columns.
* The **empty values** occur across several rows, starting from line 2 up to line 31, meaning multiple rows are missing values in these columns.

