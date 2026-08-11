# Data Commons import troubleshooting

Primary troubleshooting guide for diagnostic requests routed from
[the import diagnostics skill](../SKILL.md).

## Investigation flow

1. Understand the reported symptom and affected import.
2. Use the main skill's information routes and shared recipes to resolve
   required identifiers and gather facts.
3. Identify the last known successful stage or likely failure area.
4. Open the most relevant troubleshooting guide below when one matches.
5. Apply the guide to the observed evidence.
6. Report the likely cause, supporting evidence, remaining unknowns, and next
   action.

Load only the guide relevant to the observed issue. Do not read every guide.

## Troubleshooting guides

| Scenario | Guide |
|---|---|
| Cloud Batch task fails or stalls with evidence of memory pressure | [Cloud Batch memory issues](batch-memory.md) |

## When no guide matches

Continue with a bounded, evidence-first investigation using the main skill's
information routes and shared recipes. Report that no specific troubleshooting
guide matched, distinguish observed evidence from inference, and do not guess a
root cause.
