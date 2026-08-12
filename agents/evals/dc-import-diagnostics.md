# Data Commons import diagnostics golden queries

Use these cases to evaluate request classification and operation routing for
`dc-import-diagnostics`. Replace `<IMPORT>` with an exact absolute import name
and `<VERSION>` with an exact version when running a case.

These are routing goldens. They do not prescribe exact answer text or live
cloud results.

## Direct routes

| ID | Query | Expected route | Expected behavior |
|---|---|---|---|
| `current-status` | What is the current status of `<IMPORT>`? | `Query the current import-status snapshot` | Start with the current `ImportStatus`; do not substitute GCS version history. |
| `latest-run` | Inspect the latest run for `<IMPORT>`. | `Query the current import-status snapshot` | Treat `run` as an execution and read the current recorded attempt. |
| `current-attempt-version` | What version is recorded for the current attempt of `<IMPORT>`? | `Query the current import-status snapshot` | Return the exact recorded version when present; do not substitute another version when absent. |
| `recent-versions` | List the five most recent versions for `<IMPORT>`. | `List recent import versions` | Return bounded versions that produced `import_summary.json`; do not claim complete attempt history. |
| `latest-produced-version` | What is the latest version of `<IMPORT>` that produced an import summary? | `List recent import versions` | Select the newest returned summary-backed version. |
| `latest-finalized-version` | Show the latest finalized version for `<IMPORT>`. | `List recent import versions` | Treat the explicit version request as summary-backed version evidence without unnecessary clarification. |
| `last-successful-version` | Find the last successful version of `<IMPORT>`. | `Find the last successful import version` | Read `latest_version.txt`; do not equate technical Batch success with accepted ET output. |
| `accepted-version` | Which version of `<IMPORT>` is currently accepted as ET output? | `Find the last successful import version` | Read `latest_version.txt` and keep loader or serving status out of scope. |
| `selected-summary` | Show the import summary for version `<VERSION>` of `<IMPORT>`. | `Read one import version summary` | Read only that exact version's `import_summary.json`. |
| `selected-artifacts` | List the validation artifacts for version `<VERSION>` of `<IMPORT>`. | `List artifacts for one import version` | List only the requested artifact category below the exact version with an explicit limit. |
| `compare-current-to-successful` | Compare the version recorded for the current attempt of `<IMPORT>` with its last successful version. | `Compare an import version with the last successful version` | Resolve the current attempt's version from `ImportStatus`, the accepted version from `latest_version.txt`, and only the exact summaries or artifacts needed for the comparison. |
| `compare-selected-to-successful` | Compare version `<VERSION>` of `<IMPORT>` with its last successful version. | `Compare an import version with the last successful version` | Use the supplied version directly and do not query `ImportStatus` merely to select it. |
| `compare-latest-to-successful` | Compare the latest version of `<IMPORT>` that produced an import summary with its last successful version. | `Compare an import version with the last successful version` | Select the latest summary-backed version, read `latest_version.txt`, and compare only the requested evidence. |

## Clarification routes

| ID | Query | Expected route | Expected behavior |
|---|---|---|---|
| `ambiguous-latest-import` | Show me the latest import for `<IMPORT>`. | Clarify before routing | Ask whether `latest` means the current run, latest summary-backed version, or last successful version. |
| `ambiguous-current-version` | Show the current version for `<IMPORT>`. | Clarify before routing | Ask whether this means the version recorded for the current attempt or the accepted version. |
| `ambiguous-last-version` | Compare `<VERSION>` with the last version of `<IMPORT>`. | Clarify before routing | Ask whether `last version` means the latest summary-backed version or the last successful version. |
| `ambiguous-latest-comparison` | Compare the latest for `<IMPORT>` with the last successful version. | Clarify before routing | Ask whether `latest` means the current run's recorded version or the latest summary-backed version. |
| `ambiguous-success` | Was the last run of `<IMPORT>` successful? | Clarify before routing | Ask whether success means technical execution success or acceptance as the current ET output; do not silently equate them. |

## Unsupported boundaries

| ID | Query | Expected route | Expected behavior |
|---|---|---|---|
| `all-attempts` | List every run of `<IMPORT>` from the last 30 days. | Unsupported | Explain that complete attempt history is unavailable; do not discover runs by listing Workflow executions or Batch jobs. |
| `workflow-inspection` | Inspect the Workflow execution for the latest run of `<IMPORT>`. | Unsupported | Report that Workflow execution inspection is unsupported. |
| `serving-comparison` | Compare the current ET output of `<IMPORT>` with what is currently served. | Unsupported | Keep loader and serving-system investigation out of scope. |
| `execute-remediation` | Rerun the latest failed attempt of `<IMPORT>`. | Unsupported | Do not execute remediation or mutate cloud resources. |
