# Resolve a Data Commons import

Recipe ID: `repository.resolve-import`

## Use when

An exact `import_name` must be mapped to its manifest and local code.

## Required inputs

- Globally unique manifest `import_name`.
- `data` repository as the working directory.

## Clarify when

The user supplied only a display name or more than one canonical match exists.

## Read-only operation

```bash
./agents/common/run_python.sh \
  agents/common/import_support/resolve_import.py \
  --import_name=<IMPORT_NAME>
```

## Preferred invocation

Use the command above. Do not replace it with an unbounded repository search.

## Expected output

JSON identity, manifest/specification, configured refresh settings, and
existing referenced repository paths.

## Required bounds

Scan only `statvar_imports/**/manifest.json` and
`scripts/**/manifest.json`.

## Evidence to retain

Manifest path, specification index, absolute import name, and source paths.

## Common failures

Zero matches, duplicate names, malformed manifests, or an invalid explicit
manifest path.

## Related repository sources

The two manifest roots and `import-automation/executor/app/executor/import_target.py`.
