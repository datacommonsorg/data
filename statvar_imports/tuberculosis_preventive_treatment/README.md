<<<<<<< HEAD
# WHO Tuberculosis: Percentage of household contacts (or all close contacts) who were started on TB preventive treatment out of those eligible
=======
﻿# WHO Tuberculosis: Percentage of household contacts (or all close contacts) who were started on TB preventive treatment out of those eligible
>>>>>>> 52fd568515958ab33ac62e11b3b07a03ae2933d3

## Overview
This dataset provides the percentage of household contacts (or close contacts) of people diagnosed with a new episode of bacteriologically confirmed pulmonary TB disease who started TB preventive treatment, out of those eligible.

## Data Source

**Source URL:**
https://data.who.int/indicators/i/45274BD/F5556F8
    
The data comes from the official WHO reporting database and includes comprehensive, country-level health metrics detailing annual Tuberculosis notifications and case classifications.

## How To Download Input Data
To download the data, you'll need to run the provided download script `tb_data_download_who.py`. This script automatically queries the WHO API for the indicator, merges it with the WHO geographical master list to append standard `iso3` country codes, and saves the cleaned `Tuberculosis_preventive_treatment_input.csv` file inside an "input_files" folder.

type of place: Country.

statvars: Health / Tuberculosis.

years: 2010 to 2022

place_resolution: manually.

release_frequency: P1Y

## Processing Instructions
To process the WHO Tuberculosis data and generate statistical variables, use the following commands from your root `data` directory:

**Download input file**
```bash	
python3 statvar_imports/tuberculosis_preventive_treatment/tb_data_download_who.py
```

**For Test Data Run**
```bash
	python3 tools/statvar_importer/stat_var_processor.py \
<<<<<<< HEAD
  --input_data="statvar_imports/tuberculosis_preventive_treatment/testdata/Tuberculosis_preventive_treatment.csv" \
  --pv_map="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_pvmap.csv" \
  --output_path="statvar_imports/tuberculosis_preventive_treatment/output_files/tuberculosis_PreventiveTreatment" \
  --config_file="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```
=======
  --input_data="statvar_imports/tuberculosis_preventive_treatment/testdata/Tuberculosis_preventive_treatment_input.csv" \
  --pv_map="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_pv_mapping.csv" \
  --output_path="statvar_imports/tuberculosis_preventive_treatment/output_files/tuberculosis_PreventiveTreatment" \
  --config_file="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
>>>>>>> 52fd568515958ab33ac62e11b3b07a03ae2933d3
    
**For Main data run**
```bash
	python3 tools/statvar_importer/stat_var_processor.py \
<<<<<<< HEAD
  --input_data="statvar_imports/tuberculosis_preventive_treatment/input_files/Tuberculosis_preventive_treatment.csv" \
  --pv_map="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_pvmap.csv" \
=======
  --input_data="statvar_imports/tuberculosis_preventive_treatment/source_files/Tuberculosis_preventive_treatment.csv" \
  --pv_map="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_pv_mapping.csv" \
>>>>>>> 52fd568515958ab33ac62e11b3b07a03ae2933d3
  --output_path="statvar_imports/tuberculosis_preventive_treatment/output_files/tuberculosis_PreventiveTreatment" \
  --config_file="statvar_imports/tuberculosis_preventive_treatment/tuberculosis_PreventiveTreatment_metadata.csv" \
  --existing_statvar_mcf="gs://unresolved_mcf/scripts/statvar/stat_vars.mcf"
```

#### Refresh type: Fully Autorefresh