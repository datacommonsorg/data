# File sharder user guide

`file_sharder` partitions large structured data files into sharded output files. It reads tabular, graph, and serialized records from single files, file patterns, or file lists, and routes each record to an output shard based on a deterministic key hash.

## Table of contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Command-line usage](#command-line-usage)
- [Python API](#python-api)
- [Configuration options](#configuration-options)
- [Progress counters](#progress-counters)
- [Common recipes](#common-recipes)
  - [1. Partition a large CSV by row count](#1-partition-a-large-csv-by-row-count)
  - [2. Route MCF graph nodes into a fixed shard count](#2-route-mcf-graph-nodes-into-a-fixed-shard-count)
  - [3. Read large seekable files with parallel workers](#3-read-large-seekable-files-with-parallel-workers)
  - [4. Transform columns and evaluate expressions](#4-transform-columns-and-evaluate-expressions)
  - [5. Convert observation CSV to MCF with generated DCID and typeOf:StatVarObservation](#5-convert-observation-csv-to-mcf-with-generated-dcid-and-typeofstatvarobservation)
  - [6. Deduplicate records across inputs](#6-deduplicate-records-across-inputs)
  - [7. Deterministic key sampling](#7-deterministic-key-sampling)
- [Limitations](#limitations)

## Overview

The tool provides both a command-line script and a Python class (`FileSharder`). It uses `file_dict_io` to handle multiple input and output formats: CSV, TSV, JSON Lines, Meta Content Framework (MCF), and Apache Avro.

Key capabilities include:

- Sharding by explicit record count or target shard count.
- Deterministic routing by column value, format-specific identifier, or format pattern.
- Multi-threaded parallel input reading, including byte-range chunking for large seekable files.
- Deduplication across worker threads using fingerprint buckets.
- Deterministic key-based record sampling.
- Dynamic column selection and inline Python expression evaluation.
- Automatic DCID generation for Data Commons graph nodes.

## Prerequisites

Run commands with Python 3 from the repository root and set `PYTHONPATH` to include `.` and `util`:

```bash
cd /path/to/data
export PYTHONPATH=".:util"
```

## Command-line usage

Run `file_sharder.py` with `--shard_input` and `--shard_output`:

```bash
python3 util/file_sharder.py \
  --shard_input="/path/to/input.csv" \
  --shard_output="/path/to/output@10.csv" \
  --shard_key="geoId"
```

## Python API

Import and instantiate `FileSharder`, or call the `shard_file` convenience function:

```python
from file_sharder import FileSharder, shard_file

# Using shard_file
shard_file(
    input_file='input.csv',
    output_path='output@5.csv',
    config={
        'shard_key': 'geoId',
        'shard_threads': 4,
    },
)

# Using FileSharder directly with dynamic shard sizing
sharder = FileSharder(
    input_files='input.csv',
    output_path='output@.csv',
    config={
        'shard_key': 'geoId',
        'records_per_shard': 50000,
    },
)
sharder.process()
```

## Configuration options

The table below lists all configuration options. Each option can be passed as a command-line flag or as a key in the `config` dictionary.

| Option | Flag | Type | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `shard_input` | `--shard_input` | `str` | `''` | Input path, glob pattern, comma-separated list, or sharded pattern (`input@10.csv`). |
| `shard_output` | `--shard_output` | `str` | `''` | Output pattern (`output@10.csv`, `output-*.mcf`, or template `shard-{index:05d}-of-{shard_count:05d}.csv`). |
| `shard_key` | `--shard_key` | `str` | `''` | Column or property used to route records. Defaults to `dcid`, then `Node`, then the first header column. Format patterns such as `{geoId}-{year}` are supported. |
| `shard_key_prefix_length` | `--shard_key_prefix_length` | `int` | `0` | If greater than 0, uses only the first N characters of the key string to compute the shard hash. |
| `shard_count` | `--shard_count` | `int` | `0` | Number of output shards. If 0, derived from total estimated records divided by `records_per_shard`. |
| `records_per_shard` | `--records_per_shard` | `int` | `100000` | Target record count per shard when `shard_count` is not explicitly set. |
| `shard_threads` | `--shard_threads` | `int` | `max(1, os.cpu_count() // 2)` | Maximum number of concurrent reader worker threads (defaults to 50% of CPU cores). |
| `shard_min_chunk_size` | `--shard_min_chunk_size` | `int` | `33554432` (32 MB) | Minimum byte size for splitting a large seekable file into concurrent worker chunks. |
| `shard_skip_duplicates` | `--shard_skip_duplicates` | `bool` | `False` | When True, drops duplicate records based on canonical content fingerprint. |
| `shard_sample_rate` | `--shard_sample_rate` | `float` | `1.0` | Fraction of keys to keep in range `[0.0, 1.0]`. Records sharing the same key are kept or dropped together. |
| `shard_input_records` | `--shard_input_records` | `int` | `sys.maxsize` | Upper limit on input records to read before stopping. |
| `shard_headers` | `--shard_headers` | `list` | `[]` | Explicit column headers for output files. |
| `shard_default_pvs` | `--shard_default_pvs` | `str` | `''` | Default property values to fill when missing, separated by semicolons (e.g. `'typeOf:StatVarObservation;unit:Person'`). |
| `shard_add_columns` | `--shard_add_columns` | `str` | `''` | Columns to add or override while keeping non-ignored input columns, separated by semicolons (`<col>` or `<col>=<value_or_expr>`, e.g. `'dcid;typeOf=dcid:StatVarObservation;observationAbout=dcid:geoId/{fips}'`). |
| `shard_output_columns` | `--shard_output_columns` | `str` | `None` | Output columns and transformation expressions separated by semicolons (e.g. `'dcid;*;val=int(raw_val)*2'`). Supports `*` for all non-ignored input columns. |
| `shard_ignore_columns` | `--shard_ignore_columns` | `list` | `[]` | Column names or regular expressions (e.g. `'#input,^#.*,tmp_.*'`) to exclude from output records. For MCF outputs, `#.*` columns are ignored by default. |
| `shard_generate_dcid` | `--shard_generate_dcid` | `bool` | `False` | When True (or when an output record has an empty `dcid`/`Node` column), generates deterministic base32 DCIDs via `util/dcid_generator.py` (replicating `DcidGenerator.java` FarmHash64 `dc/o/<id>` for `StatVarObservation`, assignable IDs for `Place`, `dc/<id>` for `StatisticalVariable`, and SHA-256 base32 `dc/<id>` for general nodes). |
| `shard_dcid_ignore_props`| `--shard_dcid_ignore_props` | `list` | `[]` | Extra property names to exclude when building node DCID keys (e.g. `'value'` to compute value-independent observation DCIDs). |
| `shard_encoding` | `--shard_encoding` | `str` | `None` | Optional character encoding when reading text-based input files. |

## Progress counters

`FileSharder` tracks execution statistics using the `Counters` module. Counters are printed at completion and periodically during execution:

| Counter name | Description |
| :--- | :--- |
| `total` | Estimated total input records. |
| `processed` | Total input records processed so far. |
| `shard-workers` / `workers` | Number of active worker threads allocated. |
| `shard-tasks` | Total number of worker tasks (files and byte-range chunks). |
| `shard-tasks-completed` | Number of worker tasks completed. |
| `shard-seekable-files` | Number of input files eligible for seek-based parallel chunking. |
| `shard-non-seekable-files` | Number of input files requiring single-worker processing. |
| `shard-chunks` | Total chunks generated across all inputs. |
| `shard-input-records` | Number of records read across all inputs. |
| `shard-output-records` | Number of records written across all output shards. |
| `shard-duplicate-dropped` | Number of duplicate records dropped when deduplication is enabled. |
| `shard-sampled-dropped` | Number of records excluded by key sampling. |

## Common recipes

### 1. Partition a large CSV by row count

Partition a large CSV file into output shards containing approximately 50,000 rows each:

```bash
python3 util/file_sharder.py \
  --shard_input="data/raw_data.csv" \
  --shard_output="data/shards/part@.csv" \
  --records_per_shard=50000 \
  --shard_key="geoId"
```

Completion: The command exits with code 0 and produces shards named `data/shards/part-00000-of-NNNNN.csv`. The log prints final reader and writer record counts.

### 2. Route MCF graph nodes into a fixed shard count

Split an MCF dataset into exactly 10 shards. The reader routes records by `Node` or `dcid`:

```bash
python3 util/file_sharder.py \
  --shard_input="data/nodes.mcf" \
  --shard_output="data/shards/nodes@10.mcf" \
  --shard_count=10
```

Completion: Produces exactly 10 files from `nodes-00000-of-00010.mcf` through `nodes-00009-of-00010.mcf`.

### 3. Read large seekable files with parallel workers

When input files are uncompressed and seekable (`.csv`, `.tsv`, `.jsonl`, `.mcf`, `.avro`), specify `--shard_threads` to read different byte offsets of each file concurrently:

```bash
python3 util/file_sharder.py \
  --shard_input="data/large_dataset.csv" \
  --shard_output="data/sharded@16.csv" \
  --shard_threads=8 \
  --shard_min_chunk_size=16777216
```

Completion: Each thread reads a contiguous byte range without reading lines twice or dropping line-start records. The final log displays `shard-workers = 8` and `shard-tasks-completed = shard-tasks`.

### 4. Transform columns and evaluate expressions

Select specific output columns and apply inline Python expressions:

```bash
python3 util/file_sharder.py \
  --shard_input="input.csv" \
  --shard_output="output@4.csv" \
  --shard_output_columns="geoId;year;value=round(float(raw_val)/1000, 2);date=f'{year}-01-01'"
```

Completion: Output shards contain only the specified columns (`geoId`, `year`, `value`, `date`). The counter `shard-output-column-errors` confirms zero expression evaluation failures.

### 5. Convert observation CSV to MCF with generated DCID and typeOf:StatVarObservation

Convert an observation CSV file directly into sharded MCF files by adding `Node` (or `dcid`) and `typeOf=dcid:StatVarObservation` via `--shard_add_columns`. Leaving `Node` (or `dcid`) without a value automatically invokes `dcid_generator.generate_node_dcid`, which generates `DcidGenerator`-compatible `StatVarObservation` DCIDs (`dc/o/<id>` via 64-bit FarmHash). Any `#.*` columns (such as `#input` from `stat_var_processor.py`) are excluded automatically when writing to `.mcf`, and additional helper columns can be dropped with `--shard_ignore_columns`:

```bash
python3 util/file_sharder.py \
  --shard_input="data/observations.csv" \
  --shard_output="data/mcf/obs@10.mcf" \
  --shard_ignore_columns="#input" \
  --shard_add_columns="Node;typeOf=dcid:StatVarObservation"
```

If `observationAbout` or other properties need to be derived from input columns (such as a `fips` column), include format templates or expressions in `--shard_add_columns`:

```bash
python3 util/file_sharder.py \
  --shard_input="data/observations.csv" \
  --shard_output="data/mcf/obs@10.mcf" \
  --shard_ignore_columns="#input,fips" \
  --shard_add_columns="Node;typeOf=dcid:StatVarObservation;observationAbout=dcid:geoId/{fips}"
```

For an input CSV row:

```csv
#input,observationAbout,variableMeasured,observationDate,value,observationPeriod,unit,measurementMethod,scalingFactor
row1,dcid:geoId/06001,dcid:Count_Person,2017-01,1000,P1M,$,CACensus,100
```

This writes the MCF node:

```mcf
Node: dcid:dc/o/3mptcb1vdfvr5
typeOf: dcid:StatVarObservation
observationAbout: dcid:geoId/06001
variableMeasured: dcid:Count_Person
observationDate: 2017-01
value: 1000
observationPeriod: dcid:P1M
unit: dcid:$
measurementMethod: dcid:CACensus
scalingFactor: 100
```

Completion: Produces sharded `.mcf` files with `Node: dcid:dc/o/...` generated using `util/dcid_generator.py` (matching `DcidGenerator.forStatVarObs` in `datacommonsorg/import`), omitting `#input` and any ignored columns.

### 6. Deduplicate records across inputs

Drop duplicate rows or graph nodes across multiple files using content fingerprinting:

```bash
python3 util/file_sharder.py \
  --shard_input="data/file1.csv,data/file2.csv" \
  --shard_output="data/deduped@4.csv" \
  --shard_skip_duplicates=True
```

Completion: Outputs contain unique records only. Counter `shard-duplicate-dropped` reports the total number of duplicate records removed.

### 7. Deterministic key sampling

Keep a random sample of 10% of entities while ensuring all observations for a selected entity stay together:

```bash
python3 util/file_sharder.py \
  --shard_input="data/observations.csv" \
  --shard_output="data/sample@2.csv" \
  --shard_key="geoId" \
  --shard_sample_rate=0.10
```

Completion: Counter `shard-sampled-dropped` reflects excluded keys. Kept records are distributed across `sample-00000-of-00002.csv` and `sample-00001-of-00002.csv`.

## Limitations

- **Compressed files process with a single worker per file.** Compressed formats (`.gz`, `.bz2`, `.zst`, `.zip`, `.tgz`, `.tar`) do not support random byte seeking. The sharder allocates one worker thread per compressed file.
- **JSON Lists process as single files.** Standard `.json` containing a single root array or object does not support line-based byte seeking. Convert inputs to JSON Lines (`.jsonl`, `.ndjson`) to enable multi-threaded byte-range chunking.
- **Shard output order is hash-partitioned.** Records route to shards by key hash. Within each output shard, records appear in arrival order rather than sorted key order.
- **Output expressions use a restricted `eval()` environment.** Expressions in `shard_output_columns` and `shard_add_columns` run through `eval_functions.evaluate_statement` with input columns as variables, standard Python builtins (`int`, `float`, `round`, `str`, `len`), and `eval_functions` helpers (`format_date`, `str_to_camel_case`, `datetime_strptime`, `relativedelta`, `re_sub`, `generate_node_dcid`, `generate_statvar_obs_dcid`, `generate_place_dcid`, `generate_statvar_hash_dcid`).
