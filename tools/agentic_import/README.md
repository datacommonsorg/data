# Agentic Import Tool for Data Commons

This guide describes the complete process for importing CSV data into Data Commons using the agentic import toolchain. The process involves data sampling, metadata generation, PV mapping, and artifact creation for both standard and custom Data Commons imports.

## Table of Contents

- [Agentic Import Tool for Data Commons](#agentic-import-tool-for-data-commons)
  - [SDMX Quick Links](#sdmx-quick-links)
  - [Prerequisites](#prerequisites)
    - [Required Tools](#required-tools)
  - [Setup](#setup)
    - [Step 1: Repository Setup](#step-1-repository-setup)
    - [Step 2: Environment Setup](#step-2-environment-setup)
    - [Step 3: Working Directory Preparation](#step-3-working-directory-preparation)
  - [Data Import Process](#data-import-process)
    - [Step 4: Data Download](#step-4-data-download)
      - [SDMX Downloads](#sdmx-downloads)
    - [Step 5: Data Sampling](#step-5-data-sampling)
    - [Step 6: PV Map Generation for Sample Data](#step-6-pv-map-generation-for-sample-data)
    - [Step 7: Full Data Processing](#step-7-full-data-processing)
  - [Custom Data Commons Import (Optional)](#custom-data-commons-import-optional)
    - [Step 8: Generate Custom DC Configuration](#step-8-generate-custom-dc-configuration)
    - [Step 9: Run Custom DC Import](#step-9-run-custom-dc-import)
  - [Directory Structure](#directory-structure)
  - [Debugging](#debugging)
    - [Gemini CLI Debugging](#gemini-cli-debugging)
    - [Log Structure](#log-structure)

## SDMX Quick Links

- [SDMX import pipeline (end-to-end)](sdmx_import_pipeline.md)
- [SDMX Downloads (section)](#sdmx-downloads)
- [SDMX CLI documentation](../sdmx_import/README.md)

## Prerequisites

Before starting the import process, ensure you have the following installed and configured:

### Required Tools
1. **Gemini CLI**: Install the Gemini command-line interface
   - Installation instructions vary by platform
   - Refer to: https://github.com/google-gemini/gemini-cli

2. **Data Commons API Key**: Set up your DC_API_KEY environment variable
   - Refer to: https://docs.datacommons.org/api/#obtain-an-api-key
   ```bash
   export DC_API_KEY="your_data_commons_api_key_here"
   ```

3. **Python Environment**: Python 3.11+ with required dependencies

## Setup

### Step 1: Repository Setup

Clone the Data Commons data repository and set up environment variables:

```bash
# Clone the repository
git clone https://github.com/datacommonsorg/data.git
export DC_DATA_REPO_PATH="/path/to/your/cloned/data/repo"
cd $DC_DATA_REPO_PATH
```

### Step 2: Environment Setup

Set up the Python virtual environment:

```bash
# Setup Python virtual environment
./run_tests.sh -r

# Activate the virtual environment
source .env/bin/activate

# Note: Use this Python environment for all subsequent commands
# as it has all required dependencies installed
```

### Step 3: Working Directory Preparation

Create or navigate to your working directory where input data and metadata files will be stored:

```bash
# Create working directory
mkdir -p /path/to/working/directory
cd /path/to/working/directory
export WORKING_DIR=$(pwd)


```

## Data Import Process

**IMPORTANT:** Run all the following steps from within your working directory with the Python virtual environment activated.

```bash
# Confirm you are in the working directory
cd $WORKING_DIR

# Confirm virtual environment is activated
source $DC_DATA_REPO_PATH/.env/bin/activate
```

### Step 4: Data Download

Download your input data and metadata into this working directory; the expected structure is:

```text
working_directory/
├── input_data.csv
├── metadata_file1.json
├── metadata_file2.xml
├── metadata_file3.txt
└── ... (other metadata files)
```

#### SDMX Downloads

Refer to the [SDMX CLI documentation](../sdmx_import/README.md) for details on downloading SDMX data and metadata files.
See the [SDMX import pipeline](sdmx_import_pipeline.md) for the end-to-end SDMX flow.

Extract a simplified, token-efficient JSON metadata copy from `metadata.xml`, retaining the original XML for later PV map generation.

```bash
# Extract SDMX structural metadata to JSON (keep metadata.xml)
python $DC_DATA_REPO_PATH/tools/agentic_import/sdmx_metadata_extractor.py \
  --input_metadata="metadata.xml" \
  --output_path="sdmx_metadata.json"
```

### Step 5: Data Sampling

Create a sample of your data using the data_sampler utility. This helps with initial testing and validation:

```bash
# Sample your input CSV data (maximum 30 lines)
python $DC_DATA_REPO_PATH/tools/statvar_importer/data_sampler.py \
  --sampler_input="input_data.csv" \
  --sampler_output="sample_data.csv" \
  --sampler_output_rows=30
```

**Parameters:**
- `--sampler_input`: Path to your original CSV data file
- `--sampler_output`: Path where the sample will be saved
- `--sampler_output_rows`: Maximum number of rows to sample (recommended: 30 for testing). Note: For non-SDMX sources which don't have metadata listing all column values, set this large enough to capture all unique values across all columns.

### Step 6: PV Map Generation for Sample Data

Generate the PV map and metadata files using the pvmap_generator with command-line flags. This will use Gemini CLI to read sample data, generate pvmap.csv, metadata.csv and convert sample data to Data Commons observations as output.csv:

**WARNING:** This will run Gemini CLI in YOLO mode on Linux (unrestricted access), but will use sandboxing on macOS. Be careful when running on Linux systems.

**NOTE:** For troubleshooting Gemini CLI issues, refer to the [Debugging](#debugging) section.

```bash
# Generate PV map and metadata
python $DC_DATA_REPO_PATH/tools/agentic_import/pvmap_generator.py \
  --input_data="sample_data.csv" \
  --input_metadata="metadata_file1.json,metadata_file2.xml,metadata_file3.txt" \
  --output_path="sample_output/output"
```

For **SDMX datasets**:
*   Set the `--sdmx_dataset` flag during PV map generation.
*   Use the extracted JSON metadata (not the XML file). Refer to [SDMX Downloads](#sdmx-downloads) for more details.

```bash
# Generate PV map and metadata for SDMX
python $DC_DATA_REPO_PATH/tools/agentic_import/pvmap_generator.py \
  --input_data="sample_data.csv" \
  --input_metadata="sdmx_metadata.json" \
  --output_path="sample_output/output" \
  --sdmx_dataset
```

**Parameters:**
- `--input_data`: Path to your sample CSV data file
- `--input_metadata`: Comma-separated list of metadata file paths
- `--output_path`: Output path prefix for generated files (default: output/output)
- `--sdmx_dataset`: Set if working with SDMX dataset


This command will generate:
- `sample_output/` directory containing:
  - `output_pvmap.csv`: Property-Value mapping file
  - `output_metadata.csv`: Metadata configuration file
  - `output.csv`: Sample input data converted to Data Commons observations (each row represents one Data Commons observation)
  - `output.tmcf`: Template MCF file
  - `output_stat_vars.mcf`: Statistical variables MCF file

**Validation:**
- Check that `sample_output/output.csv` contains Data Commons observations with valid format for sample data
- Validate new StatVar schema in `sample_output/output_stat_vars.mcf`


### Step 7: Full Data Processing

Process the full input data (not sample data) using the PV map and metadata files generated from sample data in previous step  (`sample_output/output_pvmap.csv` and `sample_output/output_metadata.csv`).

**NOTE:** This will generate output in the `final_output/` directory. 

```bash
# Run the stat var processor
OUTPUT_COLUMNS="observationDate,observationAbout,variableMeasured,value,observationPeriod,measurementMethod,unit,scalingFactor"
python "$DC_DATA_REPO_PATH/tools/statvar_importer/stat_var_processor.py" \
  --input_data="input_data.csv" \
  --pv_map="sample_output/output_pvmap.csv" \
  --config_file="sample_output/output_metadata.csv" \
  --generate_statvar_name=True \
  --skip_constant_csv_columns=False \
  --output_columns="$OUTPUT_COLUMNS" \
  --output_path="final_output/output" > "processor.log" 2>&1
```


**Validation:**
- Check that `final_output/output.csv` contains Data Commons observations with a valid format for the full input data.
- Validate new StatVar schema in `final_output/output_stat_vars.mcf`.

## Custom Data Commons Import (Optional)

If importing to a custom Data Commons instance, follow these steps:

### Step 8: Generate Custom DC Configuration

Generate the custom DC configuration:

```bash
# Generate custom DC configuration
python $DC_DATA_REPO_PATH/tools/agentic_import/generate_custom_dc_config.py \
  --input_csv="final_output/output.csv" \
  --output_config="final_output/config.json"
```

**Parameters:**
- `--input_csv`: Path to the processed output CSV file
- `--output_config`: Path where the custom DC config JSON will be saved

### Step 9: Run Custom DC Import

1. **Navigate to the final_output directory:**
   ```bash
   cd final_output
   ```

2. **Prepare the files before importing:**
   - Update provenance data in config.json
   - Update name and description of StatVars in output_stat_vars.mcf file

3. **Run the import:**
   - Follow the instructions at: https://docs.datacommons.org/custom_dc/custom_data.html

**WARNING:** Output files will be overwritten if the previous data processing step is rerun.

## Directory Structure

Your working directory structure should look like this after completion:

```
working_directory/
├── input_data.csv              # Original input data
├── sample_data.csv             # Sampled data (30 lines max)
├── metadata_file1.json         # Metadata files
├── metadata_file2.yaml
├── processor.log               # Processing logs
├── .datacommons/
│   └── output_counters.log     # Output counters
├── sample_output/              # Sample data output from PV map generation
│   ├── output_pvmap.csv        # Generated PV mapping for sample data
│   ├── output_metadata.csv     # Generated metadata configuration for sample data
│   ├── output.csv              # Sample data converted to Data Commons observations
│   ├── output.tmcf             # Template MCF file
│   └── output_stat_vars.mcf    # Statistical variables MCF file
└── final_output/
    ├── output.csv              # Final processed data
    ├── output.tmcf             # Template MCF
    ├── output_stat_vars.mcf    # Statistical variables MCF
    └── config.json             # Custom DC configuration (if generated)
```

## Debugging

### Gemini CLI Debugging

When encountering errors with Gemini CLI:

1. **Restart the process**: If Gemini CLI fails, simply restart the PV map generation process
2. **Check run logs**: All Gemini CLI runs are logged in `$WORKING_DIR/.datacommons/runs/<gemini_run_id>/` directory (e.g., `gemini_20250915_163906`)
3. **Monitor for loops**: Gemini CLI can sometimes get stuck in loops - check logs at `.datacommons/runs/<gemini_run_id>/gemini_cli.log`
4. **StatVar processor attempts**: Gemini CLI will run the StatVar processor multiple times if needed. Each attempt is logged in `.datacommons/runs/<gemini_run_id>/attempt_<number>/` directory

### Log Structure

```
.datacommons/
├── runs/
│   └── gemini_20250915_163906/           # Individual run directory (gemini_run_id)
│       ├── gemini_cli.log                # Main Gemini CLI log
│       ├── attempt_1/                    # First attempt logs
│       ├── attempt_2/                    # Second attempt logs (if needed)
│       └── ...                           # Additional attempts
```

These logs contain detailed information for troubleshooting any issues during the PV map generation and data processing steps.
