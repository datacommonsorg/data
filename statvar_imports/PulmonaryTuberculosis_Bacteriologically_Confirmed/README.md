# WHO Tuberculosis Dataset: Bacteriologically Confirmed Pulmonary TB

## Overview
This dataset provides the number of people diagnosed with a new episode of pulmonary TB whose disease was bacteriologically confirmed, sourced directly from the World Health Organization (WHO). 

## Data Source

**Source URL:**
https://data.who.int/indicators/i/1891124/5D51DB1

The data comes from the official WHO reporting database and includes comprehensive, country-level health metrics detailing annual Tuberculosis notifications and case classifications.

## How To Download Input Data
To download the data, you'll need to run the provided download script `download_tb_data.py`. This script automatically queries the WHO API for the indicator, merges it with the WHO geographical master list to append standard `iso3` country codes, and saves the cleaned `TB_Bacteriologically_Confirmed_input.csv` file inside an "source_files" folder.

type of place: Country.

statvars: Health / Tuberculosis.

years: Historical to present.

## Processing Instructions
To process the WHO Tuberculosis data and generate statistical variables, use the following commands from your root `data` directory:

**Download input file**
```bash
python3 statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/download_tb_data.py
```
**For Test Data Run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/testdata/TB_Bacteriologically_Confirmed_input.csv \
  --pv_map=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/pulmonary_tb_bctpb_pvmap.csv \
  --output_path=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/testdata/TB_Bacteriologically_Confirmed_output \
  --config_file=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/pulmonary_tb_bctpb_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf 
```

**For Main data run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/source_files/TB_Bacteriologically_Confirmed_input.csv \
  --pv_map=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/pulmonary_tb_bctpb_pvmap.csv \
  --output_path=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/TB_Bacteriologically_Confirmed_output \
  --config_file=statvar_imports/PulmonaryTuberculosis_Bacteriologically_Confirmed/pulmonary_tb_bctpb_metadata.csv\
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

