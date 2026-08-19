# Data Commons import troubleshooting

Use this entry point for diagnostic requests routed from
[the import diagnostics skill](../SKILL.md).

## Route the issue

- If the request names a failure domain or suspected cause, open its guide.
- Otherwise, use current `ImportStatus` to identify the exact job or version.
- Inspect only the Batch job or import summary needed to identify the failure
  domain.

| Scenario | Route |
|---|---|
| The request asks whether all required source files or requests were acquired | Open [Source acquisition completeness](source-acquisition.md). |
| The request identifies a network, URL-fetch, or download failure without asking about overall acquisition completeness | Open [Network failures](network-failures.md). |
| A scheduled run did not start and no Batch job ID is recorded | Inspect the deployed Scheduler job. |
| A Batch job failed, stopped making progress, or has a suspected runtime cause | Open [Cloud Batch runtime issues](batch-runtime.md). |
| The request asks to debug deleted observations, or a `FAILED` rule maps to `DELETED_RECORDS_COUNT` or `DELETED_RECORDS_PERCENT` | Open [Deleted observation debugging](deleted-observations.md). |
| The user reports a validation failure, or an exact import summary reports `status=VALIDATION` | Open [Import validation failures](validation-failures.md). |

## When no guide matches

- Continue a bounded, evidence-first investigation.
- Use the main skill's information routes and operational references.
- Report that no specific troubleshooting guide matched.
- Distinguish observed evidence from inference.
- Do not guess a root cause.
