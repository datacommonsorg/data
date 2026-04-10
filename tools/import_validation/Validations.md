# Validation Config.

The default validations in [validation_config.json](validation_config.json) are
applied for all imports in auto refresh.

To add additional  import specific validations, create a validation_config.json
in the import script folder and add it to the
config_overrides.validation_config_file parameter in the manifest.json.

To override or disable a default validation rule, copy the rule to the
import specific config with the same rule id and
set the `enabled` setting to false.

Here is an example to override the deleted records threshold and
disable lint check for a specific import.
```json
{
    "schema_version": "1.0",
    "rules": [
        {
            "rule_id": "check_deleted_records_percent",
            "description": "Override default threshold to 10%",
            "validator": "DELETED_RECORDS_PERCENT",
            "params": {
                "threshold": 10
            }
        },
        {
            "rule_id": "check_lint_error_count",
            "enabled": False,
        }
    ]
}
```

Here are some additional details for each validation rule.

## Golden Set Validation with `GOLDENS_CHECK`

The `GOLDENS_CHECK` validator ensures that the import contains a specific set of expected records. This is useful for verifying that critical StatVars, Places, or specific metadata combinations are always present in the output.

The validator compares the input data (usually from the `stats` data source) against one or more "golden" files (MCF or CSV).

### Configuration Parameters
- `golden_files`: A list or glob pattern of golden MCF or CSV files to compare against.
- `goldens_key_property`: A list of properties to match on. If not specified, all properties in the golden record must match.
- `input_files`: (Optional) A list of glob pattern of input files to be compared with goldens. If not provided, the data source defined in the rule's `scope` is used.

### GOLDENS_CHECK Validator Example

**Rule:** "Ensure that observations for `Count_Person` and `Median_Age_Person` are present in the import as defined in our critical golden set."

```json
  {
      "rule_id": "verify_critical_obs",
      "validator": "GOLDENS_CHECK",
      "params": {
          "golden_files": ["golden_data/critical_stats.csv"],
          "input_files": "processed_obs.csv"
      }
  }
```

The goldens can be generated from a CSV file using the `validator_goldens.py`
script.

To generate goldens for the summary_report.csv to verify that all the expected
StatVars are generated with the corresponding number of places and dates, run
the following:

```shell
    python3 validator_goldens.py \
      --validate_goldens_input=summary_report.csv \
      --generate_goldens=goldens_data/golden_summary_report.csv \
      --generate_goldens_property_sets="StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods"
```

To generate goldens for observations that include important
statvars, places and dates, run the following with selected StatVar and
place dcids loaded from txt files:

```shell
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --generate_goldens=golden_data/golden_observations.csv \
      --goldens_must_include="variableMeasured:gs://unresolved_mcf/import_validation/nl_statvars.csv,observationAbout:gs://unresolved_mcf/import_validation/top_100k_places.csv" \
      --generate_goldens_property_sets="variableMeasured,observationAbout,observationDate"
```


To enable goldens validation with files generated above
while relaxing the default deleted records threshold, add the following
valiation rules to the validation config:

```json
{
    "schema_version": "1.0",
    "rules": [
        {
            "rule_id": "check_deleted_records_percent",
            "description": "Relax default deleted records threshold to 10% with additional goldens check to catch statvar series deletions",
            "validator": "DELETED_RECORDS_PERCENT",
            "params": {
                "threshold": 10
            }
        },
        {
            "rule_id": "check_golden_summary_report",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": "golden_data/golden_summary_report.csv"
            }
        },
        {
            "rule_id": "check_golden_observations_statvar_places_dates",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": "golden_data/golden_observations.csv"
                "input_files": "output/observations.csv",
            }
        }
    ]
}
```




