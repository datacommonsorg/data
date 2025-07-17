
# NCSES_Demographics_SEH_Import

## Import Overview

This import pipeline processes Demographic characteristics of graduate students, postdoctoral appointees, and doctorate-holding nonfaculty researchers in science, engineering, and health.

- **Source:** [NCSES - Demographics Data](https://ncses.nsf.gov/surveys/graduate-students-postdoctorates-s-e/2023#data)
- **Description:** Demographic characteristics of graduate students, postdoctoral appointees, and doctorate-holding nonfaculty researchers in science, engineering, and health.

## Configuration

The `seh_download.py` script relies on a configuration file named `configs.py` to fetch the URLs, filenames, and categories for the data to be downloaded. 

This approach makes the import process semi-automatic: if the download URLs change in future NCSES releases, only this configuration file needs to be updated, rather than modifying the Python script itself.

## Data Acquisition

The `seh_download.py` script is responsible for downloading the raw Excel data.

### How to Run:

Execute the `seh_download.py` script. This script will download the necessary Excel files into the folder `input_files`.

### Download Command:

```bash
python3 seh_download.py
```

## Processing Section

The downloaded data is processed using the `stat_var_processor.py` script, which is part of the `/data/tools/statvar_importer/` toolkit. This script converts the raw Excel data into a structured format suitable for further analysis and ingestion. Each processing command specifies the input data file(s), the Property-Value (PV) map, the configuration file (metadata), statvar remap, and the desired output path.

### General Processing Command Structure:

```bash
python3 stat_var_processor.py \
    --input_data='<path_to_input_files>.xlsx' \
    --pv_map='<path_to_pv_map.csv>' \
    --config_file='<path_to_metadata.csv>' \
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --statvar_dcid_remap_csv='<path_to_statvar_remap.csv>' \
    --output_path='<path_to_output_folder_and_filename_prefix>'
```

### How to Run Processing:

You can run `stat_var_processor.py` script from the `/data/tools/statvar_importer/` directory.

Navigate to the `/data/tools/statvar_importer/` directory before running the following command, or adjust the relative paths accordingly.

### Processing Command:

```bash
python3 stat_var_processor.py \
    --input_data=../../statvar_imports/ncses/ncses_demographics_seh_import/input_files/*.xlsx \
    --pv_map=../../statvar_imports/ncses/ncses_demographics_seh_import/seh_pvmap.csv \
    --config_file=../../statvar_imports/ncses/ncses_demographics_seh_import/seh_metadata.csv \ 
    --existing_statvar_mcf=gs://unresolved_mcf/scripts/statvar/stat_vars.mcf \
    --output_path=../../statvar_imports/ncses/ncses_demographics_seh_import/output_files/seh_output
```
