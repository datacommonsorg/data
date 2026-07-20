# WHO Tuberculosis: Tuberculosis: Treatment outcomes of people with RR/MDR-TB

## Overview
This dataset provides the percentage of TB patients who started rifampicin-resistant TB treatment and whose treatment outcome was recorded as treatment success (cured or treatment completed), treatment failed, died, lost to follow-up, or not evaluated, within the reporting period.

## Data Source

**Source URL:**
https://data.who.int/indicators/i/39E4281/F1912F6

The data comes from the official WHO reporting database and includes comprehensive, country-level health metrics detailing annual Tuberculosis notifications and case classifications.

## How To Download Input Data
To download the data, you'll need to run the provided download script `tuberculosis_rifampicin_resistant_data_download.py`. This script automatically queries the WHO API for the indicator, merges it with the WHO geographical master list to append standard `iso3` country codes, and saves the cleaned `tuberculosis_rifampicin_resistant_input.csv` file inside an "input_files" folder.
    
type of place: Country.

statvars: Health / Tuberculosis.

years: 2010 to 2022

place_resolution: manually.

release_frequency: P1Y

## Processing Instructions
To process the WHO Tuberculosis data and generate statistical variables, use the following commands from your root `data` directory:

**Download input file**
```bash	
python3 statvar_imports/tuberculosis_rifampicin_resistant/tuberculosis_rifampicin_resistant_data_download.py
```

**For Test Data Run**
```bash
	python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/tuberculosis_rifampicin_resistant/testdata/tuberculosis_rifampicin_resistant_input.csv" \
  --pv_map="statvar_imports/tuberculosis_rifampicin_resistant/tuberculosis_rifampicin_resistant_pvmap.csv" \
  --output_path="statvar_imports/tuberculosis_rifampicin_resistant/output_files/tuberculosis_rifampicin_resistant_output" \
  --config_file="statvar_imports/tuberculosis_rifampicin_resistant/tuberculosis_rifampicin_resistant_metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```
    
**For Main data run**
```bash
	python3 tools/statvar_importer/stat_var_processor.py \
  --input_data="statvar_imports/tuberculosis_rifampicin_resistant/input_files/tuberculosis_rifampicin_resistant_input.csv" \
  --pv_map="statvar_imports/tuberculosis_rifampicin_resistant/tuberculosis_rifampicin_resistant_pvmap.csv" \
  --output_path="statvar_imports/tuberculosis_rifampicin_resistant/output_files/tuberculosis_rifampicin_resistant_output" \
  --config_file="statvar_imports/tuberculosis_rifampicin_resistant/tuberculosis_rifampicin_resistant_metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

#### Refresh type: Fully Autorefresh
