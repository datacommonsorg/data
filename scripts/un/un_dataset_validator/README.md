# UN Data Commons - Dataset Validation Suite

This directory contains the Python-based validation suite used to ensure datasets conform to the UN Data Commons Schema mapping rules before ingestion.

## Prerequisites

1.  **Python 3:** Ensure Python 3.8+ is installed on your system.
2.  **Required Libraries:** Install the dependencies required by the validation scripts:
    ```bash
    cd un_dataset_validator
    pip install -r requirements.txt
    ```

## Directory Structure Expectations

To run the validation successfully, your datasets and configurations must be organized into specific nested folders. The validation suite requires paths to **three** distinct directories:

### 1. Processed Directory (`<processed_dir>`)
This is the main directory containing your custom dataset's final generated mappings and outputs. It **must** follow this nested folder structure:

```text
my_processed_dir/                         <-- This is the <processed_dir> you provide
├── processed_data/                       <-- (Required) Contains your final processed *_data.csv files
│   ├── SDG_q1-2026_OBS_AG_FLS_INDEX_data.csv     
│   └── SDG_q1-2026_OBS_AG_FLS_PCT_data.csv
├── schema/                               <-- (Required) Contains your generated schemas
│   ├── SDG_q1-2026_OBS_AG_FLS_INDEX_data_stat_vars.mcf          
│   └── SDG_q1-2026_OBS_AG_FLS_PCT_data_stat_vars.mcf
├── pvmap/                                <-- (Optional) Contains local Property-Value maps for this dataset
│   └── CL_UNIT_MEASURE_pvmap.csv         
└── dc_generated/                         <-- (Optional) Intermediate generated outputs
```
*Note: If your dataset relies on global mapping files (like a global `un_geography_pvmap.csv`), the suite will automatically look for a `pvmap/` folder in the **parent** directory of your `<processed_dir>` (e.g., `../my_processed_dir/../pvmap/`).*

### 2. Raw Input Data Directory (`<input_data_directory>`)
This folder contains the original, raw CSV files (the data you processed into the `processed_data` folder). It is critical that the base names correspond to the processed files.
```text
raw_data/
└── DATA/                                 <-- This is the <input_data_directory> you provide
    ├── SDG_q1-2026_OBS_AG_FLS_INDEX.csv
    └── SDG_q1-2026_OBS_AG_FLS_PCT.csv
```

### 3. DSD Schema Directory (`<dsd_directory>`)
This folder contains the SDMX Data Structure Definition (DSD) files used to validate your dimensions and attributes. The files typically have `_DSD_` in their names.
```text
raw_data/
└── DSD/                                  <-- This is the <dsd_directory> you provide
    ├── SDG_q1-2026_DSD_AG_FLS_INDEX.csv
    └── SDG_q1-2026_DSD_AG_FLS_PCT.csv
```

## How to Run Validations

The easiest way to run the full validation suite on your custom dataset is using the provided shell wrapper script:

```bash
cd un_dataset_validator
./run_custom_dataset.sh <dataset_name> <processed_dir> <input_data_directory> <dsd_directory>
```

### Example Usage:

Assume you have a project directory organized like this:
```text
my_project/
├── raw_inputs/
│   ├── DATA/         <-- Raw CSVs
│   └── DSD/          <-- Raw SDMX Schemas
├── processed/
│   └── health_v1/    <-- Processed Dataset Folder
│       ├── processed_data/
│       └── schema/
└── un_dataset_validator/       <-- This validation suite
```

To run the validation on `health_v1`, you would execute:

```bash
cd un_dataset_validator
./run_custom_dataset.sh health_v1 ../processed/health_v1 ../raw_inputs/DATA ../raw_inputs/DSD
```

### Output & Logs

The script will automatically create a dedicated log directory inside `un_dataset_validator/logs/` named `<dataset_name>_validation_logs/`.

Inside this folder, you will find:
1.  Individual `ruleX_..._validation.log` files containing detailed tracing of each rule's execution.
2.  A final **`summary.md`** file providing a clean, comprehensive markdown matrix of which rules passed/failed alongside detailed metrics and error samples.
