# Import code review guidelines

Apply only recommendations relevant to the changed import behavior. Current
repository contracts and instructions take precedence.

## Manifest and automation

- Validate the selected manifest specification against the current shared
  manifest contract, and verify that every referenced script and input exists.
- Use `source_files` for source artifacts that must be retained; do not confuse
  source artifacts with import inputs.
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
- Make aggregation, filtering, outlier handling, and date-range decisions
  explicit and testable; avoid arbitrary future-year cutoffs.

## Import validation

- Configure `stat_var_processor` invocations to persist output counters for
  validation.

When reviewing `validation_config*.json` or a manifest change to
`validation_config_file`, read:

- [Import validation framework](../../../../tools/import_validation/README.md)
- [Validation configuration and golden checks](../../../../tools/import_validation/Validations.md)

## Download and processing reliability

- Use `download_file` from the shared
  [download utility](../../../../util/download_util_script.py) for HTTP(S) file
  downloads instead of implementing download logic in individual imports. If
  required behavior is missing, extend the shared utility when the capability
  is reusable; use import-specific logic only for genuinely source-specific
  behavior.
- Consume every page from paginated sources.
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
