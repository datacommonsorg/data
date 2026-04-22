# WHO Tuberculosis Percentage Dataset
## Overview
This dataset provides the percentage of people diagnosed with a new episode of pulmonary TB whose disease was bacteriologically confirmed, sourced from the World Health Organization (WHO) Global Tuberculosis Programme.

## Data Source

**Source URL:**
https://data.who.int/indicators/i/1891124/449F55C

The data is fetched from the WHO's official Global Tuberculosis Database via their public API.

## How To Download Input Data
To download the latest data, use the provided download script `download_who_tuberculosis.py`. This script fetches the data from the WHO API and merges it with country ISO3 codes to generate `tuberculosisPercentage_input.csv`.

**Type of place:** Country.

**Statvars:** Tuberculosis - Bacteriologically Confirmed Percentage.

**Years:** 1999 to 2024.

## Processing Instructions
To process the Tuberculosis data and generate statistical variables, use the following commands from the project's root `data` directory:

**Download input file**
 ```bash
 python3 statvar_imports/tuberculosis_percentage/download_who_tuberculosis.py
```

**For Test Data Run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/tuberculosis_percentage/test_data/tuberculosisPercentage_input.csv \
  --pv_map=statvar_imports/tuberculosis_percentage/test_data/tuberculosisPercentage_pvmap.csv \
  --output_path=statvar_imports/tuberculosis_percentage/test_data/tuberculosisPercentage_output \
  --config_file=statvar_imports/tuberculosis_percentage/test_data/tuberculosisPercentage_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```

**For Main data run**
```bash
python3 tools/statvar_importer/stat_var_processor.py \
  --input_data=statvar_imports/tuberculosis_percentage/tuberculosisPercentage_input.csv \
  --pv_map=statvar_imports/tuberculosis_percentage/tuberculosisPercentage_pvmap.csv \
  --output_path=statvar_imports/tuberculosis_percentage/tuberculosisPercentage_output \
  --config_file=statvar_imports/tuberculosis_percentage/tuberculosisPercentage_metadata.csv \
  --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf
```
