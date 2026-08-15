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

## Keep diagnosis hypothesis-driven

```text
known symptom or minimal triage
→ failure domain
→ plausible hypothesis
→ verify, refute, or leave unknown
→ likely cause
→ mitigation or next action
```

Keep each hypothesis beside:

- when to consider it;
- evidence that confirms or refutes it; and
- mitigation when confirmed.

A user-supplied hypothesis changes investigation order but does not prove the
cause. Treat indirect signals as clues. Treat unavailable evidence as unknown,
not refuted. Test only plausible hypotheses and do not gather all evidence up
front.

Domain guides own interpretation. Operational references, such as
[Cloud Batch operations](../skills/dc-import-diagnostics/references/batch.md),
own commands, identifiers, bounds, and evidence-retrieval failure handling.
When adding an evidence source, add its operation there first and link the
hypothesis to it.

Do not repeat skill-wide safety or remediation policy in each troubleshooting
guide. Do not impose a fixed playbook schema; use the smallest structure that
makes the issue clear.

## Add a troubleshooting guide

1. Add one guide for a coherent failure domain or related set of issues.
2. Link it from `troubleshooting/troubleshooting.md` using the symptom language
   users will provide.
3. Link its evidence steps to the relevant operational reference sections.
4. Add representative cases to the
   [diagnostics golden queries](../evals/dc-import-diagnostics.md).

The contract tests ensure every troubleshooting guide is reachable from the
entry point and every referenced file or section exists. Do not add schemas,
IDs, templates, or exhaustive prose tests without a demonstrated need.
