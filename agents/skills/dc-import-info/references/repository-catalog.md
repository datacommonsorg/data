# Repository catalog

Use this path for bounded questions that can be answered entirely from import
manifests, such as finding canonical import names or configured cron intent.

## Supported criteria

- Ranked `import_name` query: exact, case-insensitive exact, prefix, substring,
  then fuzzy.
- Cron configured, cron not configured, or either.
- At most 100 returned imports; use 5 for import selection.

## Procedure

1. Run the repository catalog helper:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/list_imports.py \
     --query=<IMPORT_NAME_QUERY> \
     --autorefresh=<any|configured|not_configured> \
     --limit=<LIMIT>
   ```

2. Automatically select one unique `exact` or `case_insensitive_exact` result.
   For `prefix`, `substring`, or `fuzzy`, use the user's context and clarify if
   multiple candidates remain plausible. Do not select from an empty result.
3. Read the selected `manifest_path`, choose the specification whose
   case-sensitive `import_name` matches the result, and consult the
   [import manifest reference](../../../common/references/import-automation/manifest.md)
   before interpreting its fields.
4. Return the bounded results and all top-level helper metadata: `mode`, match
   strategy, filters, scan/match/return counts, limit, and truncation. Preserve
   repository-relative manifest paths as inline code rather than shortening
   them to basenames or using basename-only link labels.
5. Label every result `repository-configured`. A non-empty cron schedule proves
   configured auto-refresh intent only.

## Boundaries

- Do not attach deployed Scheduler, Workflow, Batch, artifact, run-history, or
  operational status claims to catalog results.
- Use live fleet search when the request includes execution time, status, or
  repeated failures.
- Do not replace the helper with ad hoc repository searches.
