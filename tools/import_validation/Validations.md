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

### Shared Global Golden Baselines in GCS

Common golden baseline lists of prominent StatVars and Places (consolidated across `website` and `mixer` NL embeddings, Topic/SDG/UNDATA configs, Explore landing page queries, Chart configs, and E2E golden test suites) are stored in GCS under `gs://unresolved_mcf/import_validation/`:

- **Global StatVars (2,104 StatVars):** `gs://unresolved_mcf/import_validation/golden_statvars.csv`
- **Global Places (249 Places):** `gs://unresolved_mcf/import_validation/golden_places.csv`
- **Additional NL StatVar & Place lists:** `gs://unresolved_mcf/import_validation/nl_statvars.csv` and `gs://unresolved_mcf/import_validation/top_100k_places.csv`

### Steps to Generate Import-Specific Goldens for a New Import

#### Step 1: Generate `golden_data/golden_summary_report.csv` (StatVars & Metadata)

From the `summary_report.csv` produced by `dc-import genmcf` (either from a local run or `gs://datcom-prod-imports/<import_dir>/<import_name>/<version>/input0/genmcf/summary_report.csv`), generate `golden_data/golden_summary_report.csv` retaining **only the 5 stable metadata columns** (`StatVar|MeasurementMethods|Units|ScalingFactors|observationPeriods`). Do **not** include volatile columns (`NumPlaces`, `NumObservations`, `MinValue`, `MaxValue`, `NumObservationsDates`, `MinDate`, `MaxDate`), which change on routine auto-refresh runs:

```shell
python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=summary_report.csv \
  --generate_goldens=golden_data/golden_summary_report.csv \
  --goldens_must_include="StatVar:gs://unresolved_mcf/import_validation/golden_statvars.csv" \
  --generate_goldens_property_sets="StatVar|MeasurementMethods|Units|ScalingFactors|observationPeriods"
```

*(If a specialized domain import has no overlap with `golden_statvars.csv`, omit `--goldens_must_include` or pass `--goldens_sample_rows=20` to sample up to 20 StatVars from `summary_report.csv`.)*

To validate `summary_report.csv` against the generated golden file:

```shell
python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=summary_report.csv \
  --validate_goldens=golden_data/golden_summary_report.csv
```

#### Step 2: Generate `golden_data/golden_observations.csv` (Places / Observations)

Identify the place column in your import's cleaned output CSV (as mapped to `observationAbout` in the `.tmcf` file — e.g., `observationAbout`, `Place`, `GeoId`, `dcid`, `location`) and generate `golden_data/golden_observations.csv` filtered against `gs://unresolved_mcf/import_validation/golden_places.csv`:

```shell
python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=output/observations.csv \
  --generate_goldens=golden_data/golden_observations.csv \
  --goldens_must_include="observationAbout:gs://unresolved_mcf/import_validation/golden_places.csv" \
  --generate_goldens_property_sets="observationAbout"
```

*(Replace `observationAbout` with your CSV's actual place column name if different. Skip generating `golden_observations.csv` if `observationAbout` is a hardcoded constant in your `.tmcf` such as `observationAbout: dcid:country/USA`.)*

To generate goldens for observations that jointly match prominent StatVars, Places, and dates across multiple property sets, you can also run:

```shell
python3 tools/import_validation/validator_goldens.py \
  --validate_goldens_input=output/observations.csv \
  --generate_goldens=golden_data/golden_observations.csv \
  --goldens_must_include="variableMeasured:gs://unresolved_mcf/import_validation/golden_statvars.csv,observationAbout:gs://unresolved_mcf/import_validation/golden_places.csv" \
  --generate_goldens_property_sets="variableMeasured|unit|scalingFactor|observationPeriod|measurementMethod,observationAbout,observationDate"
```

#### Step 3: Wire `validation_config.json` and `manifest.json`

At runtime in `ImportExecutor`, the merged `validation_config.json` is written to `<import_dir>/<import_name>/<version>/input<N>/validation/validation_config.json` (4 directory levels below `<import_dir>`), and relative paths in `params` are resolved relative to that directory (`../../../../`).

Add `check_goldens_summary_report` and `check_goldens_output_csv` to your import's `validation_config.json`:

```json
{
    "schema_version": "1.0",
    "rules": [
        {
            "rule_id": "check_goldens_summary_report",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": "../../../../golden_data/golden_summary_report.csv"
            }
        },
        {
            "rule_id": "check_goldens_output_csv",
            "description": "Verifies the generated output CSV data matches established critical golden records",
            "validator": "GOLDENS_CHECK",
            "params": {
                "golden_files": "../../../../golden_data/golden_observations.csv",
                "input_files": "../../../../output/observations.csv"
            }
        }
    ]
}
```

Then in `manifest.json`, ensure the import specification references `"validation_config_file"` and includes `"golden_data/*.csv"` in `"source_files"`:

```json
{
    "import_name": "MyImportName",
    "validation_config_file": "validation_config.json",
    "source_files": [
        "golden_data/*.csv"
    ]
}
```

#### Important Caveats for Multi-Input and Multi-Spec Imports

- **Multi-Input Imports (`len(import_inputs) > 1`):** `ImportExecutor` runs `ValidationRunner` in a loop once per `input<N>` directory using the same `validation_config.json`. If `check_goldens_summary_report` omits `input_files`, `ValidationRunner` validates `golden_summary_report.csv` against each `input<N>/genmcf/summary_report.csv` in turn — which fails if different inputs partition different StatVars. Either include only StatVars common to all inputs in `golden_summary_report.csv`, or explicitly pin `"input_files": "../../input0/genmcf/summary_report.csv"` in `check_goldens_summary_report`'s `params`.
- **Multi-Spec Manifests (`len(import_specifications) > 1`):** Use per-specification filenames (`golden_data/golden_summary_report_<import_name>.csv`, `golden_data/golden_observations_<import_name>.csv`, and `validation_config_<import_name>.json`) so specifications in the same directory do not overwrite each other.


