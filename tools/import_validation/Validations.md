# Validation Configuration

The default validations in [validation_config.json](validation_config.json) are
applied for all imports in auto refresh.

To add import-specific validations, create a `validation_config.json` in the
import directory and set `validation_config_file` on the relevant import
specification in `manifest.json` to its import-relative path.

The default and import-specific configurations are merged as follows:

- Rules are matched by `rule_id`.
- A matching import-specific rule is deep-merged into the default rule.
- A new `rule_id` adds a rule.
- `definitions` are deep-merged.
- The import-specific `schema_version` takes precedence when provided.

To override a default validation rule, provide the changed fields under the
same `rule_id`. To disable it, set `enabled` to `false`. Fields inherited from
the default rule, such as `validator`, do not need to be repeated when a rule
is disabled.

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
            "enabled": false
        }
    ]
}
```

## Rule Fields

Each entry in `rules` can contain:

- `rule_id`: Unique identifier used to merge rules and reported as
  `ValidationName`.
- `validator`: Supported validator name. See the
  [validator catalog](README.md#supported-validations).
- `description`: Optional human-readable description.
- `enabled`: Optional boolean controlling whether the rule runs; defaults to
  `true`.
- `scope`: Optional inline scope or named scope reference, such as
  `@population_scope`.
- `params`: Optional validator-specific parameters.

Reusable named scopes can be declared under `definitions.scopes`. An unknown
validator name is logged and skipped. A recognized validator can return
`CONFIG_ERROR` for invalid parameters or `DATA_ERROR` when required input data
is missing or incompatible. These results make the overall validation result
false. See the [framework documentation](README.md) for inputs, execution, and
report formats.

The following section provides additional configuration details for golden
validation.

## Golden Set Validation with `GOLDENS_CHECK`

The `GOLDENS_CHECK` validator ensures that the import contains a specific set of expected records. This is useful for verifying that critical StatVars, Places, or specific metadata combinations are always present in the output.

The validator compares the input data (usually from the `stats` data source) against one or more "golden" files (MCF or CSV).

If any of the combination of values in a row of the golden file is not present
in the input, the validation is treated as a failure.
The missing golden rows are listed in the validation report json.

### Configuration Parameters
- `golden_files`: A path, glob pattern, or list of paths or patterns for golden
  MCF or CSV files to compare against.
- `goldens_key_property`: A list of properties to match on. If not specified, all properties in the golden record must match.
- `input_files`: (Optional) A path, glob pattern, or list of paths or patterns
  for input files to compare with goldens. If not provided, the data source
  defined in the rule's `scope` is used.

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

This will generate the golden files using summary_report.csv as the default input:

```shell
    python3 validator_goldens.py \
      --validate_goldens_input=summary_report.csv \
      --generate_goldens=goldens_data/golden_summary_report.csv \
      --generate_goldens_property_sets="StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods"
```

To validate summary_report.csv against a golden file run the below command:

```shell
   python3 validator_goldens.py \
      --validate_goldens_input=summary_report.csv \
      --validate_goldens=goldens_data/golden_summary_report.csv 
```

To generate goldens for observations that include important
statvars, places and dates, run the following with selected StatVar and
place dcids loaded from txt files:

```shell
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --generate_goldens=golden_data/golden_observations.csv \
      --goldens_must_include="variableMeasured:gs://unresolved_mcf/import_validation/nl_statvars.csv,observationAbout:gs://unresolved_mcf/import_validation/top_100k_places.csv" \
      --generate_goldens_property_sets="variableMeasured|unit|scalingFactor|observationPeriod|measurementMethod,observationAbout,observationDate"
```

To enable goldens validation with files generated above
while relaxing the default deleted records threshold, add the following
validation rules to the validation config:

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
                "golden_files": "golden_data/golden_observations.csv",
                "input_files": "output/observations.csv"
            }
        }
    ]
}
```

