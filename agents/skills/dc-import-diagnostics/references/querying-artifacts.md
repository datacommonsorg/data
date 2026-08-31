# Query import artifacts

Choose an approach based on the artifact format, size, and available local
memory.

| Artifact | Useful approach |
| --- | --- |
| Manageable CSV | Query it locally with DuckDB. |
| Manageable Parquet | Query it directly with DuckDB. |
| Manageable MCF | Convert it to CSV, then query the CSV with DuckDB. |
| Large GCS CSV, Parquet, or Avro | With explicit user approval, load it into a short-lived BigQuery table. |

Use a system temporary directory for local downloads and generated CSV files.
Check the object size before downloading or converting it.

## Query locally

Prefer the DuckDB CLI when it is installed. Otherwise use DuckDB from the
repository Python environment. Query only the columns, aggregations, or sample
rows needed for the investigation.

DuckDB can read CSV and Parquet without first loading them into a persistent
database. For example:

```bash
duckdb -c "SELECT * FROM read_csv_auto('/tmp/input.csv') LIMIT 20;"
duckdb -c "SELECT * FROM read_parquet('/tmp/input.parquet') LIMIT 20;"
```

## Convert MCF to CSV

For an MCF file that fits comfortably in memory, use
[`mcf_file_util.py`](../../../../tools/statvar_importer/mcf_file_util.py):

```bash
./agents/common/run_python.sh tools/statvar_importer/mcf_file_util.py \
  --input_mcf='/tmp/input.mcf' \
  --output_mcf='/tmp/input.csv'
```

The `--output_mcf` flag writes CSV when its filename ends in `.csv`. The
converter loads the MCF nodes into memory before writing the CSV, so memory use
can substantially exceed the input size. Avoid this path when the file does
not fit comfortably in available memory.

## Query with BigQuery

For a large CSV, Parquet, or Avro file already in GCS, consult
[`create_short_lived_bq_table.sh`](../scripts/create_short_lived_bq_table.sh)
with `--help`. The helper loads a native BigQuery table and applies a time to
live.

- Show the user the exact command before running it.
- Run the helper only after the user explicitly approves that command.
- If the table already exists, report its full name and do not alter it.
- Query the table with read-only statements.
- Never update or delete the table. Allow its configured TTL to expire it.

The helper does not accept MCF. If a large MCF cannot be safely converted with
an available repository tool, narrow the artifact or report that efficient
querying requires an unavailable conversion path.
