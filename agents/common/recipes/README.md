# Import-support recipe organization

Recipes are bounded, read-only operations. Keep each recipe small enough that
an agent can load only the command needed for the requested fact.

```text
recipes/
├── README.md
├── local/
│   └── list-imports.md
└── gcp/
    ├── artifact-registry/
    ├── batch/
    ├── gcs/
    ├── logging/
    ├── scheduler/
    └── spanner/
```

## Placement

- Put repository inspection and helpers that make no cloud call in `local/`.
- Put a cloud operation in `gcp/<service>/`, named for the primary GCP service
  it reads.
- Keep operations over several objects from the same service in that service
  folder.
- Place a local Python helper by the cloud service it primarily queries. For
  example, a helper that lists GCS summaries belongs in `gcp/gcs/`.
- Do not add a general `imports/` folder; it does not identify the execution
  boundary or cloud service.

## Composition

Compose a cross-service investigation from atomic recipes. A recipe may link
to a recipe in another service folder when an observed exact identifier can
seed that operation, but it must not copy the other service's commands or run
the linked operation automatically.

The [import evidence flow](../references/import-automation/import-evidence-flow.md)
owns the end-to-end navigation sequence. The
[`dc-import-info` skill](../../skills/dc-import-info/SKILL.md) links directly to
operational recipes and does not load this README during normal execution.

## Recipe contract

Every Markdown file below `local/` or `gcp/` is an operational recipe. It must
define when to use it, required inputs, clarification conditions, its exact
read-only operation, preferred invocation, bounded output, retained evidence,
common failures, and related sources.
