# Import validation failures

Use this guide when the user reports a validation failure or an exact import
summary reports `status=VALIDATION`.

## Investigate

1. Confirm the selected version's status from the exact import summary.
2. Inspect only its relevant validation artifacts.
3. Report the observed validation category or error, supporting evidence,
   unknowns, and the next investigation step.

Do not infer a cause from `VALIDATION` alone.

If validation artifacts indicate missing or partial source input, inspect the
associated execution evidence. When that evidence indicates a network-related
failure, follow [Network failures](network-failures.md).

## When no cause is established

- Report the validation failure as unclassified.
- Return to the parent troubleshooting fallback.
