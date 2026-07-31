# Repository catalog

Use this path for bounded questions that can be answered entirely from import
manifests, such as matching import names or configured cron intent.

## Supported criteria

- Case-insensitive `import_name` substring.
- Cron configured, cron not configured, or either.
- At most 100 returned imports.

## Procedure

1. Run the repository catalog helper:

   ```bash
   ./agents/common/run_python.sh \
     agents/common/import_support/list_imports.py \
     --name_contains=<SUBSTRING> \
     --autorefresh=<any|configured|not_configured> \
     --limit=<LIMIT>
   ```

2. Return the bounded, sorted results and all top-level helper metadata:
   `mode`, filters, scan/match/return counts, limit, and truncation. Preserve
   repository-relative manifest paths as inline code rather than shortening
   them to basenames or using basename-only link labels.
3. Label every result `repository-configured`. A non-empty cron schedule proves
   configured auto-refresh intent only.

## Boundaries

- Do not attach deployed Scheduler, Workflow, Batch, artifact, run-history, or
  operational status claims to catalog results.
- Use live fleet search when the request includes execution time, status, or
  repeated failures.
- Do not replace the helper with ad hoc repository searches.
