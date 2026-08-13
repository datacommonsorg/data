# Data Commons import troubleshooting

Primary troubleshooting guide for diagnostic requests routed from
[the import diagnostics skill](../SKILL.md).

## Initial triage

Use this table only when the failure domain is unknown. When the request
identifies a failure domain or suspected cause, go directly to the matching
guide.

1. Identify the affected import, expected behavior, and actual symptom.
2. Use the main skill's current-status route to read the recorded state,
   version, and exact Batch job ID.
3. Evaluate the following table from top to bottom. Gather only the evidence
   required by the first applicable row. Evidence-collection rows continue
   classification; guide and fallback rows stop routing.

| Evidence or symptom | Next action |
|---|---|
| A scheduled execution is expected but no Batch job ID is recorded | Inspect the deployed Scheduler job, report that further attempt visibility is unsupported, and stop. Do not search Workflow or Batch for an attempt. |
| The exact Batch job failed or stopped making progress | Open [Cloud Batch runtime issues](batch-runtime.md). |
| Batch succeeded and an exact version is available | Read its exact import summary, then continue classification. |
| The exact summary reports `VALIDATION` | Classify the failure domain as validation and use the bounded fallback until a validation guide exists. |
| Batch succeeded but the user reports unexpected output | Inspect only the exact summary or selected artifacts needed, or compare the selected version with the last successful version. |
| No condition establishes the failure domain | Use the bounded evidence-first fallback. |

## When no guide matches

Continue with a bounded, evidence-first investigation using the main skill's
information routes and operational references. Report that no specific
troubleshooting guide matched, distinguish observed evidence from inference,
and do not guess a root cause.
