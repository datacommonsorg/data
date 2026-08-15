# DC import diagnostics authoring

Use this guide when extending
[dc-import-diagnostics](../skills/dc-import-diagnostics/SKILL.md) or its
troubleshooting guidance.

## Preserve the routing boundary

- Factual inspection uses the operation routes in `SKILL.md`.
- Failed, stalled, or unexpected-output requests load the
  [troubleshooting entry point](../skills/dc-import-diagnostics/troubleshooting/troubleshooting.md).
- A named failure domain or suspected cause routes directly to its guide.
- An unknown scenario gathers only enough evidence to identify the failure
  domain.

Keep `SKILL.md` responsible for global scope, safety, and information routes.
Keep `troubleshooting.md` responsible for domain selection and the bounded
fallback.

| User request | Route |
|---|---|
| "Show the current ImportStatus." | Use the factual route in `SKILL.md`. |
| "Why did this import fail?" | Open the troubleshooting entry point. |
| "Check whether this Batch job ran out of memory." | Open the Batch runtime guide and test that hypothesis first. |

## Keep diagnosis hypothesis-driven

### Investigation loop

```text
triage
→ identify the failure domain
→ choose a plausible hypothesis
→ verify or refute
  ├─ confirmed → state the likely cause → mitigate or fix
  ├─ refuted → test the next plausible hypothesis
  └─ unknown → report missing evidence or the next useful check
```

This approach follows the iterative hypothesis-testing model in Google SRE's
[Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).
This guide remains the source of truth for repository-specific structure.

### Apply a hypothesis

For each hypothesis, keep together:

- when to consider it;
- evidence that confirms or refutes it; and
- mitigation when confirmed.

During investigation:

- A user-supplied hypothesis changes investigation order, not the evidence
  needed to confirm it.
- Treat indirect signals as clues.
- Treat unavailable evidence as unknown, not refuted.
- Test only plausible hypotheses. Do not gather all evidence up front.

Example:

1. A failed Batch job routes to the Batch runtime guide.
2. If out of memory is plausible, follow
   [Out of memory](../skills/dc-import-diagnostics/troubleshooting/batch-runtime.md#out-of-memory)
   to verify or refute it.
3. If confirmed, use that guide's mitigation.
4. If refuted, test the next plausible runtime hypothesis.

### Separate diagnosis from evidence collection

- Keep hypotheses, evidence interpretation, mitigation, and short,
  conventional, read-only diagnostic actions in the domain guide.
- Use an operational reference when evidence collection requires
  service-specific identifiers, multiple coordinated commands, non-obvious
  bounds, sensitive inputs, reuse across guides, or consistent failure
  handling.
- Link the hypothesis to that operation. For example, keep bounded Batch log
  commands, filters, and bounds in
  [Cloud Batch operations](../skills/dc-import-diagnostics/references/batch.md).
- Do not repeat skill-wide safety or remediation policy in each guide.
- Do not impose a fixed playbook schema. Use the smallest structure that makes
  the issue clear.

## Add a troubleshooting guide

1. Add one guide for a coherent failure domain or related set of issues.
2. Link it from `troubleshooting/troubleshooting.md` using the symptom language
   users will provide.
3. Link reusable or service-specific evidence operations to their operational
   reference sections.
4. Add representative cases to the
   [diagnostics golden queries](../evals/dc-import-diagnostics.md).

The contract tests ensure every troubleshooting guide is reachable from the
entry point and every referenced file or section exists. Do not add schemas,
IDs, templates, or exhaustive prose tests without a demonstrated need.
