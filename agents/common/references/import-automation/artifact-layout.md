# Import artifact layout

For the current Cloud Batch executor, derive a candidate base from the effective
environment's output bucket and the absolute import name:

```text
gs://<bucket>/<manifest-directory>/<import-name>/
├── staging_version.txt
├── latest_version.txt
└── <version>/
    ├── manifest.json
    ├── source_files/...
    ├── provenance/genmcf/import_metadata_mcf.mcf
    ├── input<N>/genmcf/*.mcf
    ├── input<N>/genmcf/report.json
    ├── input<N>/genmcf/summary_report.csv
    ├── input<N>/validation/validation_output.csv
    ├── input<N>/validation/differ_summary.json
    ├── input<N>/validation/nodes-added.mcf
    ├── input<N>/validation/nodes-deleted.mcf
    ├── input<N>/validation/nodes-modified.mcf
    └── import_summary.json
```

This is a candidate template. List actual objects and report only those found.
Preserve `input<N>` because one manifest specification can contain multiple
`import_inputs`.

For the latest completed attempt, read `staging_version.txt` and then the exact
`<version>/import_summary.json`. Verify its import and job IDs before using it.
For an older run, use date-scoped summary candidates and stop when one exact job
ID matches. Never list every summary or every object below the import prefix.

List artifacts only below an already selected `<version>/` directory. Summary
status and artifact inventory are separate operations; do not list artifacts
merely to determine status.

## Categories

- Acquisition sources: URLs and source commands in the manifest.
- Raw source artifacts: actual objects below `<version>/source_files/`.
- Import-tool inputs: declared `template_mcf`, `cleaned_csv`, and `node_mcf`
  files copied to the version root when upload is enabled.
- Generated/resolved MCF: actual MCF output below `input<N>/genmcf/`.
- Validation/differ artifacts: actual files below `input<N>/validation/`.

Do not invent a separate unresolved-MCF location. Report legacy/importer-service
resolved or unresolved objects only when the selected deployment and observed
objects prove that path.

## Version pointers

- `staging_version.txt` is written when an attempt reaches summary creation,
  including `VALIDATION` and `SKIP`.
- The configured accepted pointer is currently named by
  `storage_version_filename`, whose repository default is
  `latest_version.txt`. The ingestion helper updates it only for accepted
  `STAGING` data.
- A run that fails before summary creation can update neither pointer.

Resolve configured names and verify the live objects. Do not assume a support
request mentioning `latest.txt` refers to a real object.
