# Import code review guidelines

Apply only recommendations relevant to the changed import behavior. Current
repository contracts and instructions take precedence.

## Manifest and automation

- Validate the selected manifest specification against the current shared
  manifest contract, and verify that every referenced script and input exists.
- Always retain downloaded source files in GCS via `source_files`, alongside
  other operational artifacts (e.g., counter files from `--output_counters`,
  `manifest.json`, or configs); do not confuse source artifacts with import
  inputs.
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
- Resolve local `GOLDENS_CHECK` paths relative to the validation config file
  passed to the runner, and verify that every `golden_files` path or glob
  matches at least one intended golden file.
- For auto-refresh, use the generated
  `<import>/<ImportName>/<version>/input<N>/validation/merged_validation_config.json`
  as the base. For example, reference `<import>/golden_data/golden_summary_report.csv`
  as `../../../../golden_data/golden_summary_report.csv`.

## Download and processing reliability

- Use the shared [Data Commons API wrapper](../../../../util/dc_api_wrapper.py)
  for Data Commons API calls unless it lacks the required functionality.
- Use [download_util.py](../../../../util/download_util.py) or
  [download_util_script.py](../../../../util/download_util_script.py) for
  downloads unless both lack the required functionality.
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
