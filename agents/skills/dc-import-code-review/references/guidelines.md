# Import code review guidelines

Apply only recommendations relevant to the changed import behavior. Current
repository contracts and instructions take precedence.

## Manifest and automation

- Validate the selected manifest specification against the current shared
  manifest contract, and verify that every referenced script and input exists.
- Write place, StatVar, and schema nodes to separate MCF files.
- Verify that `source_files` patterns cover every original file downloaded from
  the source, including non-data files like HTML and PDF, rather than
  sanitized copies, so each version keeps its raw source data in GCS for
  debugging and source attribution. List other operational artifacts there too
  (e.g., counter files from `--output_counters`, `manifest.json`, or configs);
  do not confuse source artifacts with import inputs.
- Add `cron_schedule`, `user_script_timeout`, and `resource_limits` only when
  the import needs scheduling or an override, and validate them when present.
- Semi-automated imports run on their `cron_schedule` like other auto-refresh
  imports. Require a `cron_schedule` on them, leave
  `config_override.disable_import_workflow` unset, and flag it when set to
  `true`.
- Keep curator contacts valid without prescribing one fixed email value.

## Documentation and organization

- Document the source, dataset coverage, prerequisites, working directory,
  download and processing steps (including any custom preprocessing or
  validation outside `stat_var_processor` and `validation_config.json`),
  important files, testing, and refresh procedure in the import's
  `README.md`, and update it when the change alters these steps.
- Preserve downloaded source files unchanged, and write transformed data to
  separate files.
- Use consistent, descriptive names for new import files; prefer lowercase
  unless source naming or an established import convention requires otherwise.
- [rule-statvar-imports-dir] Put an import under `statvar_imports/` only when
  it runs `stat_var_processor`. Keep its PV map, processor config, and
  `test_data/` fixtures in the import directory, as [rule-svp-unit-tests]
  describes. Put imports whose custom scripts write the output without
  `stat_var_processor` under `scripts/`, together with their configs.
- Declare new dependencies in the repository-supported dependency file.
- [rule-binary-files] Commit text files only; keep archives of any format,
  pickles, and other binary files out of the PR unless they are stored
  through Git LFS. Excel and PDF files are allowed only under `test_data/`;
  tests that need an archive build it at run time from test fixtures.
- Store files larger than 500 KB, including text files such as place
  mappings, in GCS or through Git LFS.
- Keep files the import writes at run time out of the repository, such as
  counter files from `--output_counters` and processor output (`.csv`,
  `.tmcf`, `_stat_vars.mcf`). Fixtures under `test_data/` are the exception.

## Execution and failure handling

- Keep module imports side-effect free by putting executable script logic behind
  a guarded `main` entry point.
- Resolve import file paths relative to the script location rather than the
  repository working directory.
- Ensure critical download or processing failures propagate and produce a
  failing job rather than partial success.
- Catch specific exceptions only when handling or enriching them; preserve the
  original traceback and include safe operational context.
- Check HTTP responses and external-command exit status before accepting their
  output.
- Make directory creation and repeated execution safe, and do not expose
  incomplete output as successful output.
- Use structured logging for operational progress and failures.
- Raise an exception for unrecoverable errors and let it propagate; put the
  details needed to debug it, such as the failed URL, file, or count, in its
  message, which the job log prints. Flag `absl.logging.fatal()` on these
  paths, since it aborts only under `app.run()`.

## Data transformation

- Verify that StatisticalVariable names, mappings, units, and generated schema
  output remain consistent with the transformation.
- [rule-existing-statvar-mcf] When using `stat_var_processor`, pass
  `--existing_statvar_mcf` (e.g.,
  `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`) to reuse existing
  StatisticalVariables and avoid creating duplicate statvar definitions.
- Make aggregation, filtering, outlier handling, and date-range decisions
  explicit and testable; avoid arbitrary future-year cutoffs.
- Retain non-numeric source placeholders (such as `-`) so `stat_var_processor`
  can drop them, or filter out those observations explicitly; convert them to `0`
  only when the source defines them as zero.
- Normalize or match case-insensitively when checking source strings, and
  check only strings needed to process the data.

## StatVar processor imports

### Manifest and schema declaration

- `node_mcf` (under `import_inputs` in `manifest.json`) is mandatory and must
  use a wildcard pattern (e.g., `*.mcf`).
- A separate manual schema change is only required if the import introduces
  new StatVars; declare them in that schema change for the initial import so
  future runs reuse ingested StatVars and only output new ones via `node_mcf`.

### PV map configuration (`*_pvmap.csv`)

- For pvmap key strings with punctuation (such as commas `,`) that can vary or
  change over time, use normalized keys in lowercase without punctuation (and
  normalize input strings accordingly) to ensure resilient lookups.
- Avoid duplicating schema mappings in pvmaps for the same import; instead,
  split the pvmap into reusable files. Within one source directory, keep rows
  that several import specs share in one common pvmap passed to each
  `--pv_map`, and keep long place mappings in a separate pvmap file.

### StatVar remapping (`--statvar_dcid_remap_csv`)

- [rule-statvar-remap] When an import config generates a StatVar DCID that
  must be overridden to a different StatVar, even one with a different
  definition, remap it with `--statvar_dcid_remap_csv`:
  1. Create a remap CSV (e.g., `statvar_remap.csv`) with the header
     `statvar,dcid`:

     ```csv
     statvar,dcid
     RealValue_Amount_EconomicActivity_NetDomesticProduction_PerCapita,RealValue_Amount_EconomicActivity_NetDomesticProduction_AsAFractionOf_Count_Person
     ```

  2. In `manifest.json`:
     - Append `--statvar_dcid_remap_csv=statvar_remap.csv` to the
       `stat_var_processor.py` command under `"scripts"`.
     - Add `"statvar_remap.csv"` under `"source_files"`.

### Metadata configuration

- In `metadata.csv`, omit settings that keep their default in
  `get_default_config()`
  ([config_flags.py](../../../../tools/statvar_importer/config_flags.py)).
  Turning off a feature the processor enables by default, such as
  `reconcile_nodes` or `output_only_new_statvars`, needs a justification in a
  `metadata.csv` comment; verify it against the code or evidence.
- Disabling `generate_schema_mcf` or `generate_statvar_mcf` leaves StatVars
  from later runs undefined, so a manual schema change does not justify it.

## Non-StatVar processor imports

- Persistent StatVars should have a single source of truth. A manual schema
  change is always preferred.
- Unlike `StatVarProcessor` (which dynamically checks if StatVars already
  exist before generating them), non-StatVar processor imports do not perform
  dynamic checks. For non-StatVar processor imports, never include StatVars or
  entities in `import_inputs.node_mcf` in `manifest.json` if they already exist
  in (or are being added to) the Data Commons schema, as this causes
  double-ingestion as instance nodes. Entity imports that add no observations
  are the exception and may list their entity nodes in `node_mcf`, since that
  import is the source of those entities.

## Import validation

- Validate data with `validation_config.json` rules on `summary_report.csv` or
  output files rather than custom Python validation scripts; when a check
  cannot be expressed in `validation_config.json`, require a comment in the
  script explaining why.
- Configure `stat_var_processor` invocations with `--output_counters` to write
  counters to a file (e.g. under `counters/`), and ensure those counter files are
  included in the manifest's `source_files` so they are copied to GCS for
  validation.


When reviewing `validation_config*.json` or a manifest change to
`validation_config_file`, read:

- [Import validation framework](../../../../tools/import_validation/README.md)
- [Validation configuration and golden checks](../../../../tools/import_validation/Validations.md)
- [Import artifact layout](../../../common/references/import-automation/artifact-layout.md)

Then apply these rules:

- Verify that each config meant for auto-refresh is set as
  `validation_config_file` on its import specification in `manifest.json`, and
  that the path exists relative to the import directory; otherwise auto-refresh
  runs only the default validations.
- Resolve local `GOLDENS_CHECK` paths relative to the validation config file
  passed to the runner, and verify that every `golden_files` path or glob
  matches at least one intended golden file.
- For auto-refresh, use the generated
  `<import>/<ImportName>/<version>/input<N>/validation/merged_validation_config.json`
  as the base. For example, reference `<import>/golden_data/golden_summary_report.csv`
  as `../../../../golden_data/golden_summary_report.csv`.
- Require explicit date validation in `validation_config.json` to ensure freshness
  and to catch refreshes that drop the latest data (since
  `golden_summary_report.csv` intentionally excludes `MaxDate`):
  - Read the latest accepted version from GCS:
    `gcloud storage cat gs://<output_bucket>/<import_prefix>/latest_version.txt`
    (use the bucket of the environment whose artifacts the PR, bug, or CL
    links; `datcom-prod-imports` by default).
  - Read the latest summary report:
    `gcloud storage cat gs://<output_bucket>/<import_prefix>/<latest_version>/input<N>/genmcf/summary_report.csv`
  - Inspect the `MaxDate` column across all StatVars in that `summary_report.csv`:
    - Require a date freshness check: use `MAX_DATE_LATEST` for current-year data, or a `SQL_VALIDATOR` rule verifying that `MaxDate` is within allowable lag (months/years) for the dataset's refresh schedule.
    - For imports where StatVars have differing maximum dates across StatVars in `summary_report.csv`, require scoped `SQL_VALIDATOR` rules or per-StatVar checks instead of a blanket `MAX_DATE_CONSISTENT`. If Per-StatVar checks get complicated (e.g. multiple sql conditions), prefer defining rules only for important StatVars.

### Validation config thresholds

- Omit rules in `validation_config.json` that repeat the global defaults in
  `tools/import_validation/validation_config.json` without changing `params`,
  `scope`, or `enabled`.
- A `DELETED_RECORDS_PERCENT` threshold up to `0.1` (0.1%) is allowed by
  default and does not require explicit reasoning or golden files.
- [rule-raised-deletion-threshold] Raise the threshold above `0.1` only with
  evidence, documented in the PR description, bug, SOP, or RCA, that refreshes
  repeatedly delete more than that. For a one-time deletion, recommend
  manually approving that refresh instead, because a raised threshold stays in
  place and lets later data loss pass unnoticed.
- Golden files may accompany higher deletion thresholds to validate expected
  deletions, but are not mandatory; if golden files are provided, verify that
  they adhere to the rules in "Golden files" below.
- For place imports, suggest adding a `DELETED_ENTITY_COUNT` rule (to catch
  deleted place entities) and a `GOLDENS_CHECK` rule in `validation_config.json`
  with a sample of place nodes and properties, since the default
  `DELETED_RECORDS_PERCENT` checks only observation deletion counts.

### Golden files (`golden_data/`)

- Ignore this section if no golden files (under `golden_data/` or referenced
  in `validation_config.json`) are present or modified in the PR.
- When golden files are present, verify they satisfy these conditions:
  - Concise sizing (typically 50–200 rows); never complete production dumps.
  - `golden_summary_report.csv` contains only the allowed fields
    (`StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods`)
    and filters statvars against
    `gs://unresolved_mcf/import_validation/nl_statvars.csv`.
  - `golden_observations.csv` contains only the unique `observationAbout`
    field and filters places against
    `gs://unresolved_mcf/import_validation/top_100k_places.csv`.
  - Naming is standardized, paths in `validation_config.json` match, and
    `"golden_data/*.csv"` is included under `source_files` in
    `manifest.json`.
- Keep existing golden files. If a PR deletes one, verify that the PR
  description or bug clearly justifies the deletion.
- If golden files do not satisfy these conditions, generate or fix them using
  [validator_goldens.py](../../../../tools/import_validation/validator_goldens.py):
  - **Summary report**:

    ```bash
    python3 validator_goldens.py \
      --validate_goldens_input=summary_report.csv \
      --generate_goldens=golden_data/golden_summary_report.csv \
      --goldens_must_include="StatVar:gs://unresolved_mcf/import_validation/nl_statvars.csv" \
      --generate_goldens_property_sets="StatVar|NumPlaces|MinDate|MeasurementMethods|Units|ScalingFactors|observationPeriods"
    ```

  - **Observations (places only)**:

    ```bash
    python3 validator_goldens.py \
      --validate_goldens_input=output/observations.csv \
      --generate_goldens=golden_data/golden_observations.csv \
      --goldens_must_include="observationAbout:gs://unresolved_mcf/import_validation/top_100k_places.csv" \
      --generate_goldens_property_sets="observationAbout"
    ```

## SQL queries

- Actively identify and suggest query simplifications during code review to
  improve readability, conciseness, and maintainability.
- Use `IN (...)` instead of chained `OR =` (e.g.,
  `WHERE category IN ('A', 'B', 'C')`).
- Use `BETWEEN` for continuous ranges instead of chained `>= AND <=` (e.g.,
  `WHERE NumObservations BETWEEN 10 AND 500`).
- Consolidate multiple token variations and chained `OR LIKE` conditions into
  a single regular expression using `regexp_matches()`:

  ```sql
  -- Prefer:
  WHERE regexp_matches(StatVar, '_ToCurrency_(EUR|INR|GBP|JPY)$')
  -- Avoid:
  WHERE StatVar LIKE '%_ToCurrency_EUR' OR StatVar LIKE '%_ToCurrency_INR' OR ...
  ```

## Download and processing reliability

- Prefer the shared helpers in [util/](../../../../util/README.md) over new code that
  does the same job, such as [mcf_dict_util.py](../../../../util/mcf_dict_util.py)
  for reading, editing, and writing MCF, and
  [file_util.py](../../../../util/file_util.py) or
  [gcs_file.py](../../../../util/gcs_file.py) for local and GCS file operations.
- Use the shared [Data Commons API wrapper](../../../../util/dc_api_wrapper.py)
  for Data Commons API calls unless it lacks the required functionality.
- Use [download_util.py](../../../../util/download_util.py) or
  [download_util_script.py](../../../../util/download_util_script.py) for
  downloads unless both lack the required functionality.
- Use [xml_to_json.py](../../../../util/xml_to_json.py) to convert XML source
  files to JSON.
- Use [sdmx_cli.py](../../../../tools/sdmx_import/sdmx_cli.py) for SDMX
  downloads. When it lacks the required functionality, use the `sdmx1` library
  it is built on instead of custom SDMX requests or parsing.
- Log each outbound request's method, sanitized URL, query parameters, and
  request body. Redact credentials and sensitive data.
- Consume every page from paginated sources.
- Reuse HTTP connections via `requests.Session` when issuing frequent
  availability checks (e.g., repeated `HEAD` requests) to avoid connection
  overhead and server throttling.
- Bound requests and retries with timeouts, limited attempts, and backoff;
  distinguish transient failures from permanent ones.
- Make resume behavior idempotent, and ensure counters count unique successful
  work across retries.
- Publish outputs atomically so partial downloads or transformations cannot
  appear successful.
- Download fresh data from the source on each run rather than reusing cached
  files; for large downloads, reuse a cached file only when HTTP headers (such
  as `ETag` or `Last-Modified`) confirm the source data is unchanged.
- Verify that download scripts for periodic or annual sources automatically
  discover or download future years (such as `2027`) when source URLs follow
  a predictable pattern, rather than relying only on a hardcoded year-to-URL
  map.
- [rule-url-access] When URLs are added or modified, verify that they exist and
  are accessible from GCP virtual machines, where import jobs run.
- Inspect both HTTP status codes and page body content to catch soft 404s
  (e.g., pages returning HTTP 200 but rendering '404', 'Not Found', or
  redirecting to an error landing page).

## Security

- Disabling SSL/TLS certificate verification (e.g., `verify=False` in Python
  requests) is strongly discouraged, as it allows downloading data from
  unverified sources.
- If certificate verification must be disabled, ensure:
  - A compelling rationale and justification are documented in the PR and
    bug.
  - The workaround is strictly temporary and time-bound.
  - An explicit `TODO` comment is placed in the code explaining why
    verification is bypassed and tracking its re-enablement.

## Tests

- In general, write unit tests for imports focusing specifically on custom
  code/fixtures, such as testing the downloader, processing, etc. Test
  important success, failure, retry, pagination, and data-transformation paths
  with representative fixtures.
- Keep test fixture files (under `test_data/` or test directories)
  representative and strictly limited in size—target < 100 KB (hard cap of
  500 KB) and under 100 rows; never check in full raw downloads or
  multi-megabyte production dumps as test fixtures (for golden files, see
  "Golden files").
- [rule-svp-unit-tests] For imports using `stat_var_processor`, ensure
  `test_data/` fixtures with sample inputs and expected outputs exist. Each
  input must have the same format as the files the import passes to
  `--input_data`, and each expected output must be the `.csv` and `.tmcf`
  files `stat_var_processor` writes for that input, so the fixtures can be fed
  to the processor and compared directly. Expected `.mcf` outputs are
  optional. Keep `stat_var_processor` out of unit tests; test the PV map and
  config through these fixtures as
  [Create test data](../../../../tools/statvar_importer/README.md#create-test-data)
  describes. Report as P1 any `*_test.py` that runs it, whether by import or
  subprocess and even when hermetic.
- Keep each test input paired with its expected CSV or TMCF output.
  `stat_var_processor` imports use `test_data/` per [rule-svp-unit-tests];
  other imports may use any layout.
- When import logic, schema mappings, or transformations change, evaluate
  whether existing `test_data/` fixtures must be updated to align with the new
  logic.
- If content is identical, prefer sharing test data files across test inputs
  within an import rather than duplicating fixtures.
- Verify that every directory from the top-level import folder (`scripts/` or
  `statvar_imports/`) down to each `*_test.py` file has an `__init__.py`, and
  report a missing one as P1; `./run_tests.sh` uses `unittest discover`, which
  skips directories without one, so those tests never run and the check still
  passes.
