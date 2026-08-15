# Data Commons import diagnostics golden queries

Use these cases to evaluate request classification and operation routing for
`dc-import-diagnostics`. Replace `<IMPORT>` with an exact absolute import name,
`<VERSION>` with an exact version, and `<JOB_ID>` with an exact Batch job ID
when running a case.

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

## Troubleshooting routes

| ID | Query | Expected route | Expected behavior |
|---|---|---|---|
| `failed-import-triage` | Why did the current attempt of `<IMPORT>` fail? | `Import troubleshooting` | Read current `ImportStatus`, gather only enough evidence to identify the failure domain, and do not assume a cause. |
| `factual-batch-inspection` | Show the current state and resources for Batch job `<JOB_ID>`. | `Describe one Batch job` | Treat this as factual inspection and do not load troubleshooting guidance. |
| `scheduled-no-batch-id` | The scheduled run for `<IMPORT>` did not start, and current `ImportStatus` has no Batch job ID. Diagnose it. | `Describe and verify a Scheduler job` | Inspect the deployed Scheduler job. |
| `failed-batch-runtime` | Current `ImportStatus` links `<IMPORT>` to Batch job `<JOB_ID>`, and the exact job failed. Why? | `Cloud Batch runtime issues` | Inspect the selected job baseline and test only plausible runtime hypotheses. |
| `stalled-batch-runtime` | Batch job `<JOB_ID>` for `<IMPORT>` is still active but has stopped making progress. Diagnose it. | `Cloud Batch runtime issues` | Inspect the selected job baseline and prioritize hypotheses for an active stalled job. |
| `explicit-oom-hypothesis` | Check whether Batch job `<JOB_ID>` for `<IMPORT>` failed because it ran out of memory. | `Out of memory` | Test OOM first, but do not treat the user's hypothesis as confirmation. |
| `confirmed-oom-evidence` | Batch job `<JOB_ID>` failed, and its task event explicitly reports `OOMKilled`. Diagnose it. | `Out of memory` | Confirm OOM from the explicit task evidence and recommend increasing `resource_limits.memory`. |
| `exit-137-only` | Batch job `<JOB_ID>` failed with exit code 137, and no memory-related event or log is available. Was it OOM? | `Out of memory` | Report OOM as not confirmed; exit code 137 alone is insufficient. |
| `explicit-gc-hypothesis` | Check whether Batch job `<JOB_ID>` for `<IMPORT>` is experiencing Java GC thrashing. | `Java GC thrashing` | Test GC thrashing first, but do not treat the user's hypothesis as confirmation. |
| `confirmed-gc-thrashing` | Bounded logs for Batch job `<JOB_ID>` show repeated Java garbage collection and stage evidence shows little useful progress. Diagnose it. | `Java GC thrashing` | Confirm GC thrashing from both evidence patterns and recommend increasing `resource_limits.memory`. |
| `gc-indirect-only` | Batch job `<JOB_ID>` has run for a long time with high CPU, but no Java GC evidence is available. Is it GC thrashing? | `Java GC thrashing` | Do not confirm GC thrashing; report the result as unknown when runtime evidence is unavailable. |
| `explicit-network-timeout` | Check whether a source request for `<IMPORT>` failed because it timed out. | `Timeout` | Test the timeout hypothesis first, identify the client and timeout stage, and do not treat the user's hypothesis as confirmation. |
| `confirmed-batch-tls` | Batch job `<JOB_ID>` failed while fetching source data, and its bounded evidence reports certificate verification failure. Diagnose it. | `TLS or SSL failure` | Follow the network guide, investigate the certificate or TLS path, and do not recommend disabling certificate verification. |
| `reported-validation` | Validation is failing for version `<VERSION>` of `<IMPORT>`. Diagnose it. | `Import validation failures` | Use the supplied version and confirm its status from the exact import summary before diagnosing the relevant validation artifacts. |
| `validation-domain` | Batch succeeded for `<IMPORT>`, and the exact import summary reports `status=VALIDATION`. Diagnose the failure. | `Import validation failures` | Use the exact summary as confirmation, then inspect only the relevant validation artifacts without guessing a cause. |
| `validation-partial-network` | Version `<VERSION>` of `<IMPORT>` reports `status=VALIDATION` with a missing required source input, and its exact summary records Batch job `<JOB_ID>` whose evidence reports a request read timeout. Diagnose it. | `Import validation failures` | Use only the exact summary's verified `job_id`, then follow the network guide for that execution's request timeout. |
| `unexpected-output` | Batch succeeded for `<IMPORT>`, but version `<VERSION>` produced unexpected output. Diagnose the difference from the last successful version. | `Compare an import version with the last successful version` | Inspect only the exact summary or selected artifacts needed for the comparison. |
| `unclassified-batch` | Batch job `<JOB_ID>` failed, but the evidence matches neither OOM nor Java GC thrashing. Diagnose it. | Bounded troubleshooting fallback | Report an unclassified Batch runtime problem and do not force a memory diagnosis. |
| `missing-runtime-evidence` | Determine whether Batch job `<JOB_ID>` failed from memory pressure, but its task and log evidence are unavailable. | `Out of memory` | Report the hypothesis result as unknown and do not recommend memory as a confirmed fix. |
