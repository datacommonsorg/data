# SDMX Agentic Import Pipeline

The SDMX Agentic Import Pipeline is a Python-based system designed to automate the retrieval and processing of SDMX (Statistical Data and Metadata eXchange) data for Data Commons. It provides a structured, step-based approach to downloading, sampling, mapping, and processing SDMX data into Data Commons artifacts.

## Overview

The pipeline orchestrates several tools to handle the end-to-end import process:
1.  **Download**: Retrieves data and metadata from SDMX endpoints.
2.  **Sample**: Creates a manageable sample of the data for analysis.
3.  **Schema Mapping**: Generates Property-Value (PV) mappings using LLM-based tools.
4.  **Full Data Processing**: Converts the full dataset into Data Commons MCF and CSV formats.
5.  **Custom DC Config**: Generates configuration for custom Data Commons instances.

## Prerequisites

Before running the pipeline, ensure you have set up your environment as described in the [main README](./README.md#step-2-environment-setup). Key requirements include:

1.  **DC_DATA_REPO_PATH**: Environment variable pointing to your cloned Data Commons data repository.
2.  **WORKING_DIR**: Environment variable pointing to your working directory.
3.  **Python Environment**: Activated virtual environment with required dependencies.
4.  **Gemini CLI**: Installed and configured for schema mapping.
5.  **Data Commons API Key**: Set in your environment.

## Usage

The pipeline is executed using the `sdmx_import_pipeline.py` script.

**Important:** The command must be run from within your working directory.

### Basic Command

```bash
# Ensure you are in your working directory
cd $WORKING_DIR

# Run the pipeline using the full path to the script
python $DC_DATA_REPO_PATH/tools/agentic_import/sdmx_import_pipeline.py \
  --sdmx.endpoint="https://sdmx.example.org/data" \
  --sdmx.agency="AGENCY_ID" \
  --sdmx.dataflow.id="DATAFLOW_ID" \
  --dataset_prefix="my_dataset"
```

### Key Flags

-   `--sdmx.endpoint`: The SDMX API endpoint URL.
-   `--sdmx.agency`: The SDMX agency ID.
-   `--sdmx.dataflow.id`: The SDMX dataflow ID.
-   `--sdmx.dataflow.key`: (Optional) Filter key for data download.
-   `--sdmx.dataflow.param`: (Optional) Additional parameters for data download.
-   `--dataset_prefix`: (Optional) Prefix for generated artifacts. Useful for disambiguating multiple datasets in the same working directory. If not provided, it is derived from the dataflow ID.
-   `--sample.rows`: Number of rows for the sample dataset (default: 1000).
-   `--force`: Force re-execution of all steps, ignoring saved state.
-   `--skip_confirmation`: Skip interactive confirmation prompts during schema mapping.
-   `--verbose`: Enable verbose logging.

## Pipeline Steps

The pipeline consists of the following steps, executed in order:

1.  **DownloadDataStep**: Downloads SDMX data to `<dataset_prefix>_data.csv`.
2.  **DownloadMetadataStep**: Downloads SDMX metadata to `<dataset_prefix>_metadata.xml`.
3.  **CreateSampleStep**: Creates `<dataset_prefix>_sample.csv` from the downloaded data.
4.  **CreateSchemaMapStep**: Generates PV map and config in `sample_output/` using `pvmap_generator.py`.
5.  **ProcessFullDataStep**: Processes the full data using `stat_var_processor.py` to generate artifacts in `output/`.
6.  **CreateDcConfigStep**: Generates `output/<dataset_prefix>_config.json` for custom DC imports.

## Directory Structure

The pipeline organizes outputs within the specified working directory:

```
working_dir/
├── <dataset_prefix>_data.csv          # Raw downloaded data
├── <dataset_prefix>_metadata.xml      # Raw downloaded metadata
├── <dataset_prefix>_sample.csv        # Sampled data
├── .datacommons/
│   └── <dataset_prefix>.state.json    # Pipeline state for resuming runs
├── sample_output/                     # Intermediate artifacts from mapping
│   ├── <dataset_prefix>_pvmap.csv
│   └── <dataset_prefix>_metadata.csv
└── output/                            # Final Data Commons artifacts
    ├── <dataset_prefix>.csv
    ├── <dataset_prefix>.mcf
    ├── <dataset_prefix>.tmcf
    └── <dataset_prefix>_config.json
```

## State Management

The pipeline automatically saves its state to a `<dataset_prefix>.state.json` file in the `.datacommons/` directory within your working directory.
-   **Resuming**: If a run is interrupted, running the same command again will resume from the last successful step.
-   **Skipping**: Steps that have already completed successfully will be skipped unless `--force` is used.
-   **Input Hashing**: The pipeline tracks input configuration. If critical configuration changes, it may trigger re-execution of steps.

## Troubleshooting

-   **Gemini CLI Errors**: If the schema mapping step fails, check the Gemini CLI logs (usually in `.datacommons/runs/` within the working directory). Refer to the [main README](./README.md#debugging) for detailed debugging instructions.
-   **Missing Data**: Ensure the SDMX endpoint, agency, and dataflow ID are correct. Use `--verbose` to see the exact commands being run.
-   **State Issues**: If the pipeline is stuck or behaving unexpectedly, you can delete the state file to reset the state, or use `--force`.
