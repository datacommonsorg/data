# Import validation failures

Use this guide when the user reports a validation failure or an exact import
summary reports `status=VALIDATION`.

## Read the owning contracts

- [Validation framework](../../../../tools/import_validation/README.md)
- [Validation rule parameters](../../../../tools/import_validation/Validations.md)
- [Import Differ](../../../../tools/import_differ/README.md)
- `<IMPORT_REPO>/docs/usage.md` for `report.json` and `summary_report.csv`
- [Import automation](../../../../import-automation/README.md)

Read only the contracts needed for the failed rule.

## Investigate

1. Read the selected version's exact summary by following
   [Read one import version summary](../references/gcs.md#read-one-import-version-summary).
2. Inspect `input<N>/validation/validation_output.csv` for each input in that
   version. Start with rows whose `Status` is not `PASSED`.
3. Use `ValidationName`, `Status`, `Message`, `Details`, and
   `ValidationParams` to identify the rule and its evidence source.
4. Use `merged_validation_config.json` when present to match `ValidationName`
   to its validator. Otherwise use correlated historical configuration
   evidence; if unavailable, report the mapping as unknown.
5. Report the confirmed validation category or cause, supporting evidence,
   unknowns, and the next investigation step.

Do not infer a cause from `VALIDATION` alone.

## Route the result

| Result | Next check |
|---|---|
| `FAILED` | Inspect the source and parameters used by that validator. |
| `CONFIG_ERROR` | Inspect the effective rule configuration and parameters. |
| `DATA_ERROR` | Inspect the named source artifact for missing or invalid data. |
| No `validation_output.csv` | Use historical configuration when available; otherwise report it as unknown. Inspect the exact execution for validation-runner failure. |

- Check the selected version's `manifest.json` for
  `import_specifications[].config_override.ignore_validation_status`.
- If validation failed but the candidate reached `STAGING` or `SKIP`, report
  that validation did not block candidate progression.
- If the manifest does not account for this, report the configuration source as
  unknown unless exact non-secret execution evidence identifies it.

If validation artifacts indicate missing or partial source input, inspect the
execution identified by the exact summary's verified `job_id`. If that ID is
missing or mismatched, report the execution evidence as unavailable; do not
substitute current `ImportStatus` or another job. When the selected execution's
evidence indicates a network-related failure, follow
[Network failures](network-failures.md).

## Deleted observation failures

If a `FAILED` rule maps to `DELETED_RECORDS_COUNT` or
`DELETED_RECORDS_PERCENT`, the validation row confirms that deleted
observations exceeded its configured threshold. Continue with
[Deleted observation debugging](deleted-observations.md).

A `DATA_ERROR` from either validator indicates missing or invalid differ data;
handle it as a validation data error instead of a confirmed deletion failure.

## When no cause is established

Report the validation failure as unclassified and return to the parent
troubleshooting fallback.
