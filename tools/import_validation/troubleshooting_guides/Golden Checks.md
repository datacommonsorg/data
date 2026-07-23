# **Implementation Guide: Golden Set Validations**

## **1\. Overview**

Due to recurring data deletion failures, we protect our imports using **Golden Set Validations (`GOLDENS_CHECK`)**. This guide helps understand how to generate "golden files" (baselines of expected data) and configure the automated validation system to prevent accidental data regressions.

Currently, to mitigate issues related to data loss, we implement two primary validations supported by specific golden baselines:

1. **`Check_goldens_output_csv`**: Verifies the final output data against an established baseline.  
2. **`Check_goldens_summary_report`**: Validates structural metrics (like number of places and dates) against a summary baseline.  
3. More regarding golden checks can be seen : [github link](https://github.com/datacommonsorg/data/blob/master/tools/import_validation/Validations.md)

## **2\. Directory Architecture**

To implement these checks, your import script folder must contain the following file structure:

Plaintext

```
your_import_folder/
│
├── manifest.json                  # Main import configuration
├── validation_config.json          # Custom validation rules
│
└── golden_data/                   # Folder holding your baseline files
    ├── golden_summary_report.csv  # Generated golden summary
    └── golden_observations.csv    # Generated golden output data
```

## **3\. Step-by-Step: How to Create Golden Files**

Golden files are created by extracting a snapshot of known-good data using the script `validator_goldens.py`. Run these commands from your terminal inside your import directory.

### **Step 3.1: Generate the Summary Report Golden File**

This step tracks metadata properties like Statistical Variables (StatVars), the number of places, and date ranges to ensure future runs don't accidentally drop the entire series.

From the data/tools/import\_validation/validator\_goldens.py directory, execute the following command:

```
python3 validator_goldens.py --validate_goldens_input=summary_report.csv  --generate_goldens=golden_data/golden_summary_report.csv  --generate_goldens_property_sets="StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods"
```

### **Step 3.2: Generate the Output Data Golden File (only use if needed)** 

This step targets critical combinations of highly utilized StatVars and top geographical regions to ensure key data points are always preserved.

From the data/tools/import\_validation/validator\_goldens.py directory, execute the following command:

```
python3  validator_goldens.py --validate_goldens_input=output.csv --generate_goldens=golden_data/golden_observations.csv --goldens_must_include="observationAbout:gs://unresolved_mcf/import_validation/top_100k_places.csv" --generate_goldens_property_sets="observationAbout"
```

## **4\. Configuring `validation_config.json`**

Create a file named `validation_config.json` in your import script directory. Paste the configuration below.

This configuration does two things:

* Overrides the default deletion tolerance rule (`check_deleted_records_percent`) to a  threshold as per history deletions & current deletions should not be more than  **0.1%**.  
* Activates the two required golden check rules pointing to the files you created in Section 3\.

JSON

```
{
    "schema_version": "1.0",
    "rules": [
        {
            "rule_id": "check_deleted_records_percent",
            "description": "Strictly enforce historical deletion average threshold of 0.1%",
            "validator": "DELETED_RECORDS_PERCENT",
            "params": {
                "threshold": 0.1
            }
        },
        {
            "rule_id": "check_goldens_summary_report",
            "description": "Validates summary_report.csv against the golden summary data",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["golden_data/golden_summary_report.csv"]
            }
        },
        {
            "rule_id": "check_goldens_output_csv",
            "description": "Verifies the generated output CSV data matches established critical golden records",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["golden_data/golden_observations.csv"],
                "input_files": ["output/observations.csv"]
            }
        }
    ]
}
```

##  **Below is how the validation\_config.json is structured for imports with multiple output CSVs:**

JSON

```
{
    "schema_version": "1.0",
    "rules": [
        {
            "rule_id": "check_deleted_records_percent",
            "description": "Checks that the percentage of deleted records for the entire import is within threshold.",
            "validator": "DELETED_RECORDS_PERCENT",
            "params": { "threshold": 0.1 }
        },
        {
            "rule_id": "check_goldens_national",
            "description": "Validates national and state-level 2000+ data against its golden summary report.",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_summary_report_national.csv"],
                "input_files": ["../../input0/genmcf/summary_report.csv"]
            }
        },
        {
            "rule_id": "check_goldens_before_2000",
            "description": "Validates data before 2000 against its golden summary report.",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_summary_report_before_2000.csv"],
                "input_files": ["../../input1/genmcf/summary_report.csv"]
            }
        },
        {
            "rule_id": "check_goldens_after_2000",
            "description": "Validates county-level 2000+ data against its golden summary report.",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_summary_report_after_2000.csv"],
                "input_files": ["../../input2/genmcf/summary_report.csv"]
            }
        },
        {
            "rule_id": "Check_goldens_output_csv_before_2000",
            "description": "Verifies the generated output CSV data matches established critical golden records",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_observations_before_2000.csv"],
                "input_files": ["../../../../output/USA_Population_Count_by_Race_before_2000.csv"]
            }
        },
        {
            "rule_id": "Check_goldens_output_csv_after_2000",
            "description": "Verifies the generated output CSV data matches established critical golden records",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_observations_after_2000.csv"],
                "input_files": ["../../../../output/USA_Population_Count_by_Race_county_after_2000.csv"]
            }
        },
        {
            "rule_id": "Check_goldens_output_csv_state",
            "description": "Verifies the generated output CSV data matches established critical golden records",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": ["../../../../golden_data/golden_observations_national.csv"],
                "input_files": ["../../../../output/USA_Population_Count_by_Race_National_state_2000.csv"]
            }
        }
    ]
}
```

##  **5\. Activating the Config in `manifest.json`**

The auto-refresh pipeline will only notice your new rules if you explicitly link them in your main `manifest.json` file.

Add the `validation_config_file` parameter pointing to your file inside the `config_overrides` object:

JSON

```
{
    "import_spec": {
        "name": "Your_Import_Name_Here"
    },
    "config_overrides": {
        "validation_config_file": "validation_config.json"
    }
}
```

*(Note: Remember that StatVar updates in this environment are driven systematically via the manifest configuration flags rather than manual file renaming.)*

## **6\. How to Read Validation Failures**

If a future data refresh breaks these rules, the pipeline will fail, and a report JSON will be generated.

* **If `Check_goldens_summary_report` fails:** It means a StatVar or a specific geographic series has unexpectedly disappeared from the pipeline.  
* **If `Check_goldens_output_csv` fails:** The specific rows of data present in your baseline file but missing in the new run will be explicitly listed in the output log.

> **When to update golden files:** Only regenerate golden files using the scripts in if a data change is intentional (e.g., source data deprecation, structural schema updates). Always have the changes reviewed by a peer before committing new golden baselines.

