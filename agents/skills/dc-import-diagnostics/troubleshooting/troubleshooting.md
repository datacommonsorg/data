# Data Commons import troubleshooting

Primary troubleshooting guide for diagnostic requests routed from
[the import diagnostics skill](../SKILL.md).

## Initial triage

When the scenario is not already established by supplied evidence:

1. Identify the affected import and symptom.
2. Use the main skill's current-status route to read the recorded state,
   version, and exact Batch job ID.
3. Follow only the recorded evidence needed to locate the failure area:
   - For an exact Batch job ID, inspect the job, then its tasks or bounded logs
     only when needed.
   - When a scheduled run has no Batch job ID, inspect the deployed Scheduler
     job and report that further attempt visibility is unsupported.
   - When Batch succeeded but output is unexpected, inspect the exact summary,
     pointer, or artifacts only as needed.
4. Classify the broad failure area and open the matching guide below.

Load only the guide relevant to the observed issue. Do not read every guide.

## Troubleshooting guides

| Scenario | Guide |
|---|---|
| Cloud Batch job failed or stopped making progress | [Cloud Batch runtime issues](batch-runtime.md) |

## When no guide matches

Continue with a bounded, evidence-first investigation using the main skill's
information routes and shared recipes. Report that no specific troubleshooting
guide matched, distinguish observed evidence from inference, and do not guess a
root cause.
