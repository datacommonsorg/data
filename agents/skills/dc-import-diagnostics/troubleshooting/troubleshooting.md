# Data Commons import troubleshooting

Primary troubleshooting guide for diagnostic requests routed from
[the import diagnostics skill](../SKILL.md).

## Route the issue

If the request names a failure domain or suspected cause, use its guide
directly. Otherwise, use current `ImportStatus` and inspect the exact Batch job
or import summary needed to identify the failure domain.

| Scenario | Route |
|---|---|
| A scheduled run did not start and no Batch job ID is recorded | Inspect the deployed Scheduler job. |
| A Batch job failed, stopped making progress, or has a suspected runtime cause | Open [Cloud Batch runtime issues](batch-runtime.md). |
| The user reports a validation failure, or an exact import summary reports `status=VALIDATION` | Open [Import validation failures](validation-failures.md). |

## When no guide matches

Continue with a bounded, evidence-first investigation using the main skill's
information routes and operational references. Report that no specific
troubleshooting guide matched, distinguish observed evidence from inference,
and do not guess a root cause.
