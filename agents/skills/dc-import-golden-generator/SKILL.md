---
name: dc-import-golden-generator
description: >-
  Generates StatVar and Place golden validation CSVs (golden_summary_report.csv
  and golden_observations.csv) and wires GOLDENS_CHECK rules in
  validation_config.json and manifest.json for Data Commons imports under
  scripts/** and statvar_imports/**. Use when adding golden validations to a
  new or existing import, refreshing golden baselines from local outputs or
  GCS auto-refresh artifacts, or configuring GOLDENS_CHECK rules. Do not use
  for code review or runtime failure diagnosis.
---

# Generate StatVar and Place Goldens for Data Commons Imports

Generate deterministic StatVar summary goldens (`golden_data/golden_summary_report*.csv`) and Place observation goldens (`golden_data/golden_observations*.csv`), wire `GOLDENS_CHECK` rules in `validation_config*.json` and `manifest.json`, and verify that every golden record passes `tools/import_validation/validator_goldens.py`.

## Required inputs

| Input | Resolution |
|---|---|
| `<IMPORT_DIR>` | Repository-relative path to the directory containing `manifest.json` under `scripts/**` or `statvar_imports/**`. Ask if missing or ambiguous. |

## References and shared baselines

Load these references only when needed:

- [Import manifest reference](../../common/references/import-automation/manifest.md) for `manifest.json` fields (`import_specifications`, `import_inputs`, `source_files`, `validation_config_file`).
- [Import artifact layout](../../common/references/import-automation/artifact-layout.md) for auto-refresh GCS version pointers (`latest_version.txt`, `staging_version.txt`) and `input<N>/genmcf/summary_report.csv` paths.
- [Import validation configuration](../../../tools/import_validation/Validations.md) for `GOLDENS_CHECK` parameters and `validator_goldens.py` flags.

Shared global golden baselines in GCS and the in-repository generator script:

- **Global StatVars (2,147 StatVars from Website, Mixer, and Data Release deletion bugs):** `gs://unresolved_mcf/import_validation/golden_statvars.csv`
- **Global Places (249 Places from Website and Mixer):** `gs://unresolved_mcf/import_validation/golden_places.csv`
- **Automated Per-Import Generator Script:** `tools/import_validation/generate_import_goldens.py` (also mirrored at `gs://unresolved_mcf/import_validation/generate_import_goldens.py`)

## Python execution

- Give a user-provided Python environment highest priority. Otherwise, use the repository-local virtual environment at `.env/`.
- Run Python commands with `.env/bin/python` from the repository root (`git rev-parse --show-toplevel`).
- If `.env/` is missing or dependencies are stale, run `./run_tests.sh -r`, then retry.
- Report an unusable environment rather than falling back to global `python` or `python3`.

## Step 1 - Inspect manifest specifications and select the artifact source

1. Read `<IMPORT_DIR>/manifest.json` and enumerate every object in `import_specifications`:
   - Record `import_name`, `import_inputs` (`template_mcf`, `cleaned_csv`), `validation_config_file`, and `source_files`.
   - Distinguish **single-spec manifests** (`len(import_specifications) == 1`) from **multi-spec manifests** (`len(import_specifications) > 1`).
   - Distinguish **single-input specs** (`len(import_inputs) == 1`) from **multi-input specs** (`len(import_inputs) > 1`).
2. Read each referenced `.tmcf` file to determine how `observationAbout` is mapped:
   - **Direct column mapping** (`observationAbout: C:<table>-><col>`): record `<col>` as `<PLACE_COL>`.
   - **Entity node mapping** (`observationAbout: E:<table>->E<N>`): inspect `Node: E:<table>->E<N>` in the `.tmcf` and record the column mapped to `dcid` (or `isoCode`, `wikidataId`, `fips52AlphaCode`) as `<PLACE_COL>`.
   - **Hardcoded constant** (such as `observationAbout: dcid:country/USA` with no CSV column reference): record `<PLACE_COL>` as `CONSTANT_PLACE` and skip Step 3 (`golden_observations*.csv`).
3. Choose the artifact source branch:
   - **Branch A - Existing auto-refresh import in `gs://datcom-prod-imports`**: When the import has already run in auto-refresh (`gs://datcom-prod-imports/<IMPORT_DIR>/<import_name>/latest_version.txt` or `staging_version.txt` exists) and no newer local output is specified, run the automated generator:
     ```bash
     .env/bin/python tools/import_validation/generate_import_goldens.py \
       --manifest <IMPORT_DIR> --force-refresh --apply
     ```
     Then proceed directly to **Step 5** to verify all generated files.
   - **Branch B - New import or local outputs**: When generating goldens from local `summary_report.csv` (produced by `dc-import genmcf`) and local `<cleaned_csv>` files, either pass them directly to `generate_import_goldens.py`:
     ```bash
     .env/bin/python tools/import_validation/generate_import_goldens.py \
       --manifest <IMPORT_DIR> \
       --summary-report <SUMMARY_REPORT_CSV> \
       --cleaned-csv <CLEANED_CSV> \
       --apply
     ```
     or execute **Step 2**, **Step 3**, **Step 4**, and **Step 5** manually using `tools/import_validation/validator_goldens.py`.

**Completion criterion:** Every `import_specification` in `<IMPORT_DIR>/manifest.json` is listed with its `<PLACE_COL>` (or `CONSTANT_PLACE`), input count, and artifact source (`GCS` or `Local`).

## Step 2 - Generate StatVar summary goldens

Generate `<IMPORT_DIR>/golden_data/golden_summary_report.csv` (or `golden_data/golden_summary_report_<import_name>.csv` for multi-spec manifests) from `summary_report.csv`:

```bash
.env/bin/python tools/import_validation/validator_goldens.py \
  --validate_goldens_input=<SUMMARY_REPORT_CSV> \
  --generate_goldens=<IMPORT_DIR>/golden_data/<SUMMARY_GOLDEN_FILENAME> \
  --goldens_must_include="StatVar:gs://unresolved_mcf/import_validation/golden_statvars.csv" \
  --generate_goldens_property_sets="StatVar|MeasurementMethods|Units|ScalingFactors|observationPeriods"
```

Enforce these summary golden invariants:

- **Retain only the 5 stable columns:** Keep only `StatVar`, `MeasurementMethods`, `Units`, `ScalingFactors`, and `observationPeriods` (omitting any of the 4 metadata columns that are empty/`NA` across selected rows).
- **Exclude volatile columns:** Keep `NumPlaces`, `NumObservations`, `MinValue`, `MaxValue`, `NumObservationsDates`, `MinDate`, and `MaxDate` out of `golden_summary_report*.csv` so routine data refreshes do not fail on expected growth.
- **Fallback for domain-specific StatVars:** If the intersection with `golden_statvars.csv` yields 0 rows, rerun without `--goldens_must_include` and pass `--goldens_sample_rows=20` to sample up to 20 StatVars from `<SUMMARY_REPORT_CSV>`.

**Completion criterion:** `<IMPORT_DIR>/golden_data/<SUMMARY_GOLDEN_FILENAME>` exists, contains at least 1 data row, and every header column belongs to `{StatVar, MeasurementMethods, Units, ScalingFactors, observationPeriods}`.

## Step 3 - Generate Place observation goldens

Skip this step when `<PLACE_COL>` is `CONSTANT_PLACE` or when `<cleaned_csv>` contains only non-observation schema/entity definitions. Otherwise, generate `<IMPORT_DIR>/golden_data/golden_observations.csv` (or `golden_data/golden_observations_<import_name>.csv` for multi-spec manifests) from `<CLEANED_CSV>`:

```bash
.env/bin/python tools/import_validation/validator_goldens.py \
  --validate_goldens_input=<CLEANED_CSV> \
  --generate_goldens=<IMPORT_DIR>/golden_data/<OBS_GOLDEN_FILENAME> \
  --goldens_must_include="<PLACE_COL>:gs://unresolved_mcf/import_validation/golden_places.csv" \
  --generate_goldens_property_sets="<PLACE_COL>"
```

Enforce these place golden invariants:

- **Preserve exact column header case:** Use the exact case-sensitive `<PLACE_COL>` header from `<CLEANED_CSV>` (for example `observationAbout`, `GeoId`, `Place`, `LOCATION`, or `dcid`).
- **Fallback for regional datasets:** If the intersection with `golden_places.csv` yields 0 rows, rerun without `--goldens_must_include` and pass `--goldens_sample_rows=20`.
- **Write bare DCIDs without namespace prefixes:** Strip `dcid:`, `dcs:`, and `schema:` prefixes from all values in 1-column `golden_observations*.csv` files. `util/file_util.py` runs `csv.Sniffer().sniff(sample, delimiters=';,\t|:')`; keeping `dcid:` in a 1-column CSV causes `csv.Sniffer` to select `:` as the column delimiter and fail validation.

**Completion criterion:** `<IMPORT_DIR>/golden_data/<OBS_GOLDEN_FILENAME>` exists, its single column header matches `<PLACE_COL>` in `<CLEANED_CSV>` case-sensitively, and zero rows contain `dcid:`, `dcs:`, or `schema:` prefixes.

## Step 4 - Wire validation_config.json and manifest.json

1. Create or update `<IMPORT_DIR>/validation_config.json` (or `validation_config_<import_name>.json` for multi-spec manifests), preserving all existing rules (`DELETED_RECORDS_PERCENT`, `MAX_DATE_CONSISTENT`, `MAX_DATE_LATEST`, `SQL_VALIDATOR`, etc.):
   ```json
   {
       "schema_version": "1.0",
       "rules": [
           {
               "rule_id": "check_goldens_summary_report",
               "description": "Verifies that expected StatVars and metadata in golden_summary_report.csv are present in the summary report",
               "validator": "GOLDENS_CHECK",
               "params": {
                   "golden_files": "../../../../golden_data/<SUMMARY_GOLDEN_FILENAME>"
               }
           },
           {
               "rule_id": "check_goldens_output_csv",
               "description": "Verifies the generated output CSV data matches established critical golden records",
               "validator": "GOLDENS_CHECK",
               "params": {
                   "golden_files": "../../../../golden_data/<OBS_GOLDEN_FILENAME>",
                   "input_files": "../../../../<CLEANED_CSV_REL>"
               }
           }
       ]
   }
   ```
2. Apply these path and multi-input rules to `validation_config*.json`:
   - **Use `../../../../` for import-relative paths:** At runtime in `ImportExecutor`, the merged config is written to `<import_dir>/<import_name>/<version>/input<N>/validation/validation_config.json` (4 levels below `<import_dir>`). Always prefix paths targeting `<import_dir>/golden_data/...` or `<import_dir>/<cleaned_csv>` with `../../../../`.
   - **Pin `input_files` on multi-input specs (`len(import_inputs) > 1`):** `ImportExecutor` executes the same `validation_config.json` once per `input<N>` directory. When `len(import_inputs) > 1`, either pin `"input_files": "../../input0/genmcf/summary_report.csv"` inside `check_goldens_summary_report.params` or restrict `golden_summary_report*.csv` to StatVars present in every `input<N>/genmcf/summary_report.csv`.
3. Update `<IMPORT_DIR>/manifest.json`:
   - Set `"validation_config_file": "<VALIDATION_CONFIG_FILENAME>"` on the target specification.
   - Add `"golden_data/*.csv"` to `"source_files"`.
   - If the specification contains a legacy `"source_file"` (singular) key, merge its entries into `"source_files"` and remove `"source_file"`.

**Completion criterion:** `<IMPORT_DIR>/manifest.json` and `<IMPORT_DIR>/<VALIDATION_CONFIG_FILENAME>` parse as valid JSON, `"golden_data/*.csv"` is in `"source_files"`, and every relative path in `params` resolves from `<IMPORT_DIR>/<import_name>/<version>/input0/validation/` to an existing target path.

## Step 5 - Verify golden files with validator_goldens.py

Run `validator_goldens.py` in validation mode against every generated golden file and its corresponding input CSV:

```bash
.env/bin/python tools/import_validation/validator_goldens.py \
  --validate_goldens_input=<SUMMARY_REPORT_CSV> \
  --validate_goldens=<IMPORT_DIR>/golden_data/<SUMMARY_GOLDEN_FILENAME>

.env/bin/python tools/import_validation/validator_goldens.py \
  --validate_goldens_input=<CLEANED_CSV> \
  --validate_goldens=<IMPORT_DIR>/golden_data/<OBS_GOLDEN_FILENAME>
```

**Completion criterion:** Every `validator_goldens.py` command exits `0` and logs `Goldens validation succeeded` with zero missing golden records.
