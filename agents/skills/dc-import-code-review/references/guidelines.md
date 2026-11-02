# Import code review guidelines

Apply only recommendations relevant to the changed import behavior. Current
repository contracts and instructions take precedence.

## Manifest and automation

- Validate the selected manifest specification against the current shared
  manifest contract, and verify that every referenced script and input exists.
- Ensure `manifest.json` includes `node_mcf` under `import_inputs` pointing to
  generated schema/statvar MCF files (e.g., `output/*.mcf`).
- Verify that `source_files` patterns cover every source file the download
  step saves, so each version keeps its source data for debugging and source
  attribution. List other operational artifacts there too (e.g., counter
  files from `--output_counters`, `manifest.json`, or configs); do not
  confuse source artifacts with import inputs.
- Add `cron_schedule`, `user_script_timeout`, and `resource_limits` only when
  the import needs scheduling or an override, and validate them when present.
- Keep curator contacts valid without prescribing one fixed email value.

## Documentation and organization

- Document the source, dataset coverage, prerequisites, working directory,
  download and processing steps, important files, testing, and refresh
  procedure in `README.md`.
- Preserve downloaded source files unchanged, and write transformed data to
  separate files.
- Use consistent, descriptive names for new import files; prefer lowercase
  unless source naming or an established import convention requires otherwise.
- Keep test inputs and expected CSV or TMCF outputs clearly paired without
  requiring one universal test-directory layout.
- Declare new dependencies in the repository-supported dependency file.

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
- Use structured logging for operational progress and failures; do not assume
  that a logging severity terminates execution.

## Data transformation

- Verify that StatisticalVariable names, mappings, units, and generated schema
  output remain consistent with the transformation.
- When using `stat_var_processor`, pass `--existing_statvar_mcf` (e.g.,
  `gs://unresolved_mcf/scripts/statvar/stat_vars.mcf`) to reuse existing
  StatisticalVariables and avoid creating duplicate statvar definitions.
- Make aggregation, filtering, outlier handling, and date-range decisions
  explicit and testable; avoid arbitrary future-year cutoffs.

## Import validation

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

## Tests

- Test important success, failure, retry, pagination, and data-transformation
  paths with representative fixtures.
- Keep checked-in fixtures representative and generally no more than 100
  records.
- Verify that every directory from the top-level import folder (`scripts/` or
  `statvar_imports/`) down to each `*_test.py` file has an `__init__.py`, and
  report a missing one as P1; `./run_tests.sh` uses `unittest discover`, which
  skips directories without one, so those tests never run and the check still
  passes.
