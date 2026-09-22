# Import Differ

Import Differ compares a current dataset with a previous version of the same
dataset. It classifies changed observation and non-observation nodes as
`ADDED`, `DELETED`, or `MODIFIED`. Output field names refer to non-observation
nodes as schema nodes.

The inputs do not need to be produced by a particular tool. Native mode reads
instance MCF files, while direct and cloud modes can also read optimized graph
TFRecord files. See [the MCF format documentation](../../docs/mcf_format.md) for
the general MCF structure.

## Usage

### Prerequisites

- Install the repository's Python dependencies for native runner mode. From the
  repository root, run `./run_tests.sh -r`.
- Direct mode requires Java and `differ-bundled-0.1-SNAPSHOT.jar` beside
  `import_differ.py`; see `<IMPORT_REPO>/pipeline/differ/README.md`.
- Configure Google Cloud Application Default Credentials when using GCS input
  or output paths, or when using cloud runner mode.

Run the command from this directory:

```bash
python3 import_differ.py \
  --current_data=<path> \
  --previous_data=<path> \
  --output_location=<path> \
  --file_format=<mcf/tfrecord> \
  --runner_mode=<native/direct/cloud> \
  --project_id=<id> \
  --job_name=<name>
```

### Parameters

- `current_data`: Path or wildcard for the new dataset. Local and GCS paths are
  supported.
- `previous_data`: Path or wildcard for the baseline dataset. Local and GCS
  paths are supported.
- `output_location`: Local or GCS output directory.
- `file_format`: Input format. Native mode reads MCF. Direct and cloud modes
  support `mcf` and `tfrecord`.
- `runner_mode`: `native` runs the Python/Pandas differ, `direct` runs the Java
  pipeline locally, and `cloud` runs the pipeline in Dataflow.
- `project_id`: Google Cloud project for a cloud runner job.
- `job_name`: Name used for the differ execution. Cloud mode uses it as the
  Dataflow job name.

## Comparison rules

### Observations

An MCF node is treated as an observation when its `typeOf` contains
`StatVarObservation`. Its comparison identity consists of these property
values, in order:

1. `variableMeasured`
2. `observationAbout`
3. `observationDate`
4. `observationPeriod`
5. `measurementMethod`
6. `unit`
7. `scalingFactor`

The `value` property is compared separately. For an observation identity:

- Present only in current data: `ADDED`
- Present only in previous data: `DELETED`
- Present in both with different values: `MODIFIED`
- Present in both with the same value: unchanged and omitted from the diff

Facet properties such as `measurementMethod`, `unit`, and `scalingFactor` are
part of the identity. Observations that differ in any of these properties are
different observation points rather than modifications of one point.

`Node` and `dcid` are not part of an observation's comparison identity.
Observation properties outside the listed identity fields and `value` are not
compared.

### Non-observation nodes

The implementation calls every non-observation node a schema node, including
nodes that are not schema definitions. A non-observation node is identified by
its `dcid` or `Node` value. Its other properties are sorted and combined for
value comparison. Duplicate non-observation comparison rows are removed before
counts and differences are generated.

## Native runner output

Native mode writes `differ_summary.json` and detailed MCF files to
`output_location`.

### `differ_summary.json`

```json
{
  "current_version": "path/to/current",
  "previous_version": "path/to/previous",
  "current_obs_count": 1000,
  "previous_obs_count": 950,
  "current_schema_count": 100,
  "previous_schema_count": 95,
  "added_obs_count": 50,
  "deleted_obs_count": 0,
  "modified_obs_count": 10,
  "added_schema_count": 5,
  "deleted_schema_count": 0,
  "modified_schema_count": 0,
  "obs_diff_count": 60,
  "schema_diff_count": 5
}
```

| Field | Meaning |
| --- | --- |
| `current_version` | The `current_data` path supplied to the differ. |
| `previous_version` | The `previous_data` path supplied to the differ. |
| `current_obs_count` | Observation nodes loaded from the current dataset. |
| `previous_obs_count` | Observation nodes loaded from the previous dataset. |
| `current_schema_count` | Unique non-observation comparison rows in the current dataset. |
| `previous_schema_count` | Unique non-observation comparison rows in the previous dataset. |
| `added_obs_count` | Observation identities found only in the current dataset. |
| `deleted_obs_count` | Observation identities found only in the previous dataset. |
| `modified_obs_count` | Observation identities whose `value` changed. |
| `added_schema_count` | Non-observation nodes found only in the current dataset. |
| `deleted_schema_count` | Non-observation nodes found only in the previous dataset. |
| `modified_schema_count` | Non-observation nodes whose compared properties changed. |
| `obs_diff_count` | Sum of added, deleted, and modified observation counts. |
| `schema_diff_count` | Sum of added, deleted, and modified non-observation counts. |

Observation counts represent individual observation points, not complete time
series.

### Detailed MCF files

> Use a new or empty `output_location`. Import Differ does not remove artifacts
> written by an earlier run.

Each file can contain both observation and non-observation nodes. A file is
created only when the corresponding difference exists.

| File | Contents |
| --- | --- |
| `nodes-added.mcf` | Current-version representation of added nodes. |
| `nodes-deleted.mcf` | Previous-version representation of deleted nodes. |
| `nodes-modified.mcf` | Current-version representation of modified nodes. |
| `nodes-original.mcf` | Previous-version representation of the nodes in `nodes-modified.mcf`. |

## Direct and cloud runner output

Direct and cloud modes invoke the Java/Beam differ. That pipeline writes raw
`obs-diff-*.csv` and `schema-diff-*.csv` files with the comparison key, current
value, previous value, and diff type. The Python wrapper does not convert those
CSV files into the native runner's JSON and MCF artifacts.

See `<IMPORT_REPO>/pipeline/differ/README.md` for the Java pipeline's complete
output contract.

## Auto-refresh integration

For each import input, the auto-refresh executor supplies the candidate's
generated MCF as current data and an accepted version selected by the executor
as previous data. See `<IMPORT_REPO>/docs/usage.md` for how the import tool
produces these particular MCF artifacts. Differ output is written below that
input's `validation` directory. The executor owns version selection; Import
Differ owns the comparison and output artifact contracts.

## Outputs not generated

Import Differ does not persist deletion summaries grouped by StatVar, place, or
StatVar-place. It also does not identify whether an entire time series was
deleted.

`nodes-deleted.mcf` contains the deleted points from the previous dataset. Its
presence, or a large deleted point count, does not by itself prove that a whole
series was deleted. Determining that requires comparing deleted points with the
current dataset using a facet-aware series identity that excludes
`observationDate`.

## Implementation references

- [Native differ and artifact generation](import_differ.py)
- [MCF loading and output helpers](differ_utils.py)
- [Native differ output tests](import_differ_test.py)
- [Auto-refresh invocation](../../import-automation/executor/app/executor/import_executor.py)
