---
name: dc-import-postmortem-doc
description: >-
  Use this skill to generate a standardized troubleshooting post-mortem document
  from the conversation context after diagnosing or fixing a Data Commons import failure.
---

# Generate Import Troubleshooting Post-Mortem Documentation

Use this skill following a troubleshooting or debugging session for a Data Commons import to generate a comprehensive, standardized post-mortem report. 

These documents form an offline repository in `agents/troubleshooting/` to help engineering teams track failure history, extract failure patterns, and design systemic architectural improvements.

---

## 1. Document Target Path

Always create the post-mortem report at:
```text
agents/troubleshooting/<import_name>/<import_name>_<YYYYMMDD>_<HHMMSS>.md
```
* `<import_name>`: The exact simple name of the import (e.g. `USCensusPEP_Sex`).
* `<YYYYMMDD>`: The UTC date without dashes (e.g. `20260806`).
* `<HHMMSS>`: The current UTC time of document generation (24-hour format, e.g. `102735` for 10:27:35 UTC). This ensures unique filenames even if multiple investigations or runs occur on the same day.

Example:
`agents/troubleshooting/USCensusPEP_Sex/USCensusPEP_Sex_20260806_102735.md`

---

## 2. Evidence Gathering Rules

- **Rely on Context**: Synthesize the post-mortem exclusively from facts, logs, exit codes, and infrastructure identifiers surfaced during the current conversation session.
- **No Extra Cloud Queries**: Do not run additional cloud commands during documentation generation.
- **Explicit Unresolved Values**: If a particular piece of metadata was not queried or discovered (e.g., source commit, workflow ID), record it explicitly as `null` or `not_discovered`. Never invent or guess values.
- **Null Value Formatting**: When values are null or unresolved, write unquoted `null` in the YAML metadata block (not `"null"`) so YAML parsers treat them as true null values rather than literal strings.
- **Use Repository-Relative Paths**: Do NOT use local machine-specific absolute filesystem paths (e.g. `/usr/local/google/home/...`). Always cite files relative to the repository root (e.g. `scripts/us_census/pep/us_pep_sex/process.py`) so documents remain portable across environments.
- **Handle Partial or Unresolved Sessions**: Troubleshooting sessions do not always conclude with a fix or definitive root cause.
  - Set `resolution_status: "RESOLVED"`, `"UNRESOLVED"`, or `"IN_PROGRESS"` in the metadata block.
  - Capture all sections for which evidence was found.
  - If no fix was implemented, replace 'Fix Applied & Verification' with a **'Future Investigation & Next Steps'** section detailing open questions, unverified hypotheses, or required access.

---

## 3. Failure Taxonomy

Populate `failure_category` in the YAML metadata block with one of the standard categories below, and provide more specific detail in `sub_category`:

| `failure_category` | When to Use | Example `sub_category` |
|---|---|---|
| `dependency_drift` | Package/library updates, version mismatches, or deprecated APIs | `pandas_delim_whitespace_removed` |
| `oom_memory_pressure` | Task ran out of memory, kernel OOM-killer invoked, VM hung/unresponsive | `batch_50002_mcf_load_oom` |
| `permission_or_auth_error` | Insufficient IAM permissions, authentication failures, expired API tokens | `gcs_permission_denied` |
| `upstream_source_error` | External data source unavailable, download 404/500, format changed | `download_url_404` |
| `schema_mismatch` | MCF/TMCF syntax errors, unknown StatVar properties or nodes | `unresolved_statvar_property` |
| `code_logic_error` | Python syntax error, unhandled exception, regex mismatch, parsing bug | `index_out_of_range` |
| `infra_timeout` | Batch job or workflow exceeded maximum allotted execution duration | `batch_timeout_exceeded` |
| `unknown` | Cause could not be definitively determined from available evidence | `unresolved_crash` |

---

## 4. Standard Document Template

Every generated troubleshooting document must strictly conform to the following template. Include the execution start time in UTC in the title if known (e.g. `# Troubleshooting Post-Mortem: USCensusPEP_Sex (2026-08-05T01:00:31Z)`), or omit it if unknown:

````markdown
# Troubleshooting Post-Mortem: <IMPORT_NAME>[ (<EXECUTION_START_TIME_UTC>)]

```yaml
import_name: "<IMPORT_NAME>"
date: "<YYYY-MM-DD>"
created_at: "<YYYY-MM-DDTHH:MM:SSZ>"
status: "FAILURE"
resolution_status: "<RESOLVED|UNRESOLVED|IN_PROGRESS>"
failure_category: "<CATEGORY_FROM_TAXONOMY>"
sub_category: "<SPECIFIC_SUB_CATEGORY>"
manifest_path: <REPO_RELATIVE_PATH_OR_NULL>
absolute_import_name: <DIRECTORY_IMPORT_NAME_OR_NULL>
environment: "<prod|test>"
job_id: <BATCH_JOB_ID_OR_NULL>
job_uid: <BATCH_JOB_UID_OR_NULL>
exit_code: <INTEGER_OR_NULL>
image_uri: <DOCKER_IMAGE_URI_OR_NULL>
source_commit: <GIT_COMMIT_OR_NULL>
workflow_id: <WORKFLOW_EXECUTION_ID_OR_NULL>
gcs_latest_version: <GCS_VERSION_URI_OR_NULL>
execution_start_time: <UTC_TIMESTAMP_OR_NULL>
execution_end_time: <UTC_TIMESTAMP_OR_NULL>
```

## 1. Executive Summary & Impact
* **Incident Description**: High-level summary of what happened.
* **Impact**: Affected import output, state in Cloud Spanner `ImportStatus`, and downstream implications.

## 2. Root Cause Analysis
Detailed technical breakdown of why the failure occurred, citing specific error messages, tracebacks, or system constraints.

## 3. Debugging Trail & Evidence
Step-by-step narrative of the investigation:
1. **Initial Discovery**: How the failed state was identified.
2. **Infrastructure Tracing**: Navigating from Spanner record to Batch job and Task list.
3. **Log Extraction**: Key log lines and stack traces retrieved from Cloud Logging.
4. **Environment Audit**: Any package version, resource limit, or configuration checks performed.

## 4. CI/CD & Testing Gap Analysis
* **Why Unit Tests Did Not Catch It**: Explain whether unit tests exist, why they failed to catch the issue (e.g. missing `__init__.py` test discovery bypass, mock differences, missing test coverage).
* **Environment Differences**: Note any dependency drift between local test environments and production Docker images.

## 5. Fix Applied & Verification (or Future Investigation & Next Steps)
* **If Resolved**: Show code diffs/snippets of the fix applied and local test/lint verification outcomes.
* **If Unresolved / In Progress**: List unresolved questions, hypotheses to test, required permissions/access, or follow-up debugging steps.

## 6. Long-Term Prevention & Recommendations
* **Short-Term Actions**: Follow-ups needed for this specific import.
* **Systemic / Architectural Recommendations**: Suggestions to prevent entire classes of similar bugs across Data Commons (e.g. test discovery enforcement, dependency pinning, resource allocation improvements).
````
