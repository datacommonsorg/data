# Agentic Import Tool for Data Commons

This guide describes the complete process for importing CSV data into Data Commons using the agentic import toolchain. The process involves data sampling, metadata generation, PV mapping, and artifact creation for both standard and custom Data Commons imports.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Directory Structure](#directory-structure)
- [Data Import Process](#data-import-process)
  - [Step 1: Repository Setup](#step-1-repository-setup)
  - [Step 2: Environment Setup](#step-2-environment-setup)
  - [Step 3: Working Directory Preparation](#step-3-working-directory-preparation)
  - [Step 4: Data Sampling](#step-4-data-sampling)
  - [Step 5: Configuration File Creation](#step-5-configuration-file-creation)
  - [Step 6: PV Map Generation](#step-6-pv-map-generation)
  - [Step 7: Data Processing](#step-7-data-processing)
  - [Step 8: Custom DC Configuration (Optional)](#step-8-custom-dc-configuration-optional)
  - [Step 9: Final Import](#step-9-final-import)
- [Validation](#validation)
- [Troubleshooting](#troubleshooting)
- [Examples](#examples)

## Prerequisites

Before starting the import process, ensure you have the following installed and configured:

### Required Tools
1. **Gemini CLI**: Install the Gemini command-line interface
   ```bash
   # Installation instructions vary by platform
   # Refer to Gemini CLI documentation for your system
   ```

2. **Data Commons API Key**: Set up your DC_API_KEY environment variable
   ```bash
   export DC_API_KEY="your_data_commons_api_key_here"
   ```

3. **Python Environment**: Python 3.7+ with required dependencies

## Setup

### Step 1: Repository Setup

Clone the Data Commons data repository and set up environment variables:

```bash
# Clone the repository
git clone <data-commons-data-repo-url>
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
```

### Step 3: Working Directory Preparation

Create or navigate to your working directory where input data and metadata files will be stored:

```bash
# Create working directory
mkdir -p /path/to/working/directory
cd /path/to/working/directory
export WORKING_DIR=$(pwd)

# Ensure you have your input data and metadata files in this directory
# Expected structure:
# working_directory/
# ├── input_data.csv
# ├── metadata_file1.json
# ├── metadata_file2.yaml
# └── ... (other metadata files)
```

## Data Import Process

### Step 4: Data Sampling

Create a sample of your data using the data_sampler utility. This helps with initial testing and validation:

```bash
# Sample your input CSV data (maximum 30 lines)
python $DC_DATA_REPO_PATH/tools/statvar_importer/data_sampler.py \
  --sampler_input="$WORKING_DIR/input_data.csv" \
  --sampler_output="$WORKING_DIR/sample_data.csv" \
  --max_rows=30
```

**Parameters:**
- `--sampler_input`: Path to your original CSV data file
- `--sampler_output`: Path where the sample will be saved
- `--max_rows`: Maximum number of rows to sample (recommended: 30 for testing)

### Step 5: Configuration File Creation

Create a configuration file for the PV map generator based on the sample data configuration template:

```bash
# Copy and modify the sample configuration
cp $DC_DATA_REPO_PATH/tools/agentic_import/testdata/sample_data_config.json \
   $WORKING_DIR/data_config.json
```

Edit `$WORKING_DIR/data_config.json` to include your actual file paths:

```json
{
  "input_data": [
    "/path/to/working/directory/sample_data.csv"
  ],
  "input_metadata": [
    "/path/to/working/directory/metadata_file1.json",
    "/path/to/working/directory/metadata_file2.yaml"
  ],
  "is_sdmx_dataset": true
}
```

### Step 6: PV Map Generation

Generate the PV map and metadata files using the pvmap_generator:

```bash
# Generate PV map and metadata
python $DC_DATA_REPO_PATH/tools/agentic_import/pvmap_generator.py \
  --config_file="$WORKING_DIR/data_config.json" \
  --output_dir="$WORKING_DIR"
```

This command will generate:
- `pvmap.csv`: Property-Value mapping file
- `metadata.csv`: Metadata configuration file
- `output/` directory containing:
  - `output.csv`: Processed data file
  - `output.tmcf`: Template MCF file
  - `output_stat_vars.mcf`: Statistical variables MCF file

**Validation:** Check that `output.csv` has proper formatting and all required fields.

### Step 7: Data Processing

Process the actual data using the generated PV map and metadata:

```bash
# Set environment variables for the processor
export INPUT_DATA="$WORKING_DIR/actual_input_data.csv"  # Your full dataset
export SCRIPT_DIR="$DC_DATA_REPO_PATH/tools/agentic_import"
export PYTHON_INTERPRETER="python"
export PROCESSOR_LOG="$WORKING_DIR/processor.log"

# Run the stat var processor
"$PYTHON_INTERPRETER" "$SCRIPT_DIR/statvar_importer/stat_var_processor.py" \
  --input_data="$INPUT_DATA" \
  --pv_map="$WORKING_DIR/pvmap.csv" \
  --config_file="$WORKING_DIR/metadata.csv" \
  --generate_statvar_name=True \
  --output_counters="$WORKING_DIR/.datacommons/output_counters.log" \
  --output_path="$WORKING_DIR/output/output" > "$PROCESSOR_LOG" 2>&1
```

**Validation:** Verify that `output/output.csv` contains properly formatted data with all required fields.

### Step 8: Custom DC Configuration (Optional)

If importing to a custom Data Commons instance, generate the custom DC configuration:

```bash
# Generate custom DC configuration
python $DC_DATA_REPO_PATH/tools/agentic_import/generate_custom_dc_config.py \
  --input_csv="$WORKING_DIR/output/output.csv" \
  --output_config="$WORKING_DIR/output/config.json"
```

**Parameters:**
- `--input_csv`: Path to the processed output CSV file
- `--output_config`: Path where the custom DC config JSON will be saved

### Step 9: Final Import

Execute the final import process:

```bash
# Navigate to output directory
cd $WORKING_DIR/output

# Run custom DC importer
# Note: The importer will automatically use output_stat_vars.mcf
# Specific import command depends on your custom DC setup
# Example:
custom_dc_importer --config=config.json --data=output.csv --mcf=output_stat_vars.mcf
```

## Directory Structure

Your working directory structure should look like this after completion:

```
working_directory/
├── input_data.csv              # Original input data
├── sample_data.csv             # Sampled data (30 lines max)
├── metadata_file1.json         # Metadata files
├── metadata_file2.yaml
├── data_config.json            # Configuration for PV map generator
├── pvmap.csv                   # Generated PV mapping
├── metadata.csv                # Generated metadata configuration
├── processor.log               # Processing logs
├── .datacommons/
│   └── output_counters.log     # Output counters
└── output/
    ├── output.csv              # Final processed data
    ├── output.tmcf             # Template MCF
    ├── output_stat_vars.mcf    # Statistical variables MCF
    └── config.json             # Custom DC configuration (if generated)
```

## Validation

### Data Validation Steps

1. **Sample Data Validation:**
   ```bash
   # Check sample data has expected columns and format
   head -5 $WORKING_DIR/sample_data.csv
   ```

2. **PV Map Validation:**
   ```bash
   # Verify PV map contains proper mappings
   head -10 $WORKING_DIR/pvmap.csv
   ```

3. **Output Validation:**
   ```bash
   # Check output CSV for proper formatting
   head -5 $WORKING_DIR/output/output.csv

   # Verify required columns exist
   head -1 $WORKING_DIR/output/output.csv | tr ',' '\n'
   ```

4. **MCF Validation:**
   ```bash
   # Check MCF files are properly formatted
   head -20 $WORKING_DIR/output/output_stat_vars.mcf
   ```

## Troubleshooting

### Common Issues

1. **Missing Environment Variables:**
   ```bash
   # Ensure all required variables are set
   echo $DC_API_KEY
   echo $DC_DATA_REPO_PATH
   echo $WORKING_DIR
   ```

2. **Python Environment Issues:**
   ```bash
   # Reactivate virtual environment
   source $DC_DATA_REPO_PATH/.env/bin/activate

   # Verify Python interpreter
   which python
   ```

3. **File Permission Issues:**
   ```bash
   # Ensure files are readable
   ls -la $WORKING_DIR/
   chmod +r $WORKING_DIR/*.csv
   ```

4. **Data Format Issues:**
   - Verify CSV files have proper headers
   - Check for special characters in data
   - Ensure metadata files are valid JSON/YAML

5. **Processing Errors:**
   ```bash
   # Check processing logs
   tail -50 $WORKING_DIR/processor.log

   # Check output counters
   cat $WORKING_DIR/.datacommons/output_counters.log
   ```

### Error Messages

| Error | Solution |
|-------|----------|
| "Config file not found" | Verify config file path and permissions |
| "Invalid CSV format" | Check CSV file encoding and format |
| "Missing required columns" | Verify input data has all required columns |
| "PV map generation failed" | Check metadata files are valid |
| "Processing timeout" | Reduce data size or increase timeout |

## Examples

### Complete Example Workflow

```bash
# 1. Setup
export DC_DATA_REPO_PATH="/home/user/data-commons-data"
export WORKING_DIR="/home/user/import_project"
export DC_API_KEY="your_api_key_here"

# 2. Environment
cd $DC_DATA_REPO_PATH
./run_tests.sh -r
source .env/bin/activate

# 3. Prepare working directory
mkdir -p $WORKING_DIR
cd $WORKING_DIR

# 4. Sample data
python $DC_DATA_REPO_PATH/tools/statvar_importer/data_sampler.py \
  --sampler_input="$WORKING_DIR/population_data.csv" \
  --sampler_output="$WORKING_DIR/sample_population.csv" \
  --max_rows=30

# 5. Create config
cat > $WORKING_DIR/data_config.json << EOF
{
  "input_data": [
    "$WORKING_DIR/sample_population.csv"
  ],
  "input_metadata": [
    "$WORKING_DIR/population_metadata.json"
  ],
  "is_sdmx_dataset": true
}
EOF

# 6. Generate PV map
python $DC_DATA_REPO_PATH/tools/agentic_import/pvmap_generator.py \
  --config_file="$WORKING_DIR/data_config.json" \
  --output_dir="$WORKING_DIR"

# 7. Process full data
export INPUT_DATA="$WORKING_DIR/population_data.csv"
export SCRIPT_DIR="$DC_DATA_REPO_PATH/tools/agentic_import"
export PYTHON_INTERPRETER="python"
export PROCESSOR_LOG="$WORKING_DIR/processor.log"

"$PYTHON_INTERPRETER" "$SCRIPT_DIR/statvar_importer/stat_var_processor.py" \
  --input_data="$INPUT_DATA" \
  --pv_map="$WORKING_DIR/pvmap.csv" \
  --config_file="$WORKING_DIR/metadata.csv" \
  --generate_statvar_name=True \
  --output_counters="$WORKING_DIR/.datacommons/output_counters.log" \
  --output_path="$WORKING_DIR/output/output" > "$PROCESSOR_LOG" 2>&1

# 8. Generate custom DC config (if needed)
python $DC_DATA_REPO_PATH/tools/agentic_import/generate_custom_dc_config.py \
  --input_csv="$WORKING_DIR/output/output.csv" \
  --output_config="$WORKING_DIR/output/config.json"

# 9. Final import
cd $WORKING_DIR/output
# Run your custom DC importer here
```

This completes the Data Commons CSV import process using the agentic import toolchain.